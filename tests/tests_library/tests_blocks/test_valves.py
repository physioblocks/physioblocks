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
from physioblocks.library.blocks.valves import ValveRLBlock
from physioblocks.simulation.state import State
from physioblocks.simulation.time_manager import Time
from physioblocks.utils.gradient_test_utils import gradient_test_from_model


@pytest.fixture
def ref_block() -> ValveRLBlock:
    block = ValveRLBlock(
        flux=Quantity(0.0011),
        pressure_1=Quantity(5002),
        pressure_2=Quantity(5003),
        conductance=Quantity(1.1e-6),
        backward_conductance=Quantity(1.2e-15),
        inductance=Quantity(3.1e3),
        scheme_ts_flux=Quantity(0.15),
        time=Time(0.0),
    )
    block.time.update(0.001)

    return block


@pytest.fixture
def state(ref_block: ValveRLBlock):
    state = State()
    state["pressure_1"] = ref_block.pressure_1
    state["pressure_2"] = ref_block.pressure_2
    state["flux"] = ref_block.flux
    return state


@pytest.fixture
def magnitudes():
    return np.array([1e5, 1e5, 1e-3])


class TestValveRLBlock:
    def test_check_gradient(self, ref_block: ValveRLBlock, state: State, magnitudes):
        assert gradient_test_from_model(ref_block, state, magnitudes)

    def test_check_gradient_flux_neg(self, ref_block: ValveRLBlock, state, magnitudes):
        ref_block.flux.initialize(-0.0011)
        assert gradient_test_from_model(ref_block, state, magnitudes)
