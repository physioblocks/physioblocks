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
import logging
import shutil
from pathlib import Path
from typing import Any

import physioblocks.library
from physioblocks.io.aliases import load_aliases
from physioblocks.launcher.constants import (
    LAUNCHER_CONFIGURATION_ALIAS_ID,
    LAUNCHER_CONFIGURATION_FILE_NAME,
    LAUNCHER_CONFIGURATION_LIBRARIES_ID,
    LAUNCHER_GITIGNORE_FILE_NAME,
    LAUNCHER_LOG_FILE_NAME,
    LAUNCHER_MODULE_INIT_FILE_NAME,
    LAUNCHER_SERIES_DIR_NAME,
    LAUNCHER_USER_ALIASES_DIR_NAME,
    LAUNCHER_USER_LIBRARY_DIR_NAME,
    PHYSIOBLOCKS_REFERENCES_PATH,
)
from physioblocks.launcher.series import SimulationInfo
from physioblocks.utils.dynamic_import_utils import import_libraries

_logger = logging.getLogger(__name__)


def create_simulation_folder_path(series_path: Path, info: SimulationInfo) -> Path:
    sim_folder_name = info.reference
    simulation_folder_path = series_path / sim_folder_name
    simulation_folder_path.mkdir()

    return simulation_folder_path


def check_target_launcher_directory(launcher_dir_path: Path) -> bool:
    """
    Check that the given directory is suitable to welcome a new launcher directory.

    It should either not exist (and therefore it will be created) or
    be an empty dir (to avoid erasing existing files)

    :param launcher_dir_path: the directory path
    :type launcher_dir_path: Path

    :return: True if the launcher dir can be created at this location,
      False otherwise
    :rtype: boolean
    """
    return launcher_dir_path.exists() is False or (
        launcher_dir_path.is_dir() and not any(launcher_dir_path.iterdir())
    )


def check_launcher_directory(launcher_dir_path: Path) -> bool:
    """
    Check that the given directory can launch a simulation.

    :param launcher_dir_path: the directory path
    :type launcher_dir_path: Path

    :return: True if a simulation can be launched at this location, False otherwise
    :rtype: boolean
    """
    return (
        launcher_dir_path.exists() is True
        and (
            (launcher_dir_path / LAUNCHER_SERIES_DIR_NAME).exists() is True
            and (launcher_dir_path / LAUNCHER_SERIES_DIR_NAME).is_dir()
        )
        and (
            (launcher_dir_path / LAUNCHER_CONFIGURATION_FILE_NAME).exists() is True
            and (launcher_dir_path / LAUNCHER_CONFIGURATION_FILE_NAME).is_file()
        )
        and (
            (launcher_dir_path / LAUNCHER_LOG_FILE_NAME).exists() is True
            and (launcher_dir_path / LAUNCHER_LOG_FILE_NAME).is_file()
        )
    )


def setup_launcher_directory(launcher_dir_path: Path) -> None:
    """
    Configure the launcher directory at the given path.

    :param launcher_dir_path:
    :type launcher_dir_path: Path
    """
    # Create the root simulation directory if it doesn't exist
    if launcher_dir_path.exists() is False:
        launcher_dir_path.mkdir()

    # Create the series directory if it doesn't exist
    series_path = launcher_dir_path / LAUNCHER_SERIES_DIR_NAME
    if series_path.exists() is False:
        series_path.mkdir()

    # create a empty log file
    launcher_log_file_path = launcher_dir_path / LAUNCHER_LOG_FILE_NAME
    launcher_log_file_path.touch()

    # copy simulations references from python package.
    physioblocks_references_folder_path = (
        Path(physioblocks.__file__).parent / PHYSIOBLOCKS_REFERENCES_PATH
    )
    launcher_references_folder_path = launcher_dir_path / PHYSIOBLOCKS_REFERENCES_PATH
    if physioblocks_references_folder_path.exists() is True:
        shutil.copytree(
            physioblocks_references_folder_path,
            launcher_references_folder_path,
            dirs_exist_ok=False,
        )
    else:
        _logger.warning(
            str.format(
                "No references configuration folder at: {0}",
                str(physioblocks_references_folder_path),
            )
        )

    # create the user library directory
    launcher_user_library_dir_path = launcher_dir_path / LAUNCHER_USER_LIBRARY_DIR_NAME
    if launcher_user_library_dir_path.exists() is False:
        launcher_user_library_dir_path.mkdir()

    # put an empty __init__.py file in the user library
    launcher_user_library_init_path = (
        launcher_user_library_dir_path / LAUNCHER_MODULE_INIT_FILE_NAME
    )
    launcher_user_library_init_path.touch()

    # create the user aliases directory
    launcher_user_aliases_dir_path = launcher_dir_path / LAUNCHER_USER_ALIASES_DIR_NAME
    if launcher_user_aliases_dir_path.exists() is False:
        launcher_user_aliases_dir_path.mkdir()

    # create a empty log file
    launcher_log_file_path = launcher_dir_path / LAUNCHER_LOG_FILE_NAME
    launcher_log_file_path.touch()

    # create the launcher configuration file
    base_library_dir_path = Path(physioblocks.library.__file__).parent
    base_aliases_dir_path = (
        Path(physioblocks.library.__file__).parent / LAUNCHER_CONFIGURATION_ALIAS_ID
    )
    base_configuration = {
        LAUNCHER_CONFIGURATION_LIBRARIES_ID: [
            str(base_library_dir_path.absolute()),
            str(launcher_user_library_dir_path.absolute()),
        ],
        LAUNCHER_CONFIGURATION_ALIAS_ID: [
            str(base_aliases_dir_path.absolute()),
            str(launcher_user_aliases_dir_path.absolute()),
        ],
    }
    launcher_configuration_file_path = (
        launcher_dir_path / LAUNCHER_CONFIGURATION_FILE_NAME
    )
    launcher_configuration_file_path.write_text(
        json.dumps(base_configuration, indent=4)
    )

    # create a gitignore file
    launcher_gitignore_path = Path(launcher_dir_path / LAUNCHER_GITIGNORE_FILE_NAME)
    launcher_gitignore_path.write_text("*")


def get_launcher_configuration(root_sim_directory: Path) -> Any:
    """
    Get the launcher configuration for the given simulation directory.

    :param root_sim_directory: the path to the launcher directory.
    :type root_sim_directory: Path

    :return: the configuration
    :rtype: dict
    """
    launcher_config_path = root_sim_directory / LAUNCHER_CONFIGURATION_FILE_NAME
    launcher_configuration = json.load(launcher_config_path.open("r"))
    return launcher_configuration


def import_configured_libraries(launcher_configuration: dict[str, Any]) -> None:
    """
    Dynamicaly import libraries in the given configuration

    :param launcher_configuration: the layncher configuration
    :type launcher_configuration: dict[str, Any]
    """
    libraries_paths = [
        Path(lib_path)
        for lib_path in launcher_configuration[LAUNCHER_CONFIGURATION_LIBRARIES_ID]
    ]

    import_libraries(libraries_paths)


def import_configured_aliases(launcher_configuration: dict[str, Any]) -> None:
    """
    Dynamicaly import all alias at the given paths in configuration

    :param launcher_configuration: the launcher configuration
    :type launcher_configuration: dict[str, Any]
    """
    for alias_path in launcher_configuration[LAUNCHER_CONFIGURATION_ALIAS_ID]:
        load_aliases(alias_path)
