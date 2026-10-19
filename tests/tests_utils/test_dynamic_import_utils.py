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

import logging
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import physioblocks.utils.dynamic_import_utils as dynamic_import_utils


def _make_package(root: Path, name: str, submodules: list[str]) -> Path:
    pkg_dir = root / name
    pkg_dir.mkdir()
    pkg_init_path = pkg_dir / "__init__.py"
    pkg_init_path.touch()
    for submodule_name in submodules:
        submodule_path = pkg_dir / f"{submodule_name}.py"
        submodule_path.touch()
    return pkg_dir


@pytest.fixture
def loaded_modules():
    created: list[str] = []
    yield created
    for module_name in created:
        sys.modules.pop(module_name, None)


def test_imports_modules_flat(tmp_path):
    pkg_dir = _make_package(
        tmp_path,
        "test_lib",
        ["module_a", "module_b"],
    )
    with patch("importlib.import_module") as import_module_mock:
        dynamic_import_utils.import_libraries([pkg_dir])
        import_module_mock.assert_called()
        assert len(import_module_mock.call_args_list) == 2
        assert "test_lib.module_a" in import_module_mock.call_args_list[0].args
        assert "test_lib.module_b" in import_module_mock.call_args_list[1].args


def test_imports_nested_module(tmp_path):
    package_a_path = _make_package(tmp_path, "package_a", [])
    module_a_path = _make_package(package_a_path, "module_a", ["sub_module_a"])

    with patch("importlib.import_module") as import_module_mock:
        dynamic_import_utils.import_libraries([module_a_path])

        import_module_mock.assert_called()
        assert len(import_module_mock.call_args_list) == 1
        assert (
            "package_a.module_a.sub_module_a"
            in import_module_mock.call_args_list[0].args
        )


def test_imports_sub_package(tmp_path):
    package_a_path = _make_package(tmp_path, "package_a", [])
    _make_package(package_a_path, "module_a", ["sub_module_a"])

    with patch("importlib.import_module") as import_module_mock:
        dynamic_import_utils.import_libraries([package_a_path])

        import_module_mock.assert_called()
        assert len(import_module_mock.call_args_list) == 2
        assert "package_a.module_a" in import_module_mock.call_args_list[0].args
        assert (
            "package_a.module_a.sub_module_a"
            in import_module_mock.call_args_list[1].args
        )


def test_imports_modules_log_no_library(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
):
    no_folder_at_path = tmp_path / "folder"

    with caplog.at_level(logging.ERROR):
        dynamic_import_utils.import_libraries([no_folder_at_path])
    assert any(
        [
            "no library" in record.message and str(no_folder_at_path) in record.message
            for record in caplog.records
        ]
    )


def test_imports_modules_error_not_a_package(tmp_path: Path):
    not_a_package_path = tmp_path / "folder"
    not_a_package_path.mkdir()

    with pytest.raises(ImportError, match="folder is not a package"):
        dynamic_import_utils.import_libraries([not_a_package_path])


def test_warns_and_already_loaded(tmp_path: Path, caplog: pytest.LogCaptureFixture):
    pkg_dir = _make_package(
        tmp_path,
        "test_lib",
        ["module_a"],
    )
    with (
        patch("sys.modules", new={"test_lib.module_a": MagicMock()}),
        caplog.at_level(logging.WARNING),
    ):
        dynamic_import_utils.import_libraries([pkg_dir])

    assert any(
        [
            "already loaded" in record.message and "test_lib.module_a" in record.message
            for record in caplog.records
        ]
    )


def test_warns_import_error(tmp_path: Path, caplog: pytest.LogCaptureFixture):
    pkg_dir = _make_package(
        tmp_path,
        "test_lib",
        ["module_a"],
    )

    with (
        caplog.at_level(logging.WARNING),
        patch("importlib.import_module", side_effect=ImportError),
    ):
        dynamic_import_utils.import_libraries([pkg_dir])

    assert any(
        "Error" in record.message and "test_lib.module_a" in record.message
        for record in caplog.records
    )
