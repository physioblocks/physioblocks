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
"""Declares processes to compute data."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas
from pandas import DataFrame, concat

from physioblocks.base.function_factories import attribute_checker
from physioblocks.registers.type_register import register_type
from physioblocks.simulation.process import AbstractProcess, run_method_checkers


@register_type("conversion_process")
class ConvertProcess(AbstractProcess):
    """Multiply every identified data in the input with the matching conversion factor.

    Parameters
    ----------
    conversion_factors : dict[str, float]
        a dictionary matching data id with a conversion factor

    Configuration
    -------------

    .. code-block:: json

        {
            "type": "conversion_process",
            "inputs": ["<str>"],         // Names of the input data
            "outputs": ["<str>"],        // Names of the output data
            "conversion_factors": {      // Conversion factor for each data column name
                "<str>": "<float>"
            }
        }

    """

    conversion_factors: dict[str, float]

    def __init__(
        self,
        conversion_factors: dict[str, float] | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.conversion_factors = (
            conversion_factors if conversion_factors is not None else {}
        )

    def run(self, *dfs: DataFrame) -> list[DataFrame]:
        """Apply the conversion on the input dataframes.

        Parameters
        ----------
        *dfs : DataFrame
            the inputs to convert

        Returns
        -------
        list[DataFrame]
            the outputs dataframes

        """
        results: list[DataFrame] = []

        for df in dfs:
            df_copy = df.copy()
            for quantity_id, conversion_factor in self.conversion_factors.items():
                if quantity_id in df:
                    df_copy[quantity_id] = df[quantity_id] * conversion_factor
            results.append(df_copy)

        return results


def _read_data_frame(path: Path, options: dict[str, Any]) -> DataFrame:
    if path.exists():
        if path.suffix == ".csv":
            return pandas.read_csv(path, **options)
        elif path.suffix == ".parquet":
            return pandas.read_parquet(path, **options)
        else:
            raise NotImplementedError(
                str.format(
                    "{0}: Format not supported for {1}",
                    str(path.suffix),
                    str(path.absolute()),
                )
            )
    else:
        raise FileNotFoundError(str.format("{0}: File not found", str(path.absolute())))


@register_type("compare_process")
@run_method_checkers(attribute_checker("reference"))
class CompareProcess(AbstractProcess):
    """Compute the absolute error between every input file with the reference file.

    Parameters
    ----------
    reference : str | None
        path to the reference file. Default is None.
    abscissas : str | None
        name of the abscissas column used to align the data and the reference.
        Default is None, then compare with the current dataframes index.
    ordinates : list[str] | None
        names of the compared columns. Default is None: every column of the input
        is compared.
    abscissas_precision : int
        number of decimals used to round the abscissas. Default is 9.
    options : dict[str, Any] | None
        Optional arguments to pass to read the file format. Default is None.

    Configuration
    -------------

    .. code-block:: json

        {
            "type": "compare_process",
            "inputs": ["<str>"],              // Names of the compared data
            "outputs": ["<str>"],             // Names of the absolute error outputs
            "reference": "<str>",             // Path to the reference file
                                              // (.csv or .parquet). The process is
                                              // skipped when it is not set.
            "abscissas": "<str>",             // Abscissas column aligning the data
                                              // (optional, default: the data index)
            "ordinates": ["<str>"],           // Compared columns
                                              // (optional, default: every column)
            "abscissas_precision": "<int>",   // Decimals to round the abscissas
                                              // (optional, default: 9)
            "options": {"<str>": "<any>"}     // Arguments to read the reference file
                                              // (optional)
        }

    """

    def __init__(
        self,
        reference: str | None = None,
        abscissas: str | None = None,
        ordinates: list[str] | None = None,
        abscissas_precision: int = 9,
        options: dict[str, Any] | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        self.options = options if options is not None else {}
        self.abscissas = abscissas
        self.ordinates = ordinates if ordinates is not None else []
        self.reference = reference
        self.abscissas_precision = abscissas_precision

        super().__init__(*args, **kwargs)

    def run(self, data: DataFrame) -> list[DataFrame]:
        """Compute absolute error for each input dataframe with the reference.

        Parameters
        ----------
        data : DataFrame
            the input to compare

        Returns
        -------
        list[DataFrame]
            the outputs dataframes

        """
        if self.reference is None:
            raise ValueError("Process reference is not initialized.")
        reference = _read_data_frame(Path(self.reference), self.options)

        data_cpy = data.copy()
        reference_cpy = reference.copy()

        # set index to abscissas
        if self.abscissas is not None:
            data_cpy[self.abscissas] = data_cpy[self.abscissas].round(
                self.abscissas_precision
            )
            data_cpy = data_cpy.set_index(self.abscissas)
            reference_cpy[self.abscissas] = reference_cpy[self.abscissas].round(
                self.abscissas_precision
            )
            reference_cpy = reference_cpy.set_index(self.abscissas)

        # set columns to compare
        ordinates = self.ordinates if len(self.ordinates) > 0 else data_cpy.columns
        data_cpy = data_cpy[ordinates]
        reference_cpy = reference_cpy[ordinates]
        diff = data_cpy - reference_cpy
        diff = diff.abs()
        if self.abscissas is not None:
            diff = diff.reset_index()

        return [diff]


@register_type("interpolation_process")
@run_method_checkers(attribute_checker("abscissas"))
class InterpolationProcess(AbstractProcess):
    """Interpolate the input data for the given range.

    The interpolation is based on
    `pandas interpolate method <https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.interpolate.html>`__
    and uses the same parameters.
    You have to pass the ``method`` argument to ``interpolation_method``

    Parameters
    ----------
    abscissas : str | None
        name of the abscissas columns. Default is None.
    abscissas_start : float
        the start value for the abscissas. Default is 0.0.
    abscissas_length : float
        the length of the abscissas range. Default is 0.001.
    abscissas_step : float
        the step of the abscissas. Default is 0.001.
    abscissas_tolerance : float | None
        the relative tolerance to consider two abscissas are
        equals. Default is 1e-6
    interpolation_method : str
        the pandas interpolation method to use.
        Default is ``index``: linear interpolation for index values.
    interpolation_options : dict[str, Any] | None
        the optional arguments to pass to the pandas
        ``interpolate`` method. Default is None.

    Configuration
    -------------

    .. code-block:: json

        {
            "type": "interpolation_process",
            "inputs": ["<str>"],                 // Names of the input data
            "outputs": ["<str>"],                // Names of the output data
            "abscissas": "<str>",                // Name of the abscissas column
            "abscissas_start": "<float>",        // Start of the abscissas range
                                                 // (optional, default: 0.0)
            "abscissas_length": "<float>",       // Length of the abscissas range
                                                 // (optional, default: 0.001)
            "abscissas_step": "<float>",         // Step of the abscissas range
                                                 // (optional, default: 0.001)
            "abscissas_tolerance": "<float>",    // Relative tolerance to consider two
                                                 // abscissas equal
                                                 // (optional, default: 1e-6)
            "interpolation_method": "<str>",     // Pandas interpolation method
                                                 // (optional, default: "index")
            "interpolation_options": {           // Arguments of the pandas
                "<str>": "<any>"                 // interpolate method (optional)
            }
        }

    """

    def __init__(
        self,
        abscissas: str | None = None,
        abscissas_start: float = 0.0,
        abscissas_length: float = 0.001,
        abscissas_step: float = 0.001,
        abscissas_tolerance: float = 1e-6,
        interpolation_method: str = "index",
        interpolation_options: dict[str, Any] | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        self.abscissas_start = abscissas_start
        self.abscissas_length = abscissas_length
        self.abscissas_step = abscissas_step
        self.abscissas = abscissas
        self.abscissas_tolerance = abscissas_tolerance
        self.interpolation_method = interpolation_method
        self.interpolation_options = (
            interpolation_options if interpolation_options is not None else {}
        )

        super().__init__(*args, **kwargs)

    def run(self, *dfs: DataFrame) -> list[DataFrame]:
        """Interpolate the dataframes.

        Parameters
        ----------
        *dfs : DataFrame
            the inputs to interpolate

        Returns
        -------
        list[DataFrame]
            the outputs dataframes

        """
        results = []

        step_magnitude = np.abs(np.log10(self.abscissas_step))
        abs_tol_mag = np.abs(np.log10(self.abscissas_tolerance))
        rounding_digit = int(np.ceil(step_magnitude)) + int(np.ceil(abs_tol_mag))

        abscissas_values = np.append(
            np.arange(
                self.abscissas_start,
                self.abscissas_start + self.abscissas_length,
                self.abscissas_step,
            ),
            self.abscissas_start + self.abscissas_length,
        )
        for data in dfs:
            interpolation_df: DataFrame = concat(
                [data, DataFrame({self.abscissas: abscissas_values})]
            )
            interpolation_df = interpolation_df.set_index(self.abscissas)
            interpolation_df = interpolation_df.interpolate(
                method=self.interpolation_method, **self.interpolation_options
            )
            interpolation_df = interpolation_df.sort_index()
            interpolation_df = interpolation_df.reset_index()
            interpolation_df[self.abscissas] = interpolation_df[self.abscissas].round(
                rounding_digit
            )
            interpolation_df = interpolation_df.drop_duplicates()
            interpolation_df = interpolation_df.reset_index(drop=True)

            results.append(interpolation_df)

        return results
