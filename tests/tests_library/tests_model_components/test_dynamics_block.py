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

import numpy as np
import pytest

from physioblocks.computing.quantities import QuantitiesRegistry, Quantity
from physioblocks.library.model_components.dynamics import (
    SphericalDynamicsModelComponent,
    exp_diff,
    power_diff,
)
from physioblocks.simulation.time_manager import Time
from physioblocks.utils.gradient_test_utils import gradient_test_from_model


@pytest.fixture
def ref_block() -> SphericalDynamicsModelComponent:
    model = SphericalDynamicsModelComponent(
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
    model.time.update(0.001)
    return model


@pytest.fixture
def state(ref_block: SphericalDynamicsModelComponent):
    state = QuantitiesRegistry()
    state["disp"] = ref_block.disp
    state["fib_deform"] = ref_block.fib_deform
    state["pressure"] = ref_block.pressure
    state["pressure_external"] = ref_block.pressure_external
    state["vel"] = ref_block.vel
    state.set_magnitudes(
        {
            "disp": 0.013,
            "fib_deform": 0.4,
            "pressure": 1e5,
            "pressure_external": 151.2,
            "vel": 1.1,
        }
    )
    return state


class TestSphericalDynamicsModelComponent:
    def test_raise_value_error_big_negative_disp(
        self, ref_block: SphericalDynamicsModelComponent
    ):
        ref_block.hyperelastic_cst.initialize(
            [620.0026747646299, 2.9, 96.35176702423303, 6.5]
        )
        ref_block.radius.initialize(0.0256)
        ref_block.thickness.initialize(0.0085)
        ref_block.pressure.initialize(900.0)
        ref_block.pressure_external.initialize(0.0)
        ref_block.damping_coef.initialize(70.0)
        ref_block.series_stiffness.initialize(1e8)
        ref_block.vol_mass.initialize(1e3)
        ref_block.disp.initialize(0.0)
        ref_block.vel.initialize(0.0)
        ref_block.fib_deform.initialize(0.0)

        with pytest.raises(
            ValueError, match="Displacement" and "negative" and "greater" and "radius"
        ):
            ref_block.initialize()

    def test_check_gradient_small_disp_diff(self, ref_block, state):
        assert gradient_test_from_model(ref_block, state)

    def test_check_gradient_big_disp_diff(self, ref_block, state):
        assert gradient_test_from_model(ref_block, state)


class TestDiffFunction:
    @pytest.mark.parametrize(
        "a", [0.15, 0.12 * np.arange(1, 4)], ids=["scalar", "vector"]
    )
    def test_exp_diff(self, a):
        diff = 1e-6 if np.isscalar(a) else 1e-6 * np.ones_like(a)
        b = a - diff
        assert exp_diff(a, b, diff) == pytest.approx(np.exp(a) - np.exp(b))

    @pytest.mark.parametrize("n", [5, -5, 0], ids=["n_positive", "n_negative", "n_nul"])
    @pytest.mark.parametrize(
        "a", [0.15, 0.12 * np.arange(1, 4)], ids=["scalar", "vector"]
    )
    def test_power_diff(self, a, n):
        diff = 1e-6 if np.isscalar(a) else 1e-6 * np.ones_like(a)
        b = a - diff
        assert power_diff(a, b, diff, n) == pytest.approx(a**n - b**n)
