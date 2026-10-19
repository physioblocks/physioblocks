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
from unittest.mock import patch

import pytest

from physioblocks.computing.assembling import EqSystem
from physioblocks.computing.quantities import QUANTITY_ID
from physioblocks.configuration.base import Configuration
from physioblocks.configuration.constants import (
    BLOCKS_ITEM_ID,
    BOUNDARIES_ID,
    DATA_ID,
    FLUX_DOF_DEFINITION_ID,
    ITERATION_MAX_VAL_ID,
    NET_ID,
    NODES_ITEM_ID,
    OUTPUTS_FUNCTIONS_ID,
    PARAMETERS_ID,
    POST_PROCESSES_ID,
    PRE_PROCESSES_ID,
    QUANTITY_MAGNITUDE_ID,
    QUANTITY_STDEV_ID,
    QUANTITY_VALUE_ID,
    RANGE_LENGTH_ID,
    SIMULATION_NAME,
    SIMULATION_OPTIONS,
    SOLVER_ID,
    STATE_ID,
    TIME_ID,
    TIME_START_TIME_VAL_ID,
    TIME_STEP_MIN_VAL_ID,
    TIME_STEP_TIME_VAL_ID,
    TOLERANCE_VAL_ID,
    UPDATE_FUNCTIONS,
)
from physioblocks.configuration.simulation.simulations import (
    load_simulation_factory,
    save_simulation_config,
)
from physioblocks.description.flux import FLUX_TYPE_REGISTER_ID, FluxDofTypesRegister
from physioblocks.description.nets import Net
from physioblocks.simulation.base import (
    MODEL_FACTORY_ID,
    RANGE_ID,
    SIMULATION_FACTORY_ID,
    QuantityInit,
    SimulationFactory,
    SimulationModel,
    SimulationModelFactory,
    SimulationRange,
)
from physioblocks.simulation.forward import FORWARD_SIM_ID, ForwardSimulation
from physioblocks.simulation.functions import (
    SIMULATION_FUNCTION_FACTORY_TYPE_ID,
    AbstractFunction,
    AbstractInitializationFunction,
    SimulationFunctionFactory,
)
from physioblocks.simulation.solvers import NEWTON_SOLVER_TYPE_ID, NewtonSolver
from tests.helpers.assertion_helpers import assert_net_equals, assert_solvers_equals

SIM_NAME = "test_sim"
STATE_QUANTITY_ID = "variable"
PARAMETER_ID = "parameter"
OUTPUT_FUNCTION_ID = "output_function"
UPDATE_FUNCTION_ID = "update_function"
FUNC_TYPE_ID = "function_type"
COMPUTED_PARAMETER_ID = "computed_parameter"
CONSTANT_FUNCTION = "constant_function"


@dataclass
class ConstantFunction(AbstractInitializationFunction):
    value: float

    def eval(self) -> float:
        return self.value


TYPE_REGISTER = {
    FUNC_TYPE_ID: AbstractFunction,
    CONSTANT_FUNCTION: ConstantFunction,
    SIMULATION_FACTORY_ID: SimulationFactory,
    FORWARD_SIM_ID: ForwardSimulation,
    RANGE_ID: SimulationRange,
    NET_ID: Net,
    FLUX_TYPE_REGISTER_ID: FluxDofTypesRegister,
    QUANTITY_ID: QuantityInit,
    MODEL_FACTORY_ID: SimulationModelFactory,
    NEWTON_SOLVER_TYPE_ID: NewtonSolver,
    SIMULATION_FUNCTION_FACTORY_TYPE_ID: SimulationFunctionFactory,
    AbstractFunction: FUNC_TYPE_ID,
    ConstantFunction: CONSTANT_FUNCTION,
    SimulationFactory: SIMULATION_FACTORY_ID,
    ForwardSimulation: FORWARD_SIM_ID,
    NewtonSolver: NEWTON_SOLVER_TYPE_ID,
    Net: NET_ID,
    SimulationRange: RANGE_ID,
    FluxDofTypesRegister: FLUX_TYPE_REGISTER_ID,
    QuantityInit: QUANTITY_ID,
    SimulationModelFactory: MODEL_FACTORY_ID,
    SimulationFunctionFactory: SIMULATION_FUNCTION_FACTORY_TYPE_ID,
}


@pytest.fixture
def ref_net() -> Net:
    return Net(FluxDofTypesRegister())


@pytest.fixture
def simulation_model_factory(ref_net: Net) -> SimulationModelFactory:
    return SimulationModelFactory(
        net=ref_net,
        time=SimulationRange(start=0.0, length=0.001, step_size=0.001),
        state={STATE_QUANTITY_ID: QuantityInit(value=0.1, magnitude=1.1, stdev=0.5)},
        parameters={PARAMETER_ID: 0.0},
        update_functions={
            UPDATE_FUNCTION_ID: SimulationFunctionFactory(AbstractFunction, {})
        },
        solver=NewtonSolver(),
    )


