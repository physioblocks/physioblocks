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
"""Implement a linear Kalman filter for tests purposes."""

import logging
from collections.abc import Callable

import numpy as np
from numpy.typing import NDArray

from physioblocks.registers.type_register import register_type
from physioblocks.simulation.estimation import AbstractFilter

_logger = logging.getLogger(__name__)

KALMAN_FILTER = "kalman_filter"


@register_type(KALMAN_FILTER)
class KalmanFilter(AbstractFilter):
    """Linear Kalman Filter implementation.

    .. note::

        Since the model function solves the state with a Newton method, we first have
        to evaluate the :math:`Ax + b` equivalent form.

    Configuration
    -------------

    .. code-block:: json

        {
            "type": "kalman_filter"
        }

    """

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
        transition_matrix, offset = _get_model_matrix(
            self.model_function,
            self.state_size,
            current_time,
            new_time,
        )
        prediction = transition_matrix @ state_mean.reshape(-1, 1) + offset.reshape(
            -1, 1
        )
        prediction_covariance = (
            transition_matrix @ state_covariance @ transition_matrix.T
        )
        prediction_covariance += self.model_noise_covariance

        return prediction.flatten(), prediction_covariance

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
        transition_matrix, offset = _get_model_matrix(
            self.observation_function, self.state_size, time
        )
        observation = transition_matrix @ predicted_state_mean.reshape(
            -1, 1
        ) + offset.reshape(-1, 1)
        innovation = measurement.reshape(-1, 1) - observation
        innovation_covariance = (
            transition_matrix @ predicted_state_covariance @ transition_matrix.T
        )
        innovation_covariance += self.measurements_noise_covariance
        innovation_covariance_inverse = np.linalg.inv(innovation_covariance)
        kalman_gain = (
            predicted_state_covariance
            @ transition_matrix.T
            @ innovation_covariance_inverse
        )

        updated_state = predicted_state_mean.reshape(-1, 1) + kalman_gain @ innovation
        updated_covariance = (
            np.identity(self.state_size) - kalman_gain @ transition_matrix
        ) @ predicted_state_covariance

        return updated_state.flatten(), updated_covariance


def _get_model_matrix(
    model_function: Callable[..., NDArray[np.float64]],
    state_size: int,
    *args: float,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """
    Get the transition matrix A and offset b from an affine function.

    Parameters
    ----------
    model_function : Callable[..., NDArray[np.float64]]
        the model solving for the state.
    state_size : int
        the state size
    *args : float
        additional arguments passed to the model function.

    Returns
    -------
    NDArray[np.float64]
        the model matrix :math:`A`
    NDArray[np.float64]
        the offset :math:`b`
    """
    x0 = np.zeros(state_size)
    offset = model_function(x0, *args)

    base = np.identity(state_size)
    model_matrix = model_function(base, *args) - offset

    return model_matrix.T, offset
