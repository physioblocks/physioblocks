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

from unittest.mock import MagicMock, patch

import pytest

from physioblocks.description.blocks import BlockDescription, ModelComponentDescription
from physioblocks.description.nets import Net, Node

NODE_ID = "node"
NODE_A_ID = "node_a"
NODE_B_ID = "node_b"

FLUX_ID = "flux"
FLUX_A_ID = "flux_a"
FLUX_TYPE = "flux_type"
FLUX_TYPE_A = "flux_type_a"
FLUX_TYPE_B = "flux_type_b"

DOF_ID = "dof"
DOF_A_ID = "dof_a"
DOF_B_ID = "dof_b"
DOF_TYPE = "dof_type"
DOF_TYPE_A = "dof_type_a"
DOF_TYPE_B = "dof_type_b"

POTENTIAL_A = "potential_a"
POTENTIAL_B = "potential_b"
OTHER_ID = "other_id"
BLOCK_ID = "block"
BLOCK_A_ID = "block_a"
BLOCK_B_ID = "block_b"
BLOCK_C_ID = "block_c"
SUBMODEL_ID = "submodel"
ALTERNATIVE_TAG = "alt"


@pytest.fixture
def expression():
    return MagicMock(size=1)


@pytest.fixture
def term_a_definition():
    return MagicMock(term_id=POTENTIAL_A, size=1, index=0)


@pytest.fixture
def term_b_definition():
    return MagicMock(term_id=POTENTIAL_B, size=1, index=0)


@pytest.fixture
def flux_a_definition(expression, term_a_definition):
    def side_effect_get_term(arg):
        if arg == 0:
            return term_a_definition
        else:
            raise KeyError

    return MagicMock(
        expression=expression,
        terms=[term_a_definition],
        get_term=MagicMock(side_effect=side_effect_get_term),
    )


@pytest.fixture
def flux_b_definition(expression, term_a_definition, term_b_definition):
    def side_effect_get_term(arg):
        if arg == 0:
            return term_b_definition
        else:
            raise KeyError

    return MagicMock(
        expression=expression,
        terms=[term_b_definition],
        get_term=MagicMock(side_effect=side_effect_get_term),
    )


@pytest.fixture
def block_a_type(flux_a_definition):
    return MagicMock(
        nodes=[0],
        fluxes_expressions={0: flux_a_definition},
        local_ids=[POTENTIAL_A],
    )


@pytest.fixture
def block_b_type(flux_a_definition, flux_b_definition):
    return MagicMock(
        nodes=[0, 1],
        fluxes_expressions={0: flux_a_definition, 1: flux_b_definition},
        local_ids=[POTENTIAL_A, POTENTIAL_B],
    )


@pytest.fixture
def submodel_type():
    return MagicMock(
        local_ids=[POTENTIAL_A],
    )


@pytest.fixture
def block_no_potential_type(flux_a_definition):
    return MagicMock(
        nodes=[0],
        fluxes_expressions={0: flux_a_definition},
        local_ids=[],
    )


