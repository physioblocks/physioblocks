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
Define decorators to register any function as a specific save function
of a configuration object.
"""

from collections.abc import Callable
from typing import Any

from physioblocks.base.registers import register

__save_functions_register: dict[type, Callable[..., Any]] = {}


def saves(
    saved_type: type,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Decorator to register a method that saves a registered type.

    :param saved_type: the saved type by the method
    :type saved_type: str

    :return: the class decorator
    :rtype: Callable
    """

    def register_decorator(
        save_function: Callable[..., Any],
    ) -> Callable[..., Any]:
        register(__save_functions_register, saved_type, save_function)
        return save_function

    return register_decorator


def has_save_function(key: type) -> bool:
    """
    Check if the type has a save function

    :param key: the key to test
    :type key: Any

    :return: True if the key is registered, False otherwise
    :rtype: bool
    """
    key_type = _get_closest_type(key)
    return key_type in __save_functions_register


def get_save_function(saved_type: type) -> Callable[..., Any]:
    """
    Get a registered save function.

    :param type_id: the registered type id
    :type type_id: str

    :raise KeyError: Raises a key error if the type is not registered.

    :return: the registered type
    :rtype: type
    """
    key_type = _get_closest_type(saved_type)

    if key_type is None:
        raise KeyError(
            str.format(
                "No save function registered for type {0}",
                saved_type.__name__,
            )
        )
    return __save_functions_register[key_type]


def _get_closest_type(searched_type: type | None) -> None | type:
    if searched_type is None:
        return None
    elif searched_type in __save_functions_register:
        return searched_type
    else:
        return _get_closest_type(searched_type.__base__)
