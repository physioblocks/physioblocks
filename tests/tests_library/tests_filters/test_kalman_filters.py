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

from unittest.mock import patch

import numpy as np
import pytest
from numpy.typing import NDArray

from physioblocks.library.filters.discrepancies import (
    DIFFERENCE_METHOD_ID,
    Difference,
)
from physioblocks.library.filters.kalman_filter import KalmanFilter
from physioblocks.library.filters.sigmas import (
    STAR_SIGMA_POINTS_METHOD_ID,
    StarSigmaPoints,
)
from physioblocks.library.filters.unscented_kalman_filter import UnscentedKalmanFilter
from physioblocks.simulation.estimation import AbstractFilter


@np.vectorize(excluded=[1, 2], signature="(n) -> (n)")
def velocity_model_function(
    x: NDArray[np.float64], current_time: float, new_time: float
):
    x_vector = x.reshape(-1, 1)
    velocity_model = np.array([[1.0, new_time - current_time], [0.0, 1.0]])
    velocity_offset = np.array([[0.0], [0.5]])
    return (velocity_model @ x_vector + velocity_offset).flatten()


@np.vectorize(excluded=[1], signature="(n) -> (m)")
def position_observation_function(x: NDArray[np.float64], new_time: float):
    x_vector = x.reshape(-1, 1)
    observation_matrix = np.array([[1.0, 0.0]])

    return (observation_matrix @ x_vector).flatten()


@np.vectorize(excluded=[1], signature="(n) -> (m)")
def direct_observation_function(x: NDArray[np.float64], new_time: float):
    return x


def get_velocity_discrete_model_noise(factor, dt):
    return factor * np.array([[dt**3 / 3.0, dt**2 / 2.0], [dt**2 / 2.0, dt]])


def get_measurement_noise_matrix(noise):
    return np.array([[noise]])


def kalman_filter_velocity_model(filter_cls: type[AbstractFilter]) -> AbstractFilter:
    return filter_cls(2, 1, velocity_model_function, position_observation_function)


def kalman_filter_velocity_model_with_noise(
    filter_cls: type[AbstractFilter],
) -> AbstractFilter:
    kalman_filter = kalman_filter_velocity_model(filter_cls)
    kalman_filter.model_noise_covariance = get_velocity_discrete_model_noise(0.1, 0.1)
    kalman_filter.measurements_noise_covariance = get_measurement_noise_matrix(1.0)
    return kalman_filter


@pytest.fixture
def type_register():
    register = {
        STAR_SIGMA_POINTS_METHOD_ID: StarSigmaPoints,
        StarSigmaPoints: STAR_SIGMA_POINTS_METHOD_ID,
        DIFFERENCE_METHOD_ID: Difference,
        Difference: DIFFERENCE_METHOD_ID,
    }
    with patch("physioblocks.registers.type_register.__type_register", new=register):
        yield register


@pytest.fixture(params=[KalmanFilter, UnscentedKalmanFilter], ids=["kalman", "ukf"])
def filter_cls(request):
    return request.param


@pytest.fixture
def filter_with_noise(type_register, filter_cls):
    return kalman_filter_velocity_model_with_noise(filter_cls)


@pytest.fixture
def direct_observations_filter(type_register, filter_cls):
    return filter_cls(2, 2, velocity_model_function, direct_observation_function)


@pytest.fixture
def state():
    return np.arange(2, dtype=np.float64)


@pytest.fixture
def covariance():
    return np.diag([0.1, 0.1])


class TestKalmanFilters:
    def test_prediction_covariance(
        self, filter_with_noise: AbstractFilter, state, covariance
    ):
        _state, covariance = filter_with_noise.prediction(0.0, 0.1, state, covariance)

        # symmetric
        assert covariance == pytest.approx(covariance.T)

        # definite semi-positive
        assert np.all(np.linalg.eigvals(covariance) >= 0.0)

    def test_update_covariance(
        self, filter_with_noise: AbstractFilter, state, covariance
    ):
        _state, covariance = filter_with_noise.update(
            0.1, state, covariance, np.array([0.1])
        )

        # symmetric
        assert covariance == pytest.approx(covariance.T)

        # definite semi-positive
        assert np.all(np.linalg.eigvals(covariance) >= 0.0)

    def test_update_decrease_covariance(self, filter_with_noise, state, covariance):
        _predicted_state, predicted_covariance = filter_with_noise.prediction(
            0.0, 0.1, state, covariance
        )
        _updated_state, updated_covariance = filter_with_noise.update(
            0.1, _predicted_state, predicted_covariance, np.array([0.1])
        )

        # Updated covariance is "lower" than predicted covariance.
        assert np.all(
            np.linalg.eigvals(predicted_covariance - updated_covariance) >= 0.0
        )

    def test_filter_without_noise(
        self, direct_observations_filter: AbstractFilter, state, covariance
    ):
        measurement = np.array([0.5, 5.0])
        filtered_state, _filtered_covar = direct_observations_filter.filter(
            0.0, 0.1, state, covariance, measurement
        )

        # the new state is the measurement
        assert filtered_state == pytest.approx(measurement)

    def test_filter_with_model_noise_only(
        self, direct_observations_filter: AbstractFilter, state, covariance
    ):
        direct_observations_filter.model_noise_covariance = (
            get_velocity_discrete_model_noise(0.1, 0.1)
        )
        measurement = np.array([0.5, 5.0])
        filtered_state, _filtered_covar = direct_observations_filter.filter(
            0.0, 0.1, state, covariance, measurement
        )
        # the new state is the measurement
        assert filtered_state == pytest.approx(measurement)

    def test_high_measurement_noise(
        self, filter_with_noise: AbstractFilter, state, covariance
    ):
        filter_with_noise.measurements_noise_covariance = np.array([[np.inf]])
        filtered_state, _filtered_covar = filter_with_noise.filter(
            0.0, 0.1, state, covariance, np.array([1.0])
        )
        predicted_state, _predicted_covar = filter_with_noise.prediction(
            0.0, 0.1, state, covariance
        )

        # the filter skips the update
        assert filtered_state == pytest.approx(predicted_state)

    def test_linear_model_compare(self, type_register):
        # Compare results from the UKF with a linear model to the kalman filter
        kalman = kalman_filter_velocity_model_with_noise(KalmanFilter)
        ukf = kalman_filter_velocity_model_with_noise(UnscentedKalmanFilter)
        state_kalman = np.arange(2, dtype=np.float64)
        covariance_kalman = np.diag([0.1, 0.1])
        state_ukf = np.arange(2, dtype=np.float64)
        covariance_ukf = np.diag([0.1, 0.1])
        times = 0.1 * np.arange(10)
        measurements = 0.12 * np.arange(10)

        for _i in range(times.size - 1):
            t_current, t_new = times[_i], times[_i + 1]
            state_kalman, covariance_kalman = kalman.filter(
                t_current, t_new, state_kalman, covariance_kalman, measurements[_i + 1]
            )
            state_ukf, covariance_ukf = ukf.filter(
                t_current, t_new, state_ukf, covariance_ukf, measurements[_i + 1]
            )
            assert state_kalman == pytest.approx(state_ukf, abs=1e-12, rel=1e-12)
            assert covariance_kalman == pytest.approx(
                covariance_ukf, abs=1e-12, rel=1e-12
            )
