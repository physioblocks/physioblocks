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

import numpy as np
import pytest

from physioblocks.computing.quantities import Quantity
from physioblocks.library.model_components.dynamics import (
    SphericalDynamicsModelComponent,
)
from physioblocks.simulation.state import State
from physioblocks.simulation.time_manager import Time
from physioblocks.utils.gradient_test_utils import gradient_test_from_model


@pytest.fixture
def ref_block() -> SphericalDynamicsModelComponent:
    return SphericalDynamicsModelComponent(
        disp=Quantity(0.00002),
        fib_deform=Quantity(0.000054),
        pressure=Quantity(10000.0),
        pressure_external=Quantity(123.4),
        vel=Quantity(1.1),
        radius=Quantity(0.03),
        vol_mass=Quantity(1000),
        thickness=Quantity(0.01),
        damping_coef=Quantity(70.0),
        series_stiffness=Quantity(1e8),
        hyperelastic_cst=Quantity(np.array([638.4135, 2.3724, 99.12522, 5.5326])),
        time=Time(0.0),
    )


@pytest.fixture
def state(ref_block: SphericalDynamicsModelComponent):
    state = State()
    state["disp"] = ref_block.disp
    state["fib_deform"] = ref_block.fib_deform
    state["pressure"] = ref_block.pressure
    state["pressure_external"] = ref_block.pressure_external
    state["vel"] = ref_block.vel
    return state


@pytest.fixture
def magnitudes():
    return np.array([0.013, 0.4, 1e5, 151.2, 1.1])


class TestSphericalDynamicsModelComponent:
    def test_check_gradient_small_disp_diff(self, ref_block, state, magnitudes):
        assert gradient_test_from_model(ref_block, state, magnitudes)

    def test_check_gradient_big_disp_diff(self, ref_block, state, magnitudes):
        magnitudes[0] = 1e-6
        assert gradient_test_from_model(ref_block, state, magnitudes)
