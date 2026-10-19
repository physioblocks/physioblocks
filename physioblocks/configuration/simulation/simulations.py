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

"""Declares simulations save and load functions."""

from collections.abc import Iterable
from os import linesep
from typing import Any

from physioblocks.computing.quantities import QuantityInit
from physioblocks.configuration.base import Configuration, ConfigurationError
from physioblocks.configuration.constants import (
    DATA_ID,
    DEFAULT_SIMULATION_NAME,
    NET_ID,
    OBSERVER_CONFIGURATION_ID,
    OUTPUTS_FUNCTIONS_ID,
    PARAMETERS_ID,
    PLOTS_CONFIGURATION_ID,
    POST_PROCESSES_ID,
    PRE_PROCESSES_ID,
    SIMULATION_NAME,
    SIMULATION_OPTIONS,
    SIMULATION_TYPE_ID,
    SOLVER_ID,
    STATE_ID,
    TIME_ID,
    UPDATE_FUNCTIONS,
)
from physioblocks.configuration.functions import load, save
from physioblocks.description.flux import FluxDofTypesRegister
from physioblocks.description.nets import Net
from physioblocks.registers.load_function_register import loads
from physioblocks.registers.save_function_register import saves
from physioblocks.registers.type_register import get_registered_type
from physioblocks.simulation import AbstractSimulation
from physioblocks.simulation.base import (
    MODEL_FACTORY_ID,
    SimulationFactory,
    SimulationModelFactory,
    SimulationRange,
)
from physioblocks.simulation.estimation import (
    ESTIMATED_PARAMETERS_ID,
    FILTER_OPTIONS_ID,
    FILTER_TYPE_ID,
    OBSERVER_FACTORY_ID,
    EstimationSimulation,
    ObserverFactory,
)
from physioblocks.simulation.forward import ForwardSimulation
from physioblocks.simulation.functions import (
    SimulationFunctionFactory,
)
from physioblocks.simulation.solvers import NewtonSolver


@loads(SimulationFactory)
def load_simulation_factory(
    config: Configuration,
    *args: Any,
    **kwargs: Any,
) -> SimulationFactory[Any]:
    """
    Load a simulation factory configuration.

    Parameters
    ----------
    config : Configuration
        the configuration to load.

    Returns
    -------
    SimulationFactory[Any]
        the configured simulation factory.
    """
    config_copy = config.copy()

    name = config_copy.get(SIMULATION_NAME, DEFAULT_SIMULATION_NAME)
    sim_type: type[AbstractSimulation] = get_registered_type(config_copy.label)
    solver = (
        load(config_copy[SOLVER_ID]) if SOLVER_ID in config_copy else NewtonSolver()
    )
    net = (
        load(config_copy[NET_ID])
        if NET_ID in config_copy
        else Net(FluxDofTypesRegister())
    )
    parameters_init = (
        load(config_copy[PARAMETERS_ID], configuration_sort=True)
        if PARAMETERS_ID in config_copy
        else {}
    )
    time = (
        load(config_copy[TIME_ID], configuration_references=parameters_init)
        if TIME_ID in config_copy
        else SimulationRange()
    )

    update_functions_factories: dict[str, SimulationFunctionFactory[Any]] = (
        _load_update_functions(config_copy[UPDATE_FUNCTIONS], parameters_init)
        if UPDATE_FUNCTIONS in config_copy
        else {}
    )

    state_init = (
        load(config_copy[STATE_ID], configuration_references=parameters_init)
        if STATE_ID in config_copy
        else {}
    )
    output_functions_factories: dict[str, SimulationFunctionFactory[Any]] = (
        _load_update_functions(
            config_copy[OUTPUTS_FUNCTIONS_ID],
            parameters_init,
        )
        if OUTPUTS_FUNCTIONS_ID in config_copy
        else {}
    )
    data = load(config_copy[DATA_ID]) if DATA_ID in config_copy else {}
    preprocesses = (
        load(config_copy[PRE_PROCESSES_ID], configuration_references=parameters_init)
        if PRE_PROCESSES_ID in config_copy
        else {}
    )
    postprocesses = (
        load(config_copy[POST_PROCESSES_ID], configuration_references=parameters_init)
        if POST_PROCESSES_ID in config_copy
        else {}
    )
    sim_options = (
        load(config_copy[SIMULATION_OPTIONS], configuration_references=parameters_init)
        if SIMULATION_OPTIONS in config_copy
        else {}
    )
    simulation_model_factory = SimulationModelFactory(
        net, time, state_init, parameters_init, update_functions_factories, solver
    )
    return SimulationFactory(
        name,
        sim_type,
        simulation_model_factory,
        output_functions_factories,
        data,
        preprocesses,
        postprocesses,
        sim_options,
    )


def _load_update_functions(
    update_functions: dict[str, Any], references: dict[str, Any]
) -> dict[str, SimulationFunctionFactory[Any]]:
    return {
        param_id: load(
            update_function_config,
            configuration_references=references,
            configuration_type=SimulationFunctionFactory,
        )
        for param_id, update_function_config in update_functions.items()
    }


