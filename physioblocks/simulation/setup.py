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
Defines functions to setup the simulation
"""

from __future__ import annotations

import logging
from collections.abc import Mapping
from dataclasses import dataclass
from os import linesep
from typing import Any, TypeAlias

from physioblocks.computing.assembling import EqSystem
from physioblocks.computing.models import (
    Expression,
    ModelComponent,
    SystemFunction,
)
from physioblocks.computing.quantities import (
    Quantity,
    mid_point,
)
from physioblocks.description.blocks import BlockDescription, ModelComponentDescription
from physioblocks.description.flux import (
    get_flux_dof_register,
)
from physioblocks.description.nets import BoundaryCondition, Net
from physioblocks.simulation.runtime import AbstractSimulation, Parameters
from physioblocks.simulation.saved_quantities import SavedQuantities
from physioblocks.simulation.solvers import AbstractSolver, NewtonSolver
from physioblocks.simulation.state import State
from physioblocks.simulation.time_manager import TIME_QUANTITY_ID, TimeManager

_logger = logging.getLogger(__name__)

SystemExpressions: TypeAlias = list[tuple[int, Expression, Any]]
"""
Type Alias matching a set of :class:`~physioblocks.computing.models.Expression` objects
with their model instance and their line in the residual.
"""

__ID_SEPARATOR = "."

_flux_dof_register = get_flux_dof_register()


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
    """
    Create a model component instance and its submodels from the given parameters.

    :param parameters: the available quantities
    :type parameters: dict[str, Quantity]

    :return: a dict containing the created model and all its submodels recursively.
    :rtype: dict[str, ModelComponent].
    """
    submodels = {}

    for submodel_id, submodel_desc in description.submodels.items():
        unique_id = __get_submodel_unique_id(model_id, submodel_id)
        submodels.update(create_models(unique_id, submodel_desc, parameters))

    model_params: dict[str, Quantity[Any]]
    model_params = {}

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


def __get_submodel_unique_id(model_id: str, submodel_id: str) -> str:
    return __ID_SEPARATOR.join([model_id, submodel_id])


def build_state(net: Net) -> State:
    """
    Build the state of the simulation from the net description.

    :param net: the net description
    :type net: Net

    :return: the initial state
    :rtype: State
    """

    state = State()

    for block in net.blocks.values():
        # Add the internal variables of the blocks
        for var_id, var_size in block.internal_variables:
            state.add_variable(var_id, var_size * [0.0])

    for node in net.nodes.values():
        if node.is_boundary is True:
            # For boundaries, only add dof as variable if the boundary condition is on
            # the flux.
            # Otherwise, the dof is given, it is not a variable, but a parameter.
            for bd in node.boundary_conditions:
                if node.has_flux_type(bd.condition_type) is True:
                    dof = node.get_flux_dof(bd.condition_type)
                    state.add_variable(dof.dof_id, 0.0)
        else:
            # add the dofs at the nodes as external variables in the state.
            for dof in node.dofs:
                state.add_variable(dof.dof_id, 0.0)

    return state


def build_parameters(net: Net, state: State) -> Parameters:
    """
    Build the initial parameter register from the net description and the initial state.

    :param net: the net description
    :type net: Net

    :param net: the state
    :type net: State

    :return: the initial parameter register
    :rtype: Parameters
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


def build_eq_system(expressions: SystemExpressions, state: State) -> EqSystem:
    """build_eq_system(expressions: SystemExpressions, state: State) -> EqSystem

    Build an :class:`~physioblocks.computing.assembling.EqSystem` instance from set of
    :class:`~physioblocks.computing.models.Expression` objects.

    :param expressions: The expressions representing the system
    :type expressions: Expressions

    :param state: the state for the system
    :tupe size: State

    :return: an equation system initialized with the given expressions
    :rtype: EqSystem
    """
    eq_system = EqSystem(state.size)
    for line_index, expression, parameters in expressions:
        expr_grad = _build_gradient(expression, state)
        eq_system.add_system_part(
            line_index, expression.size, expression.expr_func, expr_grad, parameters
        )
    return eq_system


