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
"""Declares load and save functions for simulation objects."""

from typing import Any

from physioblocks.configuration.base import Configuration
from physioblocks.configuration.functions import load, save
from physioblocks.registers.load_function_register import loads
from physioblocks.registers.save_function_register import saves
from physioblocks.registers.type_register import (
    get_registered_type,
    get_registered_type_id,
)
from physioblocks.simulation.functions import (
    SIMULATION_FUNCTION_EVALUATION_QUANTITIES,
    SimulationFunctionFactory,
)


@loads(SimulationFunctionFactory)
def load_simulation_factory_function(
    configuration: Configuration,
    configuration_references: dict[str, Any],
    *args: Any,
    **kwargs: Any,
) -> SimulationFunctionFactory[Any]:
    """
    Load a simulation factory function configuration.

    Parameters
    ----------
    configuration : Configuration
        the configuration to load.
    configuration_references : dict[str, Any]
        references to initialize function parameters and variables.

    Returns
    -------
    SimulationFunctionFactory[Any]
        the configured simulation function factory
    """
    function_type = get_registered_type(configuration.label)
    config_items_copy = configuration.configuration_items.copy()
    evaluation_quantities = config_items_copy.pop(
        SIMULATION_FUNCTION_EVALUATION_QUANTITIES, {}
    )
    parameters = load(
        config_items_copy,
        configuration_type=dict,
        configuration_references=configuration_references,
    )
    return SimulationFunctionFactory(function_type, evaluation_quantities, parameters)


@saves(SimulationFunctionFactory)
def save_simulation_factory_function(
    function_factory: SimulationFunctionFactory[Any],
    *args: Any,
    **kwargs: Any,
) -> Configuration:
    """
    Save a simulation factory function.

    Parameters
    ----------
    function_factory : SimulationFunctionFactory[Any]
        the function to save.

    Returns
    -------
    Configuration
        the simulation factory configuration.
    """
    type_id = get_registered_type_id(function_factory.function_type)
    config = Configuration(
        type_id,
        save(function_factory.function_parameters, *args, **kwargs),
    )
    if len(function_factory.evaluation_quantities) > 0:
        config[SIMULATION_FUNCTION_EVALUATION_QUANTITIES] = (
            function_factory.evaluation_quantities
        )
    return config
