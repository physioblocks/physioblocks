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
from pathlib import Path
from unittest.mock import MagicMock, PropertyMock, patch

import pytest

from physioblocks.computing.models import (
    BlockMetaClass,
    Expression,
    ExpressionDefinition,
    TermDefinition,
)
from physioblocks.computing.quantities import Quantity
from physioblocks.configuration.constants import NET_ID
from physioblocks.configuration.simulation.simulations import (
    PARAMETERS_ID,
    load_simulation_config,
    save_simulation_config,
)
from physioblocks.description.blocks import (
    BLOCK_DESCRIPTION_TYPE_ID,
    ID_SEPARATOR,
    Block,
    BlockDescription,
)
from physioblocks.description.flux import (
    FLUX_TYPE_REGISTER_ID,
    FluxDofTypesRegister,
)
from physioblocks.description.nets import BOUNDARY_CONDITION_ID, BoundaryCondition, Net
from physioblocks.io.configuration import read_json
from physioblocks.simulation.functions import AbstractFunction
from physioblocks.simulation.runtime import AbstractSimulation, ForwardSimulation
from physioblocks.simulation.setup import SimulationFactory
from physioblocks.simulation.solvers import AbstractSolver
from physioblocks.simulation.time_manager import TIME_MANAGER_ID, TimeManager
from tests.helpers.assertion_helpers import (
    assert_net_equals,
    assert_solvers_equals,
    assert_states_equals,
    assert_time_manager_equals,
)

ref_config_file_path = Path(
    "./tests/tests_config/tests_simulation/simulation_reference.json"
)

DOF_ID = "dof"
SCALAR_ID = "scalar"
VECTOR_ID = "vector"
NODE_A_ID = "node_a"
NODE_B_ID = "node_b"
BLOCK_A_ID = "block_a"
BLOCK_LOCAL_POTENTIAL = "potential_id"
INLET_FLUX_CONDITION_ID = "inlet_flux_condition"
OUTPUT_ID = "output_id"
FLUX_TYPE_ID = "flux_type"
DOF_TYPE_ID = "potential_type"
FUNC_TYPE_ID = "FunctionType"
SIM_TYPE_ID = "SimulationType"
BLOCK_TYPE_ID = "BlockType"
SOLVER_TYPE_ID = "SolverType"
OUTLET_POTENTIAL_CONDITION_ID = ID_SEPARATOR.join([BLOCK_A_ID, BLOCK_LOCAL_POTENTIAL])


@dataclass
class BlockTest(Block):
    potential_id: Quantity


def ref_func():
    pass


@pytest.fixture
def ref_term() -> TermDefinition:
    return TermDefinition(1, DOF_ID)


@pytest.fixture
def ref_expression():
    return Expression(1, ref_func)


@pytest.fixture
def ref_expression_definition(
    ref_expression: Expression, ref_term: TermDefinition
) -> ExpressionDefinition:
    return ExpressionDefinition(ref_expression, [ref_term])


@pytest.fixture
def ref_nodes():
    return {0: [FLUX_TYPE_ID], 1: [FLUX_TYPE_ID]}


@pytest.fixture
def ref_flux_expressions(ref_expression_definition: ExpressionDefinition):
    return {
        0: ref_expression_definition,
        1: ref_expression_definition,
    }


@pytest.fixture
@patch.multiple(
    "physioblocks.description.nets._flux_type_register",
    create=True,
    _fluxes_types={FLUX_TYPE_ID: DOF_TYPE_ID},
    _dof_types={DOF_TYPE_ID: FLUX_TYPE_ID},
)
def net_reference(ref_nodes, ref_flux_expressions):
    with patch.multiple(
        BlockMetaClass,
        fluxes_expressions=PropertyMock(return_value=ref_flux_expressions),
        nodes=PropertyMock(return_value=ref_nodes),
        local_ids=PropertyMock(return_value=[BLOCK_LOCAL_POTENTIAL]),
    ):
        net = Net()
        net.add_node(NODE_A_ID)
        net.add_node(NODE_B_ID)
        net.add_block(
            BLOCK_A_ID,
            BlockDescription(BLOCK_A_ID, BlockTest, FLUX_TYPE_ID),
            {0: NODE_A_ID, 1: NODE_B_ID},
        )

        net.set_boundary(NODE_A_ID, FLUX_TYPE_ID, INLET_FLUX_CONDITION_ID)
        net.set_boundary(NODE_B_ID, DOF_TYPE_ID, OUTLET_POTENTIAL_CONDITION_ID)

        return net


def time_func(self, time):
    return 0.0


def func_init(self):
    pass


