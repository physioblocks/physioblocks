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
import inspect
import warnings
from typing import Any

from physioblocks.computing.quantities import QUANTITY_ID
from physioblocks.configuration.base import Configuration
from physioblocks.configuration.constants import (
    PARAMETERS_ID,
    POST_PROCESSES_ID,
    PRE_PROCESSES_ID,
    QUANTITY_MAGNITUDE_ID,
    QUANTITY_VALUE_ID,
    RANGE_LENGTH_ID,
    SIMULATION_OPTIONS,
    STATE_ID,
    TIME_ID,
    TIME_STEP_MIN_VAL_ID,
    UPDATE_FUNCTIONS,
)
from physioblocks.configuration.migrations import migrate_keys, migrates
from physioblocks.registers.type_register import get_registered_type
from physioblocks.simulation.base import RANGE_ID
from physioblocks.simulation.forward import FORWARD_SIM_ID
from physioblocks.simulation.functions import (
    ABSTRACT_FUNCTION_TYPE_ID,
    SIMULATION_FUNCTION_EVALUATION_QUANTITIES,
    AbstractFunction,
)
from physioblocks.simulation.time_manager import TIME_QUANTITY_ID

_MIGRATION_VERSION = "2.0.0"
_TIME_MANAGER_TYPE_ID = "time"
_RANGE_DURATION_ID = "duration"
_VARIABLES_INITIALIZATION_ID = "variables_initialization"
_VARIABLES_MAGNITUDES_ID = "variables_magnitudes"
_OLD_PRE_PROCESS_KEY = "pre-processes"
_OLD_POST_PROCESS_KEY = "post-processes"


@migrates(FORWARD_SIM_ID, version=_MIGRATION_VERSION)
def _migrate_simulation_config(configuration: Configuration) -> Configuration:
    config_copy = configuration.copy()

    # Defining update functions in the parameter section is deprecated.
    # Use the "update_functions" mapping instead
    parameters_config = config_copy.get(PARAMETERS_ID, {})
    update_functions_config = config_copy.get(UPDATE_FUNCTIONS, {})
    config_copy[PARAMETERS_ID], config_copy[UPDATE_FUNCTIONS] = (
        _migrates_time_functions(parameters_config, update_functions_config)
    )

    # The time manager object is deleted in configuration
    # Use the time field with a range object and simulation options instead
    time_config = config_copy.get(TIME_ID, None)
    if isinstance(time_config, Configuration):
        time_config, min_step = _migrate_time_config(time_config)
        config_copy[TIME_ID] = time_config
        if SIMULATION_OPTIONS not in config_copy:
            config_copy[SIMULATION_OPTIONS] = {}
        if min_step is not None:
            config_copy[SIMULATION_OPTIONS][TIME_STEP_MIN_VAL_ID] = min_step

    # merge variable initialization and variable magnitudes into the
    # state field.
    config_copy = _migrate_state_initialization(config_copy)

    # Hyphen is removed from pre and post processes keys:
    processes_map = {
        _OLD_PRE_PROCESS_KEY: PRE_PROCESSES_ID,
        _OLD_POST_PROCESS_KEY: POST_PROCESSES_ID,
    }
    config_copy = migrate_keys(config_copy, processes_map, deprecated=True)

    return config_copy


