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
from physioblocks.library.blocks.capacitances import CBlock, RCBlock, RCRBlock
from physioblocks.simulation.state import State
from physioblocks.simulation.time_manager import Time
from physioblocks.utils.gradient_test_utils import gradient_test_from_model


@pytest.fixture
def ref_c_block() -> CBlock:
    return CBlock(
        pressure=Quantity(4500),
        capacitance=Quantity(1.1e-3),
        time=Time(0.0),
    )


class TestCBlock:
    def test_check_gradient(self, ref_c_block: CBlock):
        state = State()
        state["pressure"] = ref_c_block.pressure
        ref_c_block.time.update(0.001)
        magnitudes = np.array([1e5])

        assert gradient_test_from_model(ref_c_block, state, magnitudes)


@pytest.fixture
def ref_rc_block() -> RCBlock:
    return RCBlock(
        pressure_1=Quantity(5230),
        pressure_2=Quantity(4624),
        resistance=Quantity(1.5e3),
        capacitance=Quantity(2.3e-6),
        time=Time(0.0),
    )


class TestRCBlock:
    def test_check_gradient(self, ref_rc_block: RCBlock):
        state = State()
        state["pressure_1"] = ref_rc_block.pressure_1
        state["pressure_2"] = ref_rc_block.pressure_2
        ref_rc_block.time.update(0.001)

        magnitudes = np.array([1e5, 1e5])

        assert gradient_test_from_model(ref_rc_block, state, magnitudes)


@pytest.fixture
def ref_rcr_block() -> RCRBlock:
    return RCRBlock(
        pressure_1=Quantity(5230),
        pressure_mid=Quantity(4921),
        pressure_2=Quantity(4624),
        resistance_1=Quantity(1.5e7),
        resistance_2=Quantity(2.1e8),
        capacitance=Quantity(2.3e-8),
        time=Time(0.0),
    )


class TestRCRBlock:
    def test_check_gradient(self, ref_rcr_block: RCRBlock):
        state = State()
        state["pressure_1"] = ref_rcr_block.pressure_1
        state["pressure_mid"] = ref_rcr_block.pressure_mid
        state["pressure_2"] = ref_rcr_block.pressure_2
        ref_rcr_block.time.update(0.001)

        magnitudes = np.array([1e4, 1e4, 1e4])

        assert gradient_test_from_model(ref_rcr_block, state, magnitudes)
