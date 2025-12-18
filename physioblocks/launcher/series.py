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
Defines function to handles series and simulation results
"""

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


@dataclass
class SimulationInfo:
    machine_name: str
    "the mane of the machine running the simulation"
    date_time: str
    "the time stamp of the simulation run"
    series: str
    "the simulation serie"
    number: str
    "the simulation number"
    version: str
    "the PhysioBlocks version used"
    message: str = ""
    "a note associated with the simulation"

    @property
    def reference(self) -> str:
        return str.join(
            LAUNCHER_REFERENCE_SEPARATOR, [self.machine_name, self.series, self.number]
        )

    @property
    def data_frame(self) -> pd.DataFrame:
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
    dir_name_split = reference.split(LAUNCHER_REFERENCE_SEPARATOR)
    return len(dir_name_split) >= 3 and str.isdigit(dir_name_split[-1])


def is_valid_reference_dir_name(dir_name: str, series_name: str) -> bool:
    dir_name_split = dir_name.split(LAUNCHER_REFERENCE_SEPARATOR)
    dir_series_name = LAUNCHER_REFERENCE_SEPARATOR.join(dir_name_split[1:-1])
    return is_valid_reference_name(dir_name) and dir_series_name == series_name


def parse_reference_number(reference: str) -> tuple[str, str, int]:
    split_ref = reference.split(LAUNCHER_REFERENCE_SEPARATOR)

    if is_valid_reference_name(reference) is False:
        raise ValueError(
            str.format(
                "{0} is not a valid simulation reference name.",
                reference,
            )
        )

    number = split_ref[-1]
    serie = split_ref[-2]
    machine = str.join(LAUNCHER_REFERENCE_SEPARATOR, split_ref[0:-2])

    return machine, serie, int(number)


def reference_follows(tested_reference: str, base_reference: str) -> bool:
    # Return true if the base reference comes after (or is the same as)
    # the tested reference
    parsed_tested = parse_reference_number(tested_reference)
    parsed_base = parse_reference_number(base_reference)
    return parsed_tested[1] == parsed_base[1] and parsed_tested[2] >= parsed_base[2]


def get_reference_number(serie_path: Path) -> str:
    serie_name = serie_path.name
    if serie_path.exists() is False:
        raise FileNotFoundError(str.format("No series directory at {0}", serie_path))
    numbers = [
        int(d.name.split(LAUNCHER_REFERENCE_SEPARATOR)[-1])
        for d in serie_path.iterdir()
        if is_valid_reference_dir_name(d.name, serie_name) is True
    ]
    if len(numbers) > 0:
        return str(max(numbers) + 1)

    return str(1)


def get_simulation_info(serie_path: Path, message: str) -> SimulationInfo:
    number = get_reference_number(serie_path)

    # get the machine name
    host_name = socket.gethostname()
    machine_name = host_name.split(LAUNCHER_HOSTNAME_SEPARATOR, 2)[0]

    # get the current time stamp
    time_stamp = datetime.now().strftime(LAUNCHER_DATE_TIME_FORMAT)

    # get the PhysioBlocks version
    lib_version = version(physioblocks.__name__)

    return SimulationInfo(
        machine_name, time_stamp, serie_path.name, number, lib_version, message
    )
