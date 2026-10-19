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
"""Declare first order functions."""

from __future__ import annotations

from typing import Any

import numpy as np
from numpy.typing import NDArray

from physioblocks.registers.type_register import register_type
from physioblocks.simulation import AbstractFunction

# First order function id
FIRST_ORDER_NAME = "first_order"


@register_type(FIRST_ORDER_NAME)
class FirstOrder(AbstractFunction):
    """Evaluate the sum of first order functions with Heaviside steps.

    ``times_start``, ``amplitudes`` and ``time_constants`` must have the same length.

    Attributes
    ----------
    times_start : NDArray[np.float64]
        Start times of first order components
    amplitudes : NDArray[np.float64]
        Amplitudes of first order components
    time_constants : NDArray[np.float64]
        Time constants of first order components
    baseline_value : np.float64
        Baseline value of the function

    Configuration
    -------------

    .. code-block:: json

        {
            "type": "first_order",
            "times_start": ["<float>"],     // Start times of the components
            "amplitudes": ["<float>"],      // Amplitudes of the components
            "time_constants": ["<float>"],  // Time constants of the components
            "baseline_value": "<float>",    // Baseline value of the function
            "evaluation_quantities": {
                "time": "<str>"             // Global name of the time quantity
            }
        }

    """

    times_start: NDArray[np.float64]

    amplitudes: NDArray[np.float64]

    time_constants: NDArray[np.float64]

    baseline_value: np.float64

    def __init__(
        self,
        times_start: NDArray[np.float64],
        amplitudes: NDArray[np.float64],
        time_constants: NDArray[np.float64],
        baseline_value: np.float64,
    ):
        # test arguments size consistency
        if not (
            (len(times_start) == len(amplitudes))
            and (len(times_start) == len(time_constants))
        ):
            msg_error = (
                "arguments 'times_start', 'amplitudes' and 'time_constants' "
                "must have the same length. Got: "
                f"- times_start (len = {len(times_start)}): {times_start}; "
                f"- amplitudes (len = {len(amplitudes)}): {amplitudes}; "
                f"- time_constants (len = {len(time_constants)}): {time_constants}."
            )
            raise ValueError(msg_error)

        # reorder array arguments to have ascending times_start
        sorted_indices = np.argsort(times_start)
        amplitudes = amplitudes[sorted_indices]
        time_constants = time_constants[sorted_indices]

        # assign properties
        self.times_start = times_start
        self.amplitudes = amplitudes
        self.time_constants = time_constants
        self.baseline_value = baseline_value

    def eval(self, time: np.float64) -> Any:
        """Evaluate function value at the given time.

        Parameters
        ----------
        time : np.float64
            evaluation time

        Returns
        -------
        np.float64
            the function value

        """
        mask_activated = self.times_start <= time
        amplitudes_activ = self.amplitudes[mask_activated]
        time_cst_activ = self.time_constants[mask_activated]
        times_start_activ = self.times_start[mask_activated]

        output = self.baseline_value + np.sum(
            amplitudes_activ
            * (1 - np.exp(-(time - times_start_activ) / time_cst_activ))
        )

        return output
