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
import regex as re
from numpy.typing import NDArray

from physioblocks.computing.quantities import (
    QuantitiesRegistry,
    Quantity,
    diff,
    mid_alpha,
    mid_point,
    sign,
)


@pytest.fixture
def scalar_current():
    return 0.1


@pytest.fixture
def scalar_new():
    return 0.2


@pytest.fixture
def vector_current():
    return np.array([0.1, 0.2])


@pytest.fixture
def vector_new():
    return np.array([0.2, 0.3])


@pytest.fixture
def scalar_zero_reference():
    return 0.0


@pytest.fixture
def vector_zero_reference():
    return np.zeros(
        2,
    )


@pytest.fixture
def scalar_time_shift():
    return 0.25


@pytest.fixture
def vector_time_shift():
    return np.array(
        [0.25, 0.1],
    )


class TestQuantity:
    def test_constructor_scalar(self, scalar_current):
        qty = Quantity(scalar_current)

        assert qty.current == pytest.approx(scalar_current)
        assert qty.new == pytest.approx(scalar_current)

    def test_constructor_vector(self, vector_current):
        qty = Quantity(vector_current)
        assert vector_current == pytest.approx(qty.new)
        assert vector_current == pytest.approx(qty.current)

    def test_constructor_with_quantity(self, vector_current):
        qty_a = Quantity(vector_current)
        qty_b = Quantity(qty_a)

        assert qty_a is not qty_b
        assert qty_a.current == pytest.approx(qty_b.current)
        assert qty_a.new == pytest.approx(qty_b.new)

    def test_set_current_error(self, scalar_current, scalar_new):
        qty = Quantity(scalar_current)
        with pytest.raises(AttributeError):
            qty.current = scalar_new

    def test_set_new_error(self, scalar_current, scalar_new):
        qty = Quantity(scalar_current)
        with pytest.raises(AttributeError):
            qty.new = scalar_new

    def test_initialize_scalar(self, scalar_current, scalar_new):
        qty = Quantity(scalar_current)
        qty.initialize(scalar_new)
        assert qty.new == pytest.approx(scalar_new)
        assert qty.current == pytest.approx(scalar_new)

    def test_initialize_vector(self, vector_current, vector_new):
        qty = Quantity(vector_current)
        qty.initialize(vector_new)
        assert qty.new == pytest.approx(vector_new)
        assert qty.current == pytest.approx(vector_new)

    def test_initialize_wrong_size(self):
        init_value = np.array([])
        err_msg = str.format("Quantity size can not be 0. Got: {0}", init_value)
        with pytest.raises(ValueError, match=re.escape(err_msg)):
            Quantity(init_value)

    def test_update_scalar(self, scalar_current, scalar_new):
        qty = Quantity(scalar_current)
        qty.update(scalar_new)
        assert qty.new == pytest.approx(scalar_new)
        assert qty.current == pytest.approx(scalar_current)

    def test_update_vector(self, vector_current, vector_new):
        qty = Quantity(vector_current)
        qty.update(vector_new)
        assert qty.new == pytest.approx(vector_new)
        assert qty.current == pytest.approx(vector_current)

    def test_update_value_error(self, vector_current, scalar_new):
        qty = Quantity(vector_current)
        with pytest.raises(ValueError):
            qty.update(scalar_new)

    def test_eq_with_value(self):
        qty = Quantity(0.1)
        assert qty == pytest.approx(0.1)

    def test_neq_with_value(self):
        qty = Quantity(0.1)
        assert qty != pytest.approx(0.2)

    def test_eq_with_quantity(self):
        qty_a = Quantity(0.1)
        qty_b = Quantity(0.1)
        assert qty_a == qty_b

    def test_neq_with_quantity(self):
        qty_a = Quantity(0.1)
        qty_b = Quantity(0.2)
        assert qty_a != qty_b

    def test_compare_gt_with_float(self):
        qty = Quantity(0.1)
        assert qty > 0.01
        assert not qty > 0.1
        assert not qty > 1.0

    def test_compare_gt_with_quantity(self):
        qty_a = Quantity(0.1)
        qty_b = Quantity(0.01)
        qty_c = Quantity(0.1)
        qty_d = Quantity(1.0)

        assert qty_a > qty_b
        assert not qty_a > qty_c
        assert not qty_a > qty_d

    def test_compare_ge_with_float(self):
        qty = Quantity(0.1)
        assert qty >= 0.01
        assert qty >= 0.1
        assert not qty >= 1.0

    def test_compare_ge_with_quantity(self):
        qty_a = Quantity(0.1)
        qty_b = Quantity(0.01)
        qty_c = Quantity(0.1)
        qty_d = Quantity(1.0)

        assert qty_a >= qty_b
        assert qty_a >= qty_c
        assert not qty_a >= qty_d

    def test_compare_lt_with_float(self):
        qty = Quantity(0.1)
        assert qty < 1.0
        assert not qty < 0.1
        assert not qty < 0.1

    def test_compare_lt_with_quantity(self):
        qty_a = Quantity(0.1)
        qty_b = Quantity(0.01)
        qty_c = Quantity(0.1)
        qty_d = Quantity(1.0)

        assert not qty_a < qty_b
        assert not qty_a < qty_c
        assert qty_a < qty_d

    def test_compare_le_with_float(self):
        qty = Quantity(0.1)
        assert not qty <= 0.01
        assert qty <= 0.1
        assert qty <= 1.0

    def test_compare_le_with_quantity(self):
        qty_a = Quantity(0.1)
        qty_b = Quantity(0.01)
        qty_c = Quantity(0.1)
        qty_d = Quantity(1.0)

        assert not qty_a <= qty_b
        assert qty_a <= qty_c
        assert qty_a <= qty_d

    def test_add_quantity(self):
        qty_a = Quantity(0.1)
        qty_b = Quantity(0.2)

        assert qty_a + qty_b == pytest.approx(0.3)

    def test_add_float(self):
        qty = Quantity(0.1)
        assert qty + 0.1 == pytest.approx(0.2)
        assert 0.1 + qty == pytest.approx(0.2)

    def test_iadd_float(self):
        qty = Quantity(0.1)
        test_is_qty = qty
        qty += 0.1
        assert qty.current == pytest.approx(0.2)
        assert qty is test_is_qty

    def test_iadd_quantity(self):
        qty_a = Quantity(0.1)
        qty_b = Quantity(0.1)
        test_is_qty = qty_a
        qty_a += qty_b
        assert qty_a.current == pytest.approx(0.2)
        assert qty_a is test_is_qty

    def test_sub_float(self):
        qty = Quantity(0.1)

        assert qty - 0.1 == pytest.approx(0.0)
        assert 0.2 - qty == pytest.approx(0.1)

    def test_sub_quantity(self):
        qty_a = Quantity(0.1)
        qty_b = Quantity(0.2)
        assert qty_b - qty_a == pytest.approx(0.1)

    def test_isub_float(self):
        qty_a = Quantity(0.1)
        test_is_qty = qty_a
        qty_a -= 0.1
        assert qty_a.current == pytest.approx(0.0)
        assert qty_a is test_is_qty

    def test_isub_quantity(self):
        qty_a = Quantity(0.1)
        qty_b = Quantity(0.1)
        test_is_qty = qty_a
        qty_a -= qty_b
        assert qty_a.current == pytest.approx(0.0)
        assert qty_a is test_is_qty

    def test_neg(self):
        qty_a = Quantity(0.1)
        assert -qty_a == pytest.approx(-0.1)

    def test_mul_float(self):
        qty = Quantity(0.1)

        assert qty * 0.2 == pytest.approx(0.02)
        assert 0.2 * qty == pytest.approx(0.02)

    def test_mul_quantity(self):
        qty_a = Quantity(0.1)
        qty_b = Quantity(0.2)

        assert qty_b * qty_a == pytest.approx(0.02)

    def test_imul_float(self):
        qty = Quantity(0.1)
        test_is_qty = qty
        qty *= 0.2
        assert qty == pytest.approx(0.02)
        assert qty is test_is_qty

    def test_imul_quantity(self):
        qty_a = Quantity(0.1)
        qty_b = Quantity(0.2)
        test_is_qty = qty_a
        qty_a *= qty_b
        assert qty_a.current == pytest.approx(0.02)
        assert qty_a is test_is_qty

    def test_mat_mul_array(self):
        vec = np.array([1.0, 2.0])
        qty = Quantity([3.0, 4.0])

        assert np.array_equal(vec @ qty, 11.0)
        assert np.array_equal(qty @ vec, 11.0)

    def test_mat_mul_quantity(self):
        qty_a = Quantity([1.0, 2.0])
        qty_b = Quantity([3.0, 4.0])

        assert np.array_equal(qty_a @ qty_b, 11.0)

    def test_imatmul_array(self):
        vec = np.array([1.0, 2.0])
        qty = Quantity([3.0, 4.0])
        test_is_qty = qty
        qty @= vec
        assert np.array_equal(qty, 11.0)
        assert qty is test_is_qty

    def test_imatmul_quantity(self):
        qty_a = Quantity([1.0, 2.0])
        qty_b = Quantity([3.0, 4.0])
        test_is_qty = qty_a
        qty_a @= qty_b
        assert np.array_equal(qty_a, 11.0)
        assert qty_a is test_is_qty

    def test_truediv_float(self):
        qty = Quantity(0.1)

        assert qty / 0.2 == pytest.approx(0.5)
        assert 0.2 / qty == pytest.approx(2.0)

    def test_truediv_quantity(self):
        qty_a = Quantity(0.1)
        qty_b = Quantity(0.2)

        assert qty_b / qty_a == pytest.approx(2.0)

    def test_itruediv_float(self):
        qty = Quantity(0.1)
        test_is_qty = qty
        qty /= 0.2
        assert qty == pytest.approx(0.5)
        assert qty is test_is_qty

    def test_itruediv_quantity(self):
        qty_a = Quantity(0.1)
        qty_b = Quantity(0.2)
        test_is_qty = qty_a
        qty_a /= qty_b
        assert qty_a.current == pytest.approx(0.5)
        assert qty_a is test_is_qty

    def test_floordiv_float(self):
        qty = Quantity(5.4)

        assert qty // 2.5 == pytest.approx(2.0)
        assert 12.0 // qty == pytest.approx(2.0)

    def test_floordiv_quantity(self):
        qty_a = Quantity(5.4)
        qty_b = Quantity(2.1)

        assert qty_a // qty_b == pytest.approx(2.0)

    def test_ifloordiv_quantity(self):
        qty_a = Quantity(5.4)
        qty_b = Quantity(2.0)
        test_is_qty = qty_a
        qty_a //= qty_b
        assert qty_a.current == pytest.approx(2.0)
        assert qty_a is test_is_qty

    def test_ifloordiv_float(self):
        qty = Quantity(5.4)
        test_is_qty = qty
        qty //= 2.0
        assert qty == pytest.approx(2.0)
        assert qty is test_is_qty

    def test_modulo_float(self):
        qty = Quantity(1.1)

        assert qty % 0.5 == pytest.approx(0.1)
        assert 2.3 % qty == pytest.approx(0.1)

    def test_modulo_quantity(self):
        qty_a = Quantity(1.1)
        qty_b = Quantity(0.5)
        assert qty_a % qty_b == pytest.approx(0.1)

    def test_imod_float(self):
        qty = Quantity(1.1)
        test_is_qty = qty
        qty %= 0.5
        assert qty == pytest.approx(0.1)
        assert qty is test_is_qty

    def test_imod_quantity(self):
        qty_a = Quantity(1.1)
        qty_b = Quantity(0.5)
        test_is_qty = qty_a
        qty_a %= qty_b
        assert qty_a.current == pytest.approx(0.1)
        assert qty_a is test_is_qty

    def test_power_float(self):
        qty = Quantity(2.0)

        assert qty**3.0 == pytest.approx(8.0)
        assert 3.0**qty == pytest.approx(9.0)

    def test_power_quantity(self):
        qty_a = Quantity(2.0)
        qty_b = Quantity(3.0)
        assert qty_a**qty_b == pytest.approx(8.0)

    def test_ipower_float(self):
        qty = Quantity(2.0)
        test_is_qty = qty
        qty **= 3.0
        assert qty == pytest.approx(8.0)
        assert qty is test_is_qty

    def test_ipower_quantity(self):
        qty_a = Quantity(2.0)
        qty_b = Quantity(3.0)
        test_is_qty = qty_a
        qty_a **= qty_b
        assert qty_a.current == pytest.approx(8.0)
        assert qty_a is test_is_qty


