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

"""
Configure a directory to be used as a root directory for the PhysioBlocks launcher.
"""

import argparse
import logging
import sys
from pathlib import Path

from physioblocks.launcher.configuration import (
    check_target_launcher_directory,
    setup_launcher_directory,
)
from physioblocks.utils import exceptions_utils

_logger = logging.getLogger()
_logger.setLevel(logging.DEBUG)
sys.excepthook = exceptions_utils.create_uncaught_exception_logger_handler(_logger)


def main(target_dir: Path) -> int:
    if check_target_launcher_directory(target_dir) is False:
        raise OSError(
            str.format(
                "Launcher directory must either not exist already or be empty. "
                "Provided directory: {0}",
                str(target_dir.absolute()),
            )
        )

    setup_launcher_directory(target_dir)
    _logger.info(
        str.format("Launcher directory created at {0}.", str(target_dir.absolute()))
    )

    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.HelpFormatter
    )
    parser.add_argument(
        "-d",
        "--launcher_directory",
        dest="launcher_directory",
        default="./",
        required=False,
        help="The directory where to setup the launcher.",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        dest="verbose",
        action="store_true",
        default=False,
        required=False,
        help="Display logs in console",
    )

    args = parser.parse_args()

    # Direct the logs to stdout
    if args.verbose is True:
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setFormatter(logging.Formatter(logging.BASIC_FORMAT))
        stdout_handler.setLevel(logging.DEBUG)
        _logger.addHandler(stdout_handler)

    # Convert the str path to a Pathlib Path
    launcher_directory_path = Path(args.launcher_directory)
    sys.exit(main(launcher_directory_path))
