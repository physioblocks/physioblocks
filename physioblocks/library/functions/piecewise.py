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

"""Declare functions to define piecewise functions in the configuration"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from numpy.typing import NDArray

from physioblocks.registers.type_register import register_type
from physioblocks.simulation import AbstractFunction

# Piecewise linear function type name
PIECEWISE_LINEAR_NAME = "piecewise_linear"


@register_type(PIECEWISE_LINEAR_NAME)
@dataclass
class PiecewiseLinear(AbstractFunction):
    """
    Defines an evaluation method to get the value of a piecewise function
    for the given time.
    """

    points_abscissas: NDArray[np.float64]
    """The function abscissas"""

    points_ordinates: NDArray[np.float64]
    """The function ordinates"""

    left_value: np.float64 | None = None
    """Function value when the evaluation point is before the provided abscissas.
    If it is not provided, it is the first ordinate value."""

    right_value: np.float64 | None = None
    """Function value when the evaluation point is after the provided abscissas.
    If it is not provided, it is the last ordinate value."""

    def eval(self, time: np.float64) -> Any:
        """
        Evaluate piecewise function for the given time.

        :param time: the evaluated time
        :type time: np.float64

        :return: the activation point_value
        :rtype: np.float64
        """
        return np.interp(
            time,
            self.points_abscissas,
            self.points_ordinates,
            self.left_value,
            self.right_value,
        )


# Piecewise linear periodic function id
PIECEWISE_LINEAR_PERIODIC_NAME = "piecewise_linear_periodic"


@register_type(PIECEWISE_LINEAR_PERIODIC_NAME)
@dataclass
class PiecewiseLinearPeriodic(AbstractFunction):
    """
    Defines an evaluation method to get the value of a piecewise periodic function
    for the given time.
    """

    period: np.float64
    """The function period"""

    points_abscissas: NDArray[np.float64]
    """The function abscissas"""

    points_ordinates: NDArray[np.float64]
    """The function ordinates"""

    def eval(self, time: np.float64) -> Any:
        """
        Evaluate piecewise periodic function for the given time.

        :param time: the evaluated time
        :type time: np.float64

        :return: the activation point_value
        :rtype: np.float64
        """
        return np.interp(
            time, self.points_abscissas, self.points_ordinates, period=self.period
        )


# Rescale Two Phases function id
RESCALE_TWO_PHASES_FUNCTION_NAME = "rescale_two_phases_function"


@register_type(RESCALE_TWO_PHASES_FUNCTION_NAME)
class RescaleTwoPhasesFunction(AbstractFunction):
    """
    Rescale each part of the input function (a linear interpollation) depending on
    the proportion of variation of phase 0 when the period differs from the
    reference function.
    """

    rescaled_period: float
    """The actual function period"""

    reference_function: list[tuple[float, float]]
    """The reference function. Coordinates format is ``(abscissa, ordinate)``"""

    alpha: float
    """Proportion of the variation of phase 0"""

    phases: list[int]
    """For each intervals point of the reference, determine if it belong to
    phase 0 or 1."""

    def __init__(
        self,
        rescaled_period: float,
        reference_function: list[tuple[float, float]],
        alpha: float,
        phases: list[int],
    ):
        if len(phases) != len(reference_function) - 1:
            raise ValueError(
                "A phase should be defined for each interval defined in the "
                "reference function."
            )

        if any([elem not in [0, 1] for elem in phases]):
            raise ValueError(
                str.format(
                    "There are only two phases allowed: 0 or 1, got {0}.", phases
                )
            )

        if alpha >= 1.0 or alpha <= 0.0:
            raise ValueError(
                str.format(
                    "The proportion of the variation of phase 0 should be in ]0, 1[, "
                    "got {0}",
                    alpha,
                )
            )

        # check if the reference function is sorted
        if (
            all(
                [
                    reference_function[k][0] > reference_function[k - 1][0]
                    for k in range(1, len(reference_function))
                ]
            )
            is False
        ):
            raise ValueError(
                str.format(
                    "Reference function abscissas should be sorted, got {0}",
                    [coord[0] for coord in reference_function],
                )
            )

        self.reference_function = reference_function
        reference_period = (
            self.reference_function[-1][0] - self.reference_function[0][0]
        )
        self.phases = phases
        self.alpha = alpha

        self.beta = rescaled_period / reference_period
        duration_phase_0_ref = sum(
            [
                self.reference_function[index][0]
                - self.reference_function[index - 1][0]
                for index in range(1, len(self.reference_function))
                if phases[index - 1] == 0
            ]
        )
        duration_phase_1_ref = reference_period - duration_phase_0_ref

        scale_factor_phase_0 = (
            1.0
            + self.alpha * (self.beta - 1.0) * reference_period / duration_phase_0_ref
        )
        scale_factor_phase_1 = (
            1.0
            + (1.0 - self.alpha)
            * (self.beta - 1.0)
            * reference_period
            / duration_phase_1_ref
        )

        if scale_factor_phase_0 <= 0 or scale_factor_phase_1 <= 0:
            raise ValueError(
                str.format(
                    "Scale factors should not be negatives. Got ({0}, {1}) for "
                    "phase 0 and 1 respectivly. You can try changing alpha.",
                    scale_factor_phase_0,
                    scale_factor_phase_1,
                )
            )
        abscissas = [self.reference_function[0][0]]
        for index in range(1, len(self.reference_function)):
            rescaled_abs = (
                abscissas[index - 1]
                + (
                    self.reference_function[index][0]
                    - self.reference_function[index - 1][0]
                )
                * scale_factor_phase_0
                if phases[index - 1] == 0
                else abscissas[index - 1]
                + (
                    self.reference_function[index][0]
                    - self.reference_function[index - 1][0]
                )
                * scale_factor_phase_1
            )
            abscissas.append(rescaled_abs)

        ordinates = [value[1] for value in self.reference_function]

        self.rescaled_period = abscissas[-1]
        self.function_abcissas = np.array(abscissas)
        self.function_ordinates = np.array(ordinates)

    def eval(self, time: float) -> Any:
        """
        Evaluate the function.

        :param time: the evaluated time
        :type time: float

        :return: the function value
        :rtype: np.float64
        """
        return np.interp(
            time,
            self.function_abcissas,
            self.function_ordinates,
            period=self.rescaled_period,
        )
