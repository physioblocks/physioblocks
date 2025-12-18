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

from physioblocks.library.functions.first_order import FirstOrder


@pytest.fixture
def times_start():
    return np.array([1.0, 3.0])


@pytest.fixture
def amplitudes():
    return np.array([2.2, -1.7])


@pytest.fixture
def time_constants():
    return np.array([0.8, 1.6])


@pytest.fixture
def baseline_value():
    return 1.2


class TestFirstOrder:
    def test_eval(self, times_start, amplitudes, time_constants, baseline_value):
        function_ref = FirstOrder(
            times_start, amplitudes, time_constants, baseline_value
        )
        assert function_ref.eval(0.0) == pytest.approx(1.2)
        assert function_ref.eval(1.0) == pytest.approx(1.2)
        assert function_ref.eval(2.0) == pytest.approx(2.7696894469075817)
        assert function_ref.eval(2.5) == pytest.approx(3.0626190729411578)
        assert function_ref.eval(3.0) == pytest.approx(3.219413003027423)
        assert function_ref.eval(4.0) == pytest.approx(2.558205387599064)
        assert function_ref.eval(8.0) == pytest.approx(1.7743441722445386)
        assert function_ref.eval(100.0) == pytest.approx(1.7)

    def test_error(self):
        times_start = np.array([1.0, 3.0])
        amplitudes = np.array([2.2, -1.7, 1.4])
        time_constants = np.array([0.8, 1.6])
        baseline_value = 1.2

        with pytest.raises(ValueError):
            _ = FirstOrder(times_start, amplitudes, time_constants, baseline_value)
