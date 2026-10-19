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

import subprocess
import sys
from pathlib import Path

import pytest

from physioblocks.launcher.configuration import (
    check_launcher_directory,
    setup_launcher_directory,
)
from physioblocks.launcher.constants import (
    PHYSIOBLOCKS_REFERENCES_PATH,
)


@pytest.fixture
def launcher_path(tmp_path: Path):
    launcher_path = tmp_path / "test_launcher"
    setup_launcher_directory(launcher_path)
    return launcher_path


def test_configure(tmp_path: Path):
    launcher_path = tmp_path / "test_launcher"
    exit_status = subprocess.call(
        [
            sys.executable,
            "-m",
            "physioblocks.launcher.configure",
            "-d",
            f"{launcher_path}",
        ]
    )

    assert exit_status == 0
    assert launcher_path.exists() is True
    assert check_launcher_directory(launcher_path) is True


def test_configure_fails(launcher_path):
    exit_status = subprocess.call(
        [
            sys.executable,
            "-m",
            "physioblocks.launcher.configure",
            "-d",
            f"{launcher_path}",
        ]
    )

    assert exit_status != 0
    assert launcher_path.exists() is True
    assert check_launcher_directory(launcher_path) is True


def test_launch(launcher_path: Path):
    config_path = (
        Path(PHYSIOBLOCKS_REFERENCES_PATH) / "circulation_alone_forward_sim.jsonc"
    )
    series = "CirculationAlone"
    message = "Test launcher with a circulation simulation"
    exit_status = subprocess.call(
        [
            sys.executable,
            "-m",
            "physioblocks.launcher",
            f"{config_path}",
            "-d",
            f"{launcher_path}",
            "-s",
            series,
            "-m",
            message,
        ]
    )
    assert exit_status == 0


def test_launch_no_launcher_directory(tmp_path: Path):
    config_path = (
        Path(PHYSIOBLOCKS_REFERENCES_PATH) / "circulation_alone_forward_sim.jsonc"
    )
    series = "CirculationAlone"
    message = "Test launcher with a circulation simulation"
    exit_status = subprocess.call(
        [
            sys.executable,
            "-m",
            "physioblocks.launcher",
            f"{config_path}",
            "-d",
            f"{tmp_path}",
            "-s",
            series,
            "-m",
            message,
        ]
    )
    assert exit_status != 0
