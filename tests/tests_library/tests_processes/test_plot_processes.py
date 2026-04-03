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


from pathlib import Path

import pandas as pd
import pytest

from physioblocks.library.processes.plot_processes import PlotProcess, SubplotProcess


@pytest.fixture
def sample_dataframe_1():
    return pd.DataFrame(
        {
            "time": [1.0, 2.0, 3.0],
            "pressure": [100.0, 200.0, 300.0],
            "flow": [0.5, 1.0, 1.5],
        }
    )


@pytest.fixture
def sample_dataframe_2():
    return pd.DataFrame(
        {
            "time": [4.0, 5.0, 6.0],
            "pressure": [400.0, 500.0, 600.0],
            "flow": [2.0, 2.5, 3.0],
        }
    )


class TestPlotProcess:
    def test_init_with_all_parameters(self):
        process = PlotProcess(
            abscissas="time",
            ordinates=["pressure", "flow"],
            layout={"title": "Test Plot"},
            file_format="html",
            inputs=["main"],
            outputs=["plot"],
            folder_path=Path("/tmp"),
            plot_name="test",
        )
        assert process.abscissas == "time"
        assert process.ordinates == ["pressure", "flow"]
        assert process.layout == {"title": "Test Plot"}
        assert process.file_format == "html"

    def test_init_with_default_parameters(self):
        process = PlotProcess(abscissas="time")
        assert process.abscissas == "time"
        assert process.ordinates == []
        assert process.layout == {}
        assert process.file_format == "html"

    def test_run_with_single_dataframe(self, sample_dataframe_1, tmp_path):
        process = PlotProcess(
            abscissas="time",
            ordinates=["pressure", "flow"],
            folder_path=tmp_path,
            plot_name="test",
        )

        result = process.run(sample_dataframe_1)

        assert len(result) == 1
        pd.testing.assert_frame_equal(result[0], sample_dataframe_1)

        plot_file = tmp_path / "test.html"
        assert plot_file.exists() is True

    def test_run_with_multiple_dataframes(
        self, sample_dataframe_1, sample_dataframe_2, tmp_path
    ):
        process = PlotProcess(
            abscissas="time",
            ordinates=["pressure", "flow"],
            folder_path=tmp_path,
            plot_name="test",
        )

        result = process.run(sample_dataframe_1, sample_dataframe_2)

        assert len(result) == 2
        pd.testing.assert_frame_equal(result[0], sample_dataframe_1)
        pd.testing.assert_frame_equal(result[1], sample_dataframe_2)

        plot_file = tmp_path / "test.html"
        assert plot_file.exists() is True

    def test_run_with_missing_abscissa(self, tmp_path, sample_dataframe_1):
        sample_dataframe_1.pop("time")

        process = PlotProcess(
            abscissas="time",
            ordinates=["pressure", "flow"],
            folder_path=tmp_path,
            plot_name="test",
        )

        result = process.run(sample_dataframe_1)

        assert len(result) == 1
        pd.testing.assert_frame_equal(result[0], sample_dataframe_1)

        plot_file = tmp_path / "test.html"
        assert plot_file.exists() is False

    def test_run_with_json_format(self, sample_dataframe_1, tmp_path):
        process = PlotProcess(
            abscissas="time",
            ordinates=["pressure"],
            file_format="json",
            folder_path=tmp_path,
            plot_name="test",
        )

        result = process.run(sample_dataframe_1)

        assert len(result) == 1
        pd.testing.assert_frame_equal(result[0], sample_dataframe_1)

        plot_file = tmp_path / "test.json"
        assert plot_file.exists() is True

    def test_run_with_png_format(self, sample_dataframe_1, tmp_path):
        process = PlotProcess(
            abscissas="time",
            ordinates=["pressure"],
            file_format="png",
            folder_path=tmp_path,
            plot_name="test",
        )

        result = process.run(sample_dataframe_1)

        assert len(result) == 1
        pd.testing.assert_frame_equal(result[0], sample_dataframe_1)

        plot_file = tmp_path / "test.png"
        assert plot_file.exists() is False


class TestSubplotProcess:
    def test_init_with_all_parameters(self):
        process = SubplotProcess(
            abscissas="time",
            ordinates=["pressure", "flow"],
            layout={"title": "Test Subplot"},
            file_format="html",
            rows_height=400.0,
        )
        assert process.abscissas == "time"
        assert process.ordinates == ["pressure", "flow"]
        assert process.layout == {"title": "Test Subplot"}
        assert process.file_format == "html"
        assert process.rows_height == 400.0

    def test_init_with_default_parameters(self):
        process = SubplotProcess(abscissas="time")
        assert process.abscissas == "time"
        assert process.ordinates == []
        assert process.layout == {}
        assert process.file_format == "html"
        assert process.rows_height == 300.0

    def test_run_with_single_dataframe(self, sample_dataframe_1, tmp_path):
        process = SubplotProcess(
            abscissas="time",
            ordinates=["pressure", "flow"],
            folder_path=tmp_path,
            plot_name="test",
        )

        result = process.run(sample_dataframe_1)

        assert len(result) == 1
        pd.testing.assert_frame_equal(result[0], sample_dataframe_1)

        plot_file = tmp_path / "test.html"
        assert plot_file.exists() is True

    def test_run_with_multiple_dataframes(
        self, sample_dataframe_1, sample_dataframe_2, tmp_path
    ):
        process = SubplotProcess(
            abscissas="time",
            ordinates=["pressure", "flow"],
            folder_path=tmp_path,
            plot_name="test",
        )

        result = process.run(sample_dataframe_1, sample_dataframe_2)

        assert len(result) == 2
        pd.testing.assert_frame_equal(result[0], sample_dataframe_1)
        pd.testing.assert_frame_equal(result[1], sample_dataframe_2)

        plot_file = tmp_path / "test.html"
        assert plot_file.exists() is True

    def test_run_with_missing_abscissa(self, tmp_path, sample_dataframe_1):
        sample_dataframe_1.pop("time")

        process = SubplotProcess(
            abscissas="time",
            ordinates=["pressure", "flow"],
            folder_path=tmp_path,
            plot_name="test",
        )

        result = process.run(sample_dataframe_1)

        assert len(result) == 1
        pd.testing.assert_frame_equal(result[0], sample_dataframe_1)

        plot_file = tmp_path / "test.html"
        assert plot_file.exists() is False
