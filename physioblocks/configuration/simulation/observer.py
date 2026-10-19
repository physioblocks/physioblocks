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
"""Declare save and load functions for the observer module."""

from typing import Any

from physioblocks.configuration.base import Configuration
from physioblocks.configuration.constants import (
    QUANTITY_MAGNITUDE_ID,
    QUANTITY_STDEV_ID,
)
from physioblocks.configuration.functions import load
from physioblocks.registers.load_function_register import loads
from physioblocks.simulation.estimation import (
    MEASUREMENT_PARAMETER_ID,
    OPERATOR_PARAMETER_ID,
    Observation,
)
from physioblocks.simulation.functions import SimulationFunctionFactory


@loads(Observation)
def load_observation(
    configuration: Configuration,
    configuration_references: dict[str, Any],
    *args: Any,
    **kwargs: Any,
) -> Observation:
    """
    Load observation configuration.

    Parameters
    ----------
    configuration : Configuration
        the observation configuration.
    configuration_references : dict[str, Any]
        references to initialize parameters and variables of the observations operators.

    Returns
    -------
    Observation
        The configured Observation.
    """
    measurement = configuration[MEASUREMENT_PARAMETER_ID]

    operator_factory = load(
        configuration[OPERATOR_PARAMETER_ID],
        configuration_type=SimulationFunctionFactory,
        configuration_references=configuration_references,
    )
    magnitude = configuration.configuration_items.get(QUANTITY_MAGNITUDE_ID, 1.0)
    stdev = configuration.configuration_items.get(QUANTITY_STDEV_ID, 0.0)

    return Observation(measurement, operator_factory, magnitude, stdev)
