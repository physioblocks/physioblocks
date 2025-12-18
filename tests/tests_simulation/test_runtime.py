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

from unittest.mock import Mock, patch

import numpy as np
import pytest

from physioblocks.computing.models import (
    ModelComponent,
)
from physioblocks.computing.quantities import Quantity
from physioblocks.simulation.functions import AbstractFunction
from physioblocks.simulation.runtime import (
    AbstractSimulation,
    ForwardSimulation,
    SimulationError,
)
from physioblocks.simulation.setup import SimulationFactory
from physioblocks.simulation.solvers import AbstractSolver, Solution
from physioblocks.simulation.state import State


def get_solution(converged: bool) -> Solution:
    return Solution(
        np.array(
            [0.1, 0.2, 0.3],
        ),
        converged,
    )


def block_qty_update_func(model: ModelComponent):
    return 0.0


def time_func(self, time: np.float64) -> np.float64:
    return time


def no_param_func(self) -> np.float64:
    return 0.0


def state_func(self, state: State) -> np.float64:
    return state.state_vector


@pytest.fixture
@patch.multiple(AbstractSolver, __abstractmethods__=set())
@patch.multiple(AbstractSimulation, __abstractmethods__=set())
def simulation() -> AbstractSimulation:
    sim_factory = SimulationFactory(AbstractSimulation, AbstractSolver())
    return sim_factory.create_simulation()


