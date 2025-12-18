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

from unittest.mock import patch

import pytest

from physioblocks.computing.models import (
    Block,
    Expression,
    ExpressionDefinition,
    TermDefinition,
)
from physioblocks.description.blocks import BlockDescription
from physioblocks.description.flux import Dof
from physioblocks.description.nets import Net, Node

NODE_ID = "node"

FLUX_TYPE = "flux_type"
FLUX_TYPE_A = "flux_type_a"
FLUX_TYPE_B = "flux_type_b"

DOF_TYPE = "dof_type"
DOF_TYPE_A = "dof_type_a"
DOF_TYPE_B = "dof_type_b"

POTENTIAL_A = "potential_a"
POTENTIAL_B = "potential_b"


@pytest.fixture
def expression():
    return Expression(1, None, {})


@pytest.fixture
def flux_definition_type_a(expression):
    return ExpressionDefinition(expression, [TermDefinition(POTENTIAL_A, 1)])


@pytest.fixture
def flux_definition_type_b(expression):
    return ExpressionDefinition(expression, [TermDefinition(POTENTIAL_B, 1)])


class BlockA(Block):
    pass


class BlockB(Block):
    pass


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
        dof = Dof("id", DOF_TYPE)
        node.dofs.append(dof)
        assert node.dofs == []

        with pytest.raises(AttributeError):
            node.local_nodes = []
        node.local_nodes.append((0, 0))
        assert node.local_nodes == []

        with pytest.raises(AttributeError):
            node.is_boundary = True

        with pytest.raises(AttributeError):
            node.boundary_conditions = []

        node.boundary_conditions.append(DOF_TYPE)
        assert node.boundary_conditions == []

    def test_add_remove_dof(self):
        node = Node(NODE_ID)
        node.add_dof("dof_type_id", DOF_TYPE)
        assert node.dofs[0].dof_id == "dof_type_id"
        assert node.dofs[0].dof_type == DOF_TYPE

        node.remove_dof(DOF_TYPE)
        assert node.dofs == []

    def test_has_flux_type(self):
        node = Node(NODE_ID)
        node.add_dof("dof_type_a_id", DOF_TYPE_A)
        assert node.has_flux_type(FLUX_TYPE_A) is True
        assert node.has_flux_type(FLUX_TYPE_B) is False

    def test_get_dof(self):
        node = Node(NODE_ID)
        node.add_dof("dof_id", DOF_TYPE)

        assert node.dofs[0] == node.get_dof("dof_id")
        with pytest.raises(KeyError):
            node.get_dof("unregistered_dof_id")

        assert node.dofs[0] == node.get_flux_dof(FLUX_TYPE)
        with pytest.raises(KeyError):
            node.get_flux_dof(FLUX_TYPE_A)

    def test_add_remove_boundaries(self):
        node = Node(NODE_ID)
        condition_id = "condition_id"
        with pytest.raises(ValueError):
            node.add_boundary_condition(DOF_TYPE, condition_id)

        with pytest.raises(ValueError):
            node.add_boundary_condition(FLUX_TYPE, condition_id)

        node.add_dof("dof_id", DOF_TYPE)
        node.add_boundary_condition(FLUX_TYPE, condition_id)
        assert node.boundary_conditions[0].condition_type == FLUX_TYPE
        assert node.boundary_conditions[0].condition_id == condition_id

        with pytest.raises(ValueError):
            node.add_boundary_condition(DOF_TYPE, condition_id)

        with pytest.raises(ValueError):
            node.add_boundary_condition(FLUX_TYPE, condition_id)

        node.remove_boundary_condition(FLUX_TYPE)
        assert len(node.boundary_conditions) == 0

        node.add_boundary_condition(DOF_TYPE, condition_id)
        assert node.boundary_conditions[0].condition_type == DOF_TYPE
        assert node.boundary_conditions[0].condition_id == condition_id
        assert node.dofs[0].dof_id == condition_id

    def test_is_boundary(self):
        node = Node(NODE_ID)
        assert node.is_boundary is False

        condition_id = "cond_id"
        node.add_dof("dof_id", DOF_TYPE)
        node.add_boundary_condition(FLUX_TYPE, condition_id)
        assert node.is_boundary is True

    def test_node_local(self):
        node = Node(NODE_ID)
        assert node.has_node_local(0, 0) is False
        assert node.local_nodes == []

        node.add_node_local(0, 0)
        assert node.has_node_local(0, 0) is True
        assert node.local_nodes == [(0, 0)]

        node.remove_node_local(0, 0)
        assert node.has_node_local(0, 0) is False
        assert node.local_nodes == []


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
    def test_constructor(self):
        net = Net()
        assert net.blocks == {}
        assert net.nodes == {}

    def test_set(self):
        net = Net()
        block_id = "b"
        node_id = "n"
        with pytest.raises(AttributeError):
            net.blocks = {}
        net.blocks[block_id] = BlockDescription(block_id, Block, {})
        assert net.blocks == {}

        with pytest.raises(AttributeError):
            net.nodes = {}
        net.nodes[node_id] = Node(node_id)
        assert net.nodes == {}

        with pytest.raises(ValueError):
            net.local_to_global_node_id(block_id, 0)

    def test_add_remove_node(self):
        net = Net()
        node_a_id = "node_a"
        node_b_id = "node_b"
        node_a = net.add_node(node_a_id)
        node_b = net.add_node(node_b_id)

        assert node_a == net.nodes[node_a_id]
        assert node_b == net.nodes[node_b_id]

        net.remove_node(node_b_id)

        with pytest.raises(KeyError):
            net.nodes[node_b_id]

        with pytest.raises(ValueError):
            net.add_node(node_a_id)

    def test_add_remove_block(self, flux_definition_type_a, flux_definition_type_b):
        with (
            patch.object(
                BlockA,
                attribute="_fluxes",
                new={
                    0: flux_definition_type_a,
                    1: flux_definition_type_a,
                },
            ),
            patch.object(
                BlockB,
                attribute="_fluxes",
                new={0: flux_definition_type_b},
            ),
        ):
            net = Net()
            node_a_id = "node_a"
            node_b_id = "node_b"
            net.add_node(node_a_id)
            net.add_node(node_b_id)

            block_a_id = "block_a"
            block_b_id = "block_b"
            block_c_id = "block_c"

            block_a_desc = net.add_block(
                block_a_id,
                BlockDescription(block_a_id, BlockA, FLUX_TYPE_A),
                {0: node_a_id, 1: node_b_id},
            )

            block_b_desc = net.add_block(
                block_b_id,
                BlockDescription(block_b_id, BlockB, FLUX_TYPE_B),
                {0: node_b_id},
            )

            assert net.local_to_global_node_id(block_a_id, 0) == node_a_id
            assert net.local_to_global_node_id(block_a_id, 1) == node_b_id
            assert net.local_to_global_node_id(block_b_id, 0) == node_b_id

            assert net.blocks[block_a_id] == block_a_desc
            assert net.blocks[block_b_id] == block_b_desc
            assert DOF_TYPE_B in [dof.dof_type for dof in net.nodes[node_b_id].dofs]
            net.add_block(
                block_c_id,
                BlockDescription(block_c_id, BlockA, FLUX_TYPE_A),
                {0: node_a_id, 1: node_b_id},
            )
            net.remove_block(block_c_id)
            assert net.nodes[node_a_id].has_flux_type(FLUX_TYPE_A) is True

            net.remove_block(block_b_id)
            assert DOF_TYPE_B not in [dof.dof_type for dof in net.nodes[node_b_id].dofs]

            with pytest.raises(KeyError):
                net.blocks[block_b_id]

            # id already exists
            err_msg = str.format(
                "Block with id {0} is already defined in the net.", block_a_id
            )
            with pytest.raises(ValueError, match=err_msg):
                net.add_block(
                    block_a_id,
                    BlockDescription(block_a_id, BlockA, FLUX_TYPE_B),
                    {0: node_a_id, 1: node_b_id},
                )

            # too many nodes for block
            err_msg = str.format(
                "Linked node ids list and {0} local nodes list size mismatch.",
                block_b_id,
            )
            with pytest.raises(ValueError, match=err_msg):
                net.add_block(
                    block_b_id,
                    BlockDescription(block_b_id, BlockB, FLUX_TYPE_B),
                    {0: node_a_id, 1: node_b_id},
                )

            net.remove_node(node_a_id)
            with pytest.raises(KeyError):
                net.blocks[block_a_id]

    def test_set_remove_boundary(self, flux_definition_type_a):
        net = Net()
        node_a_id = "node_a"
        node_b_id = "node_b"
        flux_a_id = "flux_a"
        node_a = net.add_node(node_a_id)
        net.add_node(node_b_id)

        # No potential or flux matching the condition
        with pytest.raises(ValueError):
            net.set_boundary(node_a_id, FLUX_TYPE_A, flux_a_id)

        with pytest.raises(ValueError):
            net.set_boundary(node_a_id, DOF_TYPE_A, flux_a_id)

        block_id = "block_a"
        with patch.object(
            BlockA,
            attribute="_fluxes",
            new={0: flux_definition_type_a, 1: flux_definition_type_a},
        ):
            net.add_block(
                block_id,
                BlockDescription(block_id, BlockA, FLUX_TYPE_A),
                {0: node_a_id, 1: node_b_id},
            )

        net.set_boundary(node_a_id, FLUX_TYPE_A, flux_a_id)
        assert node_a.boundary_conditions[0].condition_type == FLUX_TYPE_A
        assert node_a.boundary_conditions[0].condition_id == flux_a_id

        assert net.boundary_conditions[node_a_id] == node_a.boundary_conditions

        # Boundary condition with a matching type already registered
        with pytest.raises(ValueError):
            net.set_boundary(node_a_id, FLUX_TYPE_A, flux_a_id)

        with pytest.raises(ValueError):
            net.set_boundary(node_a_id, DOF_TYPE_A, flux_a_id)

        net.remove_boundary(node_a_id, FLUX_TYPE_A)
        assert len(node_a.boundary_conditions) == 0
