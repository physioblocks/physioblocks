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
from physioblocks.library.model_components.active_law import (
    ActiveLawMacroscopicHuxleyTwoMoment,
)
from physioblocks.simulation.state import State
from physioblocks.simulation.time_manager import Time
from physioblocks.utils.gradient_test_utils import gradient_test_from_model


@pytest.fixture
def ref_block() -> ActiveLawMacroscopicHuxleyTwoMoment:
    return ActiveLawMacroscopicHuxleyTwoMoment(
        fib_deform=Quantity(0.1),
        active_tension_discr=Quantity(np.sqrt(10.0) * 2.5),
        active_stiffness=Quantity(10.0),
        active_energy_sqrt=Quantity(2.5),
        starling_abscissas=Quantity(
            np.array(
                [
                    -0.1668,
                    -0.0073,
                    0.0534,
                    0.0969,
                    0.1326,
                    0.2016,
                    0.4663,
                    0.9187,
                    1.1762,
                ]
            )
        ),
        starling_ordinates=Quantity(
            np.array([0.0, 0.5614, 0.7748, 0.8933, 0.9618, 1.0, 1.0, 0.1075, 0.0])
        ),
        activation=Quantity(35.0),
        destruction_rate=Quantity(10.0),
        crossbridge_stiffness=Quantity(100000.0),
        contractility=Quantity(50000.0),
        time=Time(0.0),
    )


class TestActiveLawMacroscopicHuxleyTwoMoment:
    def test_check_gradient(self, ref_block: ActiveLawMacroscopicHuxleyTwoMoment):
        state = State()
        state["fib_deform"] = ref_block.fib_deform
        state["active_stiffness"] = ref_block.active_stiffness
        state["active_energy_sqrt"] = ref_block.active_energy_sqrt
        state["active_tension_discr"] = ref_block.active_tension_discr

        ref_block.time.update(0.001)
        magnitudes = np.array([0.14, 10.4, 2.48, 12.3])

        assert gradient_test_from_model(
            ref_block,
            state,
            magnitudes,
        )
