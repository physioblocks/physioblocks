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


import pandas as pd
import pytest

from physioblocks.library.processes.conversion_process import ConvertProcess


@pytest.fixture
def conversion_factors():
    return {"pressure": 0.1, "flow": 1000}


@pytest.fixture
def sample_input_df1():
    return pd.DataFrame(
        {
            "time": [1.0, 2.0, 3.0],
            "pressure": [100.0, 200.0, 300.0],
            "flow": [0.5, 1.0, 1.5],
        }
    )


@pytest.fixture
def expected_converted_df1():
    return pd.DataFrame(
        {
            "time": [1.0, 2.0, 3.0],
            "pressure": [10.0, 20.0, 30.0],
            "flow": [500.0, 1000.0, 1500.0],
        }
    )


@pytest.fixture
def sample_input_df2():
    return pd.DataFrame(
        {
            "time": [4.0, 5.0, 6.0],
            "pressure": [400.0, 500.0, 600.0],
            "flow": [2.0, 2.5, 3.0],
        }
    )


@pytest.fixture
def expected_converted_df2():
    return pd.DataFrame(
        {
            "time": [4.0, 5.0, 6.0],
            "pressure": [40.0, 50.0, 60.0],
            "flow": [2000.0, 2500.0, 3000.0],
        }
    )


@pytest.fixture
def expected_partial_converted_df1():
    return pd.DataFrame(
        {
            "time": [1.0, 2.0, 3.0],
            "pressure": [10.0, 20.0, 30.0],
            "flow": [0.5, 1.0, 1.5],
        }
    )


class TestConvertProcess:
    def test_init_with_conversion_factors(self, conversion_factors):
        process = ConvertProcess(conversion_factors=conversion_factors)
        assert process.conversion_factors == conversion_factors

    def test_init_with_empty_conversion_factors(self):
        process = ConvertProcess()
        assert process.conversion_factors == {}

    def test_run_with_single_dataframe(
        self, conversion_factors, sample_input_df1, expected_converted_df1
    ):
        process = ConvertProcess(conversion_factors=conversion_factors)

        result = process.run(sample_input_df1)

        assert len(result) == 1
        pd.testing.assert_frame_equal(result[0], expected_converted_df1)

    def test_run_with_multiple_dataframes(
        self,
        conversion_factors,
        sample_input_df1,
        sample_input_df2,
        expected_converted_df1,
        expected_converted_df2,
    ):
        process = ConvertProcess(conversion_factors=conversion_factors)

        result = process.run(sample_input_df1, sample_input_df2)

        assert len(result) == 2
        pd.testing.assert_frame_equal(result[0], expected_converted_df1)
        pd.testing.assert_frame_equal(result[1], expected_converted_df2)

    def test_run_with_partial_conversion_factors(
        self, sample_input_df1, expected_partial_converted_df1
    ):
        partial_conversion_factors = {"pressure": 0.1}
        process = ConvertProcess(conversion_factors=partial_conversion_factors)
        result = process.run(sample_input_df1)

        assert len(result) == 1
        pd.testing.assert_frame_equal(result[0], expected_partial_converted_df1)

    def test_run_with_no_matching_columns(self, sample_input_df1):
        conversion_factors = {"temperature": 1.8}
        process = ConvertProcess(conversion_factors=conversion_factors)

        result = process.run(sample_input_df1)

        assert len(result) == 1
        pd.testing.assert_frame_equal(result[0], sample_input_df1)

    def test_run_preserves_original_dataframe(
        self, conversion_factors, sample_input_df1
    ):
        process = ConvertProcess(conversion_factors=conversion_factors)

        original_values = sample_input_df1.copy()
        result = process.run(sample_input_df1)

        assert len(result) == 1
        pd.testing.assert_frame_equal(sample_input_df1, original_values)
