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

from physioblocks.computing.quantities import Quantity
from physioblocks.library.model_components.velocity_law import (
    VelocityLawHHTModelComponent,
)
from physioblocks.simulation.state import State
from physioblocks.simulation.time_manager import Time
from physioblocks.utils.gradient_test_utils import gradient_test_from_model


@pytest.fixture
def ref_block() -> VelocityLawHHTModelComponent:
    return VelocityLawHHTModelComponent(
        disp=Quantity(0.1),
        vel=Quantity(0.2),
        accel=Quantity(0.3),
        scheme_ts_hht=Quantity(0.4),
        time=Time(0.0),
    )


class TestVelocityLawHHTModelComponent:
    def test_check_gradient(self, ref_block: VelocityLawHHTModelComponent):
        state = State()
        state["disp"] = ref_block.disp
        state["vel"] = ref_block.vel
        state["accel"] = ref_block.accel
        ref_block.time.update(0.001)

        magnitudes = np.array([1.0, 1.0, 1.0])

        assert gradient_test_from_model(ref_block, state, magnitudes)
