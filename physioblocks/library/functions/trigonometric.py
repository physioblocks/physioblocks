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

"""Declare configuration functions to set parameters with trigonometric functions."""

from dataclasses import dataclass
from typing import Any

import numpy as np

from physioblocks.registers.type_register import register_type
from physioblocks.simulation import AbstractFunction

# sinus with offset function id
SINUS_OFFSET_NAME = "sinus_offset"


@register_type(SINUS_OFFSET_NAME)
@dataclass
class SinusOffset(AbstractFunction):
    """Defines an evaluation method to get the value of an offset sine function.

    Attributes
    ----------
    offset_value : float
        Offset value of the function
    amplitude : float
        Peak amplitude of the function
    frequency : float
        Frequency of the function
    phase_shift : float
        Phase shift of the function

    Configuration
    -------------

    .. code-block:: json

        {
            "type": "sinus_offset",
            "offset_value": "<float>",        // Offset value of the sinus
            "amplitude": "<float>",           // Peak amplitude of the sinus
            "frequency": "<float>",           // Frequency of the sinus
            "phase_shift": "<float>",         // Phase shift of the sinus
            "evaluation_quantities": {
                "time": "<str>"               // Global name of the time quantity
            }
        }

    """

    offset_value: float

    amplitude: float

    frequency: float

    phase_shift: float

    def eval(self, time: float) -> Any:
        """Evaluate function value at the given time.

        Parameters
        ----------
        time : float
            evaluation time

        Returns
        -------
        np.float64
            the function value

        """
        output = self.offset_value + self.amplitude * np.sin(
            2 * np.pi * self.frequency * time + self.phase_shift
        )

        return output
