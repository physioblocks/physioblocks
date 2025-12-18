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
Describe function to handles the various launcher directory and files
"""

from pathlib import Path

import pandas as pd
import plotly
import plotly.graph_objects as go
import plotly.subplots

from physioblocks.launcher.constants import (
    LAUNCHER_DATE_COLUMN,
    LAUNCHER_LOG_FILE_NAME,
    LAUNCHER_REFERENCE_COLUMN,
    LAUNCHER_SERIES_DIR_NAME,
)
from physioblocks.launcher.series import SimulationInfo, is_valid_reference_name


def write_simulation_log_entry(root_folder_path: Path, info: SimulationInfo) -> None:
    launcher_log_path = root_folder_path / LAUNCHER_LOG_FILE_NAME
    if launcher_log_path.exists() and launcher_log_path.is_file():
        try:
            data = pd.read_csv(launcher_log_path)
            data = update_simulations_log(root_folder_path, data)
            # add the current simulation informations to the log
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


def update_simulations_log(
    root_folder_path: Path, sim_log: pd.DataFrame
) -> pd.DataFrame:
    launcher_log_path = root_folder_path / LAUNCHER_LOG_FILE_NAME
    series_dir_path = root_folder_path / LAUNCHER_SERIES_DIR_NAME

    if launcher_log_path.exists() is True:
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

    raise FileNotFoundError(
        "There is no log for the launcher at {0}", str(launcher_log_path.absolute())
    )


def write_simulation_results(
    simulation_folder: Path, info: SimulationInfo, data: pd.DataFrame, extension: str
) -> None:
    file_path = simulation_folder / str.join(".", [info.reference, extension])
    match extension:
        case "csv":
            data.to_csv(file_path, index=False, sep=";")
        case "parquet":
            data.to_parquet(file_path, index=False)
        case _:
            raise OSError(str.format("Invalid file extension: {0}", extension))


def write_figure(
    data_frame: pd.DataFrame,
    folder_path: Path,
    file_name: str,
    rows_height: float = 200.0,
) -> None:
    init_figure = go.Figure(
        layout=go.Layout(height=rows_height * len(data_frame.columns))
    )
    figure = plotly.subplots.make_subplots(
        len(data_frame.columns), 1, figure=init_figure, shared_xaxes=True
    )

    plot_index = 1
    for data_id in data_frame.columns:
        # Trace results
        figure.add_trace(
            go.Scatter(
                x=data_frame.index,
                y=data_frame[data_id],
                mode="lines",
                name=data_id,
            ),
            plot_index,
            1,
        )

        figure.update_xaxes(title="time", row=plot_index, col=1)
        figure.update_yaxes(
            title=data_id,
            row=plot_index,
            col=1,
        )
        plot_index += 1

    figure.write_html(folder_path / file_name)
