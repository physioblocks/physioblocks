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

from unittest.mock import patch

import pytest

import physioblocks.registers.load_function_register as load_reg
from physioblocks.registers.load_function_register import (
    get_load_function,
    loads,
)


class ClassA:
    pass


class ClassB(ClassA):
    pass


@patch(
    "physioblocks.registers.type_register.__type_register",
    new={
        ClassA.__name__: ClassA,
        ClassA: ClassA.__name__,
        ClassB.__name__: ClassB,
        ClassB: ClassB.__name__,
    },
)
def test_load_function_register():
    @loads(ClassA)
    def load_func():
        pass

    assert get_load_function(ClassA) == load_func
    assert get_load_function(ClassB) == load_func


@patch.object(
    load_reg,
    attribute="__load_functions_register",
    new={},
)
def test_load_function_exceptions():
    err_msg = str.format("No load function registered for type {0}", ClassA.__name__)
    with pytest.raises(KeyError, match=err_msg):
        get_load_function(ClassA)
