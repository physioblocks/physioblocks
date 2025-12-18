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

from unittest.mock import Mock, patch

import pytest

import physioblocks.configuration.aliases as aliases
from physioblocks.configuration.aliases import (
    add_alias,
    get_alias,
    has_alias,
    remove_alias,
    unwrap_aliases,
)
from physioblocks.configuration.base import Configuration

ALIAS_ID = "alias"
ALIAS_TYPE = "alias_type"
ALIAS_DICT_ID = "alias_dict"
ALIAS_REGISTER_ID = "alias_register"
ALIAS_REC_ID = "alias_rec"
ALIAS_REC_DICT_ID = "alias_rec_dict"
OTHER_ID = "other"


@pytest.fixture
def alias() -> Configuration:
    return Configuration(ALIAS_TYPE)


@pytest.fixture
def alias_dict() -> Configuration:
    return {"dict": {"val_a": 0.1, "val_b": 0.2}}


@pytest.fixture
def alias_register() -> Configuration:
    config = Configuration(ALIAS_DICT_ID)
    config["dict"] = {"val_a": 0.3, "val_c": 0.4}
    config["list"] = []
    config["value"] = 0.0
    return config


@pytest.fixture
def alias_rec(alias_register: dict) -> Configuration:
    config = Configuration(ALIAS_ID)
    config["dict"] = alias_register
    config["list"] = []
    config["value"] = 0.0
    return config


@pytest.fixture
def alias_dict_rec(alias_rec: Configuration, alias_register: dict) -> Configuration:
    return {"alias": alias_rec, "list": [alias_rec], "dict": alias_register}


@pytest.fixture
def unwrapped_alias_register() -> Configuration:
    config = {
        "dict": {"val_a": 0.3, "val_b": 0.2, "val_c": 0.4},
        "list": [],
        "value": 0.0,
    }
    return config


@pytest.fixture
def unwrapped_alias_rec(unwrapped_alias_register: dict) -> Configuration:
    config = Configuration(ALIAS_TYPE)
    config["dict"] = unwrapped_alias_register
    config["list"] = []
    config["value"] = 0.0
    return config


@pytest.fixture
def unwrapped_alias_dict_rec(
    unwrapped_alias_rec: Configuration, unwrapped_alias_register: dict
) -> Configuration:
    return {
        "alias": unwrapped_alias_rec,
        "list": [unwrapped_alias_rec],
        "dict": unwrapped_alias_register,
    }


@patch.object(aliases, attribute="__aliases_register", new={})
def test_manages_aliases(alias: Configuration):
    add_alias(ALIAS_ID, alias)
    assert has_alias(ALIAS_ID) is True
    assert get_alias(ALIAS_ID) == alias

    remove_alias(ALIAS_ID)
    assert has_alias(ALIAS_ID) is False


@patch.object(aliases, attribute="__aliases_register", new={ALIAS_ID: None})
def test_add_alias_exceptions(alias: Configuration):
    err_msg = str.format("Alias key {0} is already registered.", ALIAS_ID)
    with pytest.raises(KeyError, match=err_msg):
        add_alias(ALIAS_ID, alias)

    err_msg = str.format(
        "Incorrect type for alias: {0}, expected {1}",
        float.__name__,
        Configuration.__name__,
    )
    with pytest.raises(TypeError, match=err_msg):
        add_alias(OTHER_ID, 0.0)


@patch("physioblocks.configuration.aliases.read_json")
def test_get_alias_from_file(mock_read_json: Mock, alias: Configuration):
    mock_read_json.return_value = alias
    file_alias = get_alias(None)
    assert file_alias == alias


def test_unwrap_alias(
    alias: Configuration,
    alias_rec: Configuration,
    alias_dict: dict,
    alias_dict_rec: dict,
    unwrapped_alias_dict_rec: dict,
):
    with patch.object(
        aliases,
        attribute="__aliases_register",
        new={
            ALIAS_ID: alias,
            ALIAS_REC_ID: alias_rec,
            ALIAS_DICT_ID: alias_dict,
            ALIAS_REC_DICT_ID: alias_dict_rec,
        },
    ):
        new_alias = get_alias(ALIAS_REC_DICT_ID)
        assert new_alias == alias_dict_rec
        assert unwrap_aliases(new_alias) == unwrapped_alias_dict_rec


def test_unwrap_alias_exception(alias_rec):
    err_msg = str.format("Type {0} can not load aliases.", type(None).__name__)
    with pytest.raises(TypeError, match=err_msg):
        unwrap_aliases(None)

    err_msg = str.format("{0} is not a valid alias type.", type(None).__name__)
    with (
        patch.object(
            aliases,
            attribute="__aliases_register",
            new={ALIAS_REC_ID: alias_rec, ALIAS_ID: None},
        ),
        pytest.raises(TypeError, match=err_msg),
    ):
        unwrap_aliases(alias_rec)
