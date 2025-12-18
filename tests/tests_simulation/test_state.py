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
from numpy.typing import NDArray

from physioblocks.computing.quantities import Quantity
from physioblocks.simulation.state import State

_X0_ID = "x0"
_X1_ID = "x1"
_X2_ID = "x2"


@pytest.fixture
def scalar() -> float:
    return 1.0


@pytest.fixture
def vector() -> NDArray[np.float64]:
    return np.array(
        [1.0, 1.0],
    )


class TestState:
    def test_constructor(self):
        state = State()
        assert state.size == 0

    def test_variables(self, scalar, vector):
        state = State()

        state.add_variable(_X0_ID, scalar)
        assert state.size == 1
        assert _X0_ID in state
        assert state.get_variable_index(_X0_ID) == 0
        assert state.get_variable_size(_X0_ID) == 1
        assert state.get_variable_id(0) == _X0_ID

        message = str.format("No variable at index {0}", 1)
        with pytest.raises(KeyError, match=message):
            state.get_variable_id(1)

        state.add_variable(_X1_ID, vector)
        assert state.size == 3
        assert _X1_ID in state
        assert state.get_variable_index(_X1_ID) == 1
        assert state.get_variable_size(_X1_ID) == 2
        assert state.get_variable_id(1) == _X1_ID

        state.add_variable(_X2_ID, vector)
        assert state.size == 5
        assert state.get_variable_index(_X2_ID) == 3

        assert state.indexes == {_X0_ID: 0, _X1_ID: 1, _X2_ID: 3}

        state.remove_variable(_X1_ID)
        assert (_X1_ID in state) is False
        assert state.size == 3
        assert state.get_variable_index(_X0_ID) == 0
        assert state.get_variable_index(_X2_ID) == 1

        variables = [_X0_ID, _X2_ID]
        assert list(state.indexes.keys()) == variables

        error_message = str.format("{0} is already registered.", _X0_ID)
        with pytest.raises(KeyError, match=error_message):
            state.add_variable(_X0_ID, scalar)

    def test_set_variable_quantity(self, scalar: float, vector: NDArray[np.float64]):
        state = State()
        state[_X0_ID] = Quantity(scalar)
        state.add_variable(_X1_ID, scalar)
        state[_X1_ID] = Quantity(scalar)

        assert state[_X0_ID].current == pytest.approx(scalar)
        assert state[_X1_ID].current == pytest.approx(scalar)

        with pytest.raises(ValueError):
            state[_X0_ID] = Quantity(vector)

        with pytest.raises(KeyError):
            state["unregistered"]

    def test_state_vector(self, scalar: float, vector: NDArray[np.float64]):
        state = State()

        state.add_variable(_X0_ID, 0.0)
        state[_X0_ID].initialize(scalar)
        state.add_variable(_X1_ID, [0.0, 0.0])
        state[_X1_ID].initialize(vector)

        init_ref = np.ones(
            shape=3,
        )
        update_ref = np.array(
            [0.1, 0.2, 0.3],
        )
        set_ref = np.zeros(
            shape=3,
        )

        assert state.state_vector == pytest.approx(init_ref)

        with pytest.raises(AttributeError):
            state.state_vector = update_ref

        state.update_state_vector(update_ref)
        assert state.state_vector == pytest.approx(update_ref)
        assert state[_X0_ID].new == pytest.approx(update_ref[0])
        assert state[_X0_ID].current == pytest.approx(init_ref[0])
        assert state[_X1_ID].new == pytest.approx(update_ref[1:3])
        assert state[_X1_ID].current == pytest.approx(init_ref[1:3])

        state.set_state_vector(set_ref)
        assert state.state_vector == pytest.approx(set_ref)
        assert state[_X0_ID].new == pytest.approx(set_ref[0])
        assert state[_X0_ID].current == pytest.approx(set_ref[0])
        assert state[_X1_ID].new == pytest.approx(set_ref[1:3])
        assert state[_X1_ID].current == pytest.approx(set_ref[1:3])

        wrong_size_vector = np.zeros(
            shape=5,
        )
        with pytest.raises(ValueError):
            state.update_state_vector(wrong_size_vector)

        with pytest.raises(ValueError):
            state.set_state_vector(wrong_size_vector)
