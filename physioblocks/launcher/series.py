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

"""Defines functions to handle series and simulation results."""

import socket
from dataclasses import dataclass
from datetime import datetime
from importlib.metadata import version
from pathlib import Path

import pandas as pd

import physioblocks
from physioblocks.launcher.constants import (
    LAUNCHER_DATE_TIME_FORMAT,
    LAUNCHER_HOSTNAME_SEPARATOR,
    LAUNCHER_LOG_COLUMNS,
    LAUNCHER_LOG_FILE_SEPARATOR,
    LAUNCHER_REFERENCE_SEPARATOR,
)


@dataclass(frozen=True)
class SimulationInfo:
    """
    Hold information about the simulation.

    Parameters
    ----------
    machine_name : str
        the name of the machine running the simulation
    date_time : str
        the time stamp of the simulation run
    series : str
        the simulation series
    number : str
        the simulation number
    version : str
        the PhysioBlocks version used
    message : str
        a note associated with the simulation

    """

    machine_name: str
    date_time: str
    series: str
    number: str
    version: str
    message: str = ""

    @property
    def reference(self) -> str:
        """Get the simulation unique reference.

        Returns
        -------
        str
            the simulation reference.
        """
        return str.join(
            LAUNCHER_REFERENCE_SEPARATOR, [self.machine_name, self.series, self.number]
        )

    @property
    def data_frame(self) -> pd.DataFrame:
        """
        Get a dataframe representing the simulation information.

        Returns
        -------
        pd.DataFrame
            the simulation information in a dataframe
        """
        return pd.DataFrame(
            [
                [
                    self.date_time,
                    self.machine_name,
                    self.reference,
                    self.version,
                    self.message,
                ]
            ],
            columns=LAUNCHER_LOG_COLUMNS,
        )

    def __str__(self) -> str:
        return str.join(
            LAUNCHER_LOG_FILE_SEPARATOR,
            (
                self.date_time,
                self.machine_name,
                self.reference,
                self.version,
                self.message,
            ),
        )


def is_valid_reference_name(reference: str) -> bool:
    """
    Check a reference validity.

    A valid reference has at least 3 sections separated with underscores and ends
    with a number.

    Parameters
    ----------
    reference : str
        the reference to test.

    Returns
    -------
    bool
        True if the reference is valid, False otherwise.
    """
    dir_name_split = reference.split(LAUNCHER_REFERENCE_SEPARATOR)
    return len(dir_name_split) >= 3 and str.isdigit(dir_name_split[-1])


def is_valid_reference_dir_name(dir_name: str, series_name: str) -> bool:
    """
    Check a reference directory name validity.

    A valid reference directory name is a valid reference name that also contains the
    series name.

    Parameters
    ----------
    dir_name : str
        the name to check
    series_name : str
        the series name

    Returns
    -------
    bool
        True if the name is valid, False otherwise.
    """
    dir_name_split = dir_name.split(LAUNCHER_REFERENCE_SEPARATOR)
    dir_name_no_suffix = LAUNCHER_REFERENCE_SEPARATOR.join(dir_name_split[0:-1])
    return is_valid_reference_name(dir_name) and dir_name_no_suffix.endswith(
        series_name
    )


def get_reference_number(series_path: Path) -> str:
    """Get the next reference number for the given series folder path.

    Parameters
    ----------
    series_path : Path
        the series folder path

    Returns
    -------
    str
        the next reference number.

    Raises
    ------
    ValueError
        raises a ValueError if the given series path does not exist or is
        not a directory.

    """
    series_name = series_path.name
    if series_path.exists() is False or series_path.is_dir() is False:
        raise ValueError(str.format("No series directory at {0}", series_path))
    numbers = [
        int(d.name.split(LAUNCHER_REFERENCE_SEPARATOR)[-1])
        for d in series_path.iterdir()
        if is_valid_reference_dir_name(d.name, series_name) is True
    ]
    if len(numbers) > 0:
        return str(max(numbers) + 1)

    return str(1)


def get_simulation_info(series_path: Path, message: str) -> SimulationInfo:
    """Create simulation info from the given series path and message.

    Parameters
    ----------
    series_path : Path
        the simulation series path
    message : str
        the simulation message

    Returns
    -------
    SimulationInfo
        the simulation information

    """
    number = get_reference_number(series_path)

    # get the machine name
    host_name = socket.gethostname()
    machine_name = host_name.split(LAUNCHER_HOSTNAME_SEPARATOR, 2)[0]

    # get the current time stamp
    time_stamp = datetime.now().strftime(LAUNCHER_DATE_TIME_FORMAT)

    # get the PhysioBlocks version
    lib_version = version(physioblocks.__name__)

    return SimulationInfo(
        machine_name, time_stamp, series_path.name, number, lib_version, message
    )
