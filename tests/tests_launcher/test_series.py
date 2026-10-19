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

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from physioblocks.launcher.constants import (
    LAUNCHER_DATE_COLUMN,
    LAUNCHER_DATE_TIME_FORMAT,
    LAUNCHER_MACHINE_COLUMN,
    LAUNCHER_NOTES_COLUMN,
    LAUNCHER_REFERENCE_COLUMN,
    LAUNCHER_VERSION_COLUMN,
)
from physioblocks.launcher.series import (
    SimulationInfo,
    get_reference_number,
    get_simulation_info,
    is_valid_reference_dir_name,
    is_valid_reference_name,
)


@pytest.fixture
def infos():
    return SimulationInfo("machine", "datetime", "series_name", "7", "0.0.1", "message")


class TestSimulationInfo:
    def test_reference(self, infos: SimulationInfo):
        assert infos.reference == "machine_series_name_7"

    def test_dataframe(self, infos: SimulationInfo):
        assert infos.data_frame[LAUNCHER_DATE_COLUMN][0] == infos.date_time
        assert infos.data_frame[LAUNCHER_MACHINE_COLUMN][0] == infos.machine_name
        assert infos.data_frame[LAUNCHER_REFERENCE_COLUMN][0] == infos.reference
        assert infos.data_frame[LAUNCHER_VERSION_COLUMN][0] == infos.version
        assert infos.data_frame[LAUNCHER_NOTES_COLUMN][0] == infos.message

    def test_str(self, infos: SimulationInfo):
        assert infos.date_time in str(infos)
        assert infos.machine_name in str(infos)
        assert infos.reference in str(infos)
        assert infos.version in str(infos)
        assert infos.message in str(infos)


@pytest.mark.parametrize(
    "reference_name, is_valid",
    [
        pytest.param("", False, id="empty"),
        pytest.param("short_7", False, id="short_with_digit"),
        pytest.param("long_enough_reference_name", False, id="long_no_digit"),
        pytest.param(
            "incorrect-separator-reference-12", False, id="incorrect_separator"
        ),
        pytest.param("short_name_1", True, id="short_reference_name"),
        pytest.param("long_reference_name_1145", True, id="long_reference_name"),
    ],
)
def test_is_valid_reference_name(reference_name: str, is_valid: bool):
    assert is_valid_reference_name(reference_name) is is_valid


@pytest.mark.parametrize(
    "dir_name, series_name, is_valid",
    [
        pytest.param("", "series_name", False, id="empty"),
        pytest.param(
            "dir_name_mismatch_series_15",
            "series_name",
            False,
            id="series_names_dont_match",
        ),
        pytest.param(
            "dir_name_series_name_14", "series_name", True, id="series_names_match"
        ),
    ],
)
def test_is_valid_reference_dir_name(dir_name: str, series_name: str, is_valid: bool):
    assert is_valid_reference_dir_name(dir_name, series_name) is is_valid


@pytest.fixture
def dont_exist_series_path(tmp_path: Path):
    return tmp_path / "series_path"


@pytest.fixture
def file_series_path(tmp_path: Path):
    file_path = tmp_path / "file_series_path"
    file_path.touch()
    return file_path


@pytest.mark.parametrize(
    "series_path",
    [
        pytest.param("dont_exist_series_path", id="series_folder_dont_exist"),
        pytest.param("file_series_path", id="series_is_file"),
    ],
)
def test_get_reference_number_raise_value_error(
    series_path, request: pytest.FixtureRequest
):
    path: Path = request.getfixturevalue(series_path)
    with pytest.raises(ValueError, match=path.name):
        get_reference_number(request.getfixturevalue(series_path))


@pytest.fixture
def empty_series_path(tmp_path: Path):
    series_path = tmp_path / "series_path"
    series_path.mkdir()
    return series_path


@pytest.fixture
def populated_series_path(tmp_path: Path):
    series_path = tmp_path / "series_path"
    series_path.mkdir()
    for i in range(1, 4):
        folder_path = series_path / f"series_path_{i}"
        folder_path.mkdir()
    return series_path


@pytest.fixture
def populated_series_path_missing_numbers(tmp_path: Path):
    series_path = tmp_path / "series_path"
    series_path.mkdir()
    folder_path = series_path / "series_path_1"
    folder_path.mkdir()
    folder_path = series_path / "series_path_3"
    folder_path.mkdir()
    return series_path


@pytest.mark.parametrize(
    "series_path, ref_number",
    [
        pytest.param("empty_series_path", 1, id="empty_series_folder"),
        pytest.param("populated_series_path", 4, id="populated_series_folder"),
        pytest.param(
            "populated_series_path_missing_numbers",
            4,
            id="populated_series_folder_with_missing_numbers",
        ),
    ],
)
def test_get_reference_number(series_path, ref_number, request: pytest.FixtureRequest):
    assert get_reference_number(request.getfixturevalue(series_path)) == f"{ref_number}"


@patch("physioblocks.launcher.series.datetime")
@patch("socket.gethostname")
@patch("physioblocks.launcher.series.version")
def test_get_simulation_info(
    mock_version: MagicMock,
    mock_get_host_name: MagicMock,
    mock_datetime: MagicMock,
    empty_series_path: Path,
):
    mock_datetime.now.return_value = datetime(1, 1, 1)
    mock_get_host_name.return_value = "machine_name.something.else"
    mock_version.return_value = "0.0.1"
    infos = get_simulation_info(empty_series_path, "sim message")
    assert infos.machine_name == "machine_name"
    assert infos.version == "0.0.1"
    assert infos.number == "1"
    assert infos.series == "series_path"
    assert infos.date_time == datetime(1, 1, 1).strftime(LAUNCHER_DATE_TIME_FORMAT)
    assert infos.message == "sim message"
