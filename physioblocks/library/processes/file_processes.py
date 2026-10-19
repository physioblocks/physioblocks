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
"""Declare processes handling files."""

from __future__ import annotations

import warnings
from pathlib import Path
from typing import Any

from pandas import DataFrame

from physioblocks.base.function_factories import attribute_checker
from physioblocks.registers.type_register import register_type
from physioblocks.simulation.process import AbstractProcess, run_method_checkers


@run_method_checkers(attribute_checker("mapping"))
@register_type("rename_process")
class RenameProcess(AbstractProcess):
    """Rename components of each input with the provided mapping.

    Parameters
    ----------
    mapping : dict[str, str]
        the mapping of old to new names
    component : str
        name of the component to rename. Default is "columns".

    Configuration
    -------------

    .. code-block:: json

        {
            "type": "rename_process",
            "inputs": ["<str>"],     // Names of the input data
            "outputs": ["<str>"],    // Names of the output data
            "mapping": {             // New name for each old name
                "<str>": "<str>"
            },
            "component": "<str>"     // Renamed component ("columns" or "index")
                                     // (optional, default: "columns")
        }

    """

    def __init__(
        self,
        mapping: dict[str, str] | None = None,
        component: str = "columns",
        *args: Any,
        **kwargs: Any,
    ) -> None:
        self.mapping = mapping if mapping is not None else {}
        self.component = component
        super().__init__(*args, **kwargs)

    def run(self, *dfs: DataFrame) -> list[DataFrame]:
        """Rename components of the dataframes.

        Parameters
        ----------
        *dfs : DataFrame
            the inputs to rename

        Returns
        -------
        list[DataFrame]
            the outputs dataframes

        """
        results = [df.rename(self.mapping, axis=self.component) for df in dfs]

        return results


@register_type("drop_process")
class DropProcess(AbstractProcess):
    """Drop identified lines and columns in the data.

    Parameters
    ----------
    columns: list[str] | None
        The list of columns to drop.
        Default is 'None', no column is deleted
    abscissas_name: str
        The name of the abscissa where to drop lines
        Default is 'time'
    abscissas_interval: tuple[float, float] | None
        The interval of abscissas to drop.
        Default is `None`: no abscissas is deleted.

    Configuration
    -------------

    .. code-block:: json

        {
            "type": "drop_process",
            "inputs": ["<str>"],        // Names of the input data
            "outputs": ["<str>"],       // Names of the output data
            "columns": ["<str>"],       // Names of the columns to drop (optional)
            "abscissas_interval": "[<float>, <float>]"
                                        // start and end value of the abscissas interval
                                        // to drop. (optional)
            "abscissas_name": "<str>"   // Name of the abscissas to drop
                                        // (optional, default is 'time')
        }

    """

    def __init__(
        self,
        columns: list[str] | None = None,
        abscissas_name: str = "time",
        abscissas_interval: tuple[float, float] | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        self.columns = columns
        self.interval = abscissas_interval
        self.abscissas = abscissas_name
        super().__init__(*args, **kwargs)

    def run(self, *dfs: DataFrame) -> list[DataFrame]:
        """Drop columns and lines in input data.

        For every input, drop the columns and the specified abscissas range.
        Then map it on the outputs.

        Parameters
        ----------
        *dfs : DataFrame
            the inputs to rename

        Returns
        -------
        list[DataFrame]
            the outputs dataframes
        """
        results = []
        for df in dfs:
            out_df: DataFrame = df.copy()

            if self.columns is not None:
                out_df = out_df.drop(labels=self.columns, axis=1)

            if self.interval is not None:
                start, end = self.interval
                interval_indexes = out_df.index[
                    out_df[self.abscissas].between(start, end)
                ]
                out_df = out_df.drop(labels=interval_indexes, axis=0)

            results.append(out_df)

        return results


@register_type("write_process")
class WriteProcess(AbstractProcess):
    """
    Write the DataFrame at specified location.

    When using the launcher, every file is saved in the series folder.
    Use this process to save a dataframe anywhere else.

    Parameters
    ----------
    destinations: list[str]
        List of the paths to write the data to.
        The size should match the size of the inputs to write.

    Configuration
    -------------

    .. code-block:: json

        {
            "type": "write_process",
            "inputs": ["<str>"],        // Names of the input data
            "destinations": ["<str>"],  // Paths where to write each input respectively.
        }

    """

    def __init__(self, destinations: list[str], *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.destinations = [Path(destination) for destination in destinations]

    def run(self, *dfs: DataFrame) -> DataFrame:
        """
        Write the input data to destinations.

        Returns
        -------
        DataFrame
            the inputs dataframes
        """
        for destination, data in zip(self.destinations, dfs, strict=True):
            destination.parent.mkdir(parents=True, exist_ok=True)
            if destination.suffix == ".csv":
                data.to_csv(destination)
            elif destination.suffix == ".parquet":
                data.to_parquet(destination)
            else:
                warnings.warn(
                    f"File format not supported: {destination}. File skipped.",
                    UserWarning,
                    stacklevel=2,
                )

        return dfs
