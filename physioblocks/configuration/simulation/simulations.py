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
Define the configuration of simulations
"""

from collections.abc import Iterable
from os import linesep
from typing import Any

from physioblocks.configuration.base import Configuration, ConfigurationError
from physioblocks.configuration.constants import (
    INIT_VARIABLES_ID,
    MAGNITUDES,
    NET_ID,
    OUTPUTS_FUNCTIONS_ID,
    PARAMETERS_ID,
    SOLVER_ID,
    TIME_MANAGER_ID,
    VARIABLES_MAGNITUDES,
)
from physioblocks.configuration.functions import load, save
from physioblocks.registers.load_function_register import loads
from physioblocks.registers.save_function_register import saves
from physioblocks.registers.type_register import get_registered_type_id
from physioblocks.simulation import AbstractFunction
from physioblocks.simulation.functions import (
    is_state_function,
    is_time_function,
)
from physioblocks.simulation.runtime import AbstractSimulation
from physioblocks.simulation.setup import SimulationFactory
from physioblocks.simulation.state import STATE_NAME_ID
from physioblocks.simulation.time_manager import TIME_QUANTITY_ID


@loads(AbstractSimulation)  # type: ignore
def load_simulation_config(
    config: Configuration,
    configuration_type: type,
    configuration_object: AbstractSimulation | None = None,
    *args: Any,
    **kwargs: Any,
) -> AbstractSimulation:
    """
    Load a simulation from a configuration.

    :param config: the configuration
    :type config: Configuration

    :return: the simulation
    :rtype: AbstractSimulation
    """

    if configuration_object is None:
        net = None
        if NET_ID in config:
            net = load(config[NET_ID])

        # Solver
        solver = None
        if SOLVER_ID in config:
            solver = load(config[SOLVER_ID])

        # magnitudes
        magnitudes = None
        if VARIABLES_MAGNITUDES in config:
            magnitudes = load(config[VARIABLES_MAGNITUDES])

        sim_factory = SimulationFactory(
            configuration_type,
            solver,
            net,
            simulation_options={MAGNITUDES: magnitudes},
        )

        configuration_object = sim_factory.create_simulation()

    _configure_simulation(config, configuration_object)

    return configuration_object


def _save_sim_factory(factory: SimulationFactory) -> Configuration:
    simulation_type_id = get_registered_type_id(factory.simulation_type)
    sim_factory_config_item = Configuration(simulation_type_id)
    sim_factory_config_item[NET_ID] = save(factory.net)

    return sim_factory_config_item


@saves(AbstractSimulation)
def save_simulation_config(
    simulation: AbstractSimulation, *args: Any, **kwargs: Any
) -> Configuration:
    """
    Save a simulation in a configuration.

    :param sim: the simulation to save
    :type sim: AbstractSimulation

    :param simulation_type_id: the simulation type id
    :type simulation_type_id: str

    :return: the configuration
    :rtype: Configuration
    """

    sim_config = _save_sim_factory(simulation.factory)

    sim_config[TIME_MANAGER_ID] = save(simulation.time_manager)
    sim_config[SOLVER_ID] = save(simulation.solver)

    # State
    variable_init_values = save(simulation.state.variables)
    if isinstance(variable_init_values, dict):
        sim_config[INIT_VARIABLES_ID] = variable_init_values
    else:
        raise ConfigurationError(
            str.format(
                "Expected a dict for {0} configuration, got {1}.",
                INIT_VARIABLES_ID,
                type(variable_init_values).__name__,
            )
        )
    sim_config[VARIABLES_MAGNITUDES] = save(simulation.magnitudes)

    # Parameters
    # Get quantities
    parameters: dict[str, Any] = {
        key: qty
        for key, qty in simulation.parameters.items()
        if key not in simulation.update_functions
    }
    references: dict[str, Any] = simulation.models.copy()
    parameters_config: dict[str, Any] = save(
        parameters, configuration_references=references
    )
    references.update(parameters)

    # update with fonctions
    function_config = save(
        simulation.update_functions, configuration_references=references
    )
    parameters_config.update(function_config)
    sim_config[PARAMETERS_ID] = parameters_config

    # All the quantities (with update function in the references)
    references.update(simulation.parameters)

    if len(simulation.outputs_functions) > 0:
        sim_config[OUTPUTS_FUNCTIONS_ID] = save(
            simulation.outputs_functions,
            configuration_references=references,
        )

    return sim_config


def _configure_simulation(
    config: Configuration, simulation: AbstractSimulation
) -> None:
    # Set initial values

    # ParameterRegister
    _check_exising_config(PARAMETERS_ID, config)
    _check_missing_keys(PARAMETERS_ID, config[PARAMETERS_ID], simulation.parameters)

    constants_config = {
        key: value
        for key, value in config[PARAMETERS_ID].items()
        if isinstance(value, Configuration) is False
    }
    functions_config = {
        key: value
        for key, value in config[PARAMETERS_ID].items()
        if isinstance(value, Configuration) is True
    }

    # first load the constants
    load(constants_config, configuration_object=simulation.parameters)

    # then load functions
    references: dict[str, Any] = simulation.quantities
    references.update(simulation.models)
    loaded_functions = load(
        functions_config, configuration_references=references, configuration_sort=True
    )
    __initialize_functions(simulation, loaded_functions)

    # Time Manager
    _check_exising_config(TIME_MANAGER_ID, config)
    load(config[TIME_MANAGER_ID], configuration_object=simulation.time_manager)

    # State
    _check_exising_config(INIT_VARIABLES_ID, config)
    _check_missing_keys(INIT_VARIABLES_ID, config[INIT_VARIABLES_ID], simulation.state)

    load(
        config[INIT_VARIABLES_ID],
        configuration_object=simulation.state,
        configuration_references=simulation.quantities,
    )

    references.update(simulation.quantities)
    references.update(simulation.models)

    if OUTPUTS_FUNCTIONS_ID in config:
        outputs = load(
            config[OUTPUTS_FUNCTIONS_ID], configuration_references=references
        )
        __configure_outputs(simulation, outputs)


def __initialize_functions(
    sim: AbstractSimulation, functions_parameters: dict[str, AbstractFunction]
) -> None:
    for param_id, param_value in functions_parameters.items():
        if param_id in sim.parameters:
            arguments: dict[str, Any] = {}
            if is_time_function(param_value):
                sim.register_timed_parameter_update(param_id, param_value)
                arguments[TIME_QUANTITY_ID] = sim.time_manager.time.current
            if is_state_function(param_value):
                arguments[STATE_NAME_ID] = sim.state
            sim.parameters[param_id].initialize(param_value.eval(**arguments))


def __configure_outputs(
    sim: AbstractSimulation, config: dict[str, AbstractFunction]
) -> None:
    for output_id, update_func in config.items():
        sim.register_output_function(output_id, update_func)


def _check_exising_config(key: str, config: Configuration) -> None:
    if key not in config:
        raise ConfigurationError(
            str.format(
                "Missing key {0} in {1} configuration.",
                key,
                config.label,
            )
        )


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
