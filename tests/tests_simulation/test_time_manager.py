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
        assert time.inv_dt == pytest.approx(zero)

    def test_initialize(self, zero, step):
        time = Time(zero)
        time.initialize(step)

        assert time.current == pytest.approx(step)
        assert time.new == pytest.approx(step)
        assert time.dt == pytest.approx(zero)
        assert time.inv_dt == pytest.approx(zero)

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
    def test_constructor(self, zero, step, end):
        time_manager = TimeManager(zero, end, step)
        assert time_manager.ended is False
        assert time_manager.time.current == zero
        assert time_manager.time.new == zero

        with pytest.raises(ValueError):
            time_manager = TimeManager(end, zero, step)

        with pytest.raises(ValueError):
            time_manager = TimeManager(zero, end, -step)

        with pytest.raises(AttributeError):
            time_manager.time = Time(zero)

        with pytest.raises(ValueError):
            TimeManager(zero, end, step, 0.0)

        with pytest.raises(ValueError):
            TimeManager(zero, end, step, step + 0.1)

    def test_set(self, zero, step, end):
        time_manager = TimeManager(
            zero,
            end,
            step,
        )

        # start
        assert time_manager.start == zero
        time_manager.start = step
        assert time_manager.end == time_manager.duration + step
        assert time_manager.start == step

        # step
        assert time_manager.step_size == step
        with pytest.raises(ValueError):
            time_manager.step_size = -step

        # duration
        time_manager.duration = end + step
        assert time_manager.end == end + 2 * step
        with pytest.raises(ValueError):
            time_manager.duration = zero - step

    def test_update(self, zero, step, end):
        time_manager = TimeManager(zero, end, step)

        time_manager.update_time()
        assert time_manager.time.current == zero
        assert time_manager.time.new == step

        time_manager.update_time()
        assert time_manager.time.current == step
        assert time_manager.time.new == (step + step)

    def test_ended(self, zero, step):
        time_manager = TimeManager(zero, step, step)
        time_manager.update_time()
        assert time_manager.ended is True
        assert time_manager.time.current == zero
        assert time_manager.time.new == step

        time_manager.update_time()
        assert time_manager.ended is True
        assert time_manager.time.current == step
        assert time_manager.time.new == step

    def test_initialize(self, zero, step, end):
        time_manager = TimeManager(zero, step, end)
        time_manager.update_time()
        time_manager.update_time()
        time_manager.initialize()
        assert time_manager.time.current == zero
        assert time_manager.time.new == zero
