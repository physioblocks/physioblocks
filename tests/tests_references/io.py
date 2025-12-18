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

import numpy as np
import pandas as pd
import pytest

_logger = logging.getLogger(__name__)


def read_reference(reference_file: str) -> pd.DataFrame:
    data = pd.read_csv(reference_file, sep=";")
    return data


def results_close_to_data(
    results: pd.DataFrame,
    ref: pd.DataFrame,
    matching_ids: dict[str, str],
    tol: float,
    tol_factors: dict[str, float],
    interval: tuple[float, float] | None = None,
) -> bool:
    # if interval is provided, shorten the dataframes to
    # the provided interval
    results_df = results if interval is None else results[interval[0] : interval[1]]
    ref_df = ref if interval is None else ref[interval[0] : interval[1]]

    found_differences = False

    for var_id, data_id in matching_ids.items():
        result_array = results_df[var_id].to_numpy()
        ref_array = ref_df[data_id].to_numpy()

        if result_array != pytest.approx(ref_array, abs=tol * tol_factors[var_id]):
            found_differences = True
            message = str.format(
                "Results differ from reference for outputs: {0}", var_id
            )
            _logger.info(message)
            if result_array.shape != ref_array.shape:
                _logger.debug(
                    str.format(
                        "Reference and result shape differs: got {0} and {1}",
                        ref_array.shape,
                        result_array.shape,
                    )
                )
            else:
                absolute_error = abs(ref_array - result_array)
                mean_abs_error = np.mean(absolute_error)
                median_abs_error = np.median(absolute_error)
                max_abs_error = absolute_error.max()
                _logger.debug(str.format("absolute error mean: {0}", mean_abs_error))
                _logger.debug(
                    str.format("absolute error median: {0}", median_abs_error)
                )
                _logger.debug(str.format("absolute error max: {0}", max_abs_error))

    return not found_differences
