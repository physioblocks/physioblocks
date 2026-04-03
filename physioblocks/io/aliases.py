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

"""Defines methods to load aliases folders."""

import logging
from pathlib import Path

from physioblocks.configuration.aliases import add_alias
from physioblocks.io.configuration import read_json
from physioblocks.utils.exceptions_utils import log_exception

_logger = logging.getLogger(__name__)

_JSON_EXTENSIONS = [".json", ".jsonc"]


def load_aliases(path: str) -> None:
    """
    Load all aliases recursively in the directory into the **Alias Register**.

    .. warning::

        The given key for each alias is its file name without extensions.
        It has to be unique.

    :param path: the alias directory path to load.
    :type path: Path
    """
    directory_path = Path(path)

    if directory_path.is_dir() is False:
        raise OSError(
            str.format(
                "Provided alias directory is not a folder: {0}",
                directory_path,
            )
        )

    if directory_path.exists() is False:
        raise OSError(
            str.format(
                "Provided alias directory do not exist: {0}",
                directory_path,
            )
        )

    for child in directory_path.iterdir():
        if child.is_dir():
            # recursivly load child directories
            load_aliases(str(child))
        else:
            if child.suffix not in _JSON_EXTENSIONS:
                continue

            try:
                config_alias = read_json(str(child))

                # get file name without extension as alias id
                alias_id = child.name.removesuffix(child.suffix)
                add_alias(alias_id, config_alias)
            except Exception as error:
                _logger.warning(
                    str.format(
                        "Error while loading alias from: {0}. File skipped.",
                        str(child.absolute()),
                    )
                )
                log_exception(
                    _logger, type(error), error, error.__traceback__, logging.DEBUG
                )
