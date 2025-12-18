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
from physioblocks.library.blocks.cavity import SphericalCavityBlock
from physioblocks.simulation.state import State
from physioblocks.simulation.time_manager import Time
from physioblocks.utils.gradient_test_utils import gradient_test_from_expression


@pytest.fixture
def ref_block() -> SphericalCavityBlock:
    return SphericalCavityBlock(
        disp=Quantity(0.15),
        radius=Quantity(0.03),
        thickness=Quantity(0.001),
        time=Time(0.0),
    )


class TestSphericalCavityBlock:
    def test_check_gradient(self, ref_block: SphericalCavityBlock):
        state = State()

        state["disp"] = ref_block.disp

        ref_block.time.update(0.001)
        magnitudes = np.array([0.01])
        ref_block.initialize()

        assert gradient_test_from_expression(
            SphericalCavityBlock.fluxes_expressions[1].expression,
            ref_block,
            state,
            magnitudes,
        )