@patch.multiple(
    "physioblocks.description.nets._flux_type_register",
    create=True,
    _fluxes_types={
        FLUX_TYPE: DOF_TYPE,
        FLUX_TYPE_A: DOF_TYPE_A,
        FLUX_TYPE_B: DOF_TYPE_B,
    },
    _dof_types={DOF_TYPE: FLUX_TYPE, DOF_TYPE_A: FLUX_TYPE_A, DOF_TYPE_B: FLUX_TYPE_B},
)
class TestNode:
    def test_constructor(self):
        node = Node(NODE_ID)
        assert node.name == NODE_ID
        assert node.dofs == []
        assert node.is_boundary is False
        assert node.boundary_conditions == []
        assert node.local_nodes == []

    def test_set(self):
        node = Node(NODE_ID)

        with pytest.raises(AttributeError):
            node.name = ""

        with pytest.raises(AttributeError):
            node.dofs = []

        with pytest.raises(AttributeError):
            node.local_nodes = []

        with pytest.raises(AttributeError):
            node.is_boundary = True

        with pytest.raises(AttributeError):
            node.boundary_conditions = []

    def test_add_remove_dof(self):
        node = Node(NODE_ID)
        node.add_dof(DOF_ID, DOF_TYPE)
        assert node.dofs[0].dof_id == DOF_ID
        assert node.dofs[0].dof_type == DOF_TYPE

        node.remove_dof(DOF_TYPE)
        assert node.dofs == []

    def test_add_dof_with_unregistered_type(self):
        node = Node(NODE_ID)

        with pytest.raises(
            ValueError,
            match=f"Can not create a Dof with unregister dof type {OTHER_ID}",
        ):
            node.add_dof(DOF_ID, OTHER_ID)

    def test_has_flux_type(self):
        node = Node(NODE_ID)
        node.add_dof(DOF_A_ID, DOF_TYPE_A)
        assert node.has_flux_type(FLUX_TYPE_A) is True
        assert node.has_flux_type(FLUX_TYPE_B) is False

    def test_get_dof(self):
        node = Node(NODE_ID)
        node.add_dof(DOF_ID, DOF_TYPE)

        assert node.dofs[0] == node.get_dof(DOF_ID)

    def test_get_dof_with_unregistered_dof(self):
        node = Node(NODE_ID)
        with pytest.raises(KeyError):
            node.get_dof(OTHER_ID)

    def test_get_flux_dof(self):
        node = Node(NODE_ID)
        node.add_dof(DOF_ID, DOF_TYPE)

        assert node.dofs[0] == node.get_flux_dof(FLUX_TYPE)

    def test_get_flux_dof_with_unregistered_flux(self):
        node = Node(NODE_ID)

        with pytest.raises(KeyError):
            node.get_flux_dof(FLUX_TYPE)

    def test_add_remove_boundaries_on_flux(self):
        node = Node(NODE_ID)
        node.add_dof(DOF_ID, DOF_TYPE)
        node.add_boundary_condition(FLUX_TYPE, FLUX_ID)

        assert node.boundary_conditions[0].condition_type == FLUX_TYPE
        assert node.boundary_conditions[0].condition_id == FLUX_ID

        node.remove_boundary_condition(FLUX_TYPE)
        assert len(node.boundary_conditions) == 0

    def test_add_remove_boundaries_on_dof(self):
        node = Node(NODE_ID)
        node.add_dof(DOF_ID, DOF_TYPE)
        node.add_boundary_condition(DOF_TYPE, DOF_ID)

        assert node.boundary_conditions[0].condition_type == DOF_TYPE
        assert node.boundary_conditions[0].condition_id == DOF_ID

        node.remove_boundary_condition(DOF_TYPE)
        assert len(node.boundary_conditions) == 0

    def test_add_boundaries_with_pre_existing_condition(self):
        node = Node(NODE_ID)
        node.add_dof(DOF_ID, DOF_TYPE)
        node.add_boundary_condition(FLUX_TYPE, FLUX_ID)

        with pytest.raises(ValueError):
            node.add_boundary_condition(DOF_TYPE, OTHER_ID)

        with pytest.raises(ValueError):
            node.add_boundary_condition(FLUX_TYPE, OTHER_ID)

        node.remove_boundary_condition(FLUX_TYPE)
        node.add_boundary_condition(DOF_TYPE, DOF_ID)

        with pytest.raises(ValueError):
            node.add_boundary_condition(DOF_TYPE, OTHER_ID)

        with pytest.raises(ValueError):
            node.add_boundary_condition(FLUX_TYPE, OTHER_ID)

    def test_add_boundaries_with_no_matching_type(self):
        node = Node(NODE_ID)
        with pytest.raises(ValueError):
            node.add_boundary_condition(DOF_TYPE, DOF_ID)

        with pytest.raises(ValueError):
            node.add_boundary_condition(FLUX_TYPE, DOF_ID)

    def test_is_boundary_false(self):
        node = Node(NODE_ID)
        assert node.is_boundary is False

    def test_is_boundary_true(self):
        node = Node(NODE_ID)
        node.add_dof(DOF_ID, DOF_TYPE)
        node.add_boundary_condition(FLUX_TYPE, FLUX_ID)
        assert node.is_boundary is True

    def test_node_add_remove_node_local_true(self):
        node = Node(NODE_ID)
        node.add_node_local(BLOCK_ID, 1)
        assert node.local_nodes == [(BLOCK_ID, 1)]

        node.remove_node_local(BLOCK_ID, 1)
        assert node.local_nodes == []

    def test_node_has_node_local_false(self):
        node = Node(NODE_ID)
        assert node.has_node_local(BLOCK_ID, 0) is False

    def test_node_has_node_local_true(self):
        node = Node(NODE_ID)
        node.add_node_local(BLOCK_ID, 0)
        assert node.has_node_local(BLOCK_ID, 0) is True


