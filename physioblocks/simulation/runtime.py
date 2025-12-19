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
Defines the **Simulation** classes that define how the simulations runs
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import Any, TypeAlias

import numpy as np
from numpy.typing import NDArray

from physioblocks.computing.assembling import EqSystem
from physioblocks.computing.models import ModelComponent
from physioblocks.computing.quantities import Quantity
from physioblocks.registers.type_register import register_type
from physioblocks.simulation.functions import (
    AbstractFunction,
    is_state_function,
    is_time_function,
)
from physioblocks.simulation.saved_quantities import SavedQuantities
from physioblocks.simulation.solvers import AbstractSolver, ConvergenceError
from physioblocks.simulation.state import STATE_NAME_ID, State
from physioblocks.simulation.time_manager import TIME_QUANTITY_ID, TimeManager
from physioblocks.utils.exceptions_utils import log_exception

Parameters: TypeAlias = dict[str, Quantity[Any]]
"""Type alias for quantities collection"""

Result: TypeAlias = dict[str, np.float64 | NDArray[np.float64]]
"""Type alias for a single result line"""

Results: TypeAlias = list[Result]
"""Type alias for all the results of the simulation"""


_logger = logging.getLogger(__name__)


class AbstractSimulation(ABC):
    """
    Base class for **Simulations**

    .. note:: Use a :class:`~physioblocks.simulation.setup.SimulationFactory` instance
      to instanciate simulations.

    :param factory: the factory that created the simulation instance.
    :type factory: SimulationFactory

    :param time_manager: the simulation time manager
    :type time_manager: TimeManager

    :param solver: the solver to use for simulation steps
    :type solver: AbstractSolver

    :param state: the simulation state
    :type state: State

    :param parameters: the simulations quantities for parameters.
    :type parameters: Parameters

    :param saved_quantities: the **Saved Quantities** register
    :type saved_quantities: SavedQuantities

    :param models: the mapping of used models with their names
    :type models: ModelComponent

    :param eq_system: the equation system to solve at each time step
    :type eq_system: EqSystem

    :param magnitudes: magnitude of the state variables
    :type magnitudes: dict[str, float]
    """

    def __init__(
        self,
        factory: Any,
        time_manager: TimeManager,
        state: State,
        parameters: Parameters,
        saved_quantities: SavedQuantities,
        models: dict[str, ModelComponent],
        solver: AbstractSolver,
        eq_system: EqSystem,
        magnitudes: dict[str, float] | None = None,
    ):
        self.factory = factory
        self.state = state
        self.parameters = parameters
        self.saved_quantities = saved_quantities
        self.models = models
        self.time_manager = time_manager
        self.solver = solver
        self.eq_system = eq_system
        if magnitudes is None:
            magnitudes = {}
        self.magnitudes = self._check_magnitudes(magnitudes, state)
        self._timed_updates: dict[str, AbstractFunction] = {}
        self._output_functions_updates: dict[str, AbstractFunction] = {}

    @property
    def update_functions(self) -> dict[str, AbstractFunction]:
        """
        Get all functions to update at each time step with their matching quantity
        global name.

        :return: the update functions
        :rtype: dict[str, AbstractFunction]
        """
        return self._timed_updates.copy()

    @property
    def outputs_functions(self) -> dict[str, AbstractFunction]:
        """
        Get all functions that compute the additional output after a time step
        with their matching output global names.

        :return: the output functions
        :rtype: dict[str, AbstractFunction]
        """
        return self._output_functions_updates.copy()

    @property
    def quantities(self) -> dict[str, Quantity[Any]]:
        """
        Get all the quantities in the simulation from the parameters, the state
        and the time manager.

        :return: a dictionary containing all the simulation quantities
        :rtype: dict[str, Quantity]
        """
        quantities: dict[str, Quantity[Any]] = {
            TIME_QUANTITY_ID: self.time_manager.time
        }
        quantities.update(self.parameters)
        quantities.update(self.state.variables)

        return quantities

    def register_timed_parameter_update(
        self, parameter_id: str, update_function: AbstractFunction
    ) -> None:
        """
        Register a simulation function to update the parameters with the given global
        name at each time step.

        :param parameter_id: the global name of the parameter to update
        :type parameter_id: str

        :param update_function: the function to call to evaluate the parameter value
        :type update_function: AbstractFunction
        """

        if parameter_id not in self.parameters:
            raise KeyError(str.format("{0} not found in parameters", parameter_id))

        if (
            isinstance(update_function, AbstractFunction) is False
            or is_time_function(update_function) is False
        ):
            raise TypeError(
                str.format(
                    "{0} is not a time function",
                    type(update_function).__name__,
                )
            )

        self._timed_updates[parameter_id] = update_function

    def unregister_timed_parameter_update(self, parameter_id: str) -> None:
        """
        Unegister a simulation function from the timed updates.

        :param parameter_id: the global name of the parameter to unregister.
        :type parameter_id: str
        """
        self._timed_updates.pop(parameter_id)

    def register_output_function(
        self, output_id: str, update_function: AbstractFunction
    ) -> None:
        """
        Register a function that is called to compute an additional output.

        :param output_id: the global name of the output in the results
        :type output_id: str

        :param update_function: the function to compute the output
        :type output_id: AbstractFunction

        :raise ValueError: Raises a value error when the output id is already defined
          in the results
        """
        if (
            output_id in self._output_functions_updates
            or output_id in self.saved_quantities
            or output_id in self.state
        ):
            raise KeyError(str.format("Output {0} is already defined.", output_id))

        if isinstance(update_function, AbstractFunction) is False:
            raise TypeError(
                str.format(
                    "{0} is not a valid output function",
                    type(update_function).__name__,
                )
            )

        self._output_functions_updates[output_id] = update_function

    def unregister_output_function(self, output_id: str) -> None:
        """
        Unregister a function from the outputs updates.

        :param output_id: the global name of the output.
        :type output_id: str
        """
        self._output_functions_updates.pop(output_id)

    def _initialize(self) -> Results:
        """Initialize the simulation with current parameters.

        This method should be called when overriding the run method.
        """
        self._initial_state = self.state.state_vector
        _initialize_models(self.models.values())

        # save the initialization
        results = [self._get_current_result()]

        self.time_manager.initialize()
        self.time_manager.update_time()

        self.state.set_state_vector(self.state.state_vector)

        return results

    def _finalize(self) -> None:
        """Terminate the simulation reinitializing state and time to initial values.

        This method should be called when overriding the run method.
        """
        self.time_manager.time.initialize(self.time_manager.start)
        self.state.set_state_vector(self._initial_state)

    def _check_magnitudes(
        self, magnitudes: dict[str, float], state: State
    ) -> dict[str, float]:
        checked_magnitudes = {}

        for variable_id in state:
            if variable_id not in magnitudes:
                message = str.format(
                    "No magnitude initialized for variable {0}. Magnitude set to 1.0",
                    variable_id,
                )
                _logger.warning(message)
                checked_magnitudes[variable_id] = 1.0

            elif magnitudes[variable_id] == 0.0:
                message = str.format(
                    "Magnitude for variable {0} is initialized to 0.0. "
                    "Replacing with 1.0",
                    variable_id,
                )
                _logger.warning(message)
                checked_magnitudes[variable_id] = 1.0
            else:
                checked_magnitudes[variable_id] = magnitudes[variable_id]

        return checked_magnitudes

    @abstractmethod
    def run(self) -> Results:
        """
        Run the simulation, this method should be implemented in child classes.

        :return: the list of solution for each time step
        :rtype: list[NDArray[float64]]
        """

    def _update_time(self) -> None:
        """
        Updates all the time triggered updatable parameters.
        """
        for param_id, func in self._timed_updates.items():
            self.parameters[param_id].initialize(
                func.eval(self.time_manager.time.current)
            )
            self.parameters[param_id].update(func.eval(self.time_manager.time.new))

    def _get_current_result(self) -> Result:
        result: Result = {}

        result[TIME_QUANTITY_ID] = self.time_manager.time.current
        result.update(
            {var_id: qty.current for var_id, qty in self.state.variables.items()}
        )

        self.saved_quantities.update()
        result.update(
            {qty_id: qty.current for qty_id, qty in self.saved_quantities.items()}
        )

        for output_id, update_function in self._output_functions_updates.items():
            arguments: dict[str, Any] = {}
            if is_time_function(update_function):
                arguments[TIME_QUANTITY_ID] = self.time_manager.time.current
            if is_state_function(update_function):
                arguments[STATE_NAME_ID] = self.state

            result[output_id] = update_function.eval(**arguments)

        return result


