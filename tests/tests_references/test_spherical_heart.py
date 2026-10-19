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

import pytest

from physioblocks.simulation.estimation import (
    COVARIANCE_LABEL,
    STDEV_MIN_LABEL,
    STDEV_PLUS_LABEL,
    VARIANCE_LABEL,
)
from physioblocks.utils.gradient_test_utils import gradient_test_from_file

from .functions import (
    ReferenceCase,
    ReferenceParameters,
    get_artifact_path,
    migration_test,
    reference_test,
)


def test_spherical_heart_gradient():
    assert gradient_test_from_file(
        "tests/tests_references/spherical_heart/spherical_heart_model_gradient_test.json"
    )


@pytest.mark.parametrize(
    "older_version_path",
    [
        pytest.param(
            "tests/tests_references/spherical_heart/v1.2.0/spherical_heart_sim.jsonc",
            id="1.2.0",
        ),
        pytest.param(
            "tests/tests_references/spherical_heart/v1.2.0/spherical_heart_sim_full_configuration.jsonc",
            id="1.2.0_full",
        ),
    ],
)
@pytest.mark.filterwarnings("ignore::UserWarning")
def test_spherical_heart_migration(older_version_path):
    migration_test(older_version_path)


DISP_QUANTITY_ID = "cavity.dynamics.disp"

forward_magnitudes = {
    "cavity.dynamics.disp": 1.0e-3,
    "cavity.velocity_law.vel": 1.0e-2,
    "cavity.rheology.fib_deform": 1.0e-1,
    "cavity.rheology.active_law.active_stiffness": 1.0e5,
    "cavity.rheology.active_law.active_energy_sqrt": 1.0e2,
    "cavity.rheology.active_law.active_tension_discr": 1.0e4,
    "valve_atrium.flux": 1.0e2,
    "valve_arterial.flux": 1.0e2,
    "cavity.blood_pressure": 1.0e2,
    "aorta_proximal.blood_pressure": 1.0e2,
    "aorta_distal.blood_pressure": 1.0e2,
    "cavity.volume": 1.0e2,
    "active_law.activation": 1.0e1,
}

estimation_magnitudes = forward_magnitudes.copy()
estimation_magnitudes.update(
    {
        "circulation_aorta_distal.resistance": 1.0e8,
        "heart_contractility": 1.0e5,
        "cavity.velocity_law.accel": 1.0e1,
    }
)

stdev_plus_min_magnitudes = {
    f"{bound_label}.{field}": estimation_magnitudes.get(field, 1.0)
    for bound_label in (STDEV_PLUS_LABEL, STDEV_MIN_LABEL)
    for field in estimation_magnitudes
}
estimation_magnitudes.update(stdev_plus_min_magnitudes)

FORWARD_CASE = ReferenceCase(
    id="forward",
    config_path="references/spherical_heart_forward_sim.jsonc",
    references=[
        ReferenceParameters(
            "tests/tests_references/spherical_heart/ref_spherical_heart_sim.csv",
        ),
        ReferenceParameters(
            "tests/tests_references/spherical_heart/ref_spherical_heart_sim_espvr_edpvr.csv",
            name="espvr-edpvr",
            index=DISP_QUANTITY_ID,
        ),
    ],
    magnitudes=forward_magnitudes,
)

ESTIMATION_CASE = ReferenceCase(
    id="estimation",
    config_path="references/spherical_heart_estimation_sim.jsonc",
    references=[
        ReferenceParameters(
            "tests/tests_references/spherical_heart/ref_spherical_heart_estimation_sim.csv",
            interval=(0.0, 2.0),
            exclude_prefixes=(f"{COVARIANCE_LABEL}.", f"{VARIANCE_LABEL}."),
        )
    ],
    duration=2.0,
    magnitudes=estimation_magnitudes,
)

REFERENCE_CASES = [FORWARD_CASE, ESTIMATION_CASE]


@pytest.mark.parametrize("case", REFERENCE_CASES, ids=lambda case: case.id)
def test_spherical_heart_reference(case, request: pytest.FixtureRequest):
    reference_test(case, artifact_path=get_artifact_path(request))