@pytest.fixture
@patch.multiple(
    "physioblocks.description.nets._flux_type_register",
    create=True,
    _fluxes_types={FLUX_TYPE_ID: DOF_TYPE_ID},
    _dof_types={DOF_TYPE_ID: FLUX_TYPE_ID},
)
def simulation_reference(net_reference: Net, ref_flux_expressions, ref_nodes):
    with (
        patch.multiple(AbstractSimulation, __abstractmethods__=set()),
        patch.multiple(AbstractSolver, __abstractmethods__=set()),
        patch.multiple(AbstractFunction, __abstractmethods__=set(), eval=time_func),
        patch.multiple(
            BlockMetaClass,
            fluxes_expressions=PropertyMock(return_value=ref_flux_expressions),
            nodes=PropertyMock(return_value=ref_nodes),
            __init__=MagicMock(return_value=None),
        ),
    ):
        factory = SimulationFactory(AbstractSimulation, AbstractSolver(), net_reference)
        sim = factory.create_simulation()
        sim.magnitudes = {str.format("{0}.{1}", NODE_A_ID, DOF_TYPE_ID): 1.1}
        sim.register_timed_parameter_update(INLET_FLUX_CONDITION_ID, AbstractFunction())
        sim.register_output_function(OUTPUT_ID, AbstractFunction())
        sim.parameters[VECTOR_ID] = 3 * [0.0]
        sim.parameters[SCALAR_ID] = 0.0
        return sim


@patch(
    "physioblocks.registers.type_register.__type_register",
    new={
        FUNC_TYPE_ID: AbstractFunction,
        SIM_TYPE_ID: AbstractSimulation,
        BLOCK_DESCRIPTION_TYPE_ID: BlockDescription,
        BLOCK_TYPE_ID: BlockTest,
        SOLVER_TYPE_ID: AbstractSolver,
        TIME_MANAGER_ID: TimeManager,
        NET_ID: Net,
        BOUNDARY_CONDITION_ID: BoundaryCondition,
        FLUX_TYPE_REGISTER_ID: FluxDofTypesRegister,
        AbstractFunction: FUNC_TYPE_ID,
        AbstractSimulation: SIM_TYPE_ID,
        BlockDescription: BLOCK_DESCRIPTION_TYPE_ID,
        BlockTest: BLOCK_TYPE_ID,
        AbstractSolver: SOLVER_TYPE_ID,
        Net: NET_ID,
        TimeManager: TIME_MANAGER_ID,
        BoundaryCondition: BOUNDARY_CONDITION_ID,
        FluxDofTypesRegister: FLUX_TYPE_REGISTER_ID,
    },
)
@patch.multiple(
    "physioblocks.description.nets._flux_type_register",
    create=True,
    _fluxes_types={FLUX_TYPE_ID: DOF_TYPE_ID},
    _dof_types={DOF_TYPE_ID: FLUX_TYPE_ID},
)
def test_simulation_save_config(
    simulation_reference: ForwardSimulation, ref_flux_expressions, ref_nodes
):
    with (
        patch.multiple(
            BlockMetaClass,
            fluxes_expressions=PropertyMock(return_value=ref_flux_expressions),
            nodes=PropertyMock(return_value=ref_nodes),
        ),
        patch.multiple(
            AbstractFunction,
            __abstractmethods__=set(),
            eval=time_func,
            __init__=func_init,
        ),
    ):
        configuration = save_simulation_config(simulation_reference)
        ref_config = read_json(ref_config_file_path)
        assert configuration == ref_config


@patch.multiple(
    "physioblocks.description.nets._flux_type_register",
    create=True,
    _fluxes_types={FLUX_TYPE_ID: DOF_TYPE_ID},
    _dof_types={DOF_TYPE_ID: FLUX_TYPE_ID},
)
@patch(
    "physioblocks.registers.type_register.__type_register",
    new={
        FUNC_TYPE_ID: AbstractFunction,
        SIM_TYPE_ID: AbstractSimulation,
        BLOCK_DESCRIPTION_TYPE_ID: BlockDescription,
        BLOCK_TYPE_ID: BlockTest,
        SOLVER_TYPE_ID: AbstractSolver,
        TIME_MANAGER_ID: TimeManager,
        NET_ID: Net,
        BOUNDARY_CONDITION_ID: BoundaryCondition,
        AbstractFunction: FUNC_TYPE_ID,
        AbstractSimulation: SIM_TYPE_ID,
        BlockDescription: BLOCK_DESCRIPTION_TYPE_ID,
        BlockTest: BLOCK_TYPE_ID,
        AbstractSolver: SOLVER_TYPE_ID,
        Net: NET_ID,
        TimeManager: TIME_MANAGER_ID,
        BoundaryCondition: BOUNDARY_CONDITION_ID,
    },
)
@patch.multiple(AbstractSimulation, __abstractmethods__=set())
@patch.multiple(AbstractSolver, __abstractmethods__=set())
@patch.multiple(AbstractFunction, __abstractmethods__=set(), eval=time_func)
def test_simulation_load_config(
    simulation_reference: ForwardSimulation, ref_flux_expressions, ref_nodes
):
    with patch.multiple(
        BlockMetaClass,
        fluxes_expressions=PropertyMock(return_value=ref_flux_expressions),
        nodes=PropertyMock(return_value=ref_nodes),
    ):
        ref_config = read_json(ref_config_file_path)
        sim = load_simulation_config(ref_config, ForwardSimulation)

        assert sim.parameters == simulation_reference.parameters
        assert_net_equals(sim.factory.net, simulation_reference.factory.net)
        assert_solvers_equals(sim.solver, simulation_reference.solver)
        assert_states_equals(sim.state, simulation_reference.state)
        assert_time_manager_equals(sim.time_manager, simulation_reference.time_manager)

        # load raises exceptions correctly:
        ref_config[PARAMETERS_ID]["wrong_type_id"] = object()
        with pytest.raises(TypeError):
            load_simulation_config(ref_config)
