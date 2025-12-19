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

"""Define constants for the launcher scripts"""

# SIMULATION INFO

LAUNCHER_DATE_TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
"""Launcher format the represent date and time"""

LAUNCHER_HOSTNAME_SEPARATOR = "."
"""Launcher format the represent date and time"""

LAUNCHER_REFERENCE_SEPARATOR = "_"
"""Separator for SimulationInfo reference"""

LAUNCHER_REFERENCE_COLUMN = "reference"
"""SimulationInfo reference column id"""

LAUNCHER_DATE_COLUMN = "date_time"
"""SimulationInfo date column id"""

LAUNCHER_MACHINE_COLUMN = "machine"
"""SimulationInfo machine column id"""

LAUNCHER_VERSION_COLUMN = "version"
"""SimulationInfo version column id"""

LAUNCHER_NOTES_COLUMN = "notes"
"""SimulationInfo notes column id"""

LAUNCHER_LOG_COLUMNS = [
    LAUNCHER_DATE_COLUMN,
    LAUNCHER_MACHINE_COLUMN,
    LAUNCHER_REFERENCE_COLUMN,
    LAUNCHER_VERSION_COLUMN,
    LAUNCHER_NOTES_COLUMN,
]
"""The logged simulation info informations"""

LAUNCHER_LOG_FILE_SEPARATOR = ";"
"""the launcher log separator"""

# FILES

LAUNCHER_SERIES_DIR_NAME = "simulations"
"""name of the series directory."""

LAUNCHER_LOG_FILE_NAME = "launcher.log"
"""name of the log file."""

LAUNCHER_CONFIGURATION_FILE_NAME = "launcher.json"
"""name of the configuration file."""

LAUNCHER_GITIGNORE_FILE_NAME = ".gitignore"
"""name of the gitignore file."""

LAUNCHER_USER_LIBRARY_DIR_NAME = "user_library"
"""name of the user library directory."""

LAUNCHER_USER_ALIASES_DIR_NAME = "user_aliases"
"""name of the user aliases directory."""

LAUNCHER_CONFIGURATION_FILE_NAME = "launcher.json"
"""name of the configuration file."""

LAUNCHER_MODULE_INIT_FILE_NAME = "__init__.py"
"""Init file name"""

LAUNCHER_COMPARE_TRACE_FILE_NAME = "reference_compare.html"
"""Name of an error file generated with the compare module"""

# CONFIGURATION

LAUNCHER_CONFIGURATION_LIBRARIES_ID = "libraries"
"""name of the libraries item in the configuration"""

LAUNCHER_CONFIGURATION_ALIAS_ID = "aliases"
"""name of the aliases item in the configuration"""
