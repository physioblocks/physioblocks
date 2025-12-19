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
from pathlib import Path

import physioblocks.library
from physioblocks.io.aliases import load_aliases
from physioblocks.utils.dynamic_import_utils import import_libraries
from physioblocks.utils.exceptions_utils import log_exception

_logger = logging.getLogger()

# Dynamically import the base library content.
base_lib_path = Path(physioblocks.library.__file__).parent
try:
    import_libraries([base_lib_path])
    load_aliases(str(base_lib_path / "aliases"))
except ImportError as error:
    log_exception(_logger, type(error), error, error.__traceback__)
