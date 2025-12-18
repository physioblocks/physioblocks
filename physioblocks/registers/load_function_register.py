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
Define decorators to register any function as a specific load function
of a configuration object.
"""

from collections.abc import Callable
from typing import Any, TypeVar

from physioblocks.base.registers import register

__load_functions_register: dict[type, Callable[..., Any]] = {}


T = TypeVar("T")


def loads(
    loaded_type: type[T],
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator to register a method that loads a registered type.

    :param loaded_type: the loaded type
    :type loaded_type: str

    :return: the class decorator
    :rtype: Callable
    """

    def register_decorator(load_function: Callable[..., T]) -> Callable[..., T]:
        register(__load_functions_register, loaded_type, load_function)
        return load_function

    return register_decorator


def get_load_function(loaded_type: type) -> Callable[..., Any]:
    """
    Get a registered load function.

    :param type_id: the registered type id
    :type type_id: str

    :raise KeyError: Raises a key error if the type is not registered.

    :return: the registered type
    :rtype: type
    """
    key_type = _get_closest_type(loaded_type)

    if key_type is None:
        raise KeyError(
            str.format(
                "No load function registered for type {0}",
                loaded_type.__name__,
            )
        )
    return __load_functions_register[key_type]


def _get_closest_type(searched_type: type | None) -> None | type:
    if searched_type is None:
        return None
    elif searched_type in __load_functions_register:
        return searched_type
    else:
        return _get_closest_type(searched_type.__base__)
