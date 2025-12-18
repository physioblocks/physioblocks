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

import physioblocks.simulation.setup as setup
from physioblocks.computing.models import Block, Expression
from physioblocks.computing.quantities import Quantity
from physioblocks.description.blocks import ID_SEPARATOR, BlockDescription
from physioblocks.description.nets import (
    Net,
)
from physioblocks.simulation.runtime import AbstractSimulation
from physioblocks.simulation.solvers import AbstractSolver
from physioblocks.simulation.state import State
from physioblocks.simulation.time_manager import TIME_QUANTITY_ID

SUBBLOCK_ID = "subblock"
INTERNAL_VAR_ID = "var_id"
FLUX_TYPE_ID = "flux_type"
DOF_P1_ID = "p1"
DOF_P2_ID = "p2"
DOF_TYPE_ID = "dof_type"
NODE_0_ID = "node_0"
NODE_1_ID = "node_1"
BLOCK_ID = "block"
FLUX_ID = "flux"
DOF_0_ID = ID_SEPARATOR.join([NODE_0_ID, DOF_TYPE_ID])
DOF_1_ID = ID_SEPARATOR.join([NODE_1_ID, DOF_TYPE_ID])
INTERNAL_VARIABLE_LOCAL_ID = "internal_variable"


@dataclass
class BlockTest(Block):
    p1: Quantity[Any]
    p2: Quantity[Any]
    internal_variable: Quantity[Any]


def empty_func(model: BlockTest):
    pass


BlockTest.declares_flux_expression(0, DOF_P1_ID, Expression(1, empty_func))
BlockTest.declares_flux_expression(1, DOF_P2_ID, Expression(1, empty_func))
BlockTest.declares_internal_expression(
    INTERNAL_VARIABLE_LOCAL_ID, Expression(1, empty_func)
)


@pytest.fixture
@patch.multiple(
    "physioblocks.description.nets._flux_type_register",
    create=True,
    _fluxes_types={FLUX_TYPE_ID: DOF_TYPE_ID},
    _dof_types={DOF_TYPE_ID: FLUX_TYPE_ID},
)
def net():
    net = Net()
    node_0_id = NODE_0_ID
    node_1_id = NODE_1_ID
    net.add_node(node_0_id)
    net.add_node(node_1_id)
    net.add_block(
        BLOCK_ID,
        BlockDescription(
            BLOCK_ID,
            BlockTest,
            FLUX_TYPE_ID,
            global_ids={
                DOF_P1_ID: DOF_0_ID,
                DOF_P2_ID: DOF_1_ID,
                INTERNAL_VARIABLE_LOCAL_ID: INTERNAL_VAR_ID,
            },
        ),
        {0: node_0_id, 1: node_1_id},
    )

    return net


@patch.multiple(
    "physioblocks.simulation.setup._flux_dof_register",
    create=True,
    _fluxes_types={FLUX_TYPE_ID: DOF_TYPE_ID},
    _dof_types={DOF_TYPE_ID: FLUX_TYPE_ID},
)
class TestSetupMethods:
    def test_build_state(self, net: Net):
        state_0 = setup.build_state(net)
        assert INTERNAL_VAR_ID in state_0
        assert DOF_0_ID in state_0
        assert DOF_1_ID in state_0

        net.set_boundary(NODE_1_ID, DOF_TYPE_ID, DOF_1_ID)
        net.set_boundary(NODE_0_ID, FLUX_TYPE_ID, FLUX_ID)
        state_1 = setup.build_state(net)
        assert INTERNAL_VAR_ID in state_1
        assert DOF_0_ID in state_1
        assert DOF_1_ID not in state_1

    def test_build_parameters(self, net: Net):
        net.set_boundary(NODE_1_ID, DOF_TYPE_ID, DOF_1_ID)
        net.set_boundary(NODE_0_ID, FLUX_TYPE_ID, FLUX_ID)

        state = setup.build_state(net)
        register = setup.build_parameters(net, state)

        assert DOF_1_ID in register
        assert FLUX_ID in register
        assert DOF_0_ID not in register
        assert TIME_QUANTITY_ID not in register
        assert INTERNAL_VAR_ID not in register

    def test_build_eq_system(self):
        expression = Expression(1, empty_func, {INTERNAL_VAR_ID: empty_func})
        expressions = [
            (0, expression, None),
        ]
        state = State()
        state.add_variable(INTERNAL_VAR_ID, 0.0)
        eq_system = setup.build_eq_system(expressions, state)
        assert eq_system.system_size == 1


class TestSimulationFactory:
    @patch.multiple(
        "physioblocks.simulation.setup._flux_dof_register",
        create=True,
        _fluxes_types={FLUX_TYPE_ID: DOF_TYPE_ID},
        _dof_types={DOF_TYPE_ID: FLUX_TYPE_ID},
    )
    @patch.multiple(AbstractSolver, __abstractmethods__=set())
    @patch.multiple(AbstractSimulation, __abstractmethods__=set())
    def test_create_simulation(self):
        net = Net()
        node_0_id = NODE_0_ID
        node_1_id = NODE_1_ID
        net.add_node(node_0_id)
        net.add_node(node_1_id)

        net.add_block(
            BLOCK_ID,
            BlockDescription(
                BLOCK_ID,
                BlockTest,
                FLUX_TYPE_ID,
                global_ids={
                    DOF_P1_ID: DOF_0_ID,
                    DOF_P2_ID: DOF_1_ID,
                    INTERNAL_VARIABLE_LOCAL_ID: INTERNAL_VAR_ID,
                },
            ),
            {0: node_0_id, 1: node_1_id},
        )

        net.set_boundary(node_1_id, DOF_TYPE_ID, DOF_1_ID)
        net.set_boundary(node_0_id, FLUX_TYPE_ID, FLUX_ID)

        sim_factory = setup.SimulationFactory(
            AbstractSimulation,
            AbstractSolver(),
            net,
        )
        sim = sim_factory.create_simulation()
        assert sim.state.size == 2

    @patch.multiple(AbstractSolver, __abstractmethods__=set())
    def test_wrong_simulation_type(self):
        err_message = str.format(
            "{0} is not a {1} sub-class.", object.__name__, AbstractSimulation.__name__
        )
        with pytest.raises(TypeError, match=err_message):
            sim_factory = setup.SimulationFactory(object, AbstractSolver())
            sim_factory.create_simulation()
