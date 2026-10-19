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
"""Implement an Unscented Kalman Filter (UKF)."""

import logging
from typing import Any

import numpy as np
from numpy.typing import NDArray

from physioblocks.library.filters.discrepancies import AbstractDiscrepancy
from physioblocks.library.filters.sigmas import AbstractSigmaPoints
from physioblocks.registers.type_register import get_registered_type, register_type
from physioblocks.simulation.estimation import AbstractFilter

_logger = logging.getLogger(__name__)

UNSCENTED_KALMAN_FILTER = "unscented_kalman_filter"


@register_type(UNSCENTED_KALMAN_FILTER)
class UnscentedKalmanFilter(AbstractFilter):
    """Unscented Kalman Filter (UKF) implementation.

    The innovation :math:`Z - H(X)` of the classical UKF is generalized with a
    discrepancy operator.
    Default operator is the difference, others can be implemented.

    Attributes
    ----------
    sigma_points : AbstractSigmaPoints
        Method to get the sigma points from a vector and covariance
    discrepancy : AbstractDiscrepancy
        Method to compute the discrepancy. Default is a simple difference.

    Parameters
    ----------
    sigma_points_type : str
        The type of method to use to generate sigma points. Default is "star".
    sigma_points_options : dict[str, Any] | None
        The options for the sigma points generation. Default is None.
    discrepancy_type : str
        The discrepancy method that computes the measurement and observations
        discrepancy.
        Default is "difference".
    discrepancy_options : dict[str, Any] | None
        The options for the discrepancy method.
        Default is None

    See Also
    --------
    ~.StarSigmaPoints
        Default sigma point generation method.
    ~.Difference
        Default discrepancy method

    Configuration
    -------------

    .. code-block:: json

        {
            "type": "unscented_kalman_filter",
            "sigma_points_type": "<str>",      // Sigma points type id
                                               // (optional, default: "star")
            "sigma_points_options": {},        // Sigma points options (optional)
            "discrepancy_type": "<str>",       // Discrepancy type id
                                               // (optional, default: "difference")
            "discrepancy_options": {}          // Discrepancy options (optional)
        }

    """

    sigma_points: AbstractSigmaPoints

    discrepancy: AbstractDiscrepancy

    def __init__(
        self,
        *args: Any,
        sigma_points_type: str = "star",
        sigma_points_options: dict[str, Any] | None = None,
        discrepancy_type: str = "difference",
        discrepancy_options: dict[str, Any] | None = None,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        # Create sigma point generator
        sigma_point_factory = get_registered_type(sigma_points_type)
        sigma_points_options = (
            {} if sigma_points_options is None else sigma_points_options
        )
        self.sigma_points = sigma_point_factory(self.state_size, **sigma_points_options)

        # Create discrepancy method
        discrepancy_factory = get_registered_type(discrepancy_type)
        discrepancy_options = {} if discrepancy_options is None else discrepancy_options
        self.discrepancy = discrepancy_factory(**discrepancy_options)

    def prediction(
        self,
        current_time: float,
        new_time: float,
        state_mean: NDArray[np.float64],
        state_covariance: NDArray[np.float64],
    ) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
        """
        Predict the state based on the model.

        Parameters
        ----------
        current_time : float
            the current state time
        new_time : float
            the next state time
        state_mean : NDArray[np.float64]
            the current state
        state_covariance : NDArray[np.float64]
            the current state covariance

        Returns
        -------
        NDArray[np.float64]
            The predicted state
        NDArray[np.float64]
            The predicted covariance
        """
        particles = self.sigma_points.get_sigma_points(state_mean, state_covariance)

        new_particles_states = self.model_function(particles, current_time, new_time)

        prediction_mean = alpha_mean(
            new_particles_states, self.sigma_points.mean_weights
        )
        prediction_covariance = alpha_covariance(
            new_particles_states, prediction_mean, self.sigma_points.covariance_weights
        )
        prediction_covariance += self.model_noise_covariance

        return prediction_mean, prediction_covariance

    def update(
        self,
        time: float,
        predicted_state_mean: NDArray[np.float64],
        predicted_state_covariance: NDArray[np.float64],
        measurement: NDArray[np.float64],
    ) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
        """
        Update the predicted state with measurements.

        Parameters
        ----------
        time : float
            the current state time
        predicted_state_mean : NDArray[np.float64]
            the predicted state
        predicted_state_covariance : NDArray[np.float64]
            the predicted state covariance.
        measurement : NDArray[np.float64]
            the measurement.

        Returns
        -------
        NDArray[np.float64]
            the updated state
        NDArray[np.float64]
            the updated state covariance
        """
        particles_states = self.sigma_points.get_sigma_points(
            predicted_state_mean, predicted_state_covariance
        )

        # The commented implementation below is the classical UKF that doesn't
        # generalize the discrepancy operator and use the difference.
        particle_observations = self.observation_function(particles_states, time)
        innovation = self.discrepancy.eval(measurement, particle_observations)
        innovation_mean = alpha_mean(innovation, self.sigma_points.mean_weights)
        # observations_mean = alpha_mean(
        #     particle_observations, self.sigma_points.mean_weights
        # )
        observations_covariance = alpha_covariance(
            innovation,  # particle_observations,
            innovation_mean,  # observations_mean,
            self.sigma_points.covariance_weights,
        )
        observations_covariance += self.measurements_noise_covariance

        cross_cov_state_observations = alpha_cross_covariance(
            particles_states,
            predicted_state_mean,
            innovation,  # particle_observations,
            innovation_mean,  # observations_mean,
            self.sigma_points.covariance_weights,
        )

        inv_observation_covariance = np.linalg.inv(observations_covariance)
        kalman_gain = cross_cov_state_observations @ inv_observation_covariance

        updated_state = (
            predicted_state_mean.reshape(-1, 1)
            - kalman_gain @ innovation_mean.reshape(-1, 1)
            # + kalman_gain @ (measurement - observations_mean).reshape(-1, 1)
        ).flatten()

        updated_covariance = (
            predicted_state_covariance
            - cross_cov_state_observations
            @ inv_observation_covariance
            @ cross_cov_state_observations.T
        )

        return updated_state, updated_covariance


def alpha_mean(x: NDArray[np.float64], w: NDArray[np.float64]) -> NDArray[np.float64]:
    r"""Compute weighted mean of an array of vectors.

    .. math::

            \mathbb{E}_{\alpha}(X^*) = \sum_{i = 1}^{r}{\alpha_i X^{(i)}}


    Parameters
    ----------
    x : NDArray
        :math:`X^*` the array of vectors
    w : NDArray
        :math:`\alpha` the weights

    Returns
    -------
    NDArray[np.float64]
        :math:`\mathbb{E}_{\alpha}(X^*)` the weighted mean

    """
    return np.asarray(np.sum(w * x.T, axis=1), dtype=np.float64)


def alpha_covariance(
    x: NDArray[np.float64], x_mean: NDArray[np.float64], w: NDArray[np.float64]
) -> NDArray[np.float64]:
    r"""Compute weighted covariance of an array of vectors.

    .. math::

        \text{Cov}_{\alpha}(X^*) = \sum_{i = 1}^{r}{\alpha_i (X^{(i)} - \mathbb{E}(X))
        .(X^{(i)} - \mathbb{E}(X))^T }

    Parameters
    ----------
    x : NDArray
        :math:`X^*` the array of vectors
    x_mean : NDArray
        :math:`\mathbb{E}(X)` the expectation of :math:`X`
    w : NDArray
        :math:`\alpha` the weights

    Returns
    -------
    NDArray[np.float64]
        :math:`\text{Cov}_{\alpha}(X^*)` the weighted covariance

    """
    delta = x - x_mean
    weighted_delta = w * delta.T
    return weighted_delta @ delta


def alpha_cross_covariance(
    x: NDArray[np.float64],
    x_mean: NDArray[np.float64],
    y: NDArray[np.float64],
    y_mean: NDArray[np.float64],
    w: NDArray[np.float64],
) -> NDArray[np.float64]:
    r"""Compute weighted cross-covariance of two arrays of vectors.

    .. math::

        \text{Cov}_{\alpha}(X^*, Y^*)
        = \sum_{i = 1}^{r}{\alpha_i (X^{(i)} - \mathbb{E}(X))
        .(Y^{(i)} - \mathbb{E}(Y))^T }

    Parameters
    ----------
    x : NDArray
        :math:`X^*` an array of vectors
    x_mean : NDArray
        :math:`\mathbb{E}(X)` the expectation of :math:`X`
    y : NDArray
        :math:`Y^*` an array of vectors
    y_mean : NDArray
        :math:`\mathbb{E}(Y)` the expectation of :math:`Y`
    w : NDArray
        :math:`\alpha` the weights

    Returns
    -------
    NDArray[np.float64]
        :math:`\text{Cov}_{\alpha}(X^*, Y^*)` the weighted cross-covariance

    """
    delta_a = x - x_mean
    delta_b = y - y_mean
    weighted_delta = w * delta_a.T
    return weighted_delta @ delta_b
