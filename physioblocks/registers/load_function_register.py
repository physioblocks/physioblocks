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

"""Define decorators to register functions as a configuration load function."""

from collections.abc import Callable
from typing import Any, TypeVar

from physioblocks.base.registers import register

__load_functions_register: dict[type, Callable[..., Any]] = {}


T = TypeVar("T")


def loads(
    loaded_type: type[T],
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Register a method that loads a registered type.

    Parameters
    ----------
    loaded_type : type
        the loaded type

    Returns
    -------
    Callable
        the function decorator

    """

    def register_decorator(load_function: Callable[..., T]) -> Callable[..., T]:
        register(__load_functions_register, loaded_type, load_function)
        return load_function

    return register_decorator


def get_load_function(loaded_type: type) -> Callable[..., Any]:
    """Get a registered load function.

    When the function type itself is not registered, get the function registered for
    the closest parent type in the type MRO.

    Parameters
    ----------
    loaded_type : type
        the type to get the load function for.

    Returns
    -------
    Callable[..., Any]
        the registered load function

    Raises
    ------
    KeyError
        If the type is not registered.

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


def _get_closest_type(searched_type: type) -> type | None:
    for _parent_type in searched_type.mro():
        if _parent_type in __load_functions_register:
            return _parent_type
    return None
