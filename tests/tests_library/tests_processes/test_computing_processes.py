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

from physioblocks.library.processes.computing_processes import (
    CompareProcess,
    ConvertProcess,
    InterpolationProcess,
)


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


@pytest.fixture
def sample_dataframe():
    return pd.DataFrame({"time": [1.0, 2.0, 3.0], "value": [10.0, 20.0, 30.0]})


@pytest.fixture
def comparison_dataframe():
    return pd.DataFrame({"time": [1.0, 2.0, 3.0], "value": [11.0, 21.0, 31.0]})


@pytest.fixture
def expected_diff_dataframe():
    return pd.DataFrame({"time": [1.0, 2.0, 3.0], "value": [1.0, 1.0, 1.0]})


@pytest.fixture
def expected_diff_without_abscissas():
    return pd.DataFrame({"value": [1.0, 1.0, 1.0]}, index=[0, 1, 2])


class TestCompareProcess:
    def test_init_with_all_parameters(self):
        process = CompareProcess(
            reference="ref.csv",
            abscissas="time",
            ordinates=["value1", "value2"],
            abscissas_precision=6,
            options={"sep": ","},
        )
        assert process.reference == "ref.csv"
        assert process.abscissas == "time"
        assert process.ordinates == ["value1", "value2"]
        assert process.abscissas_precision == 6
        assert process.options == {"sep": ","}

    def test_init_with_default_parameters(self):
        process = CompareProcess()
        assert process.reference is None
        assert process.abscissas is None
        assert process.ordinates == []
        assert process.abscissas_precision == 9
        assert process.options == {}

    def test_can_run_without_reference(self):
        process = CompareProcess()
        assert process.can_run is False

    def test_can_run_with_reference(self):
        process = CompareProcess(reference="ref.csv")
        assert process.can_run is True

    def test_run_without_reference(self, sample_dataframe):
        process = CompareProcess()
        with pytest.raises(ValueError, match="Process reference is not initialized"):
            process.run(sample_dataframe)

    def test_run_with_nonexistent_reference(self, sample_dataframe):
        process = CompareProcess(reference="nonexistent.csv")
        with pytest.raises(FileNotFoundError, match="File not found"):
            process.run(sample_dataframe)

    def test_run_with_unsupported_file_format(self, sample_dataframe, tmp_path):
        test_file = tmp_path / "test.txt"
        test_file.write_text("some content")

        process = CompareProcess(reference=str(test_file))
        with pytest.raises(NotImplementedError, match="Format not supported"):
            process.run(sample_dataframe)

    def test_run_with_csv_files(
        self, sample_dataframe, comparison_dataframe, expected_diff_dataframe, tmp_path
    ):
        ref_file = tmp_path / "reference.csv"
        sample_dataframe.to_csv(ref_file, index=False)

        process = CompareProcess(reference=str(ref_file), abscissas="time")
        result = process.run(comparison_dataframe)

        assert len(result) == 1
        assert isinstance(result[0], pd.DataFrame)
        pd.testing.assert_frame_equal(result[0], expected_diff_dataframe)

    def test_run_with_parquet_files(
        self, sample_dataframe, comparison_dataframe, expected_diff_dataframe, tmp_path
    ):
        ref_file = tmp_path / "reference.parquet"
        sample_dataframe.to_parquet(ref_file)

        process = CompareProcess(reference=str(ref_file), abscissas="time")
        result = process.run(comparison_dataframe)

        assert len(result) == 1
        assert isinstance(result[0], pd.DataFrame)
        pd.testing.assert_frame_equal(result[0], expected_diff_dataframe)

    def test_run_with_abscissas_precision_set(
        self, tmp_path, sample_dataframe, comparison_dataframe, expected_diff_dataframe
    ):
        ref_file = tmp_path / "reference.csv"
        sample_dataframe["time"] = [1.01, 2.01, 3.01]
        sample_dataframe.to_csv(ref_file, index=False)

        process = CompareProcess(
            reference=str(ref_file), abscissas="time", abscissas_precision=1
        )
        result = process.run(comparison_dataframe)

        assert len(result) == 1
        assert isinstance(result[0], pd.DataFrame)
        pd.testing.assert_frame_equal(result[0], expected_diff_dataframe)

    def test_run_with_specific_ordinates(
        self, tmp_path, sample_dataframe, comparison_dataframe, expected_diff_dataframe
    ):
        sample_dataframe["other_value"] = [100.0, 200.0, 300.0]
        comparison_dataframe["other_value"] = [101.0, 201.0, 301.0]

        ref_file = tmp_path / "reference.csv"
        sample_dataframe.to_csv(ref_file, index=False)

        process = CompareProcess(
            reference=str(ref_file), abscissas="time", ordinates=["value"]
        )
        result = process.run(comparison_dataframe)

        assert len(result) == 1
        assert isinstance(result[0], pd.DataFrame)
        assert list(result[0].columns) == ["time", "value"]

        pd.testing.assert_frame_equal(result[0], expected_diff_dataframe)

    def test_run_with_csv_options(
        self, tmp_path, sample_dataframe, comparison_dataframe, expected_diff_dataframe
    ):
        ref_file = tmp_path / "reference.csv"
        sample_dataframe.to_csv(ref_file, index=False, sep=";")
        process = CompareProcess(
            reference=str(ref_file), options={"sep": ";"}, abscissas="time"
        )
        result = process.run(comparison_dataframe)

        assert len(result) == 1
        assert isinstance(result[0], pd.DataFrame)

        pd.testing.assert_frame_equal(result[0], expected_diff_dataframe)

    def test_run_without_abscissas(
        self, tmp_path, sample_dataframe, comparison_dataframe, expected_diff_dataframe
    ):
        ref_file = tmp_path / "reference.csv"
        sample_dataframe.pop("time")
        sample_dataframe.to_csv(ref_file, index=False)

        process = CompareProcess(reference=str(ref_file), abscissas=None)
        comparison_dataframe.pop("time")
        result = process.run(comparison_dataframe)

        assert len(result) == 1
        assert isinstance(result[0], pd.DataFrame)
        expected_diff_dataframe.pop("time")
        pd.testing.assert_frame_equal(result[0], expected_diff_dataframe)

    def test_run_preserves_original_dataframe(
        self, tmp_path, sample_dataframe, comparison_dataframe, expected_diff_dataframe
    ):
        ref_file = tmp_path / "reference.csv"
        sample_dataframe.to_csv(ref_file, index=False)

        original_values = sample_dataframe.copy()
        process = CompareProcess(reference=str(ref_file))
        result = process.run(comparison_dataframe)

        assert len(result) == 1
        pd.testing.assert_frame_equal(sample_dataframe, original_values)


