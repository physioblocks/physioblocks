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
"""Declare algorithms for sigma points generation for the Unscented Kalman Filter.

The implemented algorithms are detailed in [1].

References
----------
[1] Philippe Moireau, Dominique Chapelle. Reduced-order Unscented Kalman Filtering
with application to parameter identification in large-dimensional systems.
ESAIM: Control, Optimisation and Calculus of Variations, 2011, 17 (2), pp.380-405.
⟨10.1051/cocv/2010006⟩. ⟨inria-00550104⟩
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from physioblocks.registers.type_register import register_type


@dataclass(frozen=True)
class AbstractSigmaPoints(ABC):
    """Base class for methods building sigma points for estimation methods.

    Attributes
    ----------
    state_size : int
        :math:`n` the size of the extended state (variable and estimated parameters).
    nb_points : int
        :math:`N` the number of points created with the method.
    mean_weights : NDArray[np.float64]
        :math:`w_m` the weights of each sigma point to compute the mean.
    covariance_weights : NDArray[np.float64]
        :math:`w_c` the weights of each sigma point to compute the covariance.

    """

    state_size: int

    nb_points: int

    mean_weights: NDArray[np.float64]

    covariance_weights: NDArray[np.float64]

    @abstractmethod
    def get_sigma_points(
        self, state: NDArray[np.float64], covariance: NDArray[np.float64]
    ) -> NDArray[np.float64]:
        """Get the sigma points according to the implemented method.

        Sigma points are presented in a matrix of shape (N, n) with:

        * N the number of sigma points
        * n the state size

        Parameters
        ----------
        state : NDArray
            the current state
        covariance : NDArray
            the state covariance

        Returns
        -------
        NDArray
            the sigma points

        """


CANONICAL_SIGMA_POINTS_METHOD_ID = "canonical"


@register_type(CANONICAL_SIGMA_POINTS_METHOD_ID)
class CanonicalSigmaPoints(AbstractSigmaPoints):
    """Build sigma points with the canonical method.

    Parameters
    ----------
    state_size : int
        the state size.

    Configuration
    -------------

    .. code-block:: json

        {
            "type": "canonical"
        }

    """

    def __init__(self, state_size: int):
        nb_points = 2 * state_size
        weight = 1.0 / nb_points
        mean_weights = np.array(nb_points * [weight])
        mean_covar = np.array(nb_points * [weight])
        super().__init__(state_size, nb_points, mean_weights, mean_covar)

        deviation = np.zeros((self.state_size, self.nb_points))

        for i in range(0, self.state_size):
            deviation[i, i] = np.sqrt(self.state_size)
            deviation[i, self.state_size + i] = -np.sqrt(self.state_size)

        deviation_covar = deviation @ np.diag(self.mean_weights) @ deviation.T
        sqrt_dev_covar = np.linalg.cholesky(deviation_covar)
        inv_sqrt_dev_covar = np.linalg.inv(sqrt_dev_covar)

        self._base_deviation = inv_sqrt_dev_covar @ deviation

    def get_sigma_points(
        self, state: NDArray[np.float64], covariance: NDArray[np.float64]
    ) -> NDArray[np.float64]:
        """Get the sigma points aligned with the canonical base.

        Sigma points are returned in a matrix of size ``(N, n)`` where the sigma
        points are presented as rows.

        Parameters
        ----------
        state : NDArray
            the current state
        covariance : NDArray
            the state covariance

        Returns
        -------
        NDArray
            the sigma points

        """
        covariance_sqrt = np.linalg.cholesky(covariance)
        deviation = covariance_sqrt @ self._base_deviation

        return state + deviation.T


STAR_SIGMA_POINTS_METHOD_ID = "star"
"""Type id for the star generation method for sigma points"""


@register_type(STAR_SIGMA_POINTS_METHOD_ID)
class StarSigmaPoints(AbstractSigmaPoints):
    """Build sigma points with the star method.

    Parameters
    ----------
    state_size : int
        the state size.

    Configuration
    -------------

    .. code-block:: json

        {
            "type": "star"
        }

    """

    def __init__(self, state_size: int):
        state_size = state_size
        nb_points = 2 * state_size + 1
        weight = 1.0 / nb_points
        mean_weights = np.array(nb_points * [weight])
        mean_covar = np.array(nb_points * [weight])
        super().__init__(state_size, nb_points, mean_weights, mean_covar)

        deviation = np.zeros((self.state_size, self.nb_points))

        for i in range(0, self.state_size):
            deviation[i, i] = np.sqrt(self.state_size)
            deviation[i, self.state_size + i] = -np.sqrt(self.state_size)

        deviation_covar = deviation @ np.diag(self.mean_weights) @ deviation.T
        sqrt_dev_covar = np.linalg.cholesky(deviation_covar)
        inv_sqrt_dev_covar = np.linalg.inv(sqrt_dev_covar)

        self._base_deviation = inv_sqrt_dev_covar @ deviation

    def get_sigma_points(
        self, state: NDArray[np.float64], covariance: NDArray[np.float64]
    ) -> NDArray[np.float64]:
        """Get the sigma points aligned with the canonical base and the state itself.

        Sigma points are returned in a matrix of size :math:`(N, n)` where the sigma
        points are presented as rows

        Parameters
        ----------
        state : NDArray
            the current state
        covariance : NDArray
            the state covariance

        Returns
        -------
        NDArray
            the sigma points

        """
        covariance_sqrt = np.linalg.cholesky(covariance)
        deviation = covariance_sqrt @ self._base_deviation

        return state + deviation.T


SIMPLEX_SIGMA_POINTS_METHOD_ID = "simplex"
"""Type id for the simplex generation method for sigma points"""


@register_type(SIMPLEX_SIGMA_POINTS_METHOD_ID)
class SimplexSigmaPoints(AbstractSigmaPoints):
    """Build sigma points with the simplex method.

    Parameters
    ----------
    state_size : int
        the state size.

    Configuration
    -------------

    .. code-block:: json

        {
            "type": "simplex"
        }

    """

    def __init__(self, state_size: int):
        state_size = state_size
        nb_points = state_size + 1
        weight = 1.0 / nb_points
        mean_weights = np.array(nb_points * [weight])
        mean_covar = mean_weights
        super().__init__(state_size, nb_points, mean_weights, mean_covar)

        alpha = self.state_size / (self.state_size + 1)
        self._base_deviation = np.array(
            [[-1 / np.sqrt(2 * alpha), 1 / np.sqrt(2 * alpha)]], dtype=np.float64
        )
        for d in range(2, self.state_size + 1):
            temp_base_deviation = np.zeros((d, d + 1))
            temp_base_deviation[0:-1, 0:-1] = self._base_deviation
            temp_base_deviation[-1:, :-1] = 1 / np.sqrt(alpha * d * (d + 1))
            temp_base_deviation[-1, -1] = -d / np.sqrt(alpha * d * (d + 1))
            self._base_deviation = temp_base_deviation

        self._base_deviation = np.sqrt(self.state_size) * self._base_deviation

    def get_sigma_points(
        self,
        state: NDArray[np.float64],
        covariance: NDArray[np.float64],
    ) -> NDArray[np.float64]:
        r"""Get the sigma points on a regular polyhedron of radius :math:`\sqrt{n}`.

        Sigma points are returned in a matrix of size :math:`(N, n)` where the sigma
        points are presented as rows

        Parameters
        ----------
        state : NDArray
            the current state
        covariance : NDArray
            the state covariance

        Returns
        -------
        NDArray
            the sigma points

        """
        covariance_sqrt = np.linalg.cholesky(covariance)
        deviation = covariance_sqrt @ self._base_deviation

        return state + deviation.T
