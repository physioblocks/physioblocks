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

from physioblocks.library.functions.transform import (
    ArcTanTransform,
    HyperbolicTanTransform,
    PowerTransform,
)


class TestArcTanTransform:
    def test_eval_inverse(self):
        transform = ArcTanTransform(1e9, 0.0, 1.0e8)
        init_value = 1e10
        a = transform.eval(init_value)
        b = transform.eval_inverse(a)
        assert b == pytest.approx(init_value)


class TestHyperbolicTanTransform:
    def test_eval_inverse(self):
        transform = HyperbolicTanTransform(2.73e5, 0.0, 1.0e5)
        init_value = 0.3
        a = transform.eval_inverse(init_value)
        b = transform.eval(a)
        assert b == pytest.approx(init_value)


class TestPowerTransform:
    def test_eval_inverse(self):
        transform = PowerTransform(8.32, 43.8)
        init_value = 12.51
        a = transform.eval_inverse(init_value)
        b = transform.eval(a)
        assert b == pytest.approx(init_value)
