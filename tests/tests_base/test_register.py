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

from physioblocks.base.registers import (
    RegisterError,
    check_key_value_type,
    register,
)

KEY_A = "key_a"
KEY_B = "key_b"
VALUE_A = "value_a"
VALUE_B = "value_a"


def test_register():
    test_register = {}
    register(test_register, KEY_A, VALUE_A)
    assert KEY_A in test_register
    assert VALUE_A in test_register


def test_already_registered_exception():
    test_register = {KEY_A: VALUE_A, VALUE_A: KEY_A}

    message = str.format("{0}: {1} key or value is already registered.", KEY_A, VALUE_B)
    with pytest.raises(RegisterError, match=message):
        register(test_register, KEY_A, VALUE_B)

    message = str.format("{0}: {1} key or value is already registered.", KEY_B, VALUE_A)
    with pytest.raises(RegisterError, match=message):
        register(test_register, KEY_B, VALUE_A)


def test_check_key_value_type_exception():
    check_key_value_type(KEY_A, str, VALUE_A, str)
    message = str.format(
        "Expected type for key is {0} but got {1}.", str.__name__, float.__name__
    )
    with pytest.raises(TypeError, match=message):
        check_key_value_type(0.0, str, 0.0, str)

    message = str.format(
        "Expected type for value is {0} but got {1}.", str.__name__, float.__name__
    )
    with pytest.raises(TypeError, match=message):
        check_key_value_type(KEY_A, str, 0.0, str)
