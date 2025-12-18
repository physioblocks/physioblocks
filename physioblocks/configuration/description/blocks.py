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
Define how to configure block.
"""

from typing import Any

from physioblocks.configuration.base import Configuration, ConfigurationError
from physioblocks.configuration.constants import (
    BLOCK_FLUX_TYPE_ITEM_ID,
    MODEL_COMPONENT_TYPE_ITEM_ID,
    SUBMODEL_ITEM_ID,
)
from physioblocks.configuration.functions import load, save
from physioblocks.description.blocks import BlockDescription, ModelComponentDescription
from physioblocks.registers.load_function_register import loads
from physioblocks.registers.save_function_register import saves
from physioblocks.registers.type_register import (
    get_registered_type,
    get_registered_type_id,
)
from physioblocks.simulation.time_manager import TIME_QUANTITY_ID

VARIABLES_ITEM_ID = "variables"
"""Constant for variables item id in the global id dict"""

PARAMETERS_ITEM_ID = "parameters"
"""Constant for parameters item id in the global id dict"""

SAVED_QUANTITIES_ITEM_ID = "saved_quantities"
"""Constant for saved quantities item id in the global id dict"""


@saves(ModelComponentDescription)
def save_model_component_config(
    model_component: ModelComponentDescription, *args: Any, **kwargs: Any
) -> Configuration:
    """
    Create a Configuration for a model description.

    :param model_component: the model_component description
    :type model_component: ModelComponentDescription

    :return: the configuration
    :rtype: Configuration
    """

    description_type_id = get_registered_type_id(type(model_component))
    model_type_id = get_registered_type_id(model_component.described_type)
    config = Configuration(description_type_id)
    config[MODEL_COMPONENT_TYPE_ITEM_ID] = model_type_id

    # save local ids
    global_ids = _get_global_ids(model_component)

    config.configuration_items.update(global_ids)

    # save sub-models
    if len(model_component.submodels) > 0:
        config[SUBMODEL_ITEM_ID] = save(model_component.submodels, *args, **kwargs)

    return config


@saves(BlockDescription)
def save_block_description_config(
    block_description: BlockDescription, *args: Any, **kwargs: Any
) -> Configuration:
    config: Configuration = save_model_component_config(block_description)
    config[BLOCK_FLUX_TYPE_ITEM_ID] = block_description.flux_type
    return config


def _get_global_ids(model: ModelComponentDescription) -> dict[str, Any]:
    global_ids: dict[str, Any] = {}

    for local_id, global_id in model.global_ids.items():
        if global_id == TIME_QUANTITY_ID:
            global_ids[TIME_QUANTITY_ID] = TIME_QUANTITY_ID
        elif model.described_type.has_internal_variable(local_id):
            if VARIABLES_ITEM_ID not in global_ids:
                global_ids[VARIABLES_ITEM_ID] = {}
            global_ids[VARIABLES_ITEM_ID][local_id] = global_id
        elif model.described_type.has_saved_quantity(local_id):
            if SAVED_QUANTITIES_ITEM_ID not in global_ids:
                global_ids[SAVED_QUANTITIES_ITEM_ID] = {}
            global_ids[SAVED_QUANTITIES_ITEM_ID][local_id] = global_id
        else:
            if PARAMETERS_ITEM_ID not in global_ids:
                global_ids[PARAMETERS_ITEM_ID] = {}
            global_ids[PARAMETERS_ITEM_ID][local_id] = global_id

    return global_ids


@loads(ModelComponentDescription)
def load_model_component_config(
    configuration: Configuration,
    configuration_key: str,
    configuration_type: type[ModelComponentDescription],
    configuration_object: BlockDescription | None = None,
    additional_model_arguments: dict[str, Any] | None = None,
    *args: Any,
    **kwargs: Any,
) -> ModelComponentDescription:
    """
    Load a model component description from a configuration.

    :param config: the configuration
    :type config: Configuration

    :return: the model description
    :rtype: ModelComponentDescription
    """
    additional_model_arguments = (
        {} if additional_model_arguments is None else additional_model_arguments
    )
    model_type = get_registered_type(configuration[MODEL_COMPONENT_TYPE_ITEM_ID])

    model_ids = {}
    model_ids = _get_model_global_ids(configuration)

    sub_models_desc = {}
    if SUBMODEL_ITEM_ID in configuration.configuration_items:
        sub_models_desc = load(configuration[SUBMODEL_ITEM_ID], *args, **kwargs)

    if configuration_object is not None:
        new_model_ids = configuration_object.global_ids.copy()
        new_model_ids.update(model_ids)
        new_submodels = configuration_object.submodels
        new_submodels.update(sub_models_desc)
    else:
        new_model_ids = model_ids
        new_submodels = sub_models_desc

    return configuration_type(
        configuration_key,
        model_type,
        global_ids=new_model_ids,
        submodels=new_submodels,
        **additional_model_arguments,
    )


@loads(BlockDescription)
def load_block_description_config(
    configuration: Configuration,
    configuration_key: str,
    configuration_type: type[ModelComponentDescription],
    configuration_object: BlockDescription | None = None,
    *args: Any,
    **kwargs: Any,
) -> BlockDescription:
    if BLOCK_FLUX_TYPE_ITEM_ID not in configuration:
        raise ConfigurationError(
            str.format(
                """Missing item {0} in block {1}.""",
                BLOCK_FLUX_TYPE_ITEM_ID,
                configuration_key,
            )
        )
    block_additional_arguments = {
        BLOCK_FLUX_TYPE_ITEM_ID: configuration[BLOCK_FLUX_TYPE_ITEM_ID]
    }
    return load_model_component_config(
        configuration,
        configuration_key,
        configuration_type,
        configuration_object,
        *args,
        additional_model_arguments=block_additional_arguments,
        **kwargs,
    )  # type: ignore


def _get_model_global_ids(config: Configuration) -> dict[str, str]:
    model_ids = config.configuration_items.copy()

    # remove the submodels and model type keys from the model ids (keep them in the
    # configuration)
    if SUBMODEL_ITEM_ID in model_ids:
        model_ids.pop(SUBMODEL_ITEM_ID)

    if MODEL_COMPONENT_TYPE_ITEM_ID in model_ids:
        model_ids.pop(MODEL_COMPONENT_TYPE_ITEM_ID)

    if BLOCK_FLUX_TYPE_ITEM_ID in model_ids:
        model_ids.pop(BLOCK_FLUX_TYPE_ITEM_ID)

    # Recursivlely unfold global id in configuration or dict:
    model_ids = _unfold_global_ids(model_ids)

    return model_ids


def _unfold_global_ids(global_ids: dict[str, Any]) -> dict[str, str]:
    result = {}

    for key, value in global_ids.items():
        if isinstance(value, str):
            result[key] = value
        elif isinstance(value, dict):
            result.update(_unfold_global_ids(value))
        elif isinstance(value, Configuration):
            result.update(_unfold_global_ids(value.configuration_items))
        else:
            raise ConfigurationError(
                str.format(
                    """{0}: {1} is not configurable as a model local to global id.""",
                    key,
                    value,
                )
            )
    return result