def _migrates_time_functions(
    parameters_config: dict[str, Any], update_function_config: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    updated_parameters_config = parameters_config.copy()
    merged_update_functions_config = update_function_config.copy()

    for param_id, param_config in parameters_config.items():
        if isinstance(param_config, Configuration) and _is_time_function(
            get_registered_type(param_config.label)
        ):
            param_config.configuration_items[
                SIMULATION_FUNCTION_EVALUATION_QUANTITIES
            ] = {TIME_QUANTITY_ID: TIME_QUANTITY_ID}
            merged_update_functions_config[param_id] = param_config
            updated_parameters_config.pop(param_id)

            deprecation_message = str.format(
                "Key {0}: "
                "declaring time and state dependent functions in the {1} field is "
                "deprecated. Declare a function with the correct {2} in the {3} "
                "field instead.",
                param_id,
                PARAMETERS_ID,
                SIMULATION_FUNCTION_EVALUATION_QUANTITIES,
                UPDATE_FUNCTIONS,
            )
            warnings.warn(
                deprecation_message, category=DeprecationWarning, stacklevel=2
            )

    return updated_parameters_config, merged_update_functions_config


def _is_time_function(function_type: Any) -> bool:
    if (
        isinstance(function_type, type) is False
        or issubclass(function_type, AbstractFunction) is False
    ):
        return False

    evaluation_parameters = inspect.signature(function_type.eval).parameters
    return TIME_QUANTITY_ID in evaluation_parameters


def _migrate_time_config(time_config: Configuration) -> tuple[Configuration, Any]:
    if time_config.label == _TIME_MANAGER_TYPE_ID:
        min_step = time_config.configuration_items.pop(TIME_STEP_MIN_VAL_ID, None)
        range_items = time_config.configuration_items.copy()
        length = range_items.pop(_RANGE_DURATION_ID, None)
        if length is not None:
            range_items[RANGE_LENGTH_ID] = length
        range_config = Configuration(RANGE_ID, range_items)

        deprecation_message = str.format(
            "The '{0}' configuration object is deprecated. "
            "Use the '{1}' field with a '{2}' configuration object and set the '{3}' "
            "in '{4}' field instead",
            _TIME_MANAGER_TYPE_ID,
            TIME_ID,
            RANGE_ID,
            TIME_STEP_MIN_VAL_ID,
            SIMULATION_OPTIONS,
        )
        warnings.warn(deprecation_message, category=DeprecationWarning, stacklevel=2)

        return range_config, min_step

    time_config = migrate_keys(
        time_config,
        {_RANGE_DURATION_ID: RANGE_LENGTH_ID},
        deprecated=True,
        overwrite=True,
    )

    return time_config, None


def _migrate_state_initialization(
    config_copy: Configuration,
) -> Configuration:
    state_config = config_copy.get(STATE_ID, {})
    variables_initialization = config_copy.configuration_items.pop(
        _VARIABLES_INITIALIZATION_ID, None
    )
    variables_magnitudes = config_copy.configuration_items.pop(
        _VARIABLES_MAGNITUDES_ID, None
    )

    if variables_initialization is not None or variables_magnitudes is not None:
        config_copy[STATE_ID] = _merge_state_initialization(
            state_config, variables_initialization, variables_magnitudes
        )
        deprecation_message = str.format(
            "Using '{0}' or '{1}' to initialize state values is deprecated. "
            "Use the '{2}' field instead and populate it with '{3}' configuration "
            "items initializing '{4}' and '{5}'.",
            _VARIABLES_INITIALIZATION_ID,
            _VARIABLES_MAGNITUDES_ID,
            STATE_ID,
            QUANTITY_ID,
            QUANTITY_VALUE_ID,
            QUANTITY_MAGNITUDE_ID,
        )
        warnings.warn(deprecation_message, category=DeprecationWarning, stacklevel=2)

    return config_copy


def _merge_state_initialization(
    state_config: dict[str, Configuration],
    variables_initialization: dict[str, Any] | None,
    variables_magnitudes: dict[str, Any] | None,
) -> dict[str, Configuration]:
    state_config_copy = state_config.copy()
    variables_initialization = (
        variables_initialization if variables_initialization is not None else {}
    )
    variables_magnitudes = (
        variables_magnitudes if variables_magnitudes is not None else {}
    )
    variables_keys = set.union(
        set(variables_initialization.keys()), set(variables_magnitudes.keys())
    )
    for variable_id in variables_keys:
        quantity_config = Configuration(QUANTITY_ID)
        quantity_config[QUANTITY_VALUE_ID] = variables_initialization.get(
            variable_id, 0.0
        )
        quantity_config[QUANTITY_MAGNITUDE_ID] = variables_magnitudes.get(
            variable_id, 1.0
        )
        state_config_copy[variable_id] = quantity_config
    return state_config_copy


@migrates(ABSTRACT_FUNCTION_TYPE_ID, _MIGRATION_VERSION)
def _migrate_evaluation_quantities(configuration: Configuration) -> Configuration:
    config_copy = configuration.copy()

    if SIMULATION_FUNCTION_EVALUATION_QUANTITIES not in configuration:
        function_type = get_registered_type(configuration.label)
        eval_parameter_names = set(inspect.signature(function_type.eval).parameters)
        eval_parameter_names.remove("self")
        eval_quantities_names = (
            eval_parameter_names & configuration.configuration_items.keys()
        )
        if len(eval_quantities_names) != 0:
            config_copy.configuration_items[
                SIMULATION_FUNCTION_EVALUATION_QUANTITIES
            ] = {
                key: config_copy.configuration_items.pop(key)
                for key in eval_quantities_names
            }

            deprecation_message = str.format(
                "{0}: passing '{1}' directly is deprecated, declare it in "
                "'{2}' field instead with the matching quantity.",
                function_type.__name__,
                "', '".join(eval_quantities_names),
                SIMULATION_FUNCTION_EVALUATION_QUANTITIES,
            )
            warnings.warn(
                deprecation_message, category=DeprecationWarning, stacklevel=2
            )

    return config_copy
