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

import re
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, Mock

import pandas
import pytest

from physioblocks.launcher.constants import (
    LAUNCHER_DATE_COLUMN,
    LAUNCHER_DATE_TIME_FORMAT,
    LAUNCHER_LOG_COLUMNS,
    LAUNCHER_LOG_FILE_NAME,
    LAUNCHER_REFERENCE_COLUMN,
    LAUNCHER_SERIES_DIR_NAME,
)
from physioblocks.launcher.files import (
    write_simulation_log_entry,
    write_simulation_results,
)
from physioblocks.launcher.series import SimulationInfo


@pytest.fixture
def log_file_dont_exist_root_path(tmp_path: Path):
    return tmp_path


@pytest.fixture
def log_is_folder_root_path(tmp_path: Path):
    log_file_path = tmp_path / LAUNCHER_LOG_FILE_NAME
    log_file_path.mkdir()
    return tmp_path


@pytest.fixture
def empty_log_root_path(tmp_path: Path):
    log_file_path = tmp_path / LAUNCHER_LOG_FILE_NAME
    log_file_path.touch()
    series_file_path = tmp_path / LAUNCHER_SERIES_DIR_NAME
    series_file_path.mkdir()
    return tmp_path


@pytest.fixture
def existing_log_dataframe():
    return pandas.DataFrame(
        [
            [
                datetime(1, 1, 1).strftime(LAUNCHER_DATE_TIME_FORMAT),
                "machine",
                "machine_series_1",
                "0.0.1",
                "notes on simulations",
            ]
        ],
        columns=LAUNCHER_LOG_COLUMNS,
    ).set_index(LAUNCHER_DATE_COLUMN)


@pytest.fixture
def sim_info():
    return SimulationInfo(
        "launch_machine",
        datetime(1, 1, 2).strftime(LAUNCHER_DATE_TIME_FORMAT),
        "series",
        "2",
        "0.0.1",
    )


@pytest.fixture
def test_log_missing_files_root_path(
    tmp_path: Path, existing_log_dataframe: pandas.DataFrame
):
    log_file_path = tmp_path / LAUNCHER_LOG_FILE_NAME
    existing_log_dataframe.to_csv(log_file_path)
    series_file_path: Path = tmp_path / LAUNCHER_SERIES_DIR_NAME / "series"
    series_file_path.mkdir(parents=True)
    return tmp_path


@pytest.fixture
def test_log_root_path(
    test_log_missing_files_root_path, existing_log_dataframe: pandas.DataFrame
):
    series_file_path: Path = (
        test_log_missing_files_root_path
        / LAUNCHER_SERIES_DIR_NAME
        / "series"
        / existing_log_dataframe.reset_index()[LAUNCHER_REFERENCE_COLUMN][0]
    )
    series_file_path.mkdir(parents=True)
    return test_log_missing_files_root_path


@pytest.mark.parametrize(
    "path",
    [
        pytest.param("log_file_dont_exist_root_path", id="log_file_dont_exist"),
        pytest.param("log_is_folder_root_path", id="log_is_folder"),
    ],
)
def test_write_simulation_log_entry_raise_file_not_found(
    path, request: pytest.FixtureRequest
):
    root_path = request.getfixturevalue(path)
    with pytest.raises(FileNotFoundError, match=re.escape(str(root_path))):
        write_simulation_log_entry(root_path, Mock())


@pytest.mark.parametrize(
    "path",
    [
        pytest.param("empty_log_root_path", id="empty_log_file"),
        pytest.param("test_log_root_path", id="populated_log_file"),
    ],
)
def test_write_simulation_log_entry(
    path: str, sim_info: SimulationInfo, request: pytest.FixtureRequest
):
    root_path: Path = request.getfixturevalue(path)
    write_simulation_log_entry(root_path, sim_info)
    log_file_path = root_path / LAUNCHER_LOG_FILE_NAME

    assert log_file_path.exists() is True
    assert log_file_path.suffix == ".log"

    logs_df = pandas.read_csv(log_file_path, na_filter=False)

    # Check the entire simulation log dataframe is in the csv dataframe
    df_intersection = pandas.merge(
        logs_df, sim_info.data_frame, how="inner", on=LAUNCHER_LOG_COLUMNS
    )
    pandas.testing.assert_frame_equal(df_intersection, sim_info.data_frame)


def test_update_simulation_log_entry_drops_missing_files(
    test_log_missing_files_root_path: Path,
    sim_info: SimulationInfo,
    existing_log_dataframe: pandas.DataFrame,
):
    write_simulation_log_entry(test_log_missing_files_root_path, sim_info)
    log_file_path = test_log_missing_files_root_path / LAUNCHER_LOG_FILE_NAME

    assert log_file_path.exists() is True
    assert log_file_path.suffix == ".log"

    logs_df = pandas.read_csv(log_file_path, na_filter=False)

    # the sim reference is logged:
    pandas.testing.assert_frame_equal(logs_df, sim_info.data_frame)
    # but the original reference is dropped:
    df_intersection = pandas.merge(
        logs_df, existing_log_dataframe, how="inner", on=LAUNCHER_LOG_COLUMNS
    )
    assert df_intersection.empty is True


def test_write_simulation_results_raise_os_error():
    unsupported_file_format = ".txt"
    with pytest.raises(
        OSError, match="Unsupported" and "format" and f"{unsupported_file_format}"
    ):
        write_simulation_results(MagicMock(), MagicMock(), unsupported_file_format)


@pytest.mark.parametrize("file_format", ["csv", "parquet"], ids=["csv", "parquet"])
def test_write_simulation_results(tmp_path: Path, file_format: str):
    results = {"sim1": pandas.DataFrame(), "sim2": pandas.DataFrame()}
    write_simulation_results(tmp_path, results, file_format)
    for data_id in results:
        result_path = tmp_path / f"{data_id}.{file_format}"
        assert result_path.exists() is True
        assert result_path.is_file() is True
