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

"""Declare a generic solver class and solver implementations."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from physioblocks.computing.assembling import EqSystem
from physioblocks.computing.quantities import QuantitiesRegistry
from physioblocks.registers.type_register import register_type
from physioblocks.utils.exceptions_utils import log_exception

_logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Solution:
    """Represent the solution returned by a solver.

    Parameters
    ----------
    x : NDArray[np.float64]
        the actual solution
    converged : bool
        get if the solver converged.

    """

    x: NDArray[np.float64]

    converged: bool


class ConvergenceError(Exception):
    """Error raised when the solver did not converge."""


class AbstractSolver(ABC):
    """Base class for solvers.

    Attributes
    ----------
    iteration_max : int
        the solver maximum allowed number of iterations. Default is 10.
    tolerance : float
        the solver tolerance. Default is 1e-9.

    """

    iteration_max: int

    tolerance: float

    def __init__(
        self,
        tolerance: float = 1e-9,
        iteration_max: int = 10,
    ) -> None:
        self.tolerance = tolerance
        self.iteration_max = iteration_max

    @abstractmethod
    def solve(self, state: QuantitiesRegistry, system: EqSystem) -> Solution:
        """Child classes have to override this method.

        Parameters
        ----------
        state : QuantitiesRegistry
            the state holding the system variables
        system : EqSystem
            the equation system to solve

        Returns
        -------
        Solution
            the solution of the solver

        """


LINEAR_SOLVER = "linear_solver"


@register_type(LINEAR_SOLVER)
class LinearSolver(AbstractSolver):
    """Implementation of the :class:`~.AbstractSolver` class for linear problems.

    Configuration
    -------------

    .. code-block:: json

        {
            "type": "linear_solver"
        }

    """

    def solve(self, state: QuantitiesRegistry, system: EqSystem) -> Solution:
        """Solve the equation system directly.

        Parameters
        ----------
        state : QuantitiesRegistry
            the state holding the system variables
        system : EqSystem
            the equation system to solve

        Returns
        -------
        Solution
            the solution

        """
        res = system.compute_residual()
        grad = system.compute_gradient()

        xn = np.linalg.solve(grad, res)
        x = state.vector - xn

        return Solution(x, True)


# Type id for the Newton Solver
NEWTON_SOLVER_TYPE_ID = "newton_solver"


@register_type(NEWTON_SOLVER_TYPE_ID)
class NewtonSolver(AbstractSolver):
    """Newton method solver implementation.

    Configuration
    -------------

    .. code-block:: json

        {
            "type": "newton_solver",
            "tolerance": "<float>",   // Tolerance of the stop criteria, relative
                                      // to each variable magnitude
                                      // (optional, default: 1e-9)
            "iteration_max": "<int>"  // Maximum number of iterations
                                      // (optional, default: 10)
        }

    """

    def _compute_residual_and_gradient(
        self, system: EqSystem
    ) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
        res = system.compute_residual()
        grad = system.compute_gradient()
        return res, grad

    def _compute_new_state(
        self,
        state: QuantitiesRegistry,
        res: NDArray[np.float64],
        grad: NDArray[np.float64],
        state_mag: NDArray[np.float64],
    ) -> NDArray[np.float64]:
        res_grad_sol = np.linalg.solve(grad, res)
        x = state.vector - res_grad_sol * state_mag
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

    def solve(self, state: QuantitiesRegistry, system: EqSystem) -> Solution:
        """Solve the equation system using the Newton method.

        Parameters
        ----------
        state : QuantitiesRegistry
            the state holding the system variables
        system : EqSystem
            the equation system to solve

        Returns
        -------
        Solution
            the solution

        """
        with np.errstate(all="raise"):
            try:
                i = 0
                # initialize residual and magnitude
                res = np.ones(state.vector.shape)

                # step 0 outside of the loop to compute the residual and gradient
                # magnitude
                res, grad = self._compute_residual_and_gradient(system)
                res_mag_inv, grad_mag_inv = self._compute_res_grad_mag(
                    grad, state.magnitudes_vector
                )
                res, grad = self._rescale_res_grad(res, res_mag_inv, grad, grad_mag_inv)
                x = self._compute_new_state(state, res, grad, state.magnitudes_vector)
                state.update_vector(x)

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
                    x = self._compute_new_state(
                        state, res, grad, state.magnitudes_vector
                    )
                    state.update_vector(x)
                    i += 1

                sol = Solution(
                    state.vector,
                    (
                        bool(np.linalg.norm(res, ord=np.inf) <= self.tolerance)
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