def _build_quantities(
    parameters: Parameters, state: State, time_manager: TimeManager
) -> dict[str, Quantity[Any]]:
    """
    Build a dictionary joining all the quantities from
    the parameters, the state and the time manager.

    :param parameters: the parameters register
    :type parameters: Parameters

    :param state: the state
    :type state: State

    :param time_manager: the time manager
    :type time_manager: TimeManager

    :return: a dictionary containing all the simulation quantities
    :rtype: dict[str, Quantity]
    """
    quantities = {}

    quantities.update(parameters)
    quantities.update(state.variables)

    quantities[TIME_QUANTITY_ID] = time_manager.time

    return quantities


def _build_gradient(eq: Expression, state: State) -> dict[int, SystemFunction]:
    gradients = {}
    for var_id in eq.expr_gradients:
        if var_id in state.variables:
            gradients[state.get_variable_index(var_id)] = eq.expr_gradients[var_id]

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
        {flux_id: _BoundaryConditionsQuantities.boundary_condition_grad_func},
    )
    return flux_expr, bc_parameters


def _get_block_qty_ids(block: ModelComponentDescription) -> list[str]:
    ids = list(block.global_ids.values())

    for sub_model in block.submodels.values():
        child_ids = _get_block_qty_ids(sub_model)
        ids.extend(child_ids)

    return ids


def __get_model_desc(net: Net, model_id: str) -> ModelComponentDescription:
    splitted_id = model_id.split(__ID_SEPARATOR)
    submodels: Mapping[str, ModelComponentDescription] = net.blocks

    for id_part in splitted_id:
        model_desc = submodels[id_part]
        submodels = model_desc.submodels

    if model_desc is not None:
        return model_desc

    raise ValueError(str.format("No model named {0} defined in the net.", model_id))


def build_blocks(
    net: Net, quantities: dict[str, Quantity[Any]]
) -> dict[str, ModelComponent]:
    """
    Build all the blocks and their submodels holding the quantities from the net.

    :param net: the net
    :type net: Net

    :param quantities: the simulation quantities
    :type quantities: dict[str, Quantity]
    """

    block_models = {}
    for block_id, block_desc in net.blocks.items():
        block_models.update(create_models(block_id, block_desc, quantities))
    return block_models


def _get_internal_expressions(
    model_id: str,
    model_desc: ModelComponentDescription,
    state: State,
    models: dict[str, ModelComponent],
) -> SystemExpressions:
    expressions = []
    for expr_def in model_desc.internal_expressions:
        first_term = expr_def.get_term(0)
        var_index = state.get_variable_index(first_term.term_id)
        expressions.append((var_index, expr_def.expression, models[model_id]))

    return expressions


def _get_fluxes_expressions(
    net: Net,
    block_id: str,
    block_desc: BlockDescription,
    state: State,
    model: ModelComponent,
) -> SystemExpressions:
    fluxes_expr: SystemExpressions = []

    for local_node_index in block_desc.described_type.nodes:
        global_node_id = net.local_to_global_node_id(block_id, local_node_index)
        node = net.nodes[global_node_id]

        # Add the fluxes
        flux_expr = block_desc.fluxes[local_node_index]
        dof = node.get_flux_dof(block_desc.flux_type)
        # if the dof is not in state, it has been fixed with a boundary condition,
        # don't add the flux
        if dof.dof_id in state:
            dof_state_index = state.get_variable_index(dof.dof_id)
            fluxes_expr.append((dof_state_index, flux_expr, model))

    return fluxes_expr


def _get_model_internal_expressions(
    model_id: str,
    model_desc: ModelComponentDescription,
    state: State,
    models: dict[str, ModelComponent],
) -> SystemExpressions:
    int_expressions: SystemExpressions = []

    int_expressions = _get_internal_expressions(model_id, model_desc, state, models)

    for submodel_id, submodel_desc in model_desc.submodels.items():
        submodel_net_id = __get_submodel_unique_id(model_id, submodel_id)
        submodel_expressions = _get_model_internal_expressions(
            submodel_net_id, submodel_desc, state, models
        )

        int_expressions.extend(submodel_expressions)

    return int_expressions


