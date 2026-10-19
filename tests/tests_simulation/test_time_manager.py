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

from physioblocks.simulation.time_manager import Time, TimeManager


@pytest.fixture
def zero():
    return 0.0


@pytest.fixture
def step():
    return 0.1


@pytest.fixture
def end():
    return 2.0


@pytest.fixture
def min_step():
    return 0.001


class TestTime:
    def test_constructor(self, zero):
        time = Time(zero)
        assert time.current == pytest.approx(zero)
        assert time.new == pytest.approx(zero)
        assert time.dt == pytest.approx(zero)
        assert time.inv_dt == np.inf

    def test_initialize(self, zero, step):
        time = Time(zero)
        time.initialize(step)

        assert time.current == pytest.approx(step)
        assert time.new == pytest.approx(step)
        assert time.dt == pytest.approx(zero)
        assert time.inv_dt == np.inf

    def test_update(self, zero, step):
        time = Time(zero)
        time.update(step)

        assert time.current == pytest.approx(zero)
        assert time.new == pytest.approx(step)
        assert time.dt == pytest.approx(step)
        assert time.inv_dt == pytest.approx(1.0 / step)

    def test_set(self, zero, step):
        time = Time(zero)

        with pytest.raises(AttributeError):
            time.current = step

        with pytest.raises(AttributeError):
            time.new = step

        with pytest.raises(AttributeError):
            time.dt = step

        with pytest.raises(AttributeError):
            time.inv_dt = step


class TestTimeManager:
    def test_constructor(self):
        time_manager = TimeManager(0.1, 1.0, 0.2)
        assert time_manager.ended is False
        assert time_manager.time.current == pytest.approx(0.1)
        assert time_manager.time.new == pytest.approx(0.1)
        assert time_manager.step_size == pytest.approx(0.2)
        assert time_manager.duration == pytest.approx(1.0)
        assert time_manager.end == pytest.approx(1.1)
        assert time_manager.start == pytest.approx(0.1)

    def test_default_constructor(self):
        time_manager = TimeManager()
        assert time_manager.ended is False
        assert time_manager.time.current == pytest.approx(0.0)
        assert time_manager.time.new == pytest.approx(0.0)
        assert time_manager.step_size == pytest.approx(0.001)
        assert time_manager.duration == pytest.approx(0.001)
        assert time_manager.end == pytest.approx(0.001)
        assert time_manager.start == pytest.approx(0.0)

    def test_constructor_error_duration_negative(self):
        with pytest.raises(ValueError, match=f"{-1.0}"):
            TimeManager(0.0, -1.0, 0.1)

    def test_constructor_error_step_size_negative(self):
        with pytest.raises(ValueError, match=f"{-0.1}"):
            TimeManager(0.0, 1.0, -0.1)

    def test_set_step_negative_error(self):
        time_manager = TimeManager(0.0, 1.0, 0.1)
        with pytest.raises(ValueError, match=f"{-0.1}"):
            time_manager.step_size = -0.1

    def test_set_duration_negative_error(self):
        time_manager = TimeManager(0.0, 1.0, 0.1)
        with pytest.raises(ValueError, match=f"{-1.0}"):
            time_manager.duration = -1.0

    def test_ended(self):
        time_manager = TimeManager(0.0, 0.1, 0.1)
        assert time_manager.ended is False
        time_manager.time.update(0.1)
        assert time_manager.ended is True

    def test_initialize(self):
        time_manager = TimeManager(0.0, 0.1, 0.1)
        time_manager.initialize()
        assert time_manager.time.current == pytest.approx(0.0)
        assert time_manager.time.new == pytest.approx(0.1)
        assert time_manager.ended is True
