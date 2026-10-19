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

"""Defines needed migrations to transform processes configuration to 2.0.0."""

import warnings

from physioblocks.configuration.base import Configuration
from physioblocks.configuration.migrations import migrates
from physioblocks.simulation.base import RANGE_ID

_LEGACY_DISPLACEMENT_MIN_ID = "displacement_min"
_LEGACY_DISPLACEMENT_MAX_ID = "displacement_max"
_LEGACY_DISPLACEMENT_STEP_ID = "displacement_step"
_DISPLACEMENT_RANGE_ID = "displacement_range"


@migrates("compute_espvr_edpvr", version="2.0.0")
def _migrate_displacement_range(configuration: Configuration) -> Configuration:
    if _LEGACY_DISPLACEMENT_MIN_ID not in configuration:
        return configuration

    warnings.warn(
        str.format(
            "The '{0}', '{1}' and'{2}' keys of a '{3}' process configuration are "
            "deprecated. Use a '{4}' configuration of type '{5}' instead.",
            _LEGACY_DISPLACEMENT_MIN_ID,
            _LEGACY_DISPLACEMENT_MAX_ID,
            _LEGACY_DISPLACEMENT_STEP_ID,
            configuration.label,
            _DISPLACEMENT_RANGE_ID,
            RANGE_ID,
        ),
        category=DeprecationWarning,
        stacklevel=2,
    )
    items = configuration.configuration_items.copy()
    displacement_min = items.pop(_LEGACY_DISPLACEMENT_MIN_ID)
    displacement_max = items.pop(_LEGACY_DISPLACEMENT_MAX_ID)
    items[_DISPLACEMENT_RANGE_ID] = Configuration(
        RANGE_ID,
        {
            "start": displacement_min,
            "length": displacement_max - displacement_min,
            "step_size": items.pop(_LEGACY_DISPLACEMENT_STEP_ID),
        },
    )
    return Configuration(configuration.label, items)
