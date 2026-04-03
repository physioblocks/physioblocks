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

from physioblocks.library.processes.file_processes import CompareProcess


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
