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

"""
Define decorators to register any type with a name in a dedicated register.
"""

from collections.abc import Callable
from typing import Any, TypeVar

from physioblocks.base.registers import check_key_value_type, register

__type_register: dict[Any, Any] = {}


T = TypeVar("T")


def register_type(type_id: str) -> Callable[[T], T]:
    """
    Class decorator to register the class type with the given name.

    :param type_id: the defined type id for the class type
    :type type_id: str

    :return: the class decorator
    :rtype: Callable
    """

    def class_decorator(registered_type: T) -> T:
        check_key_value_type(type_id, str, registered_type, type)
        register(__type_register, type_id, registered_type)
        return registered_type

    return class_decorator


def get_registered_type(type_id: str) -> Any:
    """
    Get a registered type.

    :param type_id: the registered type id
    :type type_id: str

    :return: the registered type
    :rtype: type
    """
    return __type_register[type_id]


def get_registered_type_id(registered_type: type) -> Any:
    """
    Get a registered type name for the matching type.

    :param registered_type: the registered type id
    :type registered_type: type

    :return: the registered type id
    :rtype: str
    """
    return __type_register[registered_type]


def is_registered(key: Any) -> bool:
    """
    Get if the given value is registered as a type or type id.

    :param key: the key to test
    :type key: Any

    :return: True if the key is registered, False otherwise
    :rtype: bool
    """
    return key in __type_register
