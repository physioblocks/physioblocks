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

from dataclasses import dataclass
from typing import Any
from unittest.mock import patch

import pytest

from physioblocks.computing.models import Block, ModelComponent
from physioblocks.computing.quantities import Quantity
from physioblocks.configuration import Configuration
from physioblocks.configuration.constants import (
    BLOCK_FLUX_TYPE_ITEM_ID,
    MODEL_COMPONENT_TYPE_ITEM_ID,
    SUBMODEL_ITEM_ID,
)
from physioblocks.configuration.description.blocks import (
    PARAMETERS_ITEM_ID,
    load_block_description_config,
    save_block_description_config,
)
from physioblocks.description.blocks import (
    BLOCK_DESCRIPTION_TYPE_ID,
    ID_SEPARATOR,
    MODEL_DESCRIPTION_TYPE_ID,
    BlockDescription,
    ModelComponentDescription,
)

BLOCK_A_ID = "block_a"
BLOCK_A_TYPE_ID = "BlockA"
MODEL_B_TYPE_ID = "ModelComponentB"
SUBMODEL_KEY = "submodel"
PARAM_LOCAL_ID_A = "a"
PARAM_LOCAL_ID_B = "b"
PARAM_LOCAL_ID_C = "c"
PARAM_GLOBAL_ID_A = "param_a"
PARAM_GLOBAL_ID_B = "param_b"
PARAM_GLOBAL_ID_C = "param_c"
TIME_GLOBAL_ID = "time"
FLUX_TYPE = "flux"


@dataclass
class BlockA(Block):
    a: Quantity[Any]
    b: Quantity[Any]
    c: Quantity[Any]


@dataclass
class ModelComponentB(ModelComponent):
    a: Quantity[Any]
    b: Quantity[Any]
    c: Quantity[Any]


@pytest.fixture
def ref_block_desc():
    block_desc = BlockDescription(
        BLOCK_A_ID,
        BlockA,
        FLUX_TYPE,
        {
            PARAM_LOCAL_ID_A: PARAM_GLOBAL_ID_A,
            PARAM_LOCAL_ID_B: PARAM_GLOBAL_ID_B,
        },
    )
    block_desc.add_submodel(
        SUBMODEL_KEY,
        ModelComponentDescription(
            SUBMODEL_KEY,
            ModelComponentB,
            {
                PARAM_LOCAL_ID_A: PARAM_GLOBAL_ID_C,
                PARAM_LOCAL_ID_B: PARAM_GLOBAL_ID_A,
            },
        ),
    )
    return block_desc


@pytest.fixture
def ref_config() -> Configuration:
    config = Configuration(BLOCK_DESCRIPTION_TYPE_ID)
    config[MODEL_COMPONENT_TYPE_ITEM_ID] = BLOCK_A_TYPE_ID
    config[BLOCK_FLUX_TYPE_ITEM_ID] = FLUX_TYPE
    config[PARAMETERS_ITEM_ID] = {}
    config[PARAMETERS_ITEM_ID][PARAM_LOCAL_ID_A] = PARAM_GLOBAL_ID_A
    config[PARAMETERS_ITEM_ID][PARAM_LOCAL_ID_B] = PARAM_GLOBAL_ID_B
    submodel_config = Configuration(MODEL_DESCRIPTION_TYPE_ID)
    submodel_config[MODEL_COMPONENT_TYPE_ITEM_ID] = MODEL_B_TYPE_ID
    submodel_config[PARAMETERS_ITEM_ID] = {}
    submodel_config[PARAMETERS_ITEM_ID][PARAM_LOCAL_ID_A] = PARAM_GLOBAL_ID_C
    submodel_config[PARAMETERS_ITEM_ID][PARAM_LOCAL_ID_B] = PARAM_GLOBAL_ID_A
    config[SUBMODEL_ITEM_ID] = {SUBMODEL_KEY: submodel_config}
    return config


@pytest.fixture
def saved_config_ref(ref_config: Configuration) -> Configuration:
    config = ref_config
    config[MODEL_COMPONENT_TYPE_ITEM_ID] = BLOCK_A_TYPE_ID
    config[PARAMETERS_ITEM_ID][PARAM_LOCAL_ID_C] = ID_SEPARATOR.join(
        [BLOCK_A_ID, PARAM_LOCAL_ID_C]
    )
    config[SUBMODEL_ITEM_ID][SUBMODEL_KEY][PARAMETERS_ITEM_ID][PARAM_LOCAL_ID_C] = (
        ID_SEPARATOR.join([BLOCK_A_ID, SUBMODEL_KEY, PARAM_LOCAL_ID_C])
    )
    return config


@patch(
    "physioblocks.registers.type_register.__type_register",
    new={
        BLOCK_DESCRIPTION_TYPE_ID: BlockDescription,
        BlockDescription: BLOCK_DESCRIPTION_TYPE_ID,
        MODEL_DESCRIPTION_TYPE_ID: ModelComponentDescription,
        ModelComponentDescription: MODEL_DESCRIPTION_TYPE_ID,
        BLOCK_A_TYPE_ID: BlockA,
        BlockA: BLOCK_A_TYPE_ID,
        MODEL_B_TYPE_ID: ModelComponentB,
        ModelComponentB: MODEL_B_TYPE_ID,
    },
)
def test_get_block_config(
    saved_config_ref: Configuration, ref_block_desc: BlockDescription
):
    configuration = save_block_description_config(ref_block_desc)
    assert saved_config_ref == configuration


@patch(
    "physioblocks.registers.type_register.__type_register",
    new={
        BLOCK_DESCRIPTION_TYPE_ID: BlockDescription,
        BlockDescription: BLOCK_DESCRIPTION_TYPE_ID,
        MODEL_DESCRIPTION_TYPE_ID: ModelComponentDescription,
        ModelComponentDescription: MODEL_DESCRIPTION_TYPE_ID,
        BLOCK_A_TYPE_ID: BlockA,
        BlockA: BLOCK_A_TYPE_ID,
        MODEL_B_TYPE_ID: ModelComponentB,
        ModelComponentB: MODEL_B_TYPE_ID,
    },
)
def test_configure_block(ref_config: Configuration, ref_block_desc: BlockDescription):
    block_desc = load_block_description_config(ref_config, BLOCK_A_ID, BlockDescription)
    assert isinstance(block_desc, BlockDescription)
    assert block_desc.global_ids == ref_block_desc.global_ids
    assert (
        block_desc.submodels[SUBMODEL_KEY].global_ids
        == ref_block_desc.submodels[SUBMODEL_KEY].global_ids
    )
