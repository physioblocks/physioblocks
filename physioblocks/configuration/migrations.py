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

"""Define functions to migrate deprecated configuration to current configuration."""

from __future__ import annotations

import logging
import warnings
from collections.abc import Callable
from dataclasses import dataclass
from typing import TypeAlias

from packaging.version import Version

from physioblocks.configuration.base import Configuration
from physioblocks.registers.type_register import (
    get_registered_type,
    get_registered_type_id,
    is_registered,
)

_logger = logging.getLogger(__name__)

_MigrationFunctionType: TypeAlias = Callable[[Configuration], Configuration]

__migrations_functions: dict[str, list[_MigrationFunction]] = {}


@dataclass(frozen=True)
class _MigrationFunction:
    version: str
    migration_function: _MigrationFunctionType


def get_migration_functions(
    type_id: str, default: list[_MigrationFunction] | None = None
) -> list[_MigrationFunction] | None:
    """
    Get all the registered migration functions for the registered type.

    Parameters
    ----------
    type_id : str
        the registered type id
    default : list[_MigrationFunction] | None, optional
        fallback value when no migration function is registered.
        Default is None.

    Returns
    -------
    list[_MigrationFunction] | None
        the migration functions for the registered type.
    """
    return __migrations_functions.get(type_id, default)


def migrates(
    configuration_type: str, version: str
) -> Callable[[_MigrationFunctionType], _MigrationFunctionType]:
    """
    Register a method that migrates a type between versions.

    Decorate a function that transforms a given configuration to the target
    configuration format.
    All the migration functions for a given type are then applied in the version order.
    Therefore, the migration function should test itself if the conversion is needed
    before applying it.

    Parameters
    ----------
    configuration_type : str
        the type id of the type to migrate to a newer version
    version : str
        the target version id

    Returns
    -------
    Callable[[_MigrationFunctionType], _MigrationFunctionType]
        the function decorator

    Examples
    --------

    .. code:: python

        @migrates("foo", version="0.7.6")
        def migration_function_name(configuration: Configuration) -> Configuration:
            # Check if the migration is necessary:
            if "old_item_id" in configuration:
                # transform the configuration, for instance:
                old_item_value = configuration.configuration_items.pop("old_item_id")
                configuration["new_item_id"] = old_item_value

            return configuration

    """

    def register_decorator(
        migration_function: _MigrationFunctionType,
    ) -> _MigrationFunctionType:
        if configuration_type not in __migrations_functions:
            __migrations_functions[configuration_type] = []

        __migrations_functions[configuration_type].append(
            _MigrationFunction(version, migration_function)
        )
        __migrations_functions[configuration_type].sort(
            key=lambda x: Version(x.version)
        )
        return migration_function

    return register_decorator


def migrate(
    configuration: Configuration, configuration_type: type | None = None
) -> Configuration:
    """Migrate the provided configuration to the current configuration format.

    Apply the migration functions registered for the configuration type and its
    registered parents .

    Parameters
    ----------
    configuration : Configuration
        the configuration to migrate
    configuration_type : type | None
        the type of the configured object. Default is None, then the type
        registered with the configuration label is used.

    Returns
    -------
    Configuration
        the migrated configuration

    """
    configuration_copy = configuration.copy()
    configuration_type = configuration_type if configuration_type is not None else None
    configuration_type = (
        get_registered_type(configuration.label)
        if configuration_type is None and is_registered(configuration.label)
        else configuration_type
    )

    parent_configuration_type_ids = (
        [configuration.label]
        if configuration_type is None
        else [
            get_registered_type_id(parent_type)
            for parent_type in configuration_type.mro()
            if is_registered(parent_type)
        ]
    )

    for configuration_type_id in parent_configuration_type_ids:
        if configuration_type_id in __migrations_functions:
            for migration in __migrations_functions[configuration_type_id]:
                configuration_copy = migration.migration_function(configuration_copy)

    return configuration_copy


def migrate_keys(
    configuration: Configuration,
    key_map: dict[str, str],
    deprecated: bool = False,
    overwrite: bool = False,
) -> Configuration:
    """Migrate a set of field values in a configuration.

    Parameters
    ----------
    configuration : Configuration
        the configuration to migrate
    key_map : dict[str, str]
        the mapping between old keys and new keys
    deprecated : bool, optional
        flag to check if a deprecation warning should be raised.
        Default is False.
    overwrite : bool, optional
        flag to explicitly overwrite new configuration value with old
        configuration value when migrating to an existing key. Otherwise, keep the
        new value and discard the old one. Default is False.

    Returns
    -------
    Configuration
        a migrated copy of the configuration.

    Warns
    -----
    UserWarning
        when an old key is migrated to a key already in the configuration.
    DeprecationWarning
        when an old key is migrated and ``deprecated`` is True.

    """
    config_copy = configuration.copy()
    for old_key, new_key in key_map.items():
        config_value = config_copy.configuration_items.pop(old_key, None)
        if config_value is not None:
            if new_key in config_copy:
                warn_message = (
                    f"{old_key}: {new_key}. {new_key} already exists in configuration. "
                    "Default behavior keep the new key configuration and discard "
                    "the old key configuration. Set overwrite to True to "
                    "explicitly overwrite the new key configuration with the old "
                    "key configuration."
                )
                warnings.warn(warn_message, UserWarning, stacklevel=2)
                config_value = (
                    config_value if overwrite is True else config_copy[new_key]
                )
                if overwrite is True:
                    _logger.info(f"{new_key} value overwritten with {config_value}.")
            config_copy[new_key] = config_value

            if deprecated is True:
                deprecated_message = (
                    f"Field '{old_key}' in '{configuration.label}' configuration "
                    f"items is deprecated. Use '{new_key}' instead."
                )
                warnings.warn(
                    deprecated_message, category=DeprecationWarning, stacklevel=2
                )
    return config_copy
