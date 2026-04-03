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

from typing import Any

from pandas import DataFrame

from physioblocks.registers.type_register import register_type
from physioblocks.simulation.process import AbstractProcess


@register_type("conversion_process")
class ConvertProcess(AbstractProcess):
    """
    Multiply every identified data in the input dataframes with the matching
    conversion factor

    :param conversion_factors: a dictionary matching data id with a conversion factor
    :type conversion_factors: dict[str, float]
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
        """
        Apply the conversion on inputs the dataframes

        :return: the outputs dataframes
        :rtype: list[DataFrame]
        """
        results: list[DataFrame] = []

        for df in dfs:
            df_copy = df.copy()
            for quantity_id, conversion_factor in self.conversion_factors.items():
                if quantity_id in df:
                    df_copy[quantity_id] = df[quantity_id] * conversion_factor
            results.append(df_copy)

        return results
