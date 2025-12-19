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

"""Declare a generic **Solver** class and solver implementations"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from physioblocks.computing.assembling import EqSystem
from physioblocks.registers.type_register import register_type
from physioblocks.simulation.state import State
from physioblocks.utils.exceptions_utils import log_exception

_logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Solution:
    """
    Represent the solution return by a solver.
    """

    x: NDArray[np.float64]
    """the actual solution"""

    converged: bool
    """get if the solver converged."""


class ConvergenceError(Exception):
    """
    Error raised when the solver did not converged.
    """


class AbstractSolver(ABC):
    """
    Base class for solvers.
    """

    iteration_max: int
    """the solver maximum allowed number of iterations"""

    tolerance: float
    """the solver tolerance"""

    def __init__(
        self,
        tolerance: float = 1e-9,
        iteration_max: int = 10,
    ) -> None:
        self.tolerance = tolerance
        self.iteration_max = iteration_max

    def _get_state_magnitude(
        self, state: State, magnitudes: dict[str, float] | None = None
    ) -> NDArray[np.float64]:
        if magnitudes is None:
            return np.ones(
                state.size,
            )

        mag_dict = {}
        for var_mag_key, var_mag_value in magnitudes.items():
            var_index = state.get_variable_index(var_mag_key)
            mag_dict[var_index] = var_mag_value
        sorted_mag = sorted(mag_dict.items())
        state_mag_list = [x[1] for x in sorted_mag]
        return np.array(
            state_mag_list,
        )

    @abstractmethod
    def solve(
        self,
        state: State,
        system: EqSystem,
        magnitudes: dict[str, float] | None = None,
    ) -> Solution:
        """
        Child classes have to override this method

        :return: the solution of the solver
        :rtype: _Array
        """


# Type id for the Newton Solver
NEWTON_SOLVER_TYPE_ID = "newton_solver"


@register_type(NEWTON_SOLVER_TYPE_ID)
class NewtonSolver(AbstractSolver):
    """
    Implementation of the :class:`~.AbstractSolver` class using a **Newton method**.
    """

    def _compute_residual_and_gradient(
        self, system: EqSystem
    ) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
        res = system.compute_residual()
        grad = system.compute_gradient()
        return res, grad

    def _compute_new_state(
        self,
        state: State,
        res: NDArray[np.float64],
        grad: NDArray[np.float64],
        state_mag: NDArray[np.float64],
    ) -> NDArray[np.float64]:
        res_grad_sol = np.linalg.solve(grad, res)
        x = state.state_vector - res_grad_sol * state_mag
        return x

    def _compute_res_grad_mag(
        self, gradient: NDArray[np.float64], state_mag: NDArray[np.float64]
    ) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
        state_mag_line = np.atleast_2d(state_mag)
        state_mag_col = state_mag_line.T

        res_mag = gradient @ state_mag_col
        abs_res_mag = np.abs(res_mag)
        res_mag_inv = 1.0 / abs_res_mag

        grad_mag_inv = res_mag_inv @ state_mag_line
        return res_mag_inv.flatten(), grad_mag_inv

    def _rescale_res_grad(
        self,
        residual: NDArray[np.float64],
        res_mag_inv: NDArray[np.float64],
        gradient: NDArray[np.float64],
        grad_mag_inv: NDArray[np.float64],
    ) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
        res_rescaled = residual * res_mag_inv
        grad_rescaled = gradient * grad_mag_inv
        return res_rescaled, grad_rescaled

    def solve(
        self,
        state: State,
        system: EqSystem,
        magnitudes: dict[str, float] | None = None,
    ) -> Solution:
        """
        Solve the equation system using the Newton method.

        :return: the solution
        :rtype: Solution
        """

        with np.errstate(all="raise"):
            try:
                i = 0
                # initialize residual and magnitude
                state_mag = self._get_state_magnitude(state, magnitudes)
                res = np.ones(state.state_vector.shape)

                # step 0 outside ou the loop to compute the residual and gradient
                # magnitude
                res, grad = self._compute_residual_and_gradient(system)
                res_mag_inv, grad_mag_inv = self._compute_res_grad_mag(grad, state_mag)
                res, grad = self._rescale_res_grad(res, res_mag_inv, grad, grad_mag_inv)
                x = self._compute_new_state(state, res, grad, state_mag)
                state.update_state_vector(x)

                # Begin loop at iteration 1 (0 already done)
                i = 1
                while (
                    np.linalg.norm(res, ord=np.inf) > self.tolerance
                    and i < self.iteration_max
                ):
                    res, grad = self._compute_residual_and_gradient(system)
                    res, grad = self._rescale_res_grad(
                        res, res_mag_inv, grad, grad_mag_inv
                    )
                    x = self._compute_new_state(state, res, grad, state_mag)
                    state.update_state_vector(x)
                    i += 1

                sol = Solution(
                    state.state_vector,
                    (
                        bool(np.linalg.norm(res) <= self.tolerance)
                        and (True in np.isnan(x) or True in np.isinf(x)) is False
                    ),
                )
            except FloatingPointError as exception:
                _logger.debug(
                    str.format(
                        "Solver did not converge at step {0} due to floating "
                        "point error. The solved property is set to False.",
                        i,
                    )
                )
                log_exception(
                    _logger,
                    FloatingPointError,
                    exception,
                    exception.__traceback__,
                    logging.DEBUG,
                )
                return Solution(np.empty(state.size), False)

        return sol
