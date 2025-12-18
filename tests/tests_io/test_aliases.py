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
from unittest.mock import Mock, patch

import pytest

from physioblocks.io.aliases import load_aliases


@patch("physioblocks.io.aliases.add_alias")
@patch("physioblocks.io.aliases.read_json")
@patch("pathlib.Path.iterdir")
@patch("pathlib.Path.exists")
@patch("pathlib.Path.is_dir")
def test_load_aliases(
    mock_path_is_dir: Mock,
    mock_path_exists: Mock,
    mock_iter_dir: Mock,
    mock_read_json: Mock,
    mock_add_alias: Mock,
):
    mock_path_is_dir.side_effect = [True, True, True, False]
    mock_path_exists.return_value = True
    mock_iter_dir.side_effect = [[Path(), Path("alias.json")], []]
    mock_read_json.return_value = True

    load_aliases("")
    mock_add_alias.assert_called_once_with("alias", True)


@patch("pathlib.Path.exists")
@patch("pathlib.Path.is_dir")
def test_load_aliases_exceptions(mock_path_is_dir: Mock, mock_path_exists: Mock):
    # path does not described a directory
    mock_path_is_dir.return_value = False
    err_msg = "Provided alias directory is not a folder: "
    with pytest.raises(OSError, match=err_msg):
        load_aliases("")

    # path does not exists
    mock_path_is_dir.return_value = True
    mock_path_exists.return_value = False
    err_msg = "Provided alias directory do not exist: "
    with pytest.raises(OSError, match=err_msg):
        load_aliases("")
