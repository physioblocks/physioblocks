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

from physioblocks.computing.quantities import (
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

    def test_constructor_quantity(self, vector_current):
        qty_a = Quantity(vector_current)
        qty_b = Quantity(qty_a)

        assert qty_a is not qty_b
        assert qty_a.current == pytest.approx(qty_b.current)
        assert qty_a.new == pytest.approx(qty_b.new)

    def test_set(self, scalar_current, scalar_new):
        qty = Quantity(scalar_current)

        with pytest.raises(AttributeError):
            qty.current = scalar_new

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

    def test_eq(self):
        qty_a = Quantity(0.1)
        qty_b = Quantity(0.2)
        qty_c = Quantity(0.1)

        assert qty_a == pytest.approx(0.1)
        assert qty_a == qty_c
        assert qty_a != qty_b
        assert qty_a != pytest.approx(0.2)

    def test_compare(self):
        qty_a = Quantity(0.1)
        qty_b = Quantity(0.2)
        qty_c = Quantity(0.1)

        assert qty_a > 0.01
        assert qty_a < 1.0
        assert qty_a < qty_b
        assert qty_b > qty_a

        assert qty_a >= 0.01
        assert qty_a <= 1.0
        assert qty_a <= qty_b
        assert qty_b >= qty_a

        assert qty_a >= qty_c
        assert qty_a >= 0.1
        assert qty_a <= qty_c
        assert qty_a <= 0.1

    def test_sum(self):
        qty_a = Quantity(0.1)
        qty_b = Quantity(0.2)

        assert qty_a + 0.1 == pytest.approx(0.2)
        assert 0.1 + qty_a == pytest.approx(0.2)
        assert qty_b + qty_a == pytest.approx(0.3)

        test_is_qty = qty_a
        qty_a += 0.1
        assert qty_a == pytest.approx(0.2)
        assert qty_a is test_is_qty

    def test_sub(self):
        qty_a = Quantity(0.1)
        qty_b = Quantity(0.2)

        assert qty_a - 0.1 == pytest.approx(0.0)
        assert 0.2 - qty_a == pytest.approx(0.1)
        assert qty_b - qty_a == pytest.approx(0.1)

        test_is_qty = qty_a
        qty_a -= 0.1
        assert qty_a == pytest.approx(0.0)
        assert qty_a is test_is_qty

    def test_neg(self):
        qty_a = Quantity(0.1)
        assert -qty_a == pytest.approx(-0.1)

    def test_mul(self):
        qty_a = Quantity(0.1)
        qty_b = Quantity(0.2)

        assert qty_a * 0.2 == pytest.approx(0.02)
        assert 0.2 * qty_a == pytest.approx(0.02)
        assert qty_b * qty_a == pytest.approx(0.02)

        test_is_qty = qty_a
        qty_a *= 0.2
        assert qty_a == pytest.approx(0.02)
        assert qty_a is test_is_qty

    def test_mat_mul(self):
        vec_a = np.array([0.1, 0.2])
        vec_b = np.array([0.3, 0.4])
        qty_a = Quantity(vec_a)
        qty_b = Quantity(vec_b)

        assert np.array_equal(vec_a @ qty_a, vec_a @ vec_a)
        assert np.array_equal(qty_a @ vec_b, vec_a @ vec_b)
        assert np.array_equal(qty_a @ qty_b, vec_a @ vec_b)

        test_is_qty = qty_a
        qty_a @= vec_a
        assert np.array_equal(qty_a, vec_a @ vec_a)
        assert qty_a is test_is_qty

    def test_truediv(self):
        qty_a = Quantity(0.1)
        qty_b = Quantity(0.2)

        assert qty_a / 0.2 == pytest.approx(0.5)
        assert 0.2 / qty_a == pytest.approx(2.0)
        assert qty_b / qty_a == pytest.approx(2.0)

        test_is_qty = qty_a
        qty_a /= 0.2
        assert qty_a == pytest.approx(0.5)
        assert qty_a is test_is_qty

    def test_floordiv(self):
        qty_a = Quantity(5.4)
        qty_b = Quantity(2.1)

        assert qty_a // 2.5 == pytest.approx(2.0)
        assert 12.0 // qty_a == pytest.approx(2.0)
        assert qty_a // qty_b == pytest.approx(2.0)

        test_is_qty = qty_a
        qty_a //= 2.0
        assert qty_a == pytest.approx(2.0)
        assert qty_a is test_is_qty

    def test_modulo(self):
        qty_a = Quantity(1.1)
        qty_b = Quantity(0.5)

        assert qty_a % 0.5 == pytest.approx(0.1)
        assert 2.3 % qty_a == pytest.approx(0.1)
        assert qty_a % qty_b == pytest.approx(0.1)

        test_is_qty = qty_a
        qty_a %= 0.5
        assert qty_a == pytest.approx(0.1)
        assert qty_a is test_is_qty

    def test_power(self):
        qty_a = Quantity(1.1)
        qty_b = Quantity(2.0)

        assert qty_a**2.0 == pytest.approx(1.21)
        assert 1.1**qty_b == pytest.approx(1.21)
        assert qty_a**qty_b == pytest.approx(1.21)

        test_is_qty = qty_a
        qty_a **= 2.0
        assert qty_a == pytest.approx(1.21)
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
