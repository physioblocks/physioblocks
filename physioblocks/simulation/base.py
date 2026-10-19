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

"""Bases classes and setup functions to declare simulations."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from copy import copy
from dataclasses import dataclass, field
from typing import Any, Generic, NamedTuple, TypeAlias, TypeVar

import numpy as np
from numpy.typing import NDArray
from pandas import DataFrame
from rich.progress import Progress

from physioblocks.base.function_factories import attribute_checker
from physioblocks.computing.assembling import EqSystem
from physioblocks.computing.models import (
    Expression,
    ModelComponent,
    ModelFunction,
    Term,
)
from physioblocks.computing.quantities import (
    QuantitiesRegistry,
    Quantity,
    QuantityInit,
    mid_point,
)
from physioblocks.description.blocks import BlockDescription, ModelComponentDescription
from physioblocks.description.nets import BoundaryCondition, Net
from physioblocks.registers.type_register import register_type
from physioblocks.simulation.functions import (
    AbstractFunction,
    SimulationFunctionFactory,
)
from physioblocks.simulation.process import (
    AbstractProcess,
    run_method_checkers,
    run_processes,
)
from physioblocks.simulation.saved_quantities import SavedQuantities
from physioblocks.simulation.solvers import AbstractSolver, NewtonSolver
from physioblocks.simulation.time_manager import TIME_QUANTITY_ID, TimeManager
from physioblocks.utils.exceptions_utils import log_exception

_logger = logging.getLogger(__name__)


class SystemExpression(NamedTuple):
    """Match an expression with its parameters and its line in the residual.

    Attributes
    ----------
    line_index : int
        line where the expression is summed in the residual.
    expression : Expression
        the expression
    parameters : Any
        The parameters to compute the expression.
    """

    line_index: int
    expression: Expression
    parameters: Any


Parameters: TypeAlias = dict[str, Quantity[Any]]
"""Type alias for quantities collection"""

Result: TypeAlias = dict[str, np.float64]
"""Type alias for a single result line"""

Results: TypeAlias = list[Result]
"""Type alias for all the results of the simulation"""

# Time id in the configuration
RANGE_ID = "range"
"""Type label for simulation range initialization value"""


@dataclass
@register_type(RANGE_ID)
class SimulationRange:
    """Initialization parameters for the simulation range.

    Parameters
    ----------
    start : float
        starting time of the simulation. Default is 0.0.
    length : float
        simulation length. Default is 1e-3.
    step_size : float
        simulation step size. Default is 1e-3.

    Configuration
    -------------

    .. code-block:: json

        {
            "type": "range",
            "start": "<float>",           // Starting time (optional, default: 0.0)
            "length": "<float>",          // Simulation length (optional, default: 1e-3)
            "step_size": "<float>"        // Step size (optional, default: 1e-3)
        }

    """

    start: float = field(default=0.0)

    length: float = field(default=1e-3)

    step_size: float = field(default=1e-3)


@dataclass
class SimulationModel:
    """Holds the assembled simulation model.

    It is used to update and run the simulation.

    Parameters
    ----------
    factory : SimulationModelFactory
        the factory that generated the model
    equation_system : EqSystem
        Holds equations depending on the model quantities
    solver : AbstractSolver
        Solver used to get a solution to the equation system.
    time_manager : TimeManager
        Hold step manager driving the simulation model
        (typically on the time parameter).
    state : QuantitiesRegistry
        Registry representing the current simulation state
    parameters : Parameters
        Holds models parameters values
    saved_quantities : SavedQuantities
        Holds model saved quantities

    """

    factory: SimulationModelFactory

    equation_system: EqSystem

    solver: AbstractSolver = field(default_factory=NewtonSolver)

    time_manager: TimeManager = field(default_factory=TimeManager)

    state: QuantitiesRegistry = field(default_factory=QuantitiesRegistry)

    parameters: Parameters = field(default_factory=dict)

    saved_quantities: SavedQuantities = field(default_factory=SavedQuantities)

    _update_functions: dict[str, AbstractFunction] = field(
        init=False, default_factory=dict
    )

    @property
    def quantities(self) -> dict[str, Quantity[Any]]:
        """Get all the quantities in the simulation from the parameters and the state.

        Returns
        -------
        dict[str, Quantity]
            a dictionary containing all the simulation quantities

        """
        quantities: dict[str, Quantity[Any]] = {
            TIME_QUANTITY_ID: self.time_manager.time
        }
        quantities.update(self.parameters)
        quantities.update(self.state.quantities)

        return quantities

    @property
    def update_functions(self) -> dict[str, AbstractFunction]:
        """Get the functions that update quantities each time step.

        Returns
        -------
        dict[str, AbstractFunction]
            the update functions

        """
        return self._update_functions.copy()

    def register_parameter_update(
        self, parameter_id: str, update_function: AbstractFunction
    ) -> None:
        """Register a function to update the parameters each time step.

        Parameters
        ----------
        parameter_id : str
            the global name of the parameter to update
        update_function : AbstractFunction
            the function to call to evaluate the parameter value

        Raises
        ------
        KeyError
            if the parameter is not in the simulation parameters.
        TypeError
            if the update function is not an :class:`~.AbstractFunction`.

        """
        if parameter_id not in self.parameters:
            raise KeyError(f"{parameter_id} not found in parameters")

        if isinstance(update_function, AbstractFunction) is False:
            raise TypeError(
                f"{type(update_function).__name__} is not an update function."
            )

        self._update_functions[parameter_id] = update_function

    def unregister_parameter_update(self, parameter_id: str) -> None:
        """Unregister the parameter update function.

        Parameters
        ----------
        parameter_id : str
            the global name of the parameter.

        """
        self._update_functions.pop(parameter_id)

    def update_functions_parameters(self) -> None:
        """Update all updatable parameters."""
        for param_id, func in self._update_functions.items():
            self.parameters[param_id].initialize(func.eval_current())
            self.parameters[param_id].update(func.eval_new())


MODEL_FACTORY_ID = "simulation_model_factory"
"""Model factory type id"""


@dataclass
@register_type(MODEL_FACTORY_ID)
class SimulationModelFactory:
    """
    Create :class:`SimulationModel`.

    Parameters
    ----------
    net : Net
        the simulation net
    time : SimulationRange
        initialization values for the simulation time
    state : dict[str, QuantityInit]
        initialization values for state variables.
    parameters : dict[str, Any]
        initialization values for parameters
    update_functions : dict[str, SimulationFunctionFactory[Any]]
        functions updating simulation parameters depending on the driving quantity
    solver : AbstractSolver
        the solver used to solve the equation system.
        Default is a solver using newton method.

    Configuration
    -------------

    The simulation model factory are not configured directly: its items are set in the
    :class:`~.ForwardSimulation` or :class:`~.EstimationSimulation` configuration
    (``net``, ``time``, ``state``, ``parameters``, ``update_functions`` and ``solver``).

    """

    net: Net = field(default_factory=Net)

    time: SimulationRange = field(default_factory=SimulationRange)

    state: dict[str, QuantityInit] = field(default_factory=dict)

    parameters: dict[str, Any] = field(default_factory=dict)

    update_functions: dict[str, SimulationFunctionFactory[Any]] = field(
        default_factory=dict
    )

    solver: AbstractSolver = field(default_factory=NewtonSolver)

    def create_simulation_model(self) -> SimulationModel:
        """
        Create the model from current class attributes.

        Returns
        -------
        SimulationModel
            the resulting simulation model.

        Raises
        ------
        KeyError
            if there are initialization values for state members that don't exist.
        """
        sim_state = build_state(self.net)
        sim_parameters = build_parameters(self.net, sim_state)
        time_manager = TimeManager(
            self.time.start, self.time.length, self.time.step_size
        )
        time_manager.initialize()
        all_quantities = _build_quantities(time_manager, sim_parameters, sim_state)
        models = build_blocks(self.net, all_quantities)
        saved_quantities = build_saved_quantities(self.net, models)
        expressions = _build_net_expressions(
            self.net, sim_state, models, all_quantities
        )
        eq_system = build_eq_system(expressions, sim_state)
        key_errors = [key for key in self.state if key not in sim_state]
        if len(key_errors) != 0:
            raise KeyError(f"The state does not have variables: {key_errors}")

        # Initialize state variable values.
        state_mags = {}
        state_stdevs = {}
        for variable_id in sim_state:
            if variable_id in self.state:
                observable_init = self.state[variable_id]
                sim_state[variable_id].initialize(observable_init.value)
                state_mags[variable_id] = self.state[variable_id].magnitude
                state_stdevs[variable_id] = self.state[variable_id].stdev
        sim_state.set_magnitudes(state_mags)
        sim_state.set_stdevs(state_stdevs)

        # Initialize parameters values.
        for param_id, param_init in sim_parameters.items():
            if param_id in self.parameters:
                param_init.initialize(self.parameters[param_id])

        simulation_model = SimulationModel(
            self,
            eq_system,
            self.solver,
            time_manager,
            sim_state,
            sim_parameters,
            saved_quantities,
        )

        # Initialize update functions
        for param_id, function_factory in self.update_functions.items():
            update_func = function_factory.create_function(simulation_model.quantities)
            simulation_model.register_parameter_update(param_id, update_func)
            # initialize the parameter
            simulation_model.parameters[param_id].initialize(update_func.eval_current())

        # initialize model components
        for block_model in models.values():
            block_model.initialize()

        return simulation_model


@run_method_checkers(attribute_checker("model_factory"))
class AbstractSimulationProcess(AbstractProcess):
    """Process that can create simulations from a factory parameter.

    Parameters
    ----------
    model_factory : SimulationModelFactory
        The simulation model factory

    """

    model_factory: SimulationModelFactory


@dataclass
class AbstractSimulation(ABC):
    """Base class for simulations.

    .. note:: Use a :class:`~.SimulationFactory` instance
      to instantiate simulations easily.

    Attributes
    ----------
    factory : SimulationFactory[Any]
        The factory that created the simulation
    simulation_name : str
        the simulation name
    simulation_model : SimulationModel
        the simulation model
    data : dict[str, DataFrame]
        available data for pre and post-processes
    preprocesses : dict[str, AbstractProcess]
        Pre-Processes
    postprocesses : dict[str, AbstractProcess]
        Post-Processes

    """

    factory: SimulationFactory[Any]

    simulation_name: str

    simulation_model: SimulationModel

    data: dict[str, DataFrame] = field(default_factory=dict)

    preprocesses: dict[str, AbstractProcess] = field(default_factory=dict)

    postprocesses: dict[str, AbstractProcess] = field(default_factory=dict)

    _output_functions_updates: dict[str, AbstractFunction] = field(
        init=False, default_factory=dict
    )

    @property
    def outputs_functions(self) -> dict[str, AbstractFunction]:
        """Get all functions that compute additional output after a time step.

        Returns
        -------
        dict[str, AbstractFunction]
            the output functions

        """
        return self._output_functions_updates.copy()

    def register_output_function(
        self, output_id: str, update_function: AbstractFunction
    ) -> None:
        """Register a function that computes an additional output.

        Parameters
        ----------
        output_id : str
            the global name of the output in the results
        update_function : AbstractFunction
            the function to compute the output

        Raises
        ------
        KeyError
            if the output id is already defined in the results.
        TypeError
            if the update function is not an :class:`~.AbstractFunction`.

        """
        if (
            output_id in self._output_functions_updates
            or output_id in self.simulation_model.state
            or output_id in self.simulation_model.saved_quantities
        ):
            raise KeyError(str.format("Output {0} is already defined.", output_id))

        if isinstance(update_function, AbstractFunction) is False:
            raise TypeError(
                str.format(
                    "{0} is an invalid output function type",
                    type(update_function).__name__,
                )
            )

        self._output_functions_updates[output_id] = update_function

    def unregister_output_function(self, output_id: str) -> None:
        """Unregister a function from the outputs.

        Parameters
        ----------
        output_id : str
            the global name of the output.

        """
        self._output_functions_updates.pop(output_id)

    def _initialize(self) -> Results:
        """Initialize the simulation with current parameters.

        This method should be called when overriding the run method.
        """
        self.simulation_model.state.reset_vector()
        self.simulation_model.time_manager.initialize()

        # save the initialization
        results = [self._get_current_result()]

        return results

    def _finalize(self) -> None:
        """Terminate the simulation reinitializing state and time to initial values.

        This method should be called when overriding the run method.
        """
        self.simulation_model = self.simulation_model.factory.create_simulation_model()

        self._output_functions_updates.clear()
        for (
            output_id,
            output_function_factory,
        ) in self.factory.output_functions.items():
            output_function = output_function_factory.create_function(
                self.simulation_model.quantities
            )
            self.register_output_function(output_id, output_function)

    def run(self) -> dict[str, DataFrame]:
        """Solve the system for each time step.

        Returns
        -------
        dict[str, DataFrame]
            the simulation results in identified dataframes

        """
        # run preprocesses
        for process in self.preprocesses.values():
            if isinstance(process, AbstractSimulationProcess):
                process.model_factory = copy(self.simulation_model.factory)
        self.processed_data = run_processes(self.preprocesses, self.data)

        # initialize the simulation and save the initial results
        results = self._initialize()

        progress_step_update = (
            100.0
            * self.simulation_model.time_manager.step_size
            / self.simulation_model.time_manager.duration
        )
        with Progress() as progress:
            try:
                sim_task = progress.add_task(
                    str.format("{0}: Simulation in progress...", self.simulation_name)
                )
                while self.simulation_model.time_manager.ended is False:
                    self.run_step()

                    # store the result
                    results.append(self._get_current_result())

                    # Update progress display
                    progress.update(sim_task, advance=progress_step_update)

            except Exception as exception:
                log_exception(
                    _logger,
                    type(exception),
                    exception,
                    exception.__traceback__,
                    logging.DEBUG,
                )
                self.processed_data.update({self.simulation_name: DataFrame(results)})
                _logger.error("An error caused the simulation to stop prematurely.")

        self._finalize()

        # run post-processes
        self.processed_data.update({self.simulation_name: DataFrame(results)})

        for process in self.postprocesses.values():
            if isinstance(process, AbstractSimulationProcess):
                process.model_factory = copy(self.simulation_model.factory)
        self.processed_data = run_processes(self.postprocesses, self.processed_data)

        return self.processed_data

    @abstractmethod
    def run_step(self) -> None:
        """Run a simulation step.

        It updates the simulation model for the current simulation step according to the
        simulation type.

        This method is called in the main run loop and should be overwritten
        by child classes.
        """

    def _get_current_result(self) -> Result:
        """Format current simulation state in a mapping.

        Returns
        -------
        dict[str, Any]
            mapping of the current simulation result

        """
        result: Result = {}

        result[TIME_QUANTITY_ID] = self.simulation_model.time_manager.time.current
        for var_id, qty in self.simulation_model.state.quantities.items():
            result.update(format_result(var_id, qty.current))

        self.simulation_model.saved_quantities.update()

        for qty_id, qty in self.simulation_model.saved_quantities.items():
            result.update(format_result(qty_id, qty.current))

        for output_id, update_function in self._output_functions_updates.items():
            result.update(format_result(output_id, update_function.eval_current()))

        return result


def format_result(result_id: str, value: np.float64 | NDArray[np.float64]) -> Result:
    """Format result depending on its value type.

    Parameters
    ----------
    result_id : str
        the result id
    value : np.float64 | NDArray[np.float64]
        the result value

    Returns
    -------
    Result
        the formatted result

    """
    if value.size == 1:
        return {result_id: value if isinstance(value, float) else value[0]}
    elif isinstance(value, np.ndarray) and value.size > 1:
        # name independently each vector component
        return {f"{result_id}[{i}]": value[i] for i in range(len(value))}

    # value size is 0, return empty result
    return {}


@dataclass
class _BoundaryConditionsQuantities:
    flux: Quantity[Any]

    def boundary_condition_func(self) -> Any:
        return mid_point(self.flux)

    def boundary_condition_grad_func(self) -> Any:
        return 0.5


def create_models(
    model_id: str,
    description: ModelComponentDescription,
    parameters: dict[str, Quantity[Any]],
) -> dict[str, ModelComponent]:
    """Create a model component instance and its submodels from the given parameters.

    Parameters
    ----------
    model_id : str
        the id of the created model
    description : ModelComponentDescription
        the model description
    parameters : dict[str, Quantity]
        the available quantities

    Returns
    -------
    dict[str, ModelComponent]
        a dict containing the created model and all its submodels recursively.

    """
    submodels = {}

    for submodel_desc in description.submodels.values():
        submodels.update(create_models(submodel_desc.name, submodel_desc, parameters))

    model_params: dict[str, Quantity[Any]] = {}

    for term_id, global_id in description.global_ids.items():
        if term_id not in [
            saved_quantity.term_id
            for saved_quantity in description.described_type.saved_quantities
        ]:
            model_params[term_id] = parameters[global_id]

    model = description.described_type(**model_params)
    models = {model_id: model}
    models.update(submodels)
    return models


def build_state(net: Net) -> QuantitiesRegistry:
    """Build the state of the simulation from the net description.

    Parameters
    ----------
    net : Net
        the net description

    Returns
    -------
    QuantitiesRegistry
        the initial state

    """
    state = QuantitiesRegistry()

    for block in net.blocks.values():
        # Add the internal variables of the blocks

        indexes = []
        for term_id, term_size, term_index in block.internal_variables:
            state.add_quantity(term_id, term_size * [0.0])
            indexes.append(term_index)

    for node in net.nodes.values():
        if node.is_boundary is True:
            # For boundaries, only add dof as variable if the boundary condition is on
            # the flux.
            # Otherwise, the dof is given, it is not a variable, but a parameter.
            for bd in node.boundary_conditions:
                if node.has_flux_type(bd.condition_type) is True:
                    dof = node.get_flux_dof(bd.condition_type)
                    state.add_quantity(dof.dof_id, 0.0)
        else:
            # add the dofs at the nodes as external variables in the state.
            for dof in node.dofs:
                state.add_quantity(dof.dof_id, 0.0)

    return state


def build_parameters(net: Net, state: QuantitiesRegistry) -> Parameters:
    """
    Build the initial parameter register from the net description and the initial state.

    Parameters
    ----------
    net : Net
        the net description
    state : QuantitiesRegistry
        the state

    Returns
    -------
    dict[str, Quantity]
        the initial parameter register

    """
    parameters = {}

    for block in net.blocks.values():
        for qty_id in _get_block_qty_ids(block):
            if (
                qty_id != TIME_QUANTITY_ID
                and qty_id not in state
                and qty_id
                not in [saved_quantity[0] for saved_quantity in block.saved_quantities]
            ):
                parameters[qty_id] = Quantity(0)

    # add flux boundary conditions
    for node in net.nodes.values():
        for bc in node.boundary_conditions:
            if node.has_flux_type(bc.condition_type):
                parameters[bc.condition_id] = Quantity(0)

    return parameters


def build_eq_system(
    expressions: list[SystemExpression], state: QuantitiesRegistry
) -> EqSystem:
    """Build an equation system from a set of expressions.

    Parameters
    ----------
    expressions : list[SystemExpression]
        The expressions representing the system
    state : QuantitiesRegistry
        the state for the system

    Returns
    -------
    EqSystem
        an equation system initialized with the given expressions

    """
    eq_system = EqSystem(state.size)
    for line_index, expression, parameters in expressions:
        expr_grad = _build_gradient(expression, state)
        eq_system.add_system_part(
            line_index, expression.size, expression.expr_func, expr_grad, parameters
        )
    return eq_system


def _build_quantities(
    time_manager: TimeManager, parameters: Parameters, state: QuantitiesRegistry
) -> dict[str, Quantity[Any]]:
    """Join all the quantities from the parameters, the state and the time manager.

    Parameters
    ----------
    time_manager : TimeManager
        the manager holding the quantity driving the simulation
    parameters : Parameters
        the parameters register
    state : QuantitiesRegistry
        the state

    Returns
    -------
    dict[str, Quantity]
        a dictionary containing all the simulation quantities

    """
    quantities: dict[str, Quantity[Any]] = {TIME_QUANTITY_ID: time_manager.time}
    quantities.update(parameters)
    quantities.update(state.quantities)

    return quantities


def _build_gradient(
    eq: Expression, state: QuantitiesRegistry
) -> dict[int, ModelFunction]:
    gradients = {}
    for var_id in eq.expr_gradients:
        if var_id in state.quantities:
            gradients[state.indexes[var_id]] = eq.expr_gradients[var_id]

    return gradients


def _build_boundary_condition_expression(
    boundary_condition: BoundaryCondition, quantities: dict[str, Quantity[Any]]
) -> tuple[Expression, _BoundaryConditionsQuantities]:
    flux_id = boundary_condition.condition_id
    flux = quantities[flux_id]
    bc_parameters = _BoundaryConditionsQuantities(flux)
    flux_expr = Expression(
        flux.size,
        _BoundaryConditionsQuantities.boundary_condition_func,
        terms=[Term(flux_id, flux.size, 0)],
        expr_gradients={
            flux_id: _BoundaryConditionsQuantities.boundary_condition_grad_func
        },
    )
    return flux_expr, bc_parameters


def _get_block_qty_ids(block: ModelComponentDescription) -> list[str]:
    ids = list(block.global_ids.values())

    for sub_model in block.submodels.values():
        child_ids = _get_block_qty_ids(sub_model)
        ids.extend(child_ids)

    return ids


def build_blocks(
    net: Net, quantities: dict[str, Quantity[Any]]
) -> dict[str, ModelComponent]:
    """Build the blocks and their submodels from the net.

    Parameters
    ----------
    net : Net
        the net
    quantities : dict[str, Quantity]
        the simulation quantities

    Returns
    -------
    dict[str, ModelComponent]
        the created blocks and submodels with their ids.

    """
    block_models = {}
    for block_id, block_desc in net.blocks.items():
        block_models.update(create_models(block_id, block_desc, quantities))
    return block_models


def _get_internal_expressions(
    model_id: str,
    model_desc: ModelComponentDescription,
    state: QuantitiesRegistry,
    models: dict[str, ModelComponent],
) -> list[SystemExpression]:
    expressions = []
    for expression in model_desc.internal_expressions:
        first_term = expression.get_term(0)
        var_index = state.indexes[first_term.term_id]
        expressions.append(SystemExpression(var_index, expression, models[model_id]))

    return expressions


def _get_fluxes_expressions(
    net: Net,
    block_id: str,
    block_desc: BlockDescription,
    state: QuantitiesRegistry,
    model: ModelComponent,
) -> list[SystemExpression]:
    fluxes_expr: list[SystemExpression] = []

    for local_node_index in block_desc.described_type.nodes:
        global_node_id = net.local_to_global_node_id(block_id, local_node_index)
        node = net.nodes[global_node_id]

        # Add the fluxes
        flux_expr = block_desc.fluxes[local_node_index]
        dof = node.get_flux_dof(block_desc.flux_type)
        # if the dof is not in state, it has been fixed with a boundary condition,
        # don't add the flux
        if dof.dof_id in state:
            dof_state_index = state.indexes[dof.dof_id]
            fluxes_expr.append(SystemExpression(dof_state_index, flux_expr, model))

    return fluxes_expr


def _get_model_internal_expressions(
    model_id: str,
    model_desc: ModelComponentDescription,
    state: QuantitiesRegistry,
    models: dict[str, ModelComponent],
) -> list[SystemExpression]:
    int_expressions: list[SystemExpression] = []

    int_expressions = _get_internal_expressions(model_id, model_desc, state, models)

    for submodel_desc in model_desc.submodels.values():
        submodel_expressions = _get_model_internal_expressions(
            submodel_desc.name, submodel_desc, state, models
        )

        int_expressions.extend(submodel_expressions)

    return int_expressions


def _get_block_expressions(
    net: Net,
    block_id: str,
    state: QuantitiesRegistry,
    models: dict[str, ModelComponent],
) -> list[SystemExpression]:
    # get the expressions defined by the model part of the block (and its submodels)
    expressions = _get_model_internal_expressions(
        block_id, net.blocks[block_id], state, models
    )

    flux_expressions = _get_fluxes_expressions(
        net,
        block_id,
        net.blocks[block_id],
        state,
        models[block_id],
    )
    expressions.extend(flux_expressions)

    return expressions


def _build_net_expressions(
    net: Net,
    state: QuantitiesRegistry,
    models: dict[str, ModelComponent],
    quantities: dict[str, Quantity[Any]],
) -> list[SystemExpression]:
    """Get all expressions to build the system from the net.

    Parameters
    ----------
    net : Net
        the net
    state : QuantitiesRegistry
        the simulation state
    models : dict[str, ModelComponent]
        the models defining the expressions
    quantities : dict[str, Quantity]
        all the quantities available

    Returns
    -------
    list[SystemExpression]
        a set of expressions

    """
    expressions: list[SystemExpression] = []

    # Get all blocks expressions
    for block_id in net.blocks:
        # Add block expressions:
        block_expressions = _get_block_expressions(net, block_id, state, models)
        expressions.extend(block_expressions)

    # Add boundary conditions
    bc_expressions = _build_boundary_condition_expressions(net, state, quantities)
    expressions.extend(bc_expressions)

    return expressions


def _build_boundary_condition_expressions(
    net: Net, state: QuantitiesRegistry, quantities: dict[str, Quantity[Any]]
) -> list[SystemExpression]:
    bc_expressions = []

    for node in net.nodes.values():
        for condition in node.boundary_conditions:
            # if the condition is on the flux, add the boundary condition expression
            if condition.condition_type in net.flux_dof_type_register.flux_dof_couples:
                bc_expr, bc_param = _build_boundary_condition_expression(
                    condition, quantities
                )
                dof = node.get_flux_dof(condition.condition_type)

                bc_index = state.indexes[dof.dof_id]
                bc_expressions.append(SystemExpression(bc_index, bc_expr, bc_param))

    return bc_expressions


def _get_model_saved_quantities_expressions(
    model_id: str,
    model_desc: ModelComponentDescription,
    models: dict[str, ModelComponent],
) -> list[tuple[str, Expression, ModelComponent, int, int]]:
    expressions = [
        (
            term.term_id,
            saved_qty_expr,
            models[model_id],
            term.term_size,
            term.term_index,
        )
        for saved_qty_expr in model_desc.saved_quantities_expressions
        for term in saved_qty_expr.terms
    ]
    for submodel_desc in model_desc.submodels.values():
        expressions.extend(
            _get_model_saved_quantities_expressions(
                submodel_desc.name, submodel_desc, models
            )
        )

    return expressions


def build_saved_quantities(
    net: Net, models: dict[str, ModelComponent]
) -> SavedQuantities:
    """Create the saved quantities register for the simulation.

    Parameters
    ----------
    net : Net
        the simulation net
    models : dict[str, ModelComponent]
        the models in the simulations

    Returns
    -------
    SavedQuantities
        the simulation saved quantities

    """
    models_saved_quantities = SavedQuantities()
    for model_id, model_desc in net.blocks.items():
        saved_quantities = _get_model_saved_quantities_expressions(
            model_id, model_desc, models
        )

        for quantity_id, expression, model, size, index in saved_quantities:
            models_saved_quantities.register(
                quantity_id, expression, model, size, index
            )

    return models_saved_quantities


SIMULATION_FACTORY_ID = "simulation_factory"


SimulationType = TypeVar("SimulationType", bound=AbstractSimulation)


@dataclass
@register_type(SIMULATION_FACTORY_ID)
class SimulationFactory(Generic[SimulationType]):
    """Factory for **Simulation** objects.

    Parameters
    ----------
    simulation_name : str
        the simulation name
    simulation_type : type[SimulationType]
        The type of simulation to create
    simulation_model_factory : SimulationModelFactory
        Factory to create a simulation model
    output_functions : dict[str, SimulationFunctionFactory[Any]]
        Functions adding additional results to the simulation output
    data : dict[str, DataFrame]
        Input data for simulation processes
    preprocesses : dict[str, AbstractProcess]
        Processes to run before the simulation
    postprocesses : dict[str, AbstractProcess]
        Processes to run after the simulation
    simulation_options : dict[str, Any]
        Additional simulation parameters based on the simulation type

    Configuration
    -------------

    The simulation factory is not configured directly: its items are set in the
    :class:`~.ForwardSimulation` or :class:`~.EstimationSimulation` configuration, where
    the ``type`` gives the simulation type.

    """

    simulation_name: str

    simulation_type: type[SimulationType]

    simulation_model_factory: SimulationModelFactory

    output_functions: dict[str, SimulationFunctionFactory[Any]] = field(
        default_factory=dict
    )

    data: dict[str, DataFrame] = field(default_factory=dict)

    preprocesses: dict[str, AbstractProcess] = field(default_factory=dict)

    postprocesses: dict[str, AbstractProcess] = field(default_factory=dict)

    simulation_options: dict[str, Any] = field(default_factory=dict)

    def create_simulation(self) -> SimulationType:
        """Create a **Simulation** instance.

        Returns
        -------
        SimulationType
            a simulation instance.

        Raises
        ------
        TypeError
            if the simulation type is not an :class:`AbstractSimulation` subclass.

        """
        if issubclass(self.simulation_type, AbstractSimulation) is False:
            raise TypeError(
                str.format(
                    "{0} is not a {1} sub-class.",
                    self.simulation_type.__name__,
                    AbstractSimulation.__name__,
                )
            )

        simulation_model = self.simulation_model_factory.create_simulation_model()

        simulation = self.simulation_type(
            factory=self,
            simulation_name=self.simulation_name,
            simulation_model=simulation_model,
            data=self.data,
            preprocesses=self.preprocesses,
            postprocesses=self.postprocesses,
            **self.simulation_options,
        )

        for (
            output_id,
            output_function_factory,
        ) in self.output_functions.items():
            output_function = output_function_factory.create_function(
                simulation_model.quantities
            )
            simulation.register_output_function(output_id, output_function)

        return simulation
