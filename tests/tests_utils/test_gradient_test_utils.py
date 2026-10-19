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


from dataclasses import dataclass

import numpy as np
import pytest

import physioblocks.utils.gradient_test_utils as gradient_test_utils
from physioblocks.computing.assembling import EqSystem
from physioblocks.computing.quantities import QuantitiesRegistry, Quantity


class TestGetErrorsGradient:
    def test_get_error_gradient_no_error(self):
        computed = np.arange(9, dtype=np.float64).reshape(3, 3)
        estimated_1 = computed.copy()
        estimated_2 = computed.copy()

        assert (
            gradient_test_utils.get_errors_gradient(computed, estimated_1, estimated_2)
            == []
        )

    def test_get_error_gradient_errors(self):
        computed = np.arange(9, dtype=np.float64).reshape(3, 3)
        estimated_1 = computed.copy()
        estimated_1[1, 2] = 0.0
        estimated_2 = estimated_1.copy()

        assert gradient_test_utils.get_errors_gradient(
            computed, estimated_1, estimated_2
        ) == [(1, 2)]

    def test_get_error_gradient_errors_nan(self):
        computed = np.arange(9, dtype=np.float64).reshape(3, 3)
        estimated_1 = computed.copy()
        estimated_1[1, 2] = np.nan
        estimated_2 = computed.copy()

        assert gradient_test_utils.get_errors_gradient(
            computed, estimated_1, estimated_2
        ) == [(1, 2)]

    def test_get_gradient_multiple_errors(self):
        computed = np.arange(9, dtype=np.float64).reshape(3, 3)
        estimated_1 = computed.copy()
        estimated_1[0, 1] = 0.0
        estimated_2 = estimated_1.copy()
        estimated_1[1, 2] = np.nan

        assert gradient_test_utils.get_errors_gradient(
            computed, estimated_1, estimated_2
        ) == [(0, 1), (1, 2)]

    def test_ignores_error(self):
        computed = np.arange(9, dtype=np.float64).reshape(3, 3)
        estimated_1 = computed.copy()
        estimated_1[0, 1] = 1.01
        estimated_2 = computed.copy()
        estimated_2[0, 1] = 1.001

        assert (
            gradient_test_utils.get_errors_gradient(computed, estimated_1, estimated_2)
            == []
        )


@dataclass
class AffineModel:
    a: float
    b: float
    x: Quantity


def affine_func(affine_model: AffineModel):
    return affine_model.a * affine_model.x.new + affine_model.b


def daffine_func_dx(affine_model: AffineModel):
    return affine_model.a


def wrong_daffine_func_dx(affine_model: AffineModel):
    return affine_model.b


@pytest.fixture
def affine_model():
    return AffineModel(2.0, 3.0, Quantity(0.5))


class TestGradientTest:
    def test_gradient_test_correct(self, affine_model):
        affine_eq_system = EqSystem(1)
        affine_eq_system.add_system_part(
            0, 1, affine_func, {0: daffine_func_dx}, affine_model
        )
        state = QuantitiesRegistry()
        state.add_quantity("x", affine_model.x, 1e-3)
        assert gradient_test_utils.gradient_test(affine_eq_system, state) is True

    def test_gradient_test_raise_error(self, affine_model):
        affine_eq_system = EqSystem(1)
        affine_eq_system.add_system_part(
            0, 1, affine_func, {0: wrong_daffine_func_dx}, affine_model
        )
        state = QuantitiesRegistry()
        state.add_quantity("x", affine_model.x, 1e-3)
        with pytest.raises(
            gradient_test_utils.GradientError, match=("Error" and "(0,0)")
        ):
            gradient_test_utils.gradient_test(affine_eq_system, state)

    def test_gradient_test_return_false(self, affine_model):
        affine_eq_system = EqSystem(1)
        affine_eq_system.add_system_part(
            0, 1, affine_func, {0: wrong_daffine_func_dx}, affine_model
        )
        state = QuantitiesRegistry()
        state.add_quantity("x", affine_model.x, 1e-3)
        assert (
            gradient_test_utils.gradient_test(affine_eq_system, state, False) is False
        )