class TestDiff:
    def test_diff_scalar(self, scalar_current, scalar_new):
        qty = Quantity(scalar_current)
        assert diff(qty) == pytest.approx(0.0)

        qty.update(scalar_new)
        assert diff(qty) == pytest.approx(0.1)

    def test_diff_vector(self, vector_current, vector_new, vector_zero_reference):
        qty = Quantity(vector_current)
        assert diff(qty) == pytest.approx(vector_zero_reference)

        qty.update(vector_new)
        assert diff(qty) == pytest.approx([0.1, 0.1])


class TestMidPoint:
    def test_mid_point_scalar(self, scalar_current, scalar_new):
        qty = Quantity(scalar_current)
        assert mid_point(qty) == pytest.approx(0.1)

        qty.update(scalar_new)
        assert mid_point(qty) == pytest.approx(0.15)

    def test_mid_point_vector(self, vector_current, vector_new):
        qty = Quantity(vector_current)
        assert mid_point(qty) == pytest.approx(vector_current)

        qty.update(vector_new)
        assert mid_point(qty) == pytest.approx([0.15, 0.25])


class TestMidAlpha:
    def test_mid_alpha_scalar(self, scalar_current, scalar_new, scalar_time_shift):
        qty = Quantity(scalar_current)
        assert mid_alpha(qty, scalar_time_shift) == pytest.approx(0.1)

        qty.update(scalar_new)
        assert mid_alpha(qty, scalar_time_shift) == pytest.approx(0.175)

    def test_mid_alpha_vector(self, vector_current, vector_new, vector_time_shift):
        qty = Quantity(vector_current)
        assert mid_alpha(qty, vector_time_shift) == pytest.approx(vector_current)

        qty.update(vector_new)
        assert mid_alpha(qty, vector_time_shift) == pytest.approx([0.175, 0.26])

    def test_mid_alpha_vector_ts_scalar(
        self, vector_current, vector_new, scalar_time_shift
    ):
        qty = Quantity(vector_current)
        assert mid_alpha(qty, scalar_time_shift) == pytest.approx(vector_current)

        qty.update(vector_new)
        assert mid_alpha(qty, scalar_time_shift) == pytest.approx([0.175, 0.275])


