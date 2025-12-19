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

"""
Define functions to perform gradient tests to check the coherence between an
function and its gradient.

The gradient test principle is to compare the result of a **computed** and estimated
gradient from a :class:`~physioblocks.computing.assembling.EqSystem` object.
"""

from __future__ import annotations

import logging
from os import linesep
from typing import Any

import numpy as np
from numpy.typing import NDArray
from scipy.optimize import approx_fprime

import physioblocks.simulation.setup as setup
from physioblocks.computing.assembling import EqSystem
from physioblocks.computing.models import Block, Expression, ModelComponent
from physioblocks.configuration.aliases import unwrap_aliases
from physioblocks.configuration.functions import load
from physioblocks.io.configuration import read_json
from physioblocks.simulation.runtime import AbstractSimulation
from physioblocks.simulation.state import State

_logger = logging.getLogger(__name__)

_ZERO = 1e-16
_REL_TOL = 1e-6
_NEW_STATE_SHIFT_FACTOR = 1e-3
_SHIFT_FACTOR = 1e-4
_CONVERGENCE_FACTOR = 0.1
_CONVERGENCE_TOL = 0.11


def gradient_test_from_file(config_file_path: str) -> bool:
    """
    Read the given configuration file and perform a gradient test on the full Net
    with the provided parameters and variables.

    .. warning::

        Every type (especially **Blocks**, **ModelComponents** and **Functions**) and
        alias used in the configuration file have to be loaded.
        Follow this
        :ref:`user guide section <user_guide_level_3_block_test_dynamic_import>`
        to import libraries and aliases dynamically.

    :param config_file_path: the file path to the simulation configuration file.
    :type config_file_path: str

    :return: True if the gradient test is successfull, false otherwise.
    """
    configuration = read_json(config_file_path)
    configuration = unwrap_aliases(configuration)
    sim: AbstractSimulation = load(configuration)
    sim._initialize()  # noqa SLF001
    return gradient_test(
        sim.eq_system,
        sim.state,
        sim.solver._get_state_magnitude(sim.state, sim.magnitudes),  # noqa: SLF001
    )


def gradient_test_from_model(
    model: ModelComponent, state: State, state_magnitude: NDArray[np.float64]
) -> bool:
    """
    Create an equation system for the given block only and perform a gradient test.

    .. note::

        It does not test the submodels of the model.

    :param model: the model to test.
    :type model: str

    :param state: the state used to determine the variables in the model.
    :type state: str

    :param state_magnitude: the state variables magnitudes
    :type state_magnitude: str

    :return: True if the gradient test is successfull, false otherwise.
    """
    line_index = 0
    expressions = setup.SystemExpressions()
    for internal_expr_def in type(model).internal_expressions:
        expressions.append((line_index, internal_expr_def.expression, model))
        line_index += internal_expr_def.expression.size

    if isinstance(model, Block):
        for fluxes_expr_def in type(model).fluxes_expressions.values():
            expressions.append((line_index, fluxes_expr_def.expression, model))
            line_index += fluxes_expr_def.expression.size

    eq_system = setup.build_eq_system(expressions, state)
    model.initialize()
    return gradient_test(eq_system, state, state_magnitude)


def gradient_test_from_expression(
    expr: Expression,
    expr_params: Any,
    state: State,
    state_magnitude: NDArray[np.float64],
) -> bool:
    """
    Create an equation system for the given expression only and perform a gradient test.

    :param expr: the expression to test.
    :type expr: Expression

    :param expr_params: the parameters to pass to the expression
    :type expr_params: Any

    :param state: the state used to determine the variables in the expression.
    :type state: str

    :param state_magnitude: the state variables magnitudes
    :type state_magnitude: str

    :return: True if the gradient test is successfull, false otherwise.
    :rtype: bool
    """

    eq_system = setup.build_eq_system([(0, expr, expr_params)], state)
    return gradient_test(eq_system, state, state_magnitude)


