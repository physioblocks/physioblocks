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

"""Declare methods to write files for the launcher."""

from pathlib import Path

import pandas as pd

from physioblocks.launcher.constants import (
    LAUNCHER_DATE_COLUMN,
    LAUNCHER_LOG_FILE_NAME,
    LAUNCHER_REFERENCE_COLUMN,
    LAUNCHER_SERIES_DIR_NAME,
)
from physioblocks.launcher.series import SimulationInfo, is_valid_reference_name


def write_simulation_log_entry(root_folder_path: Path, info: SimulationInfo) -> None:
    """Update the simulations logs with the provided simulation infos.

    If the simulation series folder has been updated (a simulation has been removed),
    also remove the logs from the log file.

    Parameters
    ----------
    root_folder_path : Path
        the launcher root path
    info : SimulationInfo
        the information to write

    Raises
    ------
    FileNotFoundError
        if the log file doesn't exist

    """
    launcher_log_path = root_folder_path / LAUNCHER_LOG_FILE_NAME
    if launcher_log_path.exists() and launcher_log_path.is_file():
        try:
            data = pd.read_csv(launcher_log_path)
            data = _update_simulations_log(root_folder_path, data)
            # add the current simulation information to the log
            data = pd.concat(
                [
                    data.set_index(LAUNCHER_DATE_COLUMN),
                    info.data_frame.set_index(LAUNCHER_DATE_COLUMN),
                ]
            )
            data.to_csv(launcher_log_path)

        except pd.errors.EmptyDataError:
            # Only log the current info
            info.data_frame.set_index(LAUNCHER_DATE_COLUMN).to_csv(launcher_log_path)
    else:
        raise FileNotFoundError(
            str.format(
                "There is no log for the launcher at {0}",
                str(launcher_log_path.absolute()),
            )
        )


def _update_simulations_log(
    root_folder_path: Path, sim_log: pd.DataFrame
) -> pd.DataFrame:
    series_dir_path = root_folder_path / LAUNCHER_SERIES_DIR_NAME

    # remove previous reference from log if it has been deleted
    all_references_name = [
        reference_dir_path.name
        for serie_dir_path in series_dir_path.iterdir()
        if serie_dir_path.is_dir()
        for reference_dir_path in serie_dir_path.iterdir()
        if is_valid_reference_name(reference_dir_path.name)
    ]
    following_references_mask = [
        sim_log.loc[i][LAUNCHER_REFERENCE_COLUMN] not in all_references_name
        for i in sim_log.index
    ]
    following_references_index = sim_log.iloc[following_references_mask].index
    new_sim_log = sim_log.drop(following_references_index)
    return new_sim_log


def write_simulation_results(
    simulation_folder: Path, data: dict[str, pd.DataFrame], extension: str
) -> None:
    """Write a set of dataframes with their provided id as filename.

    Parameters
    ----------
    simulation_folder : Path
        the simulation folder path where to save the results
    data : dict[str, pd.DataFrame]
        the dataframes associated with their names
    extension : str
        the file format. Can be either 'csv' or 'parquet'.

    Raises
    ------
    OSError
        if the extension is not supported.

    """
    file_format = extension if extension in ["csv", "parquet"] else None
    if file_format is None:
        raise OSError(str.format("Unsupported result file format: {0}", extension))
    for data_id, data_frame in data.items():
        file_path = simulation_folder / str.join(".", [data_id, file_format])
        match file_format:
            case "csv":
                data_frame.to_csv(file_path, index=False)
            case "parquet":
                data_frame.to_parquet(file_path, index=False)
