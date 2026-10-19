# SPDX-FileCopyrightText: Copyright INRIA
#
# SPDX-License-Identifier: LGPL-3.0-only
#
# Copyright INRIA
#
# This file is part of PhysioBlocks, a library mostly developed by the
# [Ananke project-team](https://team.inria.fr/ananke) at INRIA.
#
# Authors:
# - Colin Drieu
# - Dominique Chapelle
# - François Kimmig
# - Philippe Moireau
#
# PhysioBlocks is free software: you can redistribute it and/or modify it under the
# terms of the GNU Lesser General Public License as published by the Free Software
# Foundation, version 3 of the License.
#
# PhysioBlocks is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE. See the GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License along with
# PhysioBlocks. If not, see <https://www.gnu.org/licenses/>.

"""Define functions to check the gradient coherence with residual.

The gradient test principle is to compare the result of a **computed** and estimated
gradient from a :class:`~.EqSystem` object.
"""

from __future__ import annotations

import logging
import warnings
from os import linesep
from typing import Any

import numpy as np
from numpy.typing import NDArray
from scipy.optimize import approx_fprime

import physioblocks.simulation.base as base
from physioblocks.computing.assembling import EqSystem
from physioblocks.computing.models import Block, Expression, ModelComponent
from physioblocks.computing.quantities import QuantitiesRegistry
from physioblocks.configuration.aliases import unwrap_aliases
from physioblocks.configuration.functions import load
from physioblocks.io.configuration import read_json
from physioblocks.simulation.base import SystemExpression

_logger = logging.getLogger(__name__)

_ZERO = 1e-16
_REL_TOL = 1e-6
_NEW_STATE_SHIFT_FACTOR = 1e-3
_SHIFT_FACTOR = 1e-4
_CONVERGENCE_FACTOR = 0.1
_CONVERGENCE_TOL = 0.11


def gradient_test_from_file(config_file_path: str) -> bool:
    """Create an :class:`~.EqSystem` from the configuration and check its gradient.

    .. warning::

        Every type (especially **Blocks**, **ModelComponents** and **Functions**) and
        alias used in the configuration file have to be loaded.
        Follow this
        :ref:`user guide section <user_guide_level_3_block_test_dynamic_import>`
        to import libraries and aliases dynamically.

    Parameters
    ----------
    config_file_path : str
        the file path to the simulation configuration file.

    Returns
    -------
    bool
        True if the gradient test is successful, false otherwise.

    """
    configuration = read_json(config_file_path)
    configuration = unwrap_aliases(configuration)
    model_factory: base.SimulationModelFactory = load(configuration)
    sim_model = model_factory.create_simulation_model()
    return gradient_test(sim_model.equation_system, sim_model.state)


def gradient_test_from_model(model: ModelComponent, state: QuantitiesRegistry) -> bool:
    """Create an equation system for the given model only and perform a gradient test.

    .. note::

        It does not test the submodels of the model.

    Parameters
    ----------
    model : ModelComponent
        the model to test.
    state : QuantitiesRegistry
        the state used to determine the variables in the model.

    Returns
    -------
    bool
        True if the gradient test is successful, false otherwise.

    """
    line_index = 0
    expressions: list[SystemExpression] = []
    for internal_expr in type(model).internal_expressions:
        expressions.append(SystemExpression(line_index, internal_expr, model))
        line_index += internal_expr.size

    if isinstance(model, Block):
        for fluxes_expr in type(model).fluxes_expressions.values():
            expressions.append(SystemExpression(line_index, fluxes_expr, model))
            line_index += fluxes_expr.size

    eq_system = base.build_eq_system(expressions, state)
    model.initialize()
    return gradient_test(eq_system, state)


def gradient_test_from_expression(
    expr: Expression, expr_params: Any, state: QuantitiesRegistry
) -> bool:
    """Create an :class:`~.EqSystem` for the expression and check its gradient.

    Parameters
    ----------
    expr : Expression
        the expression to test.
    expr_params : Any
        the parameters to pass to the expression
    state : QuantitiesRegistry
        the state used to determine the variables in the expression.

    Returns
    -------
    bool
        True if the gradient test is successful, false otherwise.

    """
    eq_system = base.build_eq_system([SystemExpression(0, expr, expr_params)], state)
    return gradient_test(eq_system, state)


