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

from unittest.mock import MagicMock

import numpy as np
import pytest

from physioblocks.simulation.forward import ForwardSimulation, solve_step
from physioblocks.simulation.solvers import ConvergenceError
from physioblocks.simulation.time_manager import Time


@pytest.fixture
def solution_converged_mock():
    return MagicMock(x=np.array([0.1, 0.2, 0.3]), converged=True)


@pytest.fixture
def solution_not_converged_mock():
    return MagicMock(x=np.array([0.1, 0.2, 0.3]), converged=False)


@pytest.fixture
def time():
    time_ref = Time(0.2)
    time_ref.update(0.3)
    return time_ref


@pytest.fixture
def time_manager_mock(time):
    return MagicMock(start=0.0, duration=1.0, step_size=0.1, time=time, ended=False)


@pytest.fixture
def solver_mock(solution_converged_mock, solution_not_converged_mock):
    solver_mock = MagicMock()
    solver_mock.solve.side_effect = [
        solution_not_converged_mock,
        solution_converged_mock,
        solution_converged_mock,
    ]
    return solver_mock


@pytest.fixture
def sim_model_mock(time_manager_mock, solver_mock):
    return MagicMock(time_manager=time_manager_mock, solver=solver_mock)


class TestSolveStep:
    def test_solve_step_converged(self, sim_model_mock):
        min_step = 0.025
        x = solve_step(sim_model_mock, min_step)
        assert x == pytest.approx([0.1, 0.2, 0.3])
        assert sim_model_mock.time_manager.time.current == pytest.approx(0.2)
        assert sim_model_mock.time_manager.time.new == pytest.approx(0.3)

    def test_solve_step_not_converged(self, sim_model_mock):
        min_step = 0.1
        with pytest.raises(
            ConvergenceError,
            match=f"{sim_model_mock.time_manager.time.current}" and str(min_step),
        ):
            solve_step(sim_model_mock, min_step)

    def test_solve_step_min_step_gt_step_size(self, sim_model_mock):
        min_step = 0.2
        with pytest.raises(
            ConvergenceError,
            match=f"{sim_model_mock.time_manager.time.current}" and str(min_step),
        ):
            solve_step(sim_model_mock, min_step)


class TestForwardSimulation:
    def test_default_constructor(self, sim_model_mock):
        forward_simulation = ForwardSimulation(
            factory=MagicMock(),
            simulation_name="forward_test",
            simulation_model=sim_model_mock,
        )
        assert forward_simulation.min_step == pytest.approx(
            forward_simulation.simulation_model.time_manager.step_size
        )

    def test_constructor(self, sim_model_mock):
        forward_simulation = ForwardSimulation(
            factory=MagicMock(),
            simulation_name="forward_test",
            simulation_model=sim_model_mock,
            min_step=0.01,
        )
        assert forward_simulation.min_step == pytest.approx(0.01)
