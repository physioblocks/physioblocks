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

from physioblocks.library.functions.trigonometric import SinusOffset


@pytest.fixture
def amplitude():
    return 32.3


@pytest.fixture
def offset_value():
    return 15.6


@pytest.fixture
def frequency():
    return 2.1


@pytest.fixture
def phase_shift():
    return np.pi / 5


class TestSinusOffset:
    def test_eval(self, offset_value, amplitude, frequency, phase_shift):
        function_ref = SinusOffset(offset_value, amplitude, frequency, phase_shift)
        assert function_ref.eval(0.0) == pytest.approx(34.58546364904688)
        assert function_ref.eval(0.5) == pytest.approx(41.73124891831079)
        assert function_ref.eval(0.25) == pytest.approx(-7.239549032325483)
        assert function_ref.eval(0.75) == pytest.approx(-13.179510731284259)
        assert function_ref.eval(1.5) == pytest.approx(47.9)
        assert function_ref.eval(2.25) == pytest.approx(-13.179510731284283)