@patch.multiple(
    "physioblocks.description.nets._flux_type_register",
    create=True,
    _fluxes_types={
        FLUX_TYPE: DOF_TYPE,
        FLUX_TYPE_A: DOF_TYPE_A,
        FLUX_TYPE_B: DOF_TYPE_B,
    },
    _dof_types={DOF_TYPE: FLUX_TYPE, DOF_TYPE_A: FLUX_TYPE_A, DOF_TYPE_B: FLUX_TYPE_B},
)
class TestNet:
    def test_default_constructor(self):
        net = Net()
        assert net.blocks == {}
        assert net.nodes == {}

    def test_set_raise_attribute_error(self):
        net = Net()
        with pytest.raises(AttributeError):
            net.blocks = {}

        with pytest.raises(AttributeError):
            net.nodes = {}

        with pytest.raises(AttributeError):
            net.boundary_conditions = {}

    def test_cant_update(self):
        net = Net()

        net.blocks[BLOCK_ID] = MagicMock()
        assert net.blocks == {}

        net.nodes[NODE_ID] = MagicMock()
        assert net.nodes == {}

        net.boundary_conditions[NODE_ID] = [MagicMock()]
        assert net.boundary_conditions == {}

    def test_add_remove_node(self):
        net = Net()
        node = net.add_node(NODE_ID)

        assert len(net.nodes) == 1
        assert NODE_ID in net.nodes
        assert node == net.nodes[NODE_ID]

        net.remove_node(NODE_ID)
        assert NODE_ID not in net.nodes
        assert len(net.nodes) == 0

    def test_add_node_raise_error(self):
        net = Net()
        net.add_node(NODE_ID)

        with pytest.raises(
            ValueError, match=f"There is already a node with id {NODE_ID} in the net"
        ):
            net.add_node(NODE_ID)

    def test_add_remove_block(self, block_a_type):
        net = Net()
        net.add_node(NODE_ID)

        net.add_block(
            BLOCK_ID,
            BlockDescription(BLOCK_ID, block_a_type, FLUX_TYPE),
            {0: NODE_ID},
        )

        assert BLOCK_ID in net.blocks
        assert len(net.blocks) == 1
        assert net.blocks[BLOCK_ID].global_ids[POTENTIAL_A] == f"{NODE_ID}.{DOF_TYPE}"

        net.remove_block(BLOCK_ID)
        assert BLOCK_ID not in net.blocks
        assert len(net.blocks) == 0

    def test_add_blocks_renames_submodels(self, block_a_type, submodel_type):
        submodel_desc = ModelComponentDescription(
            SUBMODEL_ID, submodel_type, {POTENTIAL_A: f"{BLOCK_ID}.{POTENTIAL_A}"}
        )
        net = Net()
        net.add_node(NODE_ID)
        net.add_block(
            BLOCK_ID,
            BlockDescription(
                BLOCK_ID,
                block_a_type,
                FLUX_TYPE,
                submodels={SUBMODEL_ID: submodel_desc},
            ),
            {0: NODE_ID},
        )
        assert net.blocks[BLOCK_ID].global_ids[POTENTIAL_A] == f"{NODE_ID}.{DOF_TYPE}"
        assert (
            net.blocks[BLOCK_ID].submodels[SUBMODEL_ID].global_ids[POTENTIAL_A]
            == f"{NODE_ID}.{DOF_TYPE}"
        )

    def test_remove_node_removes_block(self, block_a_type):
        net = Net()
        net.add_node(NODE_ID)
        net.add_block(
            BLOCK_ID,
            BlockDescription(BLOCK_ID, block_a_type, FLUX_TYPE),
            {0: NODE_ID},
        )
        net.remove_node(NODE_ID)
        assert len(net.nodes) == 0
        assert len(net.blocks) == 0

    def test_add_blocks_different_flux_types(self, block_a_type):
        net = Net()
        net.add_node(NODE_ID)

        net.add_block(
            BLOCK_A_ID,
            BlockDescription(BLOCK_A_ID, block_a_type, FLUX_TYPE_A),
            {0: NODE_ID},
        )

        net.add_block(
            BLOCK_B_ID,
            BlockDescription(BLOCK_B_ID, block_a_type, FLUX_TYPE_B),
            {0: NODE_ID},
        )

        assert BLOCK_A_ID in net.blocks
        assert (
            net.blocks[BLOCK_A_ID].global_ids[POTENTIAL_A] == f"{NODE_ID}.{DOF_TYPE_A}"
        )
        assert BLOCK_B_ID in net.blocks
        assert (
            net.blocks[BLOCK_B_ID].global_ids[POTENTIAL_A] == f"{NODE_ID}.{DOF_TYPE_B}"
        )

        assert len(net.blocks) == 2
        assert len(net.nodes) == 1
        assert net.nodes[NODE_ID].has_flux_type(FLUX_TYPE_A) is True
        assert net.nodes[NODE_ID].has_flux_type(FLUX_TYPE_B) is True
        assert net.nodes[NODE_ID].dofs[0].dof_type == DOF_TYPE_A
        assert net.nodes[NODE_ID].dofs[1].dof_type == DOF_TYPE_B

    def test_add_multiple_blocks(self, block_a_type, block_b_type):
        net = Net()
        net.add_node(NODE_A_ID)
        net.add_node(NODE_B_ID)

        net.add_block(
            BLOCK_A_ID,
            BlockDescription(BLOCK_A_ID, block_a_type, FLUX_TYPE_A),
            {0: NODE_A_ID},
        )
        net.add_block(
            BLOCK_B_ID,
            BlockDescription(BLOCK_B_ID, block_b_type, FLUX_TYPE_A),
            {0: NODE_A_ID, 1: NODE_B_ID},
        )
        assert len(net.nodes) == 2
        assert NODE_A_ID in net.nodes
        assert NODE_B_ID in net.nodes

        assert len(net.blocks) == 2
        assert BLOCK_A_ID in net.blocks
        assert (
            net.blocks[BLOCK_A_ID].global_ids[POTENTIAL_A]
            == f"{NODE_A_ID}.{DOF_TYPE_A}"
        )
        assert BLOCK_B_ID in net.blocks
        assert (
            net.blocks[BLOCK_B_ID].global_ids[POTENTIAL_A]
            == f"{NODE_A_ID}.{DOF_TYPE_A}"
        )
        assert (
            net.blocks[BLOCK_B_ID].global_ids[POTENTIAL_B]
            == f"{NODE_B_ID}.{DOF_TYPE_A}"
        )

    def test_add_block_raise_id_exists(self, block_a_type):
        net = Net()
        net.add_node(NODE_ID)
        net.add_block(
            BLOCK_ID,
            BlockDescription(BLOCK_ID, block_a_type, FLUX_TYPE_A),
            {0: NODE_ID},
        )

        err_msg = str.format(
            "Block with id {0} is already defined in the net.", BLOCK_ID
        )
        with pytest.raises(ValueError, match=err_msg):
            net.add_block(
                BLOCK_ID,
                BlockDescription(BLOCK_ID, block_a_type, FLUX_TYPE_A),
                {0: NODE_A_ID},
            )

    def test_add_block_raise_nodes_size_greater(self, block_a_type):
        net = Net()
        net.add_node(NODE_A_ID)
        net.add_node(NODE_B_ID)

        with pytest.raises(
            ValueError,
            match=f"Linked node ids list and {BLOCK_ID} local nodes list size mismatch",
        ):
            net.add_block(
                BLOCK_ID,
                BlockDescription(BLOCK_ID, block_a_type, FLUX_TYPE_A),
                {0: NODE_A_ID, 1: NODE_B_ID},
            )

    def test_add_block_raise_nodes_size_lesser(self, block_b_type):
        net = Net()
        net.add_node(NODE_ID)

        with pytest.raises(
            ValueError,
            match=f"Linked node ids list and {BLOCK_ID} local nodes list size mismatch",
        ):
            net.add_block(
                BLOCK_ID,
                BlockDescription(BLOCK_ID, block_b_type, FLUX_TYPE_A),
                {0: NODE_ID},
            )

    def test_local_to_global_node_id(self, block_a_type):
        net = Net()
        net.add_node(NODE_ID)

        net.add_block(
            BLOCK_ID,
            BlockDescription(BLOCK_ID, block_a_type, FLUX_TYPE_A),
            {0: NODE_ID},
        )
        assert net.local_to_global_node_id(BLOCK_ID, 0) == NODE_ID

    def test_local_to_global_node_id_multiple_blocks(self, block_a_type, block_b_type):
        net = Net()
        net.add_node(NODE_A_ID)
        net.add_node(NODE_B_ID)

        net.add_block(
            BLOCK_A_ID,
            BlockDescription(BLOCK_A_ID, block_a_type, FLUX_TYPE_A),
            {0: NODE_A_ID},
        )
        net.add_block(
            BLOCK_B_ID,
            BlockDescription(BLOCK_B_ID, block_b_type, FLUX_TYPE_A),
            {0: NODE_A_ID, 1: NODE_B_ID},
        )

        assert net.local_to_global_node_id(BLOCK_A_ID, 0) == NODE_A_ID
        assert net.local_to_global_node_id(BLOCK_B_ID, 0) == NODE_A_ID
        assert net.local_to_global_node_id(BLOCK_B_ID, 1) == NODE_B_ID

    def test_local_to_global_node_id_raise_error(self):
        net = Net()
        with pytest.raises(ValueError):
            net.local_to_global_node_id(BLOCK_ID, 0)

    def test_set_remove_flux_boundary(self, block_a_type):
        net = Net()
        node = net.add_node(NODE_ID)

        net.add_block(
            BLOCK_ID,
            BlockDescription(BLOCK_ID, block_a_type, FLUX_TYPE),
            {0: NODE_ID},
        )

        net.set_boundary(NODE_ID, FLUX_TYPE, FLUX_ID)
        assert len(node.boundary_conditions) == 1
        assert node.boundary_conditions[0].condition_type == FLUX_TYPE
        assert node.boundary_conditions[0].condition_id == FLUX_ID
        assert NODE_ID in net.boundary_conditions

        net.remove_boundary(NODE_ID, FLUX_TYPE)
        assert len(node.boundary_conditions) == 0
        assert NODE_ID not in net.boundary_conditions

    def test_set_remove_dof_boundary(self, block_a_type):
        net = Net()
        node = net.add_node(NODE_ID)

        net.add_block(
            BLOCK_ID,
            BlockDescription(BLOCK_ID, block_a_type, FLUX_TYPE),
            {0: NODE_ID},
        )
        net.set_boundary(NODE_ID, DOF_TYPE, DOF_ID)
        assert len(node.boundary_conditions) == 1
        assert node.boundary_conditions[0].condition_type == DOF_TYPE
        assert node.boundary_conditions[0].condition_id == DOF_ID
        assert NODE_ID in net.boundary_conditions
        assert net.blocks[BLOCK_ID].global_ids[POTENTIAL_A] == DOF_ID

        net.remove_boundary(NODE_ID, DOF_TYPE)
        assert len(node.boundary_conditions) == 0
        assert NODE_ID not in net.boundary_conditions

    def test_set_boundary_already_defined_flux(self, block_a_type):
        net = Net()
        net.add_node(NODE_ID)
        net.add_block(
            BLOCK_ID,
            BlockDescription(BLOCK_ID, block_a_type, FLUX_TYPE),
            {0: NODE_ID},
        )

        net.set_boundary(NODE_ID, FLUX_TYPE, FLUX_ID)

        with pytest.raises(ValueError):
            net.set_boundary(NODE_ID, FLUX_TYPE, FLUX_A_ID)

        with pytest.raises(ValueError):
            net.set_boundary(NODE_ID, DOF_TYPE, DOF_ID)

    def test_set_boundary_already_defined_dof(self, block_a_type):
        net = Net()
        net.add_node(NODE_ID)
        net.add_block(
            BLOCK_ID,
            BlockDescription(BLOCK_ID, block_a_type, FLUX_TYPE),
            {0: NODE_ID},
        )

        net.set_boundary(NODE_ID, DOF_TYPE, DOF_ID)

        with pytest.raises(ValueError):
            net.set_boundary(NODE_ID, DOF_TYPE, DOF_A_ID)

        with pytest.raises(ValueError):
            net.set_boundary(NODE_ID, FLUX_TYPE, FLUX_ID)

    def test_set_boundary_with_no_matching_flux(self):
        net = Net()
        net.add_node(NODE_A_ID)

        with pytest.raises(ValueError):
            net.set_boundary(NODE_A_ID, FLUX_TYPE_A, FLUX_ID)

    def test_set_boundary_with_no_matching_dof(self):
        net = Net()
        net.add_node(NODE_A_ID)

        with pytest.raises(ValueError):
            net.set_boundary(NODE_A_ID, DOF_TYPE_A, FLUX_ID)

    def test_set_boundary_multiple_dofs_error(self):
        net = Net()
        net.add_node(NODE_ID)

        # Manually add a second DOF to create the error condition
        net.nodes[NODE_ID].add_dof(DOF_ID, DOF_TYPE)
        net.nodes[NODE_ID].add_dof(DOF_ID, DOF_TYPE)

        with pytest.raises(
            ValueError, match="There are multiple dof matching condition_type"
        ):
            net.set_boundary(NODE_ID, DOF_TYPE, DOF_ID)

    def test_set_dof_boundary_renames_submodels(self, block_a_type, submodel_type):
        submodel_desc = ModelComponentDescription(
            SUBMODEL_ID, submodel_type, {POTENTIAL_A: POTENTIAL_A}
        )
        net = Net()
        net.add_node(NODE_ID)
        net.add_block(
            BLOCK_ID,
            BlockDescription(
                BLOCK_ID,
                block_a_type,
                FLUX_TYPE,
                global_ids={POTENTIAL_A: POTENTIAL_A},
                submodels={SUBMODEL_ID: submodel_desc},
            ),
            {0: NODE_ID},
        )
        net.set_boundary(NODE_ID, DOF_TYPE, DOF_ID)
        assert net.blocks[BLOCK_ID].global_ids[POTENTIAL_A] == DOF_ID
        assert (
            net.blocks[BLOCK_ID].submodels[SUBMODEL_ID].global_ids[POTENTIAL_A]
            == DOF_ID
        )

    def test_remove_node_removes_boundary(self, block_a_type):
        net = Net()
        net.add_node(NODE_ID)
        net.add_block(
            BLOCK_ID,
            BlockDescription(BLOCK_ID, block_a_type, FLUX_TYPE),
            {0: NODE_ID},
        )
        net.set_boundary(NODE_ID, DOF_TYPE, DOF_ID)
        net.remove_node(NODE_ID)

        assert len(net.nodes) == 0
        assert len(net.boundary_conditions) == 0

    def test_get_alternative_net_empty(self):
        net = Net()

        alternative_net = net.get_alternative_net(OTHER_ID)

        assert isinstance(alternative_net, Net) is True
        assert alternative_net.blocks == {}
        assert alternative_net.nodes == {}
        assert alternative_net.boundary_conditions == {}

    def test_get_alternative_net(self, block_a_type):
        net = Net()
        net.add_node(NODE_ID)

        # Add blocks with alternatives
        net.add_block(
            BLOCK_ID,
            BlockDescription(
                BLOCK_ID,
                block_a_type,
                FLUX_TYPE_A,
                alternative_types={ALTERNATIVE_TAG: block_a_type},
            ),
            {0: NODE_ID},
        )

        alternative_net = net.get_alternative_net(ALTERNATIVE_TAG)

        assert BLOCK_ID in alternative_net.blocks
        assert alternative_net.blocks[BLOCK_ID] is not net.blocks[BLOCK_ID]

        assert NODE_ID in alternative_net.nodes
        assert alternative_net.nodes[NODE_ID] is not net.nodes[NODE_ID]

    def test_get_alternative_net_with_dof_boundary(self, block_a_type):
        net = Net()
        net.add_node(NODE_ID)
        net.add_block(
            BLOCK_ID,
            BlockDescription(
                BLOCK_ID,
                block_a_type,
                FLUX_TYPE,
                alternative_types={ALTERNATIVE_TAG: block_a_type},
            ),
            {0: NODE_ID},
        )
        net.set_boundary(NODE_ID, DOF_TYPE, DOF_ID)

        alternative_net = net.get_alternative_net(ALTERNATIVE_TAG)

        assert NODE_ID in alternative_net.boundary_conditions
        assert len(alternative_net.boundary_conditions[NODE_ID]) == 1
        assert alternative_net.boundary_conditions[NODE_ID][0].condition_id == DOF_ID
        assert (
            alternative_net.boundary_conditions[NODE_ID][0].condition_type == DOF_TYPE
        )

    def test_get_alternative_net_with_flux_boundary(self, block_a_type):
        net = Net()
        net.add_node(NODE_ID)
        net.add_block(
            BLOCK_ID,
            BlockDescription(
                BLOCK_ID,
                block_a_type,
                FLUX_TYPE,
                alternative_types={ALTERNATIVE_TAG: block_a_type},
            ),
            {0: NODE_ID},
        )
        net.set_boundary(NODE_ID, FLUX_TYPE, FLUX_ID)

        alternative_net = net.get_alternative_net(ALTERNATIVE_TAG)

        assert NODE_ID in alternative_net.boundary_conditions
        assert len(alternative_net.boundary_conditions[NODE_ID]) == 1
        assert alternative_net.boundary_conditions[NODE_ID][0].condition_id == FLUX_ID
        assert (
            alternative_net.boundary_conditions[NODE_ID][0].condition_type == FLUX_TYPE
        )

    def test_get_alternative_net_with_missing_flux_in_alternative(
        self, block_a_type, block_b_type
    ):
        net = Net()
        net.add_node(NODE_A_ID)
        net.add_node(NODE_B_ID)

        net.add_block(
            BLOCK_ID,
            BlockDescription(
                BLOCK_ID,
                block_b_type,
                FLUX_TYPE,
                alternative_types={ALTERNATIVE_TAG: block_a_type},
            ),
            {0: NODE_A_ID, 1: NODE_B_ID},
        )

        alternative_net = net.get_alternative_net(ALTERNATIVE_TAG)

        assert NODE_A_ID in alternative_net.nodes
        assert NODE_B_ID not in alternative_net.nodes
        assert BLOCK_ID in alternative_net.blocks
