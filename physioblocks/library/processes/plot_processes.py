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
"""Declare processes that trace plots."""

import logging
from pathlib import Path
from typing import Any, ClassVar

import pandas
from pandas import DataFrame
from plotly.graph_objects import Figure, Scatter
from plotly.subplots import make_subplots

from physioblocks.registers.type_register import register_type
from physioblocks.simulation.process import AbstractPlotProcess
from physioblocks.utils.exceptions_utils import log_exception

_logger = logging.getLogger(__name__)


@register_type("plot")
class SubplotProcess(AbstractPlotProcess):
    """Create subplots for every column against the given abscissa id.

    Attributes
    ----------
    abscissas : str
        the abscissa data id
    subplots : list[str]
        the data ids subplots to plot. If empty, every data column is plotted.
    rows_height : float
        dimension of each row subplot
    layout : dict[str, Any]
        parameter to update the default layout.
    traces : dict[str, Any]
        the traces to plot in each subplot, with their matching data id pattern and
        style. Default is a blue line.
    file_format : str
        file format to save the plot (``html`` or ``json``). Default is ``html``.

    Configuration
    -------------

    Plots are set in the ``plots`` item of the simulation configuration. The plot
    name is its key in the ``plots`` item, and the launcher writes it in the
    simulation folder.

    .. code-block:: json

        {
            "type": "plot",
            "inputs": ["<str>"],          // Names of the plotted dataframes
            "abscissas": "<str>",         // Name of the abscissas column in the data
            "subplots": ["<str>"],        // Plotted columns, one subplot each
                                          // (optional, default: plot every column)
            "traces": {                   // Traces plotted in each subplot
                                          // (optional, default: one blue line for
                                          // column data)
                "<str>": {                // The trace id.
                    "matches": "<str>",   // Column name pattern, "{subplot_id}"
                                          // is replaced by the subplot column id,
                    "style": {}           // Plotly trace style
                }
            },
            "layout": {},                 // Plotly layout update (optional)
            "rows_height": "<float>",     // Height of each subplot row
                                          // (optional, default: 300.0)
            "file_format": "<str>"        // "html" or "json"
                                          // (optional, default: "html")
        }
    """

    abscissas: str
    subplots: list[str]
    rows_height: float
    layout: dict[str, Any]
    file_format: str

    _default_traces: ClassVar[dict[str, Any]] = {
        "value": {
            "matches": "{subplot_id}",
            "style": {
                "mode": "lines",
                "line": {"color": "blue"},
            },
        }
    }

    def __init__(
        self,
        abscissas: str,
        subplots: list[str] | None = None,
        traces: dict[str, Any] | None = None,
        file_format: str = "html",
        layout: dict[str, Any] | None = None,
        rows_height: float = 300.0,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        self.abscissas = abscissas
        self.subplots = subplots if subplots is not None else []
        self.layout = layout if layout is not None else {}
        self.traces = traces if traces is not None else self._default_traces
        self.rows_height = rows_height
        self.file_format = file_format
        super().__init__(*args, **kwargs)

    def run(self, *dataframes: DataFrame) -> list[DataFrame]:
        """
        Trace the plots.

        Parameters
        ----------
        *dataframes : DataFrame
            the data to plot

        Returns
        -------
        list[DataFrame]
            the input dataframes
        """
        pandas.options.plotting.backend = "plotly"
        try:
            concat_df: DataFrame = pandas.concat(dataframes).set_index(self.abscissas)
            subplots = concat_df.columns if len(self.subplots) == 0 else self.subplots
            figure: Figure = make_subplots(
                rows=len(subplots), cols=1, shared_xaxes=True, subplot_titles=subplots
            )
            show_legends = {
                trace_id: bool(trace_arguments.get("showlegend", True))
                for trace_id, trace_arguments in self.traces.items()
            }
            for index in range(len(subplots)):
                base_ordinate = subplots[index]
                for trace_id, trace_params in self.traces.items():
                    trace_ordinate = trace_params["matches"].replace(
                        "{subplot_id}", base_ordinate
                    )
                    if trace_ordinate in concat_df.columns:
                        figure.add_trace(
                            Scatter(
                                x=concat_df.index,
                                y=concat_df[trace_ordinate],
                                name=trace_id,
                                showlegend=show_legends[trace_id],
                                **trace_params["style"],
                            ),
                            row=index + 1,
                            col=1,
                        )
                        show_legends[trace_id] = False
                    else:
                        _logger.debug(
                            f"There is no column named {trace_ordinate} in results. \
                            Trace skipped."
                        )

            figure.update_xaxes(title=self.abscissas)

            # Update plot height depending on row size if height layout is not set
            if "height" not in self.layout:
                self.layout["height"] = self.rows_height * len(subplots)

            figure.update_layout(self.layout)
            _write_figure(figure, self.folder_path, self.plot_name, self.file_format)
        except (KeyError, NotImplementedError) as error:
            log_exception(_logger, KeyError, error, error.__traceback__, logging.DEBUG)
            _logger.error(f"Error while plotting {self.plot_name}. Plot skipped.")

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
