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

"""Define functions to update two-way :type:`dict` using common :type:`dict`"""

from typing import Any


def register(
    register: dict[Any, Any], registered_key: Any, registered_value: Any
) -> None:
    """
    Register the key and value to the provided register.

    :param register: the register to fill.
    :type dict[Any, Any]:

    :param registered_key: the key to register.
    :type Any:

    :param registered_value: the value to register.
    :type Any:

    :raise ValueError: Raises a ValueError if either the key or value
      is already registered in the provided register.
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
    """
    Check if key and params are of the expected types.

    If not, it raises a type error.

    :param key: the key value
    :type key: Any

    :param key_type: the expected type for the key
    :type key_type: type

    :param value: the value
    :type value: Any

    :param value_type: the expected type for the value
    :type value_type: type

    :raises TypeError: raise a type error if key or value param is not of the expected
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

    pass