@pytest.fixture
def simulation_factory(
    simulation_model_factory: SimulationModelFactory,
) -> SimulationFactory:
    return SimulationFactory(
        SIM_NAME,
        ForwardSimulation,
        simulation_model_factory,
        output_functions={
            OUTPUT_FUNCTION_ID: SimulationFunctionFactory(AbstractFunction, {})
        },
        simulation_options={TIME_STEP_MIN_VAL_ID: 0.001},
    )


@pytest.fixture
def simulation_reference(
    simulation_factory: SimulationFactory,
    simulation_model_factory: SimulationModelFactory,
) -> ForwardSimulation:
    return ForwardSimulation(
        factory=simulation_factory,
        simulation_name=SIM_NAME,
        simulation_model=SimulationModel(
            factory=simulation_model_factory, equation_system=EqSystem(0)
        ),
        min_step=0.001,
    )


@pytest.fixture
def ref_config() -> Configuration:
    config = Configuration(FORWARD_SIM_ID)
    config[SIMULATION_NAME] = SIM_NAME
    config[NET_ID] = Configuration(
        NET_ID,
        {
            FLUX_DOF_DEFINITION_ID: {},
            NODES_ITEM_ID: [],
            BLOCKS_ITEM_ID: {},
            BOUNDARIES_ID: {},
        },
    )
    config[TIME_ID] = Configuration(
        RANGE_ID,
        {
            TIME_START_TIME_VAL_ID: 0.0,
            RANGE_LENGTH_ID: 0.001,
            TIME_STEP_TIME_VAL_ID: 0.001,
        },
    )
    config[STATE_ID] = {
        STATE_QUANTITY_ID: Configuration(
            QUANTITY_ID,
            {
                QUANTITY_VALUE_ID: 0.1,
                QUANTITY_STDEV_ID: 0.5,
                QUANTITY_MAGNITUDE_ID: 1.1,
            },
        )
    }
    config[PARAMETERS_ID] = {PARAMETER_ID: 0.0}
    config[UPDATE_FUNCTIONS] = {UPDATE_FUNCTION_ID: Configuration(FUNC_TYPE_ID)}
    config[SOLVER_ID] = Configuration(
        NEWTON_SOLVER_TYPE_ID, {TOLERANCE_VAL_ID: 1.0e-9, ITERATION_MAX_VAL_ID: 10}
    )
    config[SIMULATION_OPTIONS] = {TIME_STEP_MIN_VAL_ID: 0.001}
    config[OUTPUTS_FUNCTIONS_ID] = {OUTPUT_FUNCTION_ID: Configuration(FUNC_TYPE_ID)}
    config[DATA_ID] = {}
    config[PRE_PROCESSES_ID] = {}
    config[POST_PROCESSES_ID] = {}
    return config


@pytest.mark.filterwarnings("ignore::UserWarning")
@patch("physioblocks.registers.type_register.__type_register", new=TYPE_REGISTER)
def test_simulation_save_config(simulation_reference, ref_config: Configuration):
    configuration = save_simulation_config(simulation_reference)

    assert configuration == ref_config


@patch("physioblocks.registers.type_register.__type_register", new=TYPE_REGISTER)
def test_simulation_load_config(
    simulation_factory: SimulationFactory, ref_config: Configuration
):
    ref_config[PARAMETERS_ID] = {
        **ref_config[PARAMETERS_ID],
        COMPUTED_PARAMETER_ID: Configuration(CONSTANT_FUNCTION, {"value": 0.5}),
    }

    loaded_factory = load_simulation_factory(ref_config)

    assert loaded_factory.simulation_model_factory.parameters.pop(
        COMPUTED_PARAMETER_ID
    ) == pytest.approx(0.5)

    assert loaded_factory.simulation_name == simulation_factory.simulation_name
    assert loaded_factory.simulation_type == simulation_factory.simulation_type
    assert loaded_factory.output_functions == simulation_factory.output_functions
    assert loaded_factory.simulation_options == simulation_factory.simulation_options

    loaded_model_factory = loaded_factory.simulation_model_factory
    ref_model_factory = simulation_factory.simulation_model_factory
    assert_net_equals(loaded_model_factory.net, ref_model_factory.net)
    assert_solvers_equals(loaded_model_factory.solver, ref_model_factory.solver)
    assert loaded_model_factory.time == ref_model_factory.time
    assert loaded_model_factory.state == ref_model_factory.state
    assert loaded_model_factory.parameters == ref_model_factory.parameters
    assert loaded_model_factory.update_functions == ref_model_factory.update_functions
