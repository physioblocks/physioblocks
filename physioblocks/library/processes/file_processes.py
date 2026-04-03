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

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas
from pandas import DataFrame

from physioblocks.base.function_factories import attribute_checker
from physioblocks.registers.type_register import register_type
from physioblocks.simulation.process import AbstractProcess, run_method_checkers


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
    """
    Compute the absolute error between every input file with the matching
    reference file.

    :param references: paths to references files
    :type list[str]:

    :param options: Optional arguments to pass to read the file format.
    :type options: dict[str, Any]

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
        """
        Compute absolute error for each input dataframe with the reference.

        :param df: the inputs to compare
        :type df: DataFrame

        :return: the outputs dataframes
        :rtype: list[DataFrame]
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