@loads(ForwardSimulation)
def load_forward_simulation_config(
    config: Configuration,
    *args: Any,
    **kwargs: Any,
) -> ForwardSimulation:
    """Load a forward simulation configuration.

    Parameters
    ----------
    config : Configuration
        the configuration

    Returns
    -------
    ForwardSimulation
        the simulation

    Raises
    ------
    ConfigurationError
        if parameters or state variables are missing in the configuration.

    """
    config_copy = config.copy()
    if PLOTS_CONFIGURATION_ID in config_copy:
        config_copy.configuration_items.pop(PLOTS_CONFIGURATION_ID)

    simulation_factory: SimulationFactory[ForwardSimulation] = load(
        config_copy, configuration_type=SimulationFactory
    )

    forward_simulation = simulation_factory.create_simulation()

    # Check parameters initialization
    all_parameters = list(simulation_factory.simulation_model_factory.parameters.keys())
    all_parameters.extend(
        simulation_factory.simulation_model_factory.update_functions.keys()
    )
    _check_missing_keys(
        PARAMETERS_ID,
        all_parameters,
        forward_simulation.simulation_model.parameters,
    )
    _check_missing_keys(
        STATE_ID,
        simulation_factory.simulation_model_factory.state,
        forward_simulation.simulation_model.state,
    )

    return forward_simulation


@loads(EstimationSimulation)
def load_estimation_simulation_config(
    config: Configuration,
    *args: Any,
    **kwargs: Any,
) -> EstimationSimulation:
    """Load an estimation simulation configuration.

    Parameters
    ----------
    config : Configuration
        the configuration

    Returns
    -------
    EstimationSimulation
        the simulation

    Raises
    ------
    ConfigurationError
        if parameters or state variables are missing in the configuration.

    """
    config_copy = config.copy()
    if PLOTS_CONFIGURATION_ID in config_copy:
        config_copy.configuration_items.pop(PLOTS_CONFIGURATION_ID)

    simulation_factory: SimulationFactory[EstimationSimulation] = load(
        config_copy, configuration_type=SimulationFactory
    )

    filter_type: str = config_copy.configuration_items[FILTER_TYPE_ID]
    filter_options: dict[str, Any] = config_copy.configuration_items.get(
        FILTER_OPTIONS_ID, {}
    )

    observer_factory: ObserverFactory = (
        load(
            config_copy[OBSERVER_CONFIGURATION_ID],
            configuration_references=simulation_factory.simulation_model_factory.parameters,
        )
        if OBSERVER_CONFIGURATION_ID in config_copy
        else ObserverFactory()
    )

    estimated_parameters: dict[str, QuantityInit] = (
        load(
            config_copy[ESTIMATED_PARAMETERS_ID],
            configuration_references=simulation_factory.simulation_model_factory.parameters,
        )
        if ESTIMATED_PARAMETERS_ID in config_copy
        else {}
    )

    simulation_factory.simulation_options.update(
        {
            FILTER_TYPE_ID: filter_type,
            FILTER_OPTIONS_ID: filter_options,
            OBSERVER_FACTORY_ID: observer_factory,
            ESTIMATED_PARAMETERS_ID: estimated_parameters,
        }
    )
    estimation_simulation = simulation_factory.create_simulation()

    # Check parameters initialization
    all_parameters = list(simulation_factory.simulation_model_factory.parameters.keys())
    all_parameters.extend(
        simulation_factory.simulation_model_factory.update_functions.keys()
    )
    all_parameters.extend(estimated_parameters.keys())
    _check_missing_keys(
        PARAMETERS_ID,
        all_parameters,
        estimation_simulation.simulation_model.parameters,
    )
    _check_missing_keys(
        STATE_ID,
        simulation_factory.simulation_model_factory.state,
        estimation_simulation.simulation_model.state,
    )

    return estimation_simulation


@saves(AbstractSimulation)
def save_simulation_config(
    simulation: AbstractSimulation, *args: Any, **kwargs: Any
) -> Configuration:
    """Save a simulation configuration.

    Parameters
    ----------
    simulation : AbstractSimulation
        the simulation to save

    Returns
    -------
    Configuration
        the configuration

    """
    sim_config: Configuration = save(simulation.factory)
    sim_type = sim_config.configuration_items.pop(SIMULATION_TYPE_ID)
    sim_config.label = sim_type

    model_factory_configuration: Configuration = sim_config.configuration_items.pop(
        MODEL_FACTORY_ID
    )
    sim_config.configuration_items.update(
        model_factory_configuration.configuration_items
    )

    return sim_config


def _check_missing_keys(
    name: str, tested: Iterable[str], reference: Iterable[str]
) -> None:
    missing_keys = [key for key in reference if key not in tested]
    if len(missing_keys) > 0:
        raise ConfigurationError(
            str.format(
                "Missing keys in {0} configuration:{2}{1}", name, missing_keys, linesep
            )
        )