class TestSignQuantity:
    def test_sign_qty(self, scalar_current, scalar_new):
        flux = Quantity(scalar_current)
        flux.update(scalar_new)
        assert sign(flux) == pytest.approx(1.0)

        flux.update(-scalar_new)
        assert sign(flux) == pytest.approx(-1.0)


_X0_ID = "x0"
_X1_ID = "x1"
_X2_ID = "x2"


@pytest.fixture
def scalar() -> float:
    return 1.0


@pytest.fixture
def other_scalar() -> float:
    return 2.0


@pytest.fixture
def vector() -> NDArray[np.float64]:
    return np.array(
        [1.0, 1.0],
    )


@pytest.fixture
def other_vector() -> NDArray[np.float64]:
    return np.array(
        [2.0, 2.0],
    )


class TestQuantitiesRegistry:
    def test_default_constructor(self):
        quantities = QuantitiesRegistry()

        assert quantities.quantities == {}
        assert quantities.magnitudes == {}
        assert quantities.stdevs == {}

        assert quantities.size == 0
        assert quantities.vector.size == 0
        assert quantities.magnitudes_vector.size == 0
        assert quantities.stdevs_vector.size == 0

    def test_add_quantity(self, scalar):
        quantities = QuantitiesRegistry()
        quantities.add_quantity(_X0_ID, scalar)

        assert quantities.size == 1
        assert _X0_ID in quantities
        assert quantities.indexes[_X0_ID] == 0
        assert quantities.get_quantity_size(_X0_ID) == 1
        assert quantities.get_quantity_id(0) == _X0_ID
        assert quantities.quantities[_X0_ID] == pytest.approx(scalar)
        assert quantities.get(_X0_ID) == pytest.approx(scalar)

    def test_add_two_quantities(self, scalar, vector):
        quantities = QuantitiesRegistry()
        quantities.add_quantity(_X0_ID, scalar)
        quantities.add_quantity(_X1_ID, vector)

        assert quantities.size == 3
        assert _X1_ID in quantities
        assert quantities.indexes[_X1_ID] == 1
        assert quantities.get_quantity_size(_X1_ID) == 2
        assert quantities.get_quantity_id(1) == _X1_ID

    def test_add_three_quantities(self, scalar, vector):
        quantities = QuantitiesRegistry()
        quantities.add_quantity(_X0_ID, scalar)
        quantities.add_quantity(_X1_ID, vector)
        quantities.add_quantity(_X2_ID, vector)

        assert quantities.size == 5
        assert quantities.indexes[_X2_ID] == 3
        assert quantities.indexes == {_X0_ID: 0, _X1_ID: 1, _X2_ID: 3}

    def test_get_quantity_id_error(self):
        quantities = QuantitiesRegistry()

        message = "No quantity at index 0"
        with pytest.raises(KeyError, match=message):
            quantities.get_quantity_id(0)

    def test_add_duplicate_quantity_error(self, scalar):
        quantities = QuantitiesRegistry()
        quantities.add_quantity(_X0_ID, scalar)

        error_message = str.format("{0} is already registered.", _X0_ID)
        with pytest.raises(KeyError, match=error_message):
            quantities.add_quantity(_X0_ID, scalar)

    def test_remove_middle_quantity(self, scalar, vector):
        quantities = QuantitiesRegistry()
        quantities.add_quantity(_X0_ID, scalar)
        quantities.add_quantity(_X1_ID, vector)
        quantities.add_quantity(_X2_ID, vector)

        quantities.remove_quantity(_X1_ID)
        assert _X1_ID not in quantities
        assert quantities.size == 3
        assert quantities.indexes[_X0_ID] == 0
        assert quantities.indexes[_X2_ID] == 1
        assert list(quantities.indexes.keys()) == [_X0_ID, _X2_ID]

    def test_quantity_index_error(self):
        quantities = QuantitiesRegistry()

        with pytest.raises(KeyError, match=_X1_ID):
            quantities.indexes[_X1_ID]

    def test_assign_quantity(self, scalar: float):
        quantities = QuantitiesRegistry()
        quantities[_X0_ID] = Quantity(scalar)

        assert quantities.size == 1
        assert _X0_ID in quantities
        assert quantities.indexes[_X0_ID] == 0
        assert quantities.get_quantity_size(_X0_ID) == 1
        assert quantities.get_quantity_id(0) == _X0_ID
        assert quantities.quantities[_X0_ID] == pytest.approx(scalar)
        assert quantities.get(_X0_ID) == pytest.approx(scalar)

    def test_assign_quantity_float(self, scalar: float, other_scalar):
        quantities = QuantitiesRegistry()
        quantities[_X0_ID] = Quantity(scalar)

        quantities[_X0_ID] = other_scalar
        assert quantities[_X0_ID].current == pytest.approx(other_scalar)
        assert quantities[_X0_ID].new == pytest.approx(other_scalar)

    def test_assign_quantity_array(self, vector: float, other_vector):
        quantities = QuantitiesRegistry()
        quantities[_X0_ID] = Quantity(vector)

        quantities[_X0_ID] = other_vector
        assert np.array_equal(quantities[_X0_ID].current, other_vector)
        assert np.array_equal(quantities[_X0_ID].new, other_vector)

    def test_assign_quantity_error(self, scalar, vector):
        quantities = QuantitiesRegistry()
        quantities[_X0_ID] = Quantity(scalar)

        with pytest.raises(ValueError):
            quantities[_X0_ID] = vector

    def test_get_quantity(self, scalar):
        quantities = QuantitiesRegistry()
        qty = Quantity(scalar)
        quantities[_X0_ID] = qty
        assert quantities[_X0_ID] is qty

    def test_get_quantity_unregistered(self, scalar):
        quantities = QuantitiesRegistry()
        with pytest.raises(KeyError):
            quantities[_X0_ID]

    def test_update_quantity(self, scalar: float):
        quantities = QuantitiesRegistry()
        quantities[_X0_ID] = Quantity(scalar)
        quantities[_X1_ID] = Quantity(scalar)
        new_quantities_values = {
            _X0_ID: 2.0,
            _X1_ID: 3.0,
            _X2_ID: 4.0,
        }
        quantities.update(new_quantities_values)
        assert _X2_ID in quantities
        assert quantities[_X0_ID] == pytest.approx(2.0)
        assert quantities[_X1_ID] == pytest.approx(3.0)
        assert quantities[_X2_ID] == pytest.approx(4.0)

    def test_contains(self):
        quantities = QuantitiesRegistry()
        quantities.add_quantity(_X0_ID, 0.0)

        assert (_X0_ID in quantities) is True
        assert (_X1_ID in quantities) is False

    def test_array_interface(self):
        quantities = QuantitiesRegistry()
        quantities.add_quantity(_X0_ID, 0.1)
        quantities.add_quantity(_X1_ID, [0.2, 0.3])

        arr = np.array(quantities)
        assert arr.size == 3
        assert arr.shape == (3,)
        assert np.array_equal(arr, [0.1, 0.2, 0.3])

    def test_get(self):
        quantities = QuantitiesRegistry()
        quantities.add_quantity(_X0_ID, 0.0)
        quantities.add_quantity(_X1_ID, 0.0)

        assert quantities.get(_X0_ID) is not None
        assert quantities.get(_X0_ID) is quantities[_X0_ID]
        assert quantities.get(_X2_ID) is None

    def test_update_vector(self):
        quantities = QuantitiesRegistry()
        quantities.add_quantity(_X0_ID, 0.0)
        quantities.add_quantity(_X1_ID, [0.0, 0.0])

        update_ref = np.array([0.1, 0.2, 0.3])
        quantities.update_vector(update_ref)
        assert quantities[_X0_ID].current == pytest.approx(0.0)
        assert quantities[_X1_ID].current == pytest.approx(0.0)
        assert quantities[_X0_ID].new == pytest.approx(update_ref[0])
        assert quantities[_X1_ID].new == pytest.approx(update_ref[1:3])

    def test_set_vector(self):
        quantities = QuantitiesRegistry()
        quantities.add_quantity(_X0_ID, 0.0)
        quantities.add_quantity(_X1_ID, [0.0, 0.0])
        set_ref = np.array([0.5, 0.6, 0.7])
        quantities.set_vector(set_ref)
        assert quantities[_X0_ID].new == pytest.approx(set_ref[0])
        assert quantities[_X0_ID].current == pytest.approx(set_ref[0])
        assert quantities[_X1_ID].new == pytest.approx(set_ref[1:3])
        assert quantities[_X1_ID].current == pytest.approx(set_ref[1:3])

    def test_set_vector_error(self):
        quantities = QuantitiesRegistry()
        quantities.add_quantity(_X0_ID, 0.0)
        quantities.add_quantity(_X1_ID, [0.0, 0.0])
        set_ref = np.array([0.1, 0.2, 0.3, 0.4])

        with pytest.raises(
            ValueError,
            match=r"Provided vector size 4 does not match quantities vector size 3.",
        ):
            quantities.set_vector(set_ref)

    def test_reset_vector(self):
        quantities = QuantitiesRegistry()
        quantities.add_quantity(_X0_ID, 0.0)
        quantities.add_quantity(_X1_ID, [0.0, 0.0])

        update_ref = np.array([0.1, 0.2, 0.3])
        quantities.update_vector(update_ref)
        quantities.reset_vector()
        assert np.array(quantities) == pytest.approx(np.zeros(3))

    def test_quantities_iter(self):
        quantities = QuantitiesRegistry()
        quantities.add_quantity(_X0_ID, 0.0)
        quantities.add_quantity(_X1_ID, 0.0)
        quantities.add_quantity(_X2_ID, 0.0)
        for quantity_id in quantities:
            assert quantity_id in [_X0_ID, _X1_ID, _X2_ID]

    def test_add_quantity_default(self):
        quantities = QuantitiesRegistry()

        assert quantities.magnitudes_vector.size == 0

        quantities.add_quantity(_X0_ID, 0.002)
        quantities.add_quantity(_X1_ID, [1.3, 10.5])
        assert quantities.magnitudes_vector == pytest.approx(np.ones(3))
        assert quantities.stdevs_vector == pytest.approx(np.zeros(3))

    def test_add_quantity_with_magnitude(self):
        quantities = QuantitiesRegistry()
        scalar_mag = 1e-3
        vector_mag = [1.0, 10.0]
        quantities.add_quantity(_X0_ID, 0.002, scalar_mag)
        quantities.add_quantity(_X1_ID, [1.3, 10.5], vector_mag)
        quantities.add_quantity(_X2_ID, [105.3, 503.0], scalar_mag)

        assert quantities.magnitudes_vector[0] == pytest.approx(scalar_mag)
        assert quantities.magnitudes_vector[1:3] == pytest.approx(vector_mag)
        assert quantities.magnitudes_vector[3:5] == pytest.approx([scalar_mag] * 2)

    def test_add_quantity_with_stdev(self):
        quantities = QuantitiesRegistry()
        scalar_mag = 1e-3
        vector_mag = [1.0, 10.0]
        quantities.add_quantity(_X0_ID, 0.002, stdev=scalar_mag)
        quantities.add_quantity(_X1_ID, [1.3, 10.5], stdev=vector_mag)
        quantities.add_quantity(_X2_ID, [105.3, 503.0], stdev=scalar_mag)

        assert quantities.stdevs_vector[0] == pytest.approx(scalar_mag)
        assert quantities.stdevs_vector[1:3] == pytest.approx(vector_mag)
        assert quantities.stdevs_vector[3:5] == pytest.approx([scalar_mag] * 2)

    def test_remove_quantity(self):
        quantities = QuantitiesRegistry()
        quantities.add_quantity(_X0_ID, 0.0)
        quantities.remove_quantity(_X0_ID)

        assert _X0_ID not in quantities
        assert _X0_ID not in quantities.magnitudes
        assert _X0_ID not in quantities.stdevs

    def test_add_quantity_magnitude_error(self):
        quantities = QuantitiesRegistry()
        with pytest.raises(ValueError, match="Quantity and value sizes mismatch"):
            quantities.add_quantity(_X0_ID, 1.0, magnitude=[1.0, 1.0])

        with pytest.raises(ValueError, match="Quantity and value sizes mismatch"):
            quantities.add_quantity(_X1_ID, [2.0, 3.0, 4.0], magnitude=[1.0, 1.0])

    def test_set_quantity_magnitude(self):
        quantities = QuantitiesRegistry()
        quantities.add_quantity(_X0_ID, 0.002)
        quantities.add_quantity(_X1_ID, [0.3, 0.04])

        new_mag = {_X0_ID: 1e-3, _X1_ID: [0.1, 0.01]}
        quantities.set_magnitudes(new_mag)
        assert quantities.magnitudes_vector == pytest.approx(
            [new_mag[_X0_ID], *new_mag[_X1_ID]]
        )

    def test_set_quantity_stdev(self):
        quantities = QuantitiesRegistry()
        quantities.add_quantity(_X0_ID, 0.002)
        quantities.add_quantity(_X1_ID, [0.3, 0.04])

        new_mag = {_X0_ID: 1e-3, _X1_ID: [0.1, 0.01]}
        quantities.set_stdevs(new_mag)
        assert quantities.stdevs_vector == pytest.approx(
            [new_mag[_X0_ID], *new_mag[_X1_ID]]
        )

    def test_set_magnitude_errors(self):
        quantities = QuantitiesRegistry()
        quantities.add_quantity(_X0_ID, 0.002)
        quantities.add_quantity(_X1_ID, [0.3, 0.04])

        new_mag = {_X0_ID: 1e-3, _X1_ID: [0.1, 0.01], _X2_ID: 1.0}
        with pytest.raises(
            KeyError, match=f"Collection has no quantities named {set([_X2_ID])}"
        ):
            quantities.set_magnitudes(new_mag)

    def test_add_quantity_stdev_errors(self):
        quantities = QuantitiesRegistry()

        # Test stdev size mismatch
        with pytest.raises(ValueError, match="Quantity and value sizes mismatch"):
            quantities.add_quantity(_X0_ID, 1.0, stdev=[1.0, 1.0])

        with pytest.raises(ValueError, match="Quantity and value sizes mismatch"):
            quantities.add_quantity(_X1_ID, [2.0, 3.0, 4.0], stdev=[1.0, 1.0])

    def test_set_mapping_values_errors(self):
        quantities = QuantitiesRegistry()
        quantities.add_quantity(_X0_ID, 0.0)
        quantities.add_quantity(_X1_ID, [0.0, 0.0])

        with pytest.raises(KeyError, match="Collection has no quantities named"):
            quantities.set_magnitudes({_X2_ID: 1.0})

        with pytest.raises(ValueError, match="Quantities and values size mismatch"):
            quantities.set_magnitudes({_X1_ID: 1.0})

        with pytest.raises(ValueError, match="Quantities and values size mismatch"):
            quantities.set_magnitudes({_X1_ID: [1.0]})
