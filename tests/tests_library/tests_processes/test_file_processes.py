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

import pandas
import pytest
from pandas import DataFrame

from physioblocks.library.processes.file_processes import (
    DropProcess,
    RenameProcess,
    WriteProcess,
)


class TestRenameProcess:
    def test_default_constructor(self):
        process = RenameProcess()
        assert process.mapping == {}
        assert process.component == "columns"

    def test_can_run_true(self):
        process = RenameProcess()
        assert process.can_run is True

    def test_can_run_false(self):
        process = RenameProcess()
        process.mapping = None
        assert process.can_run is False

    def test_run(self):
        dataframe_reference = pandas.DataFrame({"x": [], "y": []})
        dataframe_a = pandas.DataFrame(
            {
                "a1": [],
                "a2": [],
            }
        )
        dataframe_b = pandas.DataFrame(
            {
                "b1": [],
                "b2": [],
            }
        )
        process = RenameProcess(
            mapping={
                "a1": "x",
                "a2": "y",
                "b1": "x",
                "b2": "y",
            }
        )
        dataframe_a, dataframe_b = process.run(dataframe_a, dataframe_b)

        pandas.testing.assert_frame_equal(dataframe_a, dataframe_reference)
        pandas.testing.assert_frame_equal(dataframe_b, dataframe_reference)


class TestDropProcess:
    def test_default_constructor(self):
        process = DropProcess()
        assert process.columns is None
        assert process.interval is None
        assert process.abscissas == "time"

    def test_drop_columns(self):
        in_df = pandas.DataFrame({"x": [], "y": []})
        process = DropProcess(columns="y")

        [out_df] = process.run(in_df)
        assert "x" in out_df.columns
        assert "y" not in out_df.columns

    def test_drop_lines(self):
        in_df = pandas.DataFrame(
            {"x": [0.1 * i for i in range(5)], "y": [1.0 * i for i in range(5)]}
        )
        process = DropProcess(abscissas_name="x", abscissas_interval=[0.1, 0.3])

        [out_df] = process.run(in_df)
        assert "x" in out_df.columns
        assert "y" in out_df.columns
        assert out_df["x"].size == 3
        assert out_df["y"].size == 3


class TestWriteProcess:
    @pytest.mark.parametrize(
        "file_name",
        [
            pytest.param("tmp_file.csv", id="csv"),
            pytest.param("tmp_file.parquet", id="parquet"),
        ],
    )
    def test_write(self, tmp_path: Path, file_name: str):
        file_path = tmp_path / file_name
        process = WriteProcess([str(file_path)])
        process.run(DataFrame())
        assert file_path.exists() is True

    def test_skip_warn_unsupported(self, tmp_path: Path):
        json_file = tmp_path / "test_file.json"
        csv_file = tmp_path / "test_file.csv"
        process = WriteProcess([str(json_file), str(csv_file)])
        with pytest.warns(UserWarning, match=("not supported" and ".json")):
            process.run(DataFrame(), DataFrame())
        # json file skipped, csv file is still written
        assert json_file.exists() is False
        assert csv_file.exists() is True