def _initialize_models(models: Iterable[ModelComponent]) -> None:
    """
    Initialize all provided models

    :param blocks: the blocks to initialize
    :type blocks: Iterable[Block]
    """
    for block in models:
        block.initialize()


# Forward simulation type id
FORWARD_SIM_ID = "forward_simulation"


@register_type(FORWARD_SIM_ID)
class ForwardSimulation(AbstractSimulation):
    """
    Extend :class:`~.AbstractSimulation` class to define a **Forward Simulation**.

    The forward simulation solve the **Equation System** at each time step using
    the simulation **Solver**.

    If the solver did not converge at a given time step, it breaks the current time
    step into smaller steps and try again.
    If it still do not converge, it recursivly breaks the current time steps again and
    stops if the time step is under the minimum time step allowed by the time manager.

    When finding a solution for a reduced time step, the simulation
    then tries to solve for the remaining time interval in the current time step.

    .. note::

        When breaking a simulation step, the forward simulation still only provide a
        result for the time step interval given to the time manager.

    """

    def run(self) -> Results:
        """
        Solve the system for each time steps.

        :return: the list of solution for each time step
        :rtype: list[NDArray[float64]]

        :raise SimulationError: raise a Simulation Error holding the current results
          if the simulation stops before reaching the end time.
        """
        # initialize the simulation and save the initial results
        results = self._initialize()

        try:
            while self.time_manager.ended is False:
                next_step = self.time_manager.time.new

                self._update_time()

                while (
                    np.abs(next_step - self.time_manager.time.current)
                    > self.time_manager.min_step
                ):
                    self.state.reset_state_vector()

                    sol = self.solver.solve(self.state, self.eq_system, self.magnitudes)

                    if sol.converged is False:
                        inter_time = 0.5 * self.time_manager.current_step_size
                        if inter_time < self.time_manager.min_step:
                            raise ConvergenceError(
                                str.format(
                                    "The solver did not converge at {0}s for minimal"
                                    "time step {1}",
                                    self.time_manager.time.current,
                                    self.time_manager.min_step,
                                )
                            )

                        self.time_manager.current_step_size = inter_time
                        self.time_manager.time.update(
                            self.time_manager.time.current
                            + self.time_manager.current_step_size
                        )
                    else:
                        self.state.set_state_vector(sol.x)

                        self.time_manager.update_time()
                        if (
                            np.abs(next_step - self.time_manager.time.current)
                            >= self.time_manager.min_step
                        ):
                            self.time_manager.current_step_size = (
                                next_step - self.time_manager.time.current
                            )
                            self.time_manager.time.update(next_step)
                        else:
                            self.time_manager.time.initialize(next_step)
                            self.time_manager.current_step_size = (
                                self.time_manager.step_size
                            )
                            self.time_manager.time.update(
                                self.time_manager.time.current
                                + self.time_manager.current_step_size
                            )

                self.state.set_state_vector(sol.x)
                results.append(self._get_current_result())
        except Exception as exception:
            log_exception(
                _logger,
                type(exception),
                exception,
                exception.__traceback__,
                logging.DEBUG,
            )
            raise SimulationError(
                str.format(
                    "An error caused the simulation to stop prematurely",
                    intermediate_results=results,
                ),
                results,
            ) from exception

        self._finalize()
        return results


class SimulationError(Exception):
    """
    Error raised when the simulation encounter a problem.
    """

    intermediate_results: Results
    """Results obtained before the simulation error occured"""

    def __init__(
        self, message: str, intermediate_results: Results, *args: Any, **kwargs: Any
    ) -> None:
        super().__init__(message, *args, **kwargs)
        self.intermediate_results = intermediate_results
