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

import physioblocks.registers.save_function_register as save_reg
from physioblocks.registers.save_function_register import (
    get_save_function,
    has_save_function,
    saves,
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
def test_save_function_register():
    @saves(ClassA)
    def save_func():
        pass

    assert has_save_function(ClassA) is True
    assert has_save_function(ClassB) is True
    assert get_save_function(ClassA) == save_func
    assert get_save_function(ClassB) == save_func


@patch.object(
    save_reg,
    attribute="__save_functions_register",
    new={},
)
def test_save_function_exceptions():
    err_msg = str.format("No save function registered for type {0}", ClassA.__name__)
    with pytest.raises(KeyError, match=err_msg):
        get_save_function(ClassA)
