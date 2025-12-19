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

import pytest

from physioblocks.configuration import Configuration
from physioblocks.configuration.constants import ITERATION_MAX_VAL_ID, TOLERANCE_VAL_ID
from physioblocks.configuration.functions import load, save
from physioblocks.registers.type_register import get_registered_type
from physioblocks.simulation.solvers import NEWTON_SOLVER_TYPE_ID, NewtonSolver


@pytest.fixture
def ref_solver_config() -> Configuration:
    config = Configuration(NEWTON_SOLVER_TYPE_ID)
    config[TOLERANCE_VAL_ID] = 1e-12
    config[ITERATION_MAX_VAL_ID] = 2
    return config


@pytest.fixture
def ref_newton_solver() -> NewtonSolver:
    return NewtonSolver(tolerance=1e-12, iteration_max=2)


def test_get_solver_config(
    ref_newton_solver: NewtonSolver, ref_solver_config: Configuration
):
    configuration = save(ref_newton_solver)
    assert ref_solver_config == configuration


def test_load_solver(ref_solver_config: Configuration):
    solver_type = get_registered_type(ref_solver_config.label)
    assert solver_type == NewtonSolver

    solver: NewtonSolver = load(ref_solver_config)
    assert solver.iteration_max == 2
    assert solver.tolerance == pytest.approx(1e-12)
