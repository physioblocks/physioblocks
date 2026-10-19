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

import pytest

from physioblocks.library.functions.base_operations import (
    Product,
    Sum,
)


class TestSumFunction:
    def test_eval_without_arguments(self):
        scalar_list = [0.1, 0.2, 0.3]
        func = Sum(scalar_list)
        assert func.eval() == pytest.approx(0.6)

        vector_list = [scalar_list, scalar_list, scalar_list]
        func = Sum(vector_list)
        assert func.eval() == pytest.approx([0.3, 0.6, 0.9])

        func = Sum(vector_list, vector_list)
        assert func.eval() == pytest.approx([0.0, 0.0, 0.0])

    def test_eval_with_arguments(self):
        to_add = ["a", "b"]
        func = Sum(to_add)
        assert func.eval(a=0.1, b=0.2) == pytest.approx(0.3)

    def test_eval_with_arguments_inverse(self):
        to_add = ["a"]
        to_remove = ["b"]
        func = Sum(to_add, to_remove)
        assert func.eval(a=1.0, b=0.5) == pytest.approx(0.5)


class TestProductFunction:
    def test_eval_without_arguments(self):
        scalar_list = [0.1, 0.1, 0.1]
        func = Product(scalar_list)
        assert func.eval() == pytest.approx(1.0e-3)

        # vector
        vector_list = [scalar_list, scalar_list, scalar_list]
        func = Product(vector_list)
        assert func.eval() == pytest.approx([1.0e-3, 1.0e-3, 1.0e-3])

    def test_eval_with_arguments(self):
        factors = ["a", "b"]
        func = Product(factors)
        assert func.eval(a=0.1, b=0.2) == pytest.approx(2.0e-2)

    def test_eval_with_arguments_inverse(self):
        factors = ["a"]
        inverses = ["b"]
        func = Product(factors, inverses)
        assert func.eval(a=1.0, b=2.0) == pytest.approx(0.5)
