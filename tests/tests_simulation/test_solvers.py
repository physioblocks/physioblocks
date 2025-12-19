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

from unittest.mock import Mock, patch

import numpy as np
import pytest

from physioblocks.computing.assembling import EqSystem
from physioblocks.simulation.solvers import AbstractSolver, NewtonSolver
from physioblocks.simulation.state import State


def mock_residual_converge():
    return np.zeros(
        shape=2,
    )


def mock_residual_dont_converge():
    return np.ones(
        shape=2,
    )


def mock_residual_nan():
    vec = np.empty(
        shape=2,
    )
    vec[:] = np.nan
    return vec


def mock_residual_inf():
    vec = np.empty(
        shape=2,
    )
    vec[:] = np.inf
    return vec


def mock_gradient():
    return np.array(
        [[1, 0], [0, 1]],
    )


@pytest.fixture
def system() -> EqSystem:
    return EqSystem(2)


@pytest.fixture
def state() -> State:
    state = State()
    state.add_variable("x0", 0.0)
    state.add_variable("x1", 0.0)
    return state


@pytest.fixture
def magnitudes() -> dict[str, float]:
    return {"x0": 1.0, "x1": 2.0}


class TestAbstractSolver:
    @patch.multiple(AbstractSolver, __abstractmethods__=set())
    def test_constructor(self):
        solver_mag = AbstractSolver(1e-12, 2)
        assert solver_mag.iteration_max == 2
        assert solver_mag.tolerance == pytest.approx(1e-12)


class TestNewtonSolver:
    @patch.multiple(
        EqSystem,
        compute_residual=Mock(return_value=mock_residual_converge()),
        compute_gradient=Mock(return_value=mock_gradient()),
    )
    def test_converge(self, state, system, magnitudes):
        solver = NewtonSolver(1e-9, 10)
        sol = solver.solve(state, system, magnitudes)
        assert sol.converged is True
        assert sol.x == pytest.approx([0, 0])

    @patch.multiple(
        EqSystem,
        compute_residual=Mock(return_value=mock_residual_dont_converge()),
        compute_gradient=Mock(return_value=mock_gradient()),
    )
    def test_dont_converge_sol(self, state, system, magnitudes):
        solver = NewtonSolver(1e-9, 10)
        sol = solver.solve(state, system, magnitudes)
        assert sol.converged is False

    @patch.multiple(
        EqSystem,
        compute_residual=Mock(return_value=mock_residual_nan()),
        compute_gradient=Mock(return_value=mock_gradient()),
    )
    def test_dont_converge_nan(self, state, system, magnitudes):
        solver = NewtonSolver(1e-9, 10)
        sol = solver.solve(state, system, magnitudes)
        assert sol.converged is False

    @patch.multiple(
        EqSystem,
        compute_residual=Mock(return_value=mock_residual_inf()),
        compute_gradient=Mock(return_value=mock_gradient()),
    )
    def test_dont_converge_inf(self, state, system, magnitudes):
        solver = NewtonSolver(1e-9, 10)
        sol = solver.solve(state, system, magnitudes)
        assert sol.converged is False
