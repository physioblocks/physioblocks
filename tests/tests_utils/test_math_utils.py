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

import physioblocks.utils.math_utils as math_utils


@pytest.fixture
def a():
    return 1.3


@pytest.fixture
def b(a: float):
    return a + 1e-9


class TestMathHelper:
    def test_exp_diff(self, a: float, b: float):
        exp_diff_expected = np.exp(a) - np.exp(b)
        exp_diff = math_utils.exp_diff(a, b, a - b)
        assert exp_diff == pytest.approx(exp_diff_expected, 1e-16)

    def test_power_diff_n_pos(self, a: float, b: float):
        power_diff_expected = np.pow(a, 4) - np.pow(b, 4)
        power_diff = math_utils.power_diff(a, b, a - b, 4)

        assert power_diff == pytest.approx(power_diff_expected, 1e-16)

    def test_power_diff_n_neg(self, a: float, b: float):
        power_diff_expected = np.pow(a, -3) - np.pow(b, -3)
        power_diff = math_utils.power_diff(a, b, a - b, -3)

        assert power_diff == pytest.approx(power_diff_expected, 1e-16)

    def test_power_diff_n_nul(self, a: float, b: float):
        power_diff = math_utils.power_diff(a, b, a - b, 0)

        assert power_diff == pytest.approx(0.0, 1e-16)
