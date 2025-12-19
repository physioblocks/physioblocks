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
Define the base configurations objects
"""

from __future__ import annotations

from collections.abc import ItemsView, Iterator, KeysView, Mapping, ValuesView
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Configuration(Mapping[str, Any]):
    """
    Define a generic configuration object that can easily be serialized.

    .. note::

        The ``configuration_items`` can also be :class:`~.Configuration` instances.
    """

    label: str
    """The item type name"""

    configuration_items: dict[str, Any] = field(default_factory=dict)
    """Configuration values"""

    def __getitem__(self, key: str) -> Any:
        return self.configuration_items[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.configuration_items[key] = value

    def __contains__(self, key: object) -> bool:
        return key in self.configuration_items

    def __iter__(self) -> Iterator[str]:
        yield from self.configuration_items

    def __eq__(self, config: Any) -> bool:
        if isinstance(config, Configuration):
            if config.label != self.label:
                return False
            if len(config.configuration_items) != len(self.configuration_items):
                return False
            for key, val in self.items():
                if key not in config:
                    return False
                if config[key] != val:
                    return False
            return True
        return False

    def __len__(self) -> int:
        return len(self.configuration_items)

    def items(self) -> ItemsView[str, Any]:
        """
        Get a view on configuration key and value pairs.

        :return: a view on configuration key-value
        :rtype: ItemsView[str, Any]
        """
        return self.configuration_items.items()

    def keys(self) -> KeysView[str]:
        """
        Get a view on configuration keys

        :return: a view on configuration keys
        :rtype: KeysView[str]
        """
        return self.configuration_items.keys()

    def values(self) -> ValuesView[Any]:
        """
        Get an iterable on configuration values

        :return: a view on configuration values
        :rtype: ValuesView[Any]
        """
        return self.configuration_items.values()

    def copy(self) -> Configuration:
        """
        Get a copy of the configuration.

        :return: a copy of the configuration item.
        :rtype: Configuration
        """
        return Configuration(self.label, self.configuration_items.copy())


class ConfigurationError(Exception):
    """
    Error raised when a configuration can not be loaded or saved.
    """
