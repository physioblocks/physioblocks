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

"""Define functions to update two-way :class:`dict` using common :class:`dict`."""

from typing import Any


def register(
    register: dict[Any, Any], registered_key: Any, registered_value: Any
) -> None:
    """Register the key and value to the provided register.

    Parameters
    ----------
    register : dict[Any, Any]
        the register to fill.
    registered_key : Any
        the key to register.
    registered_value : Any
        the value to register.

    Raises
    ------
    RegisterError
        if either the key or value is already registered.

    """
    if registered_key in register or registered_value in register:
        raise RegisterError(
            str.format(
                "{0}: {1} key or value is already registered.",
                registered_key,
                registered_value,
            )
        )

    register[registered_key] = registered_value
    register[registered_value] = registered_key


def check_key_value_type(
    key: Any, key_type: type[Any], value: Any, value_type: type[Any]
) -> None:
    """Check if key and value are of the expected types.

    If not, it raises a type error.

    Parameters
    ----------
    key : Any
        the key value
    key_type : type
        the expected type for the key
    value : Any
        the value
    value_type : type
        the expected type for the value

    Raises
    ------
    TypeError
        raise a type error if key or value param is not of the expected
        types

    """
    if isinstance(key, key_type) is False:
        raise TypeError(
            str.format(
                "Expected type for key is {0} but got {1}.",
                key_type.__name__,
                type(key).__name__,
            )
        )

    elif isinstance(value, value_type) is False:
        raise TypeError(
            str.format(
                "Expected type for value is {0} but got {1}.",
                value_type.__name__,
                type(value).__name__,
            )
        )


class RegisterError(Exception):
    """Error Raised when a key or value has already been registered."""
