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

import logging
from pathlib import Path
from typing import Any

import pandas
from pandas import DataFrame
from plotly.graph_objects import Figure, Scatter
from plotly.subplots import make_subplots

from physioblocks.registers.type_register import register_type
from physioblocks.simulation.process import AbstractPlotProcess
from physioblocks.utils.exceptions_utils import log_exception

_logger = logging.getLogger(__name__)


@register_type("plot")
class PlotProcess(AbstractPlotProcess):
    """
    Plots the inputs dataframe using plotly

    If several dataframe are passed to the process, it concatenate them
    before plotting.
    """

    abscissas: str
    """the abscissa data id"""
    ordinates: list[str]
    """the data ids to plot"""
    layout: dict[str, Any]
    """parameter to update the default layout"""
    file_format: str
    """format to save the plot"""

    def __init__(
        self,
        abscissas: str,
        ordinates: list[str] | None = None,
        layout: dict[str, Any] | None = None,
        file_format: str = "html",
        *args: Any,
        **kwargs: Any,
    ) -> None:
        self.abscissas = abscissas
        self.ordinates = ordinates if ordinates is not None else []
        self.layout = layout if layout is not None else {}
        self.file_format = file_format

        super().__init__(*args, **kwargs)

    def run(self, *dataframes: DataFrame) -> list[DataFrame]:
        pandas.options.plotting.backend = "plotly"

        plot_df = pandas.concat(dataframes)
        try:
            plot_df = plot_df.set_index(self.abscissas)
            plot_df = plot_df[self.ordinates] if len(self.ordinates) > 0 else plot_df
            figure: Figure = plot_df.plot()
            figure.update_layout(self.layout)
            _write_figure(figure, self.folder_path, self.plot_name, self.file_format)
        except (KeyError, NotImplementedError) as error:
            log_exception(_logger, KeyError, error, error.__traceback__, logging.DEBUG)
            _logger.error("Error while plotting {0}. Plot skipped.")

        return [*dataframes]


@register_type("subplot")
class SubplotProcess(AbstractPlotProcess):
    """
    For every dataframe in input, create subplots for every column against
    the given abscissa id.
    """

    abscissas: str
    """the abscissa data id"""
    ordinates: list[str]
    """the data ids columns to plot. If empty, every column is plotted."""
    rows_height: float
    """dimension of each row subplot"""
    layout: dict[str, Any]
    """parameter to update the default layout."""
    file_format: str
    """file format to save the plot"""

    def __init__(
        self,
        abscissas: str,
        ordinates: list[str] | None = None,
        file_format: str = "html",
        layout: dict[str, Any] | None = None,
        rows_height: float = 300.0,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        self.abscissas = abscissas
        self.ordinates = ordinates if ordinates is not None else []
        self.layout = layout if layout is not None else {}
        self.rows_height = rows_height
        self.file_format = file_format
        super().__init__(*args, **kwargs)

    def run(self, *dataframes: DataFrame) -> list[DataFrame]:
        pandas.options.plotting.backend = "plotly"
        try:
            concat_df: DataFrame = pandas.concat(dataframes).set_index(self.abscissas)
            ordinates = (
                concat_df.columns if len(self.ordinates) == 0 else self.ordinates
            )
            figure: Figure = make_subplots(
                rows=len(ordinates), cols=1, shared_xaxes=True, subplot_titles=ordinates
            )
            for index in range(len(ordinates)):
                figure.add_trace(
                    Scatter(
                        x=concat_df.index,
                        y=concat_df[ordinates[index]],
                        mode="lines",
                        name=ordinates[index],
                    ),
                    row=index + 1,
                    col=1,
                )
            figure.update_xaxes(title=self.abscissas)

            # Update plot height depending on row size if height layout is not set
            if "height" not in self.layout:
                self.layout["height"] = self.rows_height * len(ordinates)

            figure.update_layout(self.layout)
            _write_figure(figure, self.folder_path, self.plot_name, self.file_format)
        except (KeyError, NotImplementedError) as error:
            log_exception(_logger, KeyError, error, error.__traceback__, logging.DEBUG)
            _logger.error("Error while plotting {0}. Plot skipped.")

        return [*dataframes]


def _write_figure(
    figure: Figure, folder_path: Path | None, file_name: str | None, file_format: str
) -> None:
    if file_name is None or folder_path is None:
        raise ValueError("Incomplete file_name or folder_path")
    file_path = folder_path / ".".join([file_name, file_format])

    if file_format == "html":
        figure.write_html(file_path)
    elif file_format == "json":
        figure.write_json(file_path)
    else:
        raise NotImplementedError(
            str.format(
                "Unsupported file format {0}. Supported file format are {1}",
                file_format,
                ["html", "json"],
            )
        )
