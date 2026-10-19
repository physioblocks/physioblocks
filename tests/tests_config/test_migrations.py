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

from unittest.mock import MagicMock, Mock, patch

import pytest

from physioblocks.configuration import migrations
from physioblocks.configuration.base import Configuration
from physioblocks.configuration.migrations import migrate, migrate_keys, migrates


@patch.object(migrations, attribute="__migrations_functions", new={})
def test_migrates_registers_function():
    migration_mock = Mock()
    decorator_factory = migrates("type_id", version="0.0.1")
    decorated_func = decorator_factory(migration_mock)

    assert decorated_func is migration_mock
    migration_functions = migrations.get_migration_functions("type_id")
    assert len(migration_functions) == 1
    assert migration_functions[0].version == "0.0.1"
    assert migration_functions[0].migration_function == decorated_func


@patch.object(migrations, attribute="__migrations_functions", new={})
def test_migrates_sort():
    migration_mock = Mock()
    migrates("type_id", version="0.9.0")(migration_mock)
    migrates("type_id", version="0.7.6")(migration_mock)

    migration_functions = migrations.get_migration_functions("type_id")
    assert len(migration_functions) == 2
    assert migration_functions[0].version == "0.7.6"
    assert migration_functions[1].version == "0.9.0"


@patch.object(migrations, attribute="__migrations_functions", new={})
def test_migrate():
    migration_mock = Mock(side_effect=lambda configuration: configuration)
    migrates("type_id", version="0.0.1")(migration_mock)

    mock_configuration = MagicMock(label="type_id")
    migrate(mock_configuration)

    migration_mock.assert_called_once_with(mock_configuration.copy())


@patch.object(migrations, attribute="__migrations_functions", new={})
def test_migrate_with_registered_type():
    migration_mock = Mock(side_effect=lambda configuration: configuration)
    migrates("base_id", version="0.0.1")(migration_mock)

    base_type_mock = MagicMock()
    child_type_mock = MagicMock()
    child_type_mock.mro.return_value = [base_type_mock]

    mock_configuration = MagicMock(label="child_id")

    with patch(
        "physioblocks.registers.type_register.__type_register",
        new={
            "base_id": base_type_mock,
            base_type_mock: "base_id",
            "child_id": child_type_mock,
            child_type_mock: "child_id",
        },
    ):
        migrate(mock_configuration, child_type_mock)

    migration_mock.assert_called_once_with(mock_configuration.copy())


@patch.object(migrations, attribute="__migrations_functions", new={})
def test_migrate_with_configuration_type():
    migration_mock = Mock(side_effect=lambda configuration: configuration)
    migrates("other_id", version="0.0.1")(migration_mock)

    other_type_mock = MagicMock()
    other_type_mock.mro.return_value = [other_type_mock]

    mock_configuration = MagicMock(label="type_id")

    with patch(
        "physioblocks.registers.type_register.__type_register",
        new={
            "other_id": other_type_mock,
            other_type_mock: "other_id",
        },
    ):
        migrate(mock_configuration, other_type_mock)

    migration_mock.assert_called_once_with(mock_configuration.copy())


@patch.object(migrations, attribute="__migrations_functions", new={})
def test_migrate_without_migration_function_():
    configuration = MagicMock(label="type_id")
    result = migrate(configuration)

    assert result == configuration.copy()


def test_migrate_multiple_versions_migrations():
    migration_a = Mock(side_effect=lambda configuration: configuration)
    migration_b = Mock(side_effect=lambda configuration: configuration)

    migrates("type_id", version="1.0.0")(migration_a)
    migrates("type_id", version="2.0.0")(migration_b)

    mock_configuration = MagicMock(label="type_id")
    new_configuration = migrate(mock_configuration)

    migration_a.assert_called_once_with(mock_configuration.copy())
    migration_b.assert_called_once_with(mock_configuration.copy())
    assert new_configuration == mock_configuration.copy()


def test_migrate_keys():
    configuration_value_mock = Mock()
    configuration = Configuration(
        label="type_id", configuration_items={"a": configuration_value_mock}
    )

    result = migrate_keys(configuration, {"a": "b"})

    assert "a" not in result.configuration_items
    assert "b" in result.configuration_items
    assert result.configuration_items["b"] == configuration_value_mock


def test_migrate_keys_warns_deprecated():
    configuration_value_mock = Mock()
    configuration = Configuration(
        label="type_id", configuration_items={"a": configuration_value_mock}
    )

    with pytest.warns(DeprecationWarning, match="a" and "type_id" and "b"):
        migrate_keys(configuration, {"a": "b"}, deprecated=True)


def test_migrate_keys_overwrites_false():
    configuration = Configuration("label", {"a": "old_value", "b": "new_value"})

    mock_a_value = MagicMock()
    mock_b_value = MagicMock()
    configuration = Configuration("label", {"a": mock_a_value, "b": mock_b_value})

    with pytest.warns(UserWarning):
        result = migrate_keys(configuration, {"a": "b"}, overwrite=False)
    assert "a" not in result
    assert result["b"] == mock_b_value


def test_migrate_keys_overwrites_true():
    mock_a_value = MagicMock()
    mock_b_value = MagicMock()
    configuration = Configuration("label", {"a": mock_a_value, "b": mock_b_value})

    with pytest.warns(UserWarning):
        result = migrate_keys(configuration, {"a": "b"}, overwrite=True)
    assert "a" not in result
    assert result["b"] == mock_a_value
