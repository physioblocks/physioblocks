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
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import regex as re

from physioblocks.launcher.configuration import (
    check_launcher_directory,
    check_target_launcher_directory,
    create_simulation_folder_path,
    get_launcher_configuration,
    setup_launcher_directory,
)
from physioblocks.launcher.constants import (
    LAUNCHER_CONFIGURATION_ALIAS_ID,
    LAUNCHER_CONFIGURATION_FILE_NAME,
    LAUNCHER_CONFIGURATION_LIBRARIES_ID,
    PHYSIOBLOCKS_REFERENCES_PATH,
)


@pytest.fixture
def launcher_config():
    return {
        LAUNCHER_CONFIGURATION_LIBRARIES_ID: [],
        LAUNCHER_CONFIGURATION_ALIAS_ID: [],
    }


def test_create_configuration_folder_path(tmp_path: Path):
    sim_info_mock = MagicMock(reference="sim_reference")
    new_path = create_simulation_folder_path(tmp_path, sim_info_mock)

    assert new_path.is_dir() is True
    assert new_path.exists() is True
    assert new_path == tmp_path / "sim_reference"


def test_check_target_launcher_directory_dont_exist(tmp_path: Path):
    dir_path = tmp_path / "not_created_dir"
    assert check_target_launcher_directory(dir_path) is True


def test_check_target_launcher_directory_is_empty(tmp_path: Path):
    dir_path = tmp_path / "empty_dir"
    dir_path.mkdir()
    assert check_target_launcher_directory(dir_path) is True


def test_check_target_launcher_directory_is_not_empty(tmp_path: Path):
    dir_path = tmp_path / "sim_dir"
    dir_path.mkdir()
    element_path = dir_path / "element"
    element_path.mkdir()

    assert check_target_launcher_directory(dir_path) is False


def test_check_launcher_directory_empty(tmp_path: Path):
    dir_path = tmp_path / "sim_dir"
    dir_path.mkdir()

    assert check_launcher_directory(dir_path) is False


def test_setup_launcher_directory(tmp_path: Path):
    dir_path = tmp_path / "sim_dir"
    reference_path = tmp_path / PHYSIOBLOCKS_REFERENCES_PATH
    with (
        patch.object(Path, "parent", tmp_path),
        pytest.warns(UserWarning, match=re.escape(str(reference_path))),
    ):
        setup_launcher_directory(dir_path)

    assert check_launcher_directory(dir_path) is True


def test_setup_launcher_directory_copy_references(tmp_path: Path):
    dir_path = tmp_path / "sim_dir"
    reference_path = tmp_path / PHYSIOBLOCKS_REFERENCES_PATH
    reference_path.mkdir()
    with patch.object(Path, "parent", tmp_path):
        setup_launcher_directory(dir_path)

    assert check_launcher_directory(dir_path) is True
    assert (dir_path / PHYSIOBLOCKS_REFERENCES_PATH).exists() is True


def test_get_launcher_configuration(tmp_path: Path, launcher_config: dict[str, Any]):
    config_file = tmp_path / LAUNCHER_CONFIGURATION_FILE_NAME
    launcher_config_str = json.dumps(launcher_config)
    config_file.write_text(launcher_config_str)

    configuration = get_launcher_configuration(tmp_path)

    assert configuration == launcher_config