@pytest.fixture
def input_dataframe():
    return pd.DataFrame(
        {
            "time": [0.0, 0.002, 0.004],
            "pressure": [100.0, 200.0, 300.0],
            "flow": [0.5, 1.0, 1.5],
        }
    )


@pytest.fixture
def output_dataframe():
    return pd.DataFrame(
        {
            "time": [0.0, 0.001, 0.002, 0.003, 0.004],
            "pressure": [100.0, 150.0, 200.0, 250.0, 300.0],
            "flow": [0.5, 0.75, 1.0, 1.25, 1.5],
        }
    )


class TestInterpolationProcess:
    def test_constructor(self):
        process = InterpolationProcess(
            abscissas="time",
            abscissas_start=0.0,
            abscissas_length=0.004,
            abscissas_step=0.001,
            interpolation_method="linear",
            interpolation_options={"param": 2},
        )
        assert process.abscissas == "time"
        assert process.abscissas_start == 0.0
        assert process.abscissas_length == 0.004
        assert process.abscissas_step == 0.001
        assert process.interpolation_method == "linear"
        assert process.interpolation_options == {"param": 2}

    def test_default_constructor(self):
        process = InterpolationProcess()
        assert process.abscissas is None
        assert process.abscissas_start == 0.0
        assert process.abscissas_length == 0.001
        assert process.abscissas_step == 0.001
        assert process.interpolation_method == "index"
        assert process.interpolation_options == {}

    def test_can_run_true(self):
        process = InterpolationProcess(abscissas="anything")
        assert process.can_run is True

    def test_can_run_false(self):
        process = InterpolationProcess()
        assert process.can_run is False

    def test_run_single_input(self, input_dataframe, output_dataframe):
        process = InterpolationProcess(
            abscissas="time",
            abscissas_start=0.0,
            abscissas_length=0.004,
            abscissas_step=0.001,
        )

        result = process.run(input_dataframe)

        assert len(result) == 1
        assert len(result[0]) == 5
        assert output_dataframe.equals(result[0])

    def test_run_with_custom_interpolation_options(
        self, input_dataframe, output_dataframe
    ):
        process = InterpolationProcess(
            abscissas="time",
            abscissas_start=0.0,
            abscissas_length=0.004,
            abscissas_step=0.001,
            interpolation_method="polynomial",
            interpolation_options={"order": 1},
        )

        result = process.run(input_dataframe)

        assert len(result) == 1
        assert output_dataframe.equals(result[0])

    def test_run_with_zero_duration(self, input_dataframe):
        process = InterpolationProcess(
            abscissas="time",
            abscissas_start=0.0,
            abscissas_length=0.0,
            abscissas_step=0.001,
        )

        result = process.run(input_dataframe)

        assert len(result) == 1
        assert input_dataframe.equals(result[0])

    def test_run_with_large_step_size(self, input_dataframe):
        process = InterpolationProcess(
            abscissas="time",
            abscissas_start=0.0,
            abscissas_length=0.004,
            abscissas_step=0.01,
        )

        result = process.run(input_dataframe)

        assert len(result) == 1
        assert input_dataframe.equals(result[0])
