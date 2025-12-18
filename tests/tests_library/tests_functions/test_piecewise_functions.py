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

import re

import numpy as np
import pytest

from physioblocks.library.functions.piecewise import (
    PiecewiseLinear,
    PiecewiseLinearPeriodic,
    RescaleTwoPhasesFunction,
)


@pytest.fixture
def piecewise_func_absissas():
    return np.array([0.0, 0.5, 1.0])


@pytest.fixture
def piecewise_func_ordinates():
    return np.array([0.0, 0.5, 1.5])


@pytest.fixture
def period():
    return 2.0


class TestPiecewiseLinearPeriodic:
    def test_eval(self, period, piecewise_func_absissas, piecewise_func_ordinates):
        function_ref = PiecewiseLinearPeriodic(
            period, piecewise_func_absissas, piecewise_func_ordinates
        )
        assert function_ref.eval(0.5) == pytest.approx(0.5)
        assert function_ref.eval(0.25) == pytest.approx(0.25)
        assert function_ref.eval(0.75) == pytest.approx(1.0)
        assert function_ref.eval(1.5) == pytest.approx(0.75)
        assert function_ref.eval(2.25) == pytest.approx(0.25)


@pytest.fixture
def left_value():
    return -2.0


@pytest.fixture
def right_value():
    return 2.3


class TestPiecewiseLinear:
    def test_eval_left_right_value(
        self, left_value, right_value, piecewise_func_absissas, piecewise_func_ordinates
    ):
        function_ref = PiecewiseLinear(
            piecewise_func_absissas, piecewise_func_ordinates, left_value, right_value
        )
        assert function_ref.eval(0.0) == pytest.approx(0.0)
        assert function_ref.eval(0.5) == pytest.approx(0.5)
        assert function_ref.eval(0.25) == pytest.approx(0.25)
        assert function_ref.eval(0.75) == pytest.approx(1.0)
        assert function_ref.eval(1.5) == pytest.approx(right_value)
        assert function_ref.eval(-0.3) == pytest.approx(left_value)

    def test_eval_no_left_right_value(
        self, piecewise_func_absissas, piecewise_func_ordinates
    ):
        piecewise_function = PiecewiseLinear(
            piecewise_func_absissas, piecewise_func_ordinates
        )
        assert piecewise_function.eval(1.5) == pytest.approx(1.5)
        assert piecewise_function.eval(-1.0) == pytest.approx(0.0)


@pytest.fixture
def piecewise_func():
    return [
        [0.0, -1.0],
        [0.249, -1.0],
        [0.25, 1.0],
        [0.749, 1.0],
        [0.75, -1.0],
        [1.0, -1.0],
    ]


@pytest.fixture
def piecewise_func_shifted():
    return [
        [-0.5, -1.0],
        [-0.251, -1.0],
        [-0.25, 1.0],
        [0.249, 1.0],
        [0.25, -1.0],
        [0.5, -1.0],
    ]


@pytest.fixture
def func_phases():
    return [0, 0, 1, 1, 0]


class TestRescaleFunction:
    def test_mid_scaling_factor(self, piecewise_func, func_phases):
        function_reduction_alpha_mid = RescaleTwoPhasesFunction(
            0.5, piecewise_func, 0.5, func_phases
        )
        assert function_reduction_alpha_mid.rescaled_period == pytest.approx(0.5)
        assert function_reduction_alpha_mid.eval(0.0) == pytest.approx(-1.0)
        assert function_reduction_alpha_mid.eval(0.1245) == pytest.approx(-1.0)
        assert function_reduction_alpha_mid.eval(0.125) == pytest.approx(1.0)
        assert function_reduction_alpha_mid.eval(0.5) == pytest.approx(-1.0)

        function_reduction_alpha_mid_shifted = RescaleTwoPhasesFunction(
            0.5, piecewise_func, 0.5, func_phases
        )
        assert function_reduction_alpha_mid_shifted.rescaled_period == pytest.approx(
            0.5
        )
        assert function_reduction_alpha_mid_shifted.eval(-0.5) == pytest.approx(-1.0)
        assert function_reduction_alpha_mid_shifted.eval(-0.3755) == pytest.approx(-1.0)
        assert function_reduction_alpha_mid_shifted.eval(-0.375) == pytest.approx(1.0)
        assert function_reduction_alpha_mid_shifted.eval(0.0) == pytest.approx(-1.0)

    def test_big_scaling_factor(self, piecewise_func, func_phases):
        function_reduction_alpha_mid = RescaleTwoPhasesFunction(
            0.5, piecewise_func, 0.90, func_phases
        )
        assert function_reduction_alpha_mid.rescaled_period == pytest.approx(0.5)
        assert function_reduction_alpha_mid.eval(0.0) == pytest.approx(-1.0)
        assert function_reduction_alpha_mid.eval(0.0249) == pytest.approx(-1.0)
        assert function_reduction_alpha_mid.eval(0.025) == pytest.approx(1.0)
        assert function_reduction_alpha_mid.eval(0.474) == pytest.approx(1.0)
        assert function_reduction_alpha_mid.eval(0.475) == pytest.approx(-1.0)
        assert function_reduction_alpha_mid.eval(0.5) == pytest.approx(-1.0)

    def test_exceptions(self, piecewise_func: list[tuple], func_phases: list[int]):
        with pytest.raises(
            ValueError,
            match=re.escape(
                "A phase should be defined for each interval defined in the "
                "reference function."
            ),
        ):
            RescaleTwoPhasesFunction(0.5, piecewise_func, 0.90, [0.0, 1.0])
        wrong_phases_neg = [0, -1, 1, 1, 0]
        wrong_phases_sup = [0, 1, 1, 1, 2]
        with pytest.raises(
            ValueError,
            match=re.escape(
                str.format(
                    "There are only two phases allowed: 0 or 1, got {0}.",
                    wrong_phases_neg,
                )
            ),
        ):
            RescaleTwoPhasesFunction(0.5, piecewise_func, 0.90, wrong_phases_neg)
        with pytest.raises(
            ValueError,
            match=re.escape(
                str.format(
                    "There are only two phases allowed: 0 or 1, got {0}",
                    wrong_phases_sup,
                )
            ),
        ):
            RescaleTwoPhasesFunction(0.5, piecewise_func, 0.90, wrong_phases_sup)

        with pytest.raises(
            ValueError,
            match=re.escape(
                str.format(
                    "The proportion of the variation of phase 0 should be in ]0, 1[, "
                    "got {0}",
                    -0.9,
                )
            ),
        ):
            RescaleTwoPhasesFunction(0.5, piecewise_func, -0.90, func_phases)

        unsorted_abscissas_func = [
            [0.0, 0.0],
            [0.1, 0.0],
            [0.05, 0.0],
            [0.2, 0.0],
            [0.3, 0.0],
            [0.4, 0.0],
        ]
        with pytest.raises(
            ValueError,
            match=re.escape(
                str.format(
                    "Reference function abscissas should be sorted, got {0}",
                    [0.0, 0.1, 0.05, 0.2, 0.3, 0.4],
                )
            ),
        ):
            RescaleTwoPhasesFunction(0.5, unsorted_abscissas_func, 0.5, func_phases)
