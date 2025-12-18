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
from numpy.typing import NDArray

from physioblocks.computing.assembling import EqSystem


@dataclass
class ParamsF1:
    a: float
    x0: float


def f1(params: ParamsF1) -> float:
    return params.a * params.x0


def df1_dx0(params: ParamsF1) -> float:
    return params.a


@dataclass
class ParamsF2:
    a: float
    b: float
    x0: float
    x1: float


def f2(params: ParamsF2) -> NDArray[np.float64]:
    return np.array(
        [params.a * params.x0 + params.x1, params.b * params.x1 + params.x0],
    )


def df2_dx0(params: ParamsF2) -> NDArray[np.float64]:
    return np.array(
        [params.a, 1.0],
    )


def df2_dx1(params: ParamsF2) -> NDArray[np.float64]:
    return np.array(
        [1.0, params.b],
    )


@dataclass
class ParamsF3:
    a: float
    b: float
    c: float
    x1: float
    x2: float
    x3: float


def f3(params: ParamsF3):
    return np.array(
        [
            params.a * params.x1,
            params.b * params.x2 + params.x3,
            params.c * params.x3 + params.x2,
        ]
    )


def df3_dx1(params: ParamsF3):
    return np.array(
        [
            params.a,
            0.0,
            0.0,
        ]
    )


def df3_dx2(params: ParamsF3):
    return np.array([0.0, params.b, 1.0])


def df3_dx3(params: ParamsF3):
    return np.array([0.0, 1.0, params.c])


@pytest.fixture
def params_f1():
    return ParamsF1(1.0, 0.1)


@pytest.fixture
def params_f2():
    return ParamsF2(a=1.0, b=2.0, x0=0.1, x1=0.2)


@pytest.fixture
def res_ref():
    return np.array([0.4, 0.5, 0.7, 0.7])


@pytest.fixture
def grad_ref():
    return np.array(
        [
            [2.0, 1.0, 0.0, 0.0],
            [1.0, 2.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 1.0],
            [0.0, 0.0, 1.0, 1.0],
        ]
    )


@pytest.fixture
def eq_system_ref():
    eq_system = EqSystem(4)
    x0 = 0.1
    x1 = 0.2
    x2 = 0.3
    x3 = 0.4
    a = 1.0

    eq_system.add_system_part(0, 1, f1, {0: df1_dx0}, ParamsF1(a, x0))

    eq_system.add_system_part(
        0, 2, f2, {0: df2_dx0, 1: df2_dx1}, ParamsF2(a, a, x0, x1)
    )

    eq_system.add_system_part(
        1,
        3,
        f3,
        {1: df3_dx1, 2: df3_dx2, 3: df3_dx3},
        ParamsF3(a, a, a, x1, x2, x3),
    )
    return eq_system


class TestEqSystem:
    def test_constructor(self):
        eq_system = EqSystem(0)
        assert eq_system.system_size == 0

    def test_set(self):
        eq_system = EqSystem(0)
        with pytest.raises(AttributeError):
            eq_system.system_size = 1

    def test_add_part(self, params_f1):
        eq_system = EqSystem(1)

        grads = {0: df1_dx0}
        eq_system.add_system_part(0, 1, f1, grads, params_f1)

    def test_add_part_exceed_residual_size(self, params_f2):
        eq_system = EqSystem(1)

        grads = {0: df2_dx0, 1: df2_dx1}
        with pytest.raises(ValueError):
            eq_system.add_system_part(0, 2, f2, grads, params_f2)

    def test_add_part_exceed_gradient_size(self, params_f2):
        eq_system = EqSystem(2)
        grads = {0: df2_dx0, 2: df2_dx1}
        with pytest.raises(ValueError):
            eq_system.add_system_part(0, 2, f2, grads, params_f2)

    def test_residual_gradient(self, eq_system_ref: EqSystem, res_ref, grad_ref):
        res = eq_system_ref.compute_residual()
        grad = eq_system_ref.compute_gradient()

        assert res == pytest.approx(res_ref)
        assert grad == pytest.approx(grad_ref)
