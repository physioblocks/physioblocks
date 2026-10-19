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
"""Define configurable discrepancy operators."""

from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from physioblocks.registers.type_register import register_type


@dataclass(frozen=True)
class AbstractDiscrepancy(ABC):
    """Base class for methods computing the discrepancy operators.

    The discrepancy generalizes the innovation :math:`Z - H(X)` of the Kalman filter.
    """

    @abstractmethod
    def eval(
        self, measurement: NDArray[np.float64], observations: NDArray[np.float64]
    ) -> NDArray[np.float64]:
        """Get the discrepancy between the measurement and each of the observations.

        Observations are in a matrix of shape (N, m) with :
            * N the number of sigma points
            * m the observations size

        Parameters
        ----------
        measurement : NDArray
            the current measurement of shape (m,)
        observations : NDArray
            the observations of shape (N, m)

        Returns
        -------
        NDArray
            the discrepancies of shape (N, m)

        """


DIFFERENCE_METHOD_ID = "difference"


@register_type(DIFFERENCE_METHOD_ID)
class Difference(AbstractDiscrepancy):
    """Compute the difference between the measurement and the observations.

    This is the innovation :math:`Z - H(X)` of the classical Kalman filter.

    Configuration
    -------------

    .. code-block:: json

        {
            "type": "difference"
        }

    """

    def eval(
        self, measurement: NDArray[np.float64], observations: NDArray[np.float64]
    ) -> NDArray[np.float64]:
        """Get the difference between the measurement and observations.

        Parameters
        ----------
        measurement : NDArray
            the current measurement of shape (m,)
        observations : NDArray
            the observations of shape (N, m)

        Returns
        -------
        NDArray
            the discrepancies of shape (N, m)

        """
        return measurement - observations
