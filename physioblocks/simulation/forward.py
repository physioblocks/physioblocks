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

"""Declare classes to run forward simulations."""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
from numpy.typing import NDArray

from physioblocks.registers.type_register import register_type
from physioblocks.simulation.base import (
    AbstractSimulation,
    SimulationModel,
)
from physioblocks.simulation.solvers import ConvergenceError

_logger = logging.getLogger(__name__)


def solve_step(sim_model: SimulationModel, min_step: float) -> NDArray[np.float64]:
    """Solve the current simulation model step.

    Solve the new simulation model state, set it to the solution and advance the
    simulation time step.

    Use continuation algorithm to update the step when no solution is found.

    Parameters
    ----------
    sim_model : SimulationModel
        the simulation model to update
    min_step : float
        the minimum step for the continuation algorithm

    Returns
    -------
    NDArray[np.float64]
        the state value for the target step

    Raises
    ------
    ConvergenceError
        if no solution is found for the given step

    """
    start_state = sim_model.state.vector
    start_step = sim_model.time_manager.time.current
    next_step = sim_model.time_manager.time.new
    current_step_size = sim_model.time_manager.step_size
    while current_step_size >= min_step:
        sim_model.state.reset_vector()
        solution = sim_model.solver.solve(sim_model.state, sim_model.equation_system)

        if solution.converged is False:
            # smaller time step
            current_step_size = 0.5 * current_step_size
            sim_model.time_manager.time.update(
                sim_model.time_manager.time.current + current_step_size
            )
        elif sim_model.time_manager.time.new < next_step:
            # we solved a subdivision, solve the next
            current_step_size = next_step - sim_model.time_manager.time.new
            sim_model.time_manager.time.initialize(sim_model.time_manager.time.new)
            sim_model.time_manager.time.update(next_step)
            sim_model.state.set_vector(solution.x)
        else:
            # the step is solved
            sim_model.state.set_vector(start_state)
            sim_model.state.update_vector(solution.x)

            # restore time manager
            sim_model.time_manager.time.initialize(start_step)
            sim_model.time_manager.time.update(next_step)

            return solution.x

    raise ConvergenceError(
        "The solver did not converge at step "
        f"{start_step} for "
        f"minimal time step {min_step}",
    )


FORWARD_SIM_ID = "forward_simulation"
"""Forward simulation type id"""


@register_type(FORWARD_SIM_ID)
class ForwardSimulation(AbstractSimulation):
    """Extend :class:`~.AbstractSimulation` class to define a **Forward Simulation**.

    Solve the **Equation System** at each time step using
    the simulation **Solver**.

    If the solver did not converge at a given time step, it breaks the current time
    step into smaller steps and tries again.
    If it still does not converge, it recursively breaks the current time step again and
    stops if the time step is under the minimum time step allowed.

    When finding a solution for a reduced time step, the simulation
    then tries to solve for the remaining time interval in the current time step.

    .. note::

        When breaking a simulation step, the forward simulation still only provides a
        result for the time step interval given to the time manager.

    Parameters
    ----------
    min_step : float
        Minimum step_size allowed for the continuation algorithm.
        Default is the simulation step size (i.e. there is no continuation
        algorithm)

    Configuration
    -------------

    .. code-block:: json

        {
            "type": "forward_simulation",
            "simulation_name": "<str>",        // Simulation name
                                               // (optional, default: "main")
            "net": "<net type>",               // The simulation net
            "solver": "<solver type>",         // The solver
                                               // (optional, default: newton_solver)
            "time": "<range type>",            // The simulation time range
            "parameters": {                    // Initialization of each parameter
                "<str>": "<float | initialization function type>"
            },
            "state": {                         // Initialization of each state
                "<str>": "<quantity type>"     // variable
            },
            "update_functions": {              // Function updating each parameter at
                "<str>": "<function type>"     // each time step (optional)
            },
            "output_functions": {              // Function computing each additional
                "<str>": "<function type>"     // output (optional)
            },
            "data": {                          // Input data for the processes
                "<str>": "<data reader type>"  // (optional)
            },
            "preprocesses": {                  // Processes run before the simulation
                "<str>": "<process type>"      // (optional)
            },
            "postprocesses": {                 // Processes run after the simulation
                "<str>": "<process type>"      // (optional)
            },
            "plots": {                         // Plots traced by the launcher
                "<str>": "<plot type>"         // (optional)
            },
            "simulation_options": {
                "min_step": "<float>"          // Minimum step of the continuation
                                               // algorithm (optional, default: no
                                               // continuation)
            }
        }

    See the :mod:`~physioblocks.library.aliases.simulations` module for forward
    simulation aliases.

    """

    def __init__(self, min_step: float | None = None, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self.min_step = (
            min_step
            if min_step is not None
            else self.simulation_model.time_manager.step_size
        )

    def run_step(self) -> None:
        """Run a single simulation step."""
        self.simulation_model.update_functions_parameters()
        new_state = solve_step(self.simulation_model, self.min_step)
        self.simulation_model.state.set_vector(new_state)
        self.simulation_model.time_manager.update()
