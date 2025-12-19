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

import json
from dataclasses import dataclass
from pathlib import Path

import pytest

from physioblocks.configuration.base import Configuration
from physioblocks.io.configuration import read_json, write_json
from tests.helpers.file_helpers import clean_files

write_file_path = "./tests/tests_io/references/test_write.json"
ref_file_path = "./tests/tests_io/references/configuration.json"
alternative_config_file_path = "./tests/tests_io/references/alt_config_file_path.json"
commented_config_file_path = (
    "./tests/tests_io/references/commented_config_file_path.jsonc"
)

ROOT_ID = "root_item"
FLOAT_VAL_ID = "float_value"
INT_VAL_ID = "int_value"
STR_VAL_ID = "str_value"
CHILD_ID = "child"
CHILD_ITEM_ID = "child_item"


@dataclass
class NonSerializable:
    val_1: float
    val_2: int


@pytest.fixture
def ref_config():
    root = Configuration(ROOT_ID)
    root.configuration_items[FLOAT_VAL_ID] = 1.0
    root.configuration_items[INT_VAL_ID] = 1
    root.configuration_items[STR_VAL_ID] = "one"

    child = Configuration(CHILD_ITEM_ID)
    child.configuration_items[FLOAT_VAL_ID] = 2.0
    child.configuration_items[INT_VAL_ID] = 2
    child.configuration_items[STR_VAL_ID] = "two"

    root[CHILD_ID] = child

    return root


@pytest.fixture
def ref_alt_config(ref_config: Configuration) -> dict:
    return ref_config.configuration_items.copy()


def test_read_json(ref_config: Configuration, ref_alt_config: Configuration):
    config = read_json(ref_file_path)
    assert config == ref_config

    commented_config = read_json(commented_config_file_path)
    assert commented_config == ref_config

    alt_config = read_json(alternative_config_file_path)
    assert alt_config == ref_alt_config


@clean_files(write_file_path)
def test_write_json(ref_config: Configuration):
    write_json(write_file_path, ref_config)

    write_json_txt = Path(write_file_path).read_text()
    write_json_obj = json.loads(write_json_txt)

    ref_json_txt = Path(ref_file_path).read_text()
    ref_json_obj = json.loads(ref_json_txt)

    assert write_json_obj == ref_json_obj

    obj = NonSerializable(1.0, 2)
    with pytest.raises(TypeError):
        write_json(write_file_path, obj)
