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

from unittest.mock import PropertyMock, patch

import pytest

import physioblocks.registers.type_register as type_reg
from physioblocks.computing.models import (
    Block,
    BlockMetaClass,
    Expression,
    ExpressionDefinition,
    TermDefinition,
)
from physioblocks.configuration import Configuration
from physioblocks.configuration.constants import (
    BLOCK_FLUX_TYPE_ITEM_ID,
    BLOCKS_ITEM_ID,
    BOUNDARIES_ID,
    CONDITION_NAME_ID,
    CONDITION_TYPE_ID,
    FLUX_DOF_DEFINITION_ID,
    MODEL_COMPONENT_TYPE_ITEM_ID,
    NET_ID,
    NODES_ITEM_ID,
)
from physioblocks.configuration.description.nets import load_net_config, save_net_config
from physioblocks.description.blocks import BLOCK_DESCRIPTION_TYPE_ID, BlockDescription
from physioblocks.description.nets import BOUNDARY_CONDITION_ID, BoundaryCondition, Net
from tests.helpers.assertion_helpers import assert_net_equals

BLOCK_DESC_ID = "Block"
FLUX_TYPE = "flux_type"
DOF_TYPE = "dof_type"
DOF_ID = "dof"
FLUX_ID = "flux"

NODE_0_ID = "n0"
NODE_1_ID = "n1"
BLOCK_0_ID = "b0"


@pytest.fixture
def ref_expression():
    return Expression(1, None)


@pytest.fixture
def ref_nodes():
    return {0: [FLUX_TYPE], 1: [FLUX_TYPE]}


@pytest.fixture
def flux_definition(ref_expression):
    return ExpressionDefinition(ref_expression, [TermDefinition(DOF_ID, 1)])


@pytest.fixture
def ref_flux_expressions(flux_definition):
    return {0: flux_definition, 1: flux_definition}


@pytest.fixture
def ref_config() -> Configuration:
    config = Configuration(NET_ID)

    config[FLUX_DOF_DEFINITION_ID] = {FLUX_TYPE: DOF_TYPE}
    config[NODES_ITEM_ID] = [NODE_0_ID, NODE_1_ID]
    blocks = {}
    block_item = Configuration(BLOCK_DESCRIPTION_TYPE_ID)
    block_item[MODEL_COMPONENT_TYPE_ITEM_ID] = BLOCK_DESC_ID
    block_item[BLOCK_FLUX_TYPE_ITEM_ID] = FLUX_TYPE
    block_item[NODES_ITEM_ID] = {}
    block_item[NODES_ITEM_ID]["0"] = NODE_0_ID
    block_item[NODES_ITEM_ID]["1"] = NODE_1_ID
    blocks[BLOCK_0_ID] = block_item
    config[BLOCKS_ITEM_ID] = blocks
    config[BOUNDARIES_ID] = {
        NODE_0_ID: [
            Configuration(
                BOUNDARY_CONDITION_ID,
                {CONDITION_TYPE_ID: FLUX_TYPE, CONDITION_NAME_ID: FLUX_ID},
            )
        ],
        NODE_1_ID: [
            Configuration(
                BOUNDARY_CONDITION_ID,
                {CONDITION_TYPE_ID: DOF_TYPE, CONDITION_NAME_ID: DOF_ID},
            )
        ],
    }

    return config


@pytest.fixture
@patch.multiple(
    "physioblocks.description.nets._flux_type_register",
    create=True,
    _fluxes_types={FLUX_TYPE: DOF_TYPE},
    _dof_types={DOF_TYPE: FLUX_TYPE},
)
def ref_net(ref_flux_expressions, ref_nodes) -> Net:
    with patch.multiple(
        BlockMetaClass,
        fluxes_expressions=PropertyMock(return_value=ref_flux_expressions),
        nodes=PropertyMock(return_value=ref_nodes),
    ):
        net = Net()
        net.add_node(NODE_0_ID)
        net.add_node(NODE_1_ID)
        net.add_block(
            BLOCK_0_ID,
            BlockDescription(BLOCK_0_ID, Block, FLUX_TYPE),
            {0: NODE_0_ID, 1: NODE_1_ID},
        )

        net.set_boundary(NODE_0_ID, FLUX_TYPE, FLUX_ID)
        net.set_boundary(NODE_1_ID, DOF_TYPE, DOF_ID)
        return net


@patch.multiple(
    "physioblocks.description.nets._flux_type_register",
    create=True,
    _fluxes_types={FLUX_TYPE: DOF_TYPE},
    _dof_types={DOF_TYPE: FLUX_TYPE},
)
@patch.object(
    type_reg,
    attribute="__type_register",
    new={
        BLOCK_DESCRIPTION_TYPE_ID: BlockDescription,
        BlockDescription: BLOCK_DESCRIPTION_TYPE_ID,
        BLOCK_DESC_ID: Block,
        Block: BLOCK_DESC_ID,
        BOUNDARY_CONDITION_ID: BoundaryCondition,
        BoundaryCondition: BOUNDARY_CONDITION_ID,
    },
)
class TestNetConfiguration:
    def test_get_net_config(
        self, ref_net: Net, ref_config: Configuration, ref_flux_expressions, ref_nodes
    ):
        with patch.multiple(
            BlockMetaClass,
            fluxes_expressions=PropertyMock(return_value=ref_flux_expressions),
            nodes=PropertyMock(return_value=ref_nodes),
        ):
            net_configuration = save_net_config(ref_net)
            assert ref_config == net_configuration

    def test_create_net_from_config(
        self, ref_net: Net, ref_config: Configuration, ref_nodes, ref_flux_expressions
    ):
        with patch.multiple(
            BlockMetaClass,
            fluxes_expressions=PropertyMock(return_value=ref_flux_expressions),
            nodes=PropertyMock(return_value=ref_nodes),
        ):
            net = load_net_config(ref_config, Net)
            assert_net_equals(net, ref_net)
