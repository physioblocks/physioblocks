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

import numpy as np
import pytest

from physioblocks.library.filters.sigmas import (
    CanonicalSigmaPoints,
    SimplexSigmaPoints,
    StarSigmaPoints,
)
from physioblocks.library.filters.unscented_kalman_filter import (
    alpha_covariance,
    alpha_mean,
)


@pytest.fixture
def n():
    return 3


@pytest.fixture
def x():
    return np.array([0.1, 0.2, 0.3])


@pytest.fixture
def covariance():
    return np.array([[0.2, -0.15, 0.3], [-0.15, 0.2, -0.1], [0.3, -0.1, 2.0]])


def test_star_sigma_points(n, x, covariance):
    sigma_points_generator = StarSigmaPoints(n)
    assert sigma_points_generator.state_size == n
    assert sigma_points_generator.nb_points == 2 * n + 1
    assert sigma_points_generator.mean_weights == pytest.approx(
        sigma_points_generator.nb_points * [1 / sigma_points_generator.nb_points]
    )
    assert sigma_points_generator.covariance_weights == pytest.approx(
        sigma_points_generator.mean_weights
    )

    sigma_points = sigma_points_generator.get_sigma_points(x, covariance)

    assert alpha_mean(
        sigma_points, sigma_points_generator.mean_weights
    ) == pytest.approx(x)
    assert alpha_covariance(
        sigma_points, x, sigma_points_generator.covariance_weights
    ) == pytest.approx(covariance)


def test_canonical_sigma_points(n, x, covariance):
    sigma_points_generator = CanonicalSigmaPoints(n)
    assert sigma_points_generator.state_size == n
    assert sigma_points_generator.nb_points == 2 * n
    assert sigma_points_generator.mean_weights == pytest.approx(
        sigma_points_generator.nb_points * [1 / sigma_points_generator.nb_points]
    )
    assert sigma_points_generator.covariance_weights == pytest.approx(
        sigma_points_generator.mean_weights
    )

    sigma_points = sigma_points_generator.get_sigma_points(x, covariance)

    assert alpha_mean(
        sigma_points, sigma_points_generator.mean_weights
    ) == pytest.approx(x)
    assert alpha_covariance(
        sigma_points, x, sigma_points_generator.covariance_weights
    ) == pytest.approx(covariance)


def test_simplex_sigma_points(n, x, covariance):
    sigma_points_generator = SimplexSigmaPoints(n)
    assert sigma_points_generator.state_size == n
    assert sigma_points_generator.nb_points == n + 1
    assert sigma_points_generator.mean_weights == pytest.approx(
        sigma_points_generator.nb_points * [1 / sigma_points_generator.nb_points]
    )
    assert sigma_points_generator.covariance_weights == pytest.approx(
        sigma_points_generator.mean_weights
    )

    sigma_points = sigma_points_generator.get_sigma_points(x, covariance)

    assert alpha_mean(
        sigma_points, sigma_points_generator.mean_weights
    ) == pytest.approx(x)
    assert alpha_covariance(
        sigma_points, x, sigma_points_generator.covariance_weights
    ) == pytest.approx(covariance)
