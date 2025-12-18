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
Defines classes and functions to turn objects into a generic configuration
that can easily be saved or loaded.
"""

__all__ = ["Configuration", "load", "save", "unwrap_aliases"]
import physioblocks.configuration.computing
import physioblocks.configuration.description
import physioblocks.configuration.simulation  # noqa: F401
from physioblocks.configuration.aliases import unwrap_aliases
from physioblocks.configuration.base import Configuration
from physioblocks.configuration.functions import load, save