def gradient_test(
    eq_system: EqSystem, state: State, state_magnitude: NDArray[np.float64]
) -> bool:
    """
    Test the computed gradient for the equation system by comparing it to
    a gradient estimated with finite differences.

    :param eq_system: the equation system providing method to compute a residual and a
      gradient
    :type eq_system: EqSystem

    :param state: system state
    :type state: State

    :param state_magnitude: the state variables magnitudes
    :type state_magnitude: str

    :return: True if the estimated and computed gradient meet tolerance,
      False otherwise.
    """

    _logger.info(str.format("State:{0}{1}", linesep, state))
    _logger.info(str.format("System:{0}{1}", linesep, eq_system))

    new_state = state.state_vector + _NEW_STATE_SHIFT_FACTOR * state_magnitude

    shift_1 = _SHIFT_FACTOR * state_magnitude
    state.update_state_vector(new_state)

    res = eq_system.compute_residual()
    grad = eq_system.compute_gradient()

    grad_estimated_1 = _estimate_gradient(eq_system, shift_1, state)

    shift_2 = _CONVERGENCE_FACTOR * shift_1
    state.update_state_vector(new_state)
    grad_estimated_2 = _estimate_gradient(eq_system, shift_2, state)

    state.update_state_vector(new_state)

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
            "Variable Id: {0}.{1}", state.get_variable_id(col_error), linesep
        )
        _logger.debug(error_msg_line)

        error_msg_line = str.format("Residual Index: {0}.{1}{1}", line_error, linesep)
        _logger.debug(error_msg_line)

    if len(grad_error_pos) != 0:
        raise GradientError(error_message)

    return len(grad_error_pos) == 0


def _estimate_gradient(
    eq_system: EqSystem, shift: NDArray[np.float64], state: State
) -> NDArray[np.float64]:
    """
    Gradient finite difference estimation

    :param eq_system: the equation system providing method to compute a residual
      and a gradient
    :type eq_system: EqSystem

    :param shift_factor: the shift factor to apply on the state (can be 0).
      It is multiplied with the variables magnitude then added to the state.
    :type shift_factor: NDArray

    :param state: system state
    :type state: State
    """

    def residual(x: NDArray[np.float64]) -> NDArray[np.float64]:
        state.update_state_vector(x)
        res = eq_system.compute_residual()

        return res

    x0 = state.state_vector
    grad_est = np.atleast_2d(approx_fprime(x0, residual, shift))

    return grad_est


def get_errors_gradient(
    computed: NDArray[np.float64],
    estimated_1: NDArray[np.float64],
    estimated_2: NDArray[np.float64],
) -> list[tuple[int, int]]:
    """
    Get the ``(line, column)`` positions of the errors in the gradient matrix.

    :param computed: computed gradient
    :type computed: NDArray[np.float64]

    :param estimated_1: first gradient estimate
    :type estimated_1: NDArray[np.float64]

    :param estimated_2: second gradient estimate
    :type estimated_2: NDArray[np.float64]

    :return: the position of the errors in the gradient matrix
    :rtype: list[tuple[int, int]]
    """
    abs_computed = np.abs(computed)

    error_1 = np.empty(computed.shape)
    error_1[:] = np.inf
    error_2 = error_1.copy()

    for grad_line in range(0, computed.shape[0]):
        for grad_col in range(0, computed.shape[1]):
            if abs_computed[grad_line, grad_col] < _ZERO:
                error_1[grad_line, grad_col] = (
                    np.abs(
                        computed[grad_line, grad_col] - estimated_1[grad_line, grad_col]
                    )
                    / _ZERO
                )
                error_2[grad_line, grad_col] = (
                    np.abs(
                        computed[grad_line, grad_col] - estimated_2[grad_line, grad_col]
                    )
                    / _ZERO
                )
            else:
                error_1[grad_line, grad_col] = (
                    np.abs(
                        computed[grad_line, grad_col] - estimated_1[grad_line, grad_col]
                    )
                    / abs_computed[grad_line, grad_col]
                )
                error_2[grad_line, grad_col] = (
                    np.abs(
                        computed[grad_line, grad_col] - estimated_2[grad_line, grad_col]
                    )
                    / abs_computed[grad_line, grad_col]
                )

    with np.printoptions(precision=9, linewidth=10000, suppress=False):
        _logger.debug(str.format("Error:{0}{1}", error_1, linesep))

    error_positions = []

    for grad_line in range(0, computed.shape[0]):
        for grad_col in range(0, computed.shape[1]):
            if error_1[grad_line, grad_col] > _REL_TOL:
                err_div = error_2[grad_line, grad_col] / error_1[grad_line, grad_col]
                if err_div > _CONVERGENCE_TOL:
                    error_positions.append((grad_line, grad_col))
            elif np.isnan(error_1[grad_line, grad_col]):
                error_positions.append((grad_line, grad_col))

    return error_positions


class GradientError(Exception):
    """Error raised when the estimated and computed gradients do not match."""

    pass
