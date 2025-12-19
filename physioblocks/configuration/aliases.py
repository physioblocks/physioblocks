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

"""
Declares functions to handle configuration aliases.

**Aliases** are :class:`~physioblocks.configuration.base.Configuration`
instances representing a complete or incomplete type and that can be loaded
and completed or overwritten with the load function.
"""

import functools
from copy import copy
from pathlib import Path
from typing import Any, TypeAlias

from physioblocks.configuration.base import Configuration
from physioblocks.io.configuration import read_json

ConfigurationAlias: TypeAlias = Configuration | dict[str, Any]
"""type alias for configuration aliases"""

__aliases_register: dict[str, ConfigurationAlias] = {}


def add_alias(alias_key: str, alias: ConfigurationAlias) -> None:
    """
    Add an alias to the global alias register

    :param alias_key: the alias unique key
    :type alias_key: str

    :param alias_key: the alias unique key
    :type alias_key: str
    """
    if alias_key in __aliases_register:
        raise KeyError(str.format("Alias key {0} is already registered.", alias_key))

    if isinstance(alias, Configuration | dict) is False:
        raise TypeError(
            str.format(
                "Incorrect type for alias: {0}, expected {1}",
                type(alias).__name__,
                Configuration.__name__,
            )
        )

    __aliases_register[alias_key] = alias


def has_alias(alias_key: str) -> bool:
    """
    Get if an alias is defined for the given key.

    :param alias_key: the key to test
    :type alias_key: str

    :return: True if an alias is defined for the key, False otherwise
    :rtype: bool
    """
    if alias_key in __aliases_register:
        return True

    # if the alias is not registered, check if the given alias key
    # is a path to the alias configuration file.
    alias_path = Path(alias_key)
    return alias_path.exists() is True and alias_path.is_file() is True


@functools.singledispatch
def unwrap_aliases(item: Any) -> Any:
    """
    Process the given item and create a new one with all its alias replaced with
    their matching configuration object recursivly.

    :param item: the item to process
    :param item: Configuration | dict | list

    :return: the item to process
    :rtype: Configuration | dict | list
    """
    raise TypeError(str.format("Type {0} can not load aliases.", type(item).__name__))


@unwrap_aliases.register
def _unwrap_aliases_config(configuration: Configuration) -> Any:
    new_config: ConfigurationAlias = configuration.copy()

    # recursively unwrap the alias defined by the label
    while isinstance(new_config, Configuration) and has_alias(new_config.label):
        new_alias = get_alias(new_config.label)
        new_config = _update_configuration(new_config, new_alias)

    # update the alias values with the current config values
    new_config = _update_configuration(configuration, new_config)

    # The unwrap configuration values
    if isinstance(new_config, Configuration):
        values_config: dict[str, Any] = unwrap_aliases(new_config.configuration_items)
        new_config.configuration_items = values_config
        return new_config
    else:
        return unwrap_aliases(new_config)


@unwrap_aliases.register
def _unwrap_aliases_dict(items: dict) -> dict[str, Any]:  # type: ignore
    return {
        key: value
        if isinstance(value, Configuration | dict | list) is False
        else unwrap_aliases(value)
        for key, value in items.items()
    }


@unwrap_aliases.register
def _unwrap_aliases_list(items: list) -> list[Any]:  # type: ignore
    return [
        value
        if isinstance(value, Configuration | dict | list) is False
        else unwrap_aliases(value)
        for value in items
    ]


def get_alias(alias_key: str) -> Any:
    """
    Get an alias from the global alias register.

    :param alias_key: the alias unique key
    :type alias_key: str

    :return: the alias
    :rtype: Configuration | dict | list
    """

    alias_config = None
    if alias_key in __aliases_register:
        alias_config = copy(__aliases_register[alias_key])
    else:
        alias_config = read_json(alias_key)

    return alias_config


def _update_configuration(
    configuration: Configuration, alias: ConfigurationAlias
) -> ConfigurationAlias:
    if isinstance(alias, Configuration):
        new_values = alias.configuration_items.copy()
        new_values = _recursive_update(new_values, configuration.configuration_items)
        return Configuration(alias.label, new_values)
    elif isinstance(alias, dict):
        new_values = alias.copy()
        new_values = _recursive_update(new_values, configuration.configuration_items)
        return new_values
    raise TypeError(str.format("{0} is not a valid alias type.", type(alias).__name__))


def _recursive_update(
    updated: dict[str, Any], updater: dict[str, Any]
) -> dict[str, Any]:
    new_values = updated.copy()
    for key, value in updater.items():
        if key in updated and isinstance(value, dict):
            new_values[key] = _recursive_update(updated[key], value)
        else:
            new_values[key] = value

    return new_values


def remove_alias(alias_key: str) -> None:
    """
    Remove an alias from the global alias register

    :param alias_key: the alias unique key
    :type alias_key: str
    """
    __aliases_register.pop(alias_key)