def _get_block_expressions(
    net: Net,
    block_id: str,
    state: State,
    models: dict[str, ModelComponent],
) -> SystemExpressions:
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
    state: State,
    models: dict[str, ModelComponent],
    quantities: dict[str, Quantity[Any]],
) -> SystemExpressions:
    """
    Get all expressions to build the system from the net.

    :param net: the net
    :type net: Net

    :param blocks: the blocks defining the expressions
    :type blocks: dict[str, Block]

    :param quantities: all the quantities availables
    :type quantities: dict[str, Quantity]

    :return: a set of expressions
    :rtype: SystemExpressions
    """
    expressions: SystemExpressions = []

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
    net: Net, state: State, quantities: dict[str, Quantity[Any]]
) -> SystemExpressions:
    bc_expressions = []

    for node in net.nodes.values():
        for condition in node.boundary_conditions:
            # if the condition is on the flux, add the boundary condition expression
            if condition.condition_type in _flux_dof_register.flux_dof_couples:
                bc_expr, bc_param = _build_boundary_condition_expression(
                    condition, quantities
                )
                dof = node.get_flux_dof(condition.condition_type)

                bc_index = state.get_variable_index(dof.dof_id)
                bc_expressions.append((bc_index, bc_expr, bc_param))

    return bc_expressions


def _get_model_saved_quantities_expressions(
    model_id: str,
    model_desc: ModelComponentDescription,
    models: dict[str, ModelComponent],
) -> list[tuple[str, Expression, ModelComponent, int, int]]:
    expressions = [
        (
            term_def.term_id,
            saved_qty_expr_def.expression,
            models[model_id],
            term_def.size,
            term_def.index,
        )
        for saved_qty_expr_def in model_desc.saved_quantities_expressions
        for term_def in saved_qty_expr_def.terms
    ]
    for submodel_id, submodel_desc in model_desc.submodels.items():
        expressions.extend(
            _get_model_saved_quantities_expressions(submodel_id, submodel_desc, models)
        )

    return expressions


def build_saved_quantities(
    net: Net, models: dict[str, ModelComponent]
) -> SavedQuantities:
    """
    Create the saved quantities register for the simulation.

    :param net: the simulation net
    :type net: Net
    :param models: the models in the simulations
    :type models: dict[str, ModelComponent]
    :return: the simulation saved quantities
    :rtype: SavedQuantities
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


class SimulationFactory:
    """
    Factory for **Simulation** objects

    :param simulation_type: The simulation type to create
    :type simulation_type: type[AbstractSimulation]

    :param net: the net to initialize the simulation parameters
    :type net: Net

    :param solver: the solver the simulation will use
    :type solver: AbstractSolver

    :param simulation_options: additional simulation options depending on the
      simulation type
    :type simulation_options: dict[str, Any]
    """

    def __init__(
        self,
        simulation_type: type[AbstractSimulation],
        solver: AbstractSolver | None = None,
        net: Net | None = None,
        simulation_options: dict[str, Any] | None = None,
    ):
        self.simulation_type = simulation_type
        self.solver = solver if solver is not None else NewtonSolver()
        self.net = net if net is not None else Net()
        self.simulation_options = (
            simulation_options if simulation_options is not None else {}
        )

    def create_simulation(self) -> AbstractSimulation:
        """
        Create a **Simulation** instance.

        :return: a simulation instance.
        :rtype: AbstractSimulation
        """

        if issubclass(self.simulation_type, AbstractSimulation) is False:
            raise TypeError(
                str.format(
                    "{0} is not a {1} sub-class.",
                    self.simulation_type.__name__,
                    AbstractSimulation.__name__,
                )
            )

        time_manager = TimeManager()
        state = build_state(self.net)
        parameters = build_parameters(self.net, state)
        all_quantities = _build_quantities(parameters, state, time_manager)
        models = build_blocks(self.net, all_quantities)
        saved_quantities = build_saved_quantities(self.net, models)
        expressions = _build_net_expressions(self.net, state, models, all_quantities)
        eq_system = build_eq_system(expressions, state)

        # Log simulation informations
        _logger.info(str.format("Net:{1}{0}", self.net, linesep))
        _logger.info(str.format("State:{1}{0}", state, linesep))
        _logger.info(str.format("System:{1}{0}", eq_system, linesep))

        return self.simulation_type(
            factory=self,
            time_manager=time_manager,
            state=state,
            parameters=parameters,
            saved_quantities=saved_quantities,
            models=models,
            solver=self.solver,
            eq_system=eq_system,
            **self.simulation_options,
        )