class TestSimulation:
    def test_register_time_update_exceptions(self, simulation: AbstractSimulation):
        with patch.multiple(
            AbstractFunction, __abstractmethods__=set(), eval=time_func
        ):
            wrong_param_id = "no_param"
            err_message = str.format("{0} not found in parameters", wrong_param_id)
            with pytest.raises(KeyError, match=err_message):
                simulation.register_timed_parameter_update(
                    wrong_param_id, AbstractFunction()
                )

        with patch.multiple(
            AbstractFunction, __abstractmethods__=set(), eval=no_param_func
        ):
            time_triggered_qty_id = "time_triggered_qty"
            time_triggered_qty = Quantity(0.0)
            simulation.parameters[time_triggered_qty_id] = time_triggered_qty

            err_message = str.format(
                "{0} is not a time function", type(AbstractFunction()).__name__
            )
            with pytest.raises(TypeError, match=err_message):
                simulation.register_timed_parameter_update(
                    time_triggered_qty_id, AbstractFunction()
                )

    @patch.multiple(AbstractFunction, __abstractmethods__=set(), eval=time_func)
    def test_update_time(self, simulation: AbstractSimulation):
        simulation.time_manager.step_size = 0.1
        simulation.time_manager.start = 0.0
        simulation.time_manager.duration = 0.2

        time_triggered_qty_id = "time_triggered_qty"
        time_triggered_qty = Quantity(0.0)
        simulation.parameters[time_triggered_qty_id] = time_triggered_qty

        simulation.register_timed_parameter_update(
            time_triggered_qty_id, AbstractFunction()
        )
        assert simulation.parameters[time_triggered_qty_id].current == pytest.approx(
            0.0
        )
        assert simulation.parameters[time_triggered_qty_id].new == pytest.approx(0.0)
        simulation.time_manager.update_time()
        simulation._update_time()  # noqa SLF001
        assert simulation.parameters[time_triggered_qty_id].current == pytest.approx(
            0.0
        )
        assert simulation.parameters[time_triggered_qty_id].new == pytest.approx(0.1)
        simulation.unregister_timed_parameter_update(time_triggered_qty_id)

    @patch.multiple(AbstractFunction, __abstractmethods__=set(), eval=no_param_func)
    def test_register_simulation_outputs(self, simulation: AbstractSimulation):
        # test functions with no parameters
        no_param_func_id = "no_param_func"
        output_func = AbstractFunction()
        simulation.register_output_function(no_param_func_id, output_func)
        simulation.outputs_functions.pop(no_param_func_id)
        assert no_param_func_id in simulation.outputs_functions

        simulation.unregister_output_function(no_param_func_id)
        assert no_param_func_id not in simulation.outputs_functions

    @patch.multiple(AbstractFunction, __abstractmethods__=set(), eval=no_param_func)
    def test_register_simulation_exceptions(self, simulation: AbstractSimulation):
        output_id = "output"
        error_message = str.format("Output {0} is already defined.", output_id)
        with (
            patch.object(
                simulation, attribute="_output_functions_updates", new={output_id: None}
            ),
            pytest.raises(KeyError, match=error_message),
        ):
            simulation.register_output_function(output_id, AbstractFunction())

        with (
            patch.object(
                simulation.saved_quantities,
                attribute="_saved_quantities",
                new={output_id: None},
            ),
            pytest.raises(KeyError, match=error_message),
        ):
            simulation.register_output_function(output_id, AbstractFunction())

        with (
            patch.object(State, attribute="__contains__", return_value=True),
            pytest.raises(KeyError, match=error_message),
        ):
            simulation.register_output_function(output_id, AbstractFunction())

        error_message = str.format(
            "{0} is not a valid output function", object.__name__
        )
        with pytest.raises(TypeError, match=error_message):
            simulation.register_output_function(output_id, object())

    @patch.multiple(AbstractFunction, __abstractmethods__=set(), eval=no_param_func)
    def test_no_parameter_output_function(self, simulation: AbstractSimulation):
        no_param_func_id = "no_param_func"
        output_func = AbstractFunction()
        simulation.register_output_function(no_param_func_id, output_func)

        results = simulation._get_current_result()  # noqa SLF001
        assert results[no_param_func_id] == pytest.approx(0.0)

    @patch.multiple(AbstractFunction, __abstractmethods__=set(), eval=time_func)
    def test_time_parameter_output_function(self, simulation: AbstractSimulation):
        time_func_id = "time_func"
        output_func = AbstractFunction()
        simulation.register_output_function(time_func_id, output_func)

        simulation.time_manager.time.initialize(0.001)
        results = simulation._get_current_result()  # noqa SLF001
        assert results[time_func_id] == pytest.approx(0.001)

    @patch.multiple(AbstractFunction, __abstractmethods__=set(), eval=state_func)
    def test_state_parameter_output_function(self, simulation: AbstractSimulation):
        state_vector_value = np.array([0.1, 0.2])
        with patch.object(
            State, attribute="state_vector", create=True, new=state_vector_value
        ):
            state_func_id = "state_func"
            output_func = AbstractFunction()
            simulation.register_output_function(state_func_id, output_func)

            results = simulation._get_current_result()  # noqa SLF001
            assert results[state_func_id] == pytest.approx(state_vector_value)


@pytest.fixture
@patch.multiple(AbstractSolver, __abstractmethods__=set())
def forward_simulation() -> ForwardSimulation:
    sim_factory = SimulationFactory(ForwardSimulation, solver=AbstractSolver())
    sim = sim_factory.create_simulation()
    sim.time_manager.start = 0.0
    sim.time_manager.duration = 0.010
    sim.time_manager.step_size = 0.001
    sim.state.add_variable("x", [0.0, 0.0, 0.0])
    return sim


class TestForwardSimulation:
    def test_run(self, forward_simulation: ForwardSimulation):
        sol = get_solution(True)
        forward_simulation.state["x"].initialize(sol.x)
        with patch.multiple(
            AbstractSolver,
            __abstractmethods__=set(),
            solve=Mock(return_value=sol),
        ):
            results = forward_simulation.run()
            for result in results:
                assert result["x"] == pytest.approx(sol.x)

    def test_run_no_solution(self, forward_simulation: ForwardSimulation):
        sol = get_solution(False)
        forward_simulation.state["x"].initialize(sol.x)
        with (
            patch.multiple(
                AbstractSolver, __abstractmethods__=set(), solve=Mock(return_value=sol)
            ),
            pytest.raises(SimulationError),
        ):
            forward_simulation.run()
