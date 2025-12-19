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
from physioblocks.library.model_components.rheology import (
    RheologyFiberAdditiveModelComponent,
)
from physioblocks.simulation.state import State
from physioblocks.simulation.time_manager import Time
from physioblocks.utils.gradient_test_utils import gradient_test_from_model


@pytest.fixture
def ref_model() -> RheologyFiberAdditiveModelComponent:
    return RheologyFiberAdditiveModelComponent(
        disp=Quantity(0.15),
        fib_deform=Quantity(0.1),
        active_tension_discr=Quantity(2000.0),
        radius=Quantity(0.03),
        series_stiffness=Quantity(100000),
        damping_parallel=Quantity(70.0),
        time=Time(0.0),
    )


class TestRheologyFiberAdditiveModelComponent:
    def test_check_gradient(self, ref_model: RheologyFiberAdditiveModelComponent):
        state = State()
        state["fib_deform"] = ref_model.fib_deform
        state["disp"] = ref_model.disp
        state["active_tension_discr"] = ref_model.active_tension_discr

        ref_model.time.update(0.001)
        magnitudes = np.array([0.14, 0.015, 1999.3])

        assert gradient_test_from_model(ref_model, state, magnitudes)