def gradient_test(
    eq_system: EqSystem, state: QuantitiesRegistry, raise_error: bool = True
) -> bool:
    """Check system gradient against an estimation.

    Estimate the system gradient with finite differences, then compare it to the
    gradient computed directly.

    Parameters
    ----------
    eq_system : EqSystem
        the equation system providing method to compute a residual and a
        gradient
    state : QuantitiesRegistry
        system state
    raise_error : bool
        when set to true, raise a :class:`GradientError` instead of returning
        false. Default is True.

    Returns
    -------
    bool
        True if the estimated and computed gradient meet tolerance,
        False otherwise.

    Raises
    ------
    GradientError
        if the estimated and the computed gradient do not match,
        and ``raise_error`` is set to True

    """
    _logger.info(str.format("State:{0}{1}", linesep, state))
    _logger.info(str.format("System:{0}{1}", linesep, eq_system))

    new_state = state.vector + _NEW_STATE_SHIFT_FACTOR * state.magnitudes_vector

    shift_1 = _SHIFT_FACTOR * state.magnitudes_vector
    state.update_vector(new_state)

    res = eq_system.compute_residual()
    grad = eq_system.compute_gradient()

    grad_estimated_1 = _estimate_gradient(eq_system, shift_1, state)

    shift_2 = _CONVERGENCE_FACTOR * shift_1
    state.update_vector(new_state)
    grad_estimated_2 = _estimate_gradient(eq_system, shift_2, state)

    state.update_vector(new_state)

    with np.printoptions(precision=9, linewidth=10000, suppress=True):
        _logger.debug(str.format("Residual:{0}{1}", linesep, res))
        _logger.debug(str.format("Gradient{0}{1}", linesep, grad))
        _logger.debug(
            str.format("Gradient Estimated:{0}{1}", linesep, grad_estimated_1)
        )

    grad_error_pos = get_errors_gradient(grad, grad_estimated_1, grad_estimated_2)

    error_message = str.format("State:{0}{1}", linesep, state)
    error_message += str.format("System:{0}{1}{0}{0}", linesep, eq_system)

    for line_error, col_error in grad_error_pos:
        error_msg_line = str.format(
            "Error in gradient at ({0},{1}).{2}", line_error, col_error, linesep
        )
        _logger.debug(error_msg_line)
        error_message += error_msg_line

        error_msg_line = str.format(
            "Variable Id: {0}.{1}", state.get_quantity_id(col_error), linesep
        )
        _logger.debug(error_msg_line)

        error_msg_line = str.format("Residual Index: {0}.{1}{1}", line_error, linesep)
        _logger.debug(error_msg_line)

    if raise_error and len(grad_error_pos) != 0:
        raise GradientError(error_message)

    return len(grad_error_pos) == 0


def _estimate_gradient(
    eq_system: EqSystem, shift: NDArray[np.float64], state: QuantitiesRegistry
) -> Any:
    """Gradient finite difference estimation.

    Parameters
    ----------
    eq_system : EqSystem
        the equation system providing method to compute a residual
        and a gradient
    shift : NDArray[np.float64]
        the finite difference step for each variable of the state.
    state : QuantitiesRegistry
        system state

    Returns
    -------
    Any
        the estimated gradient matrix

    """

    def residual(x: NDArray[np.float64]) -> NDArray[np.float64]:
        state.update_vector(x)
        res = eq_system.compute_residual()

        return res

    x0 = state.vector
    grad_est = np.atleast_2d(approx_fprime(x0, residual, shift))

    return grad_est


def get_errors_gradient(
    computed: NDArray[np.float64],
    estimated_1: NDArray[np.float64],
    estimated_2: NDArray[np.float64],
) -> list[tuple[int, int]]:
    """Get the ``(line, column)`` positions of the errors in the gradient matrix.

    Parameters
    ----------
    computed : NDArray[np.float64]
        computed gradient
    estimated_1 : NDArray[np.float64]
        first gradient estimate
    estimated_2 : NDArray[np.float64]
        second gradient estimate

    Returns
    -------
    list[tuple[int, int]]
        the position of the errors in the gradient matrix

    """
    abs_computed = np.abs(computed)
    abs_computed[abs_computed < _ZERO] = _ZERO

    error_1 = np.abs(computed - estimated_1) / abs_computed
    error_2 = np.abs(computed - estimated_2) / abs_computed

    with np.printoptions(precision=9, linewidth=10000, suppress=False):
        _logger.debug(str.format("Error:{0}{1}", error_1, linesep))

    with warnings.catch_warnings():
        # Filter the occasional invalid value or division by zero warnings.
        # It is expected that error has values set to nan or 0.0.
        warnings.filterwarnings("ignore", category=RuntimeWarning)
        err_div = error_2 / error_1

    error_mask = (
        (error_1 > _REL_TOL) & (err_div > _CONVERGENCE_TOL) & (~np.isnan(err_div))
    )
    error_mask |= np.isnan(error_1)

    error_positions = [(line, col) for line, col in np.argwhere(error_mask)]

    return error_positions


class GradientError(Exception):
    """Error raised when the estimated and computed gradients do not match."""

    pass
