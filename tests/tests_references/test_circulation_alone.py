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

from physioblocks.utils.gradient_test_utils import gradient_test_from_file

from .functions import (
    ReferenceCase,
    ReferenceParameters,
    get_artifact_path,
    migration_test,
    reference_test,
)


def test_circulation_alone_gradient():
    assert gradient_test_from_file(
        "tests/tests_references/circulation_alone/circulation_alone_model_gradient_test.json"
    )


FORWARD_CASE = ReferenceCase(
    id="forward",
    config_path="references/circulation_alone_forward_sim.jsonc",
    references=[
        ReferenceParameters(
            "tests/tests_references/circulation_alone/ref_circulation_alone_forward_sim.csv",
            interval=(0.0, 5.0),
        )
    ],
    duration=5.0,
    use_state_magnitudes=True,
)

ESTIMATION_CASE = ReferenceCase(
    id="estimation",
    config_path="references/circulation_alone_estimation_sim.jsonc",
    references=[
        ReferenceParameters(
            "tests/tests_references/circulation_alone/ref_circulation_alone_estimation_ukf_sim.csv",
            interval=(0.0, 1.0),
        )
    ],
    duration=1.0,
    magnitudes={
        "aorta_distal.resistance": 1e8,
        "stdev_plus.aorta_distal.resistance": 1e8,
        "stdev_min.aorta_distal.resistance": 1e8,
    },
    use_state_magnitudes=True,
)

REFERENCE_CASES = [FORWARD_CASE, ESTIMATION_CASE]


@pytest.mark.parametrize(
    "case", REFERENCE_CASES, ids=[case.id for case in REFERENCE_CASES]
)
def test_circulation_alone_reference(case, request: pytest.FixtureRequest):
    reference_test(case, artifact_path=get_artifact_path(request))


@pytest.mark.parametrize(
    "older_version_path",
    [
        pytest.param(
            "tests/tests_references/circulation_alone/v1.2.0/circulation_alone_sim.jsonc",
            id="1.2.0",
        ),
        pytest.param(
            "tests/tests_references/circulation_alone/v1.2.0/circulation_alone_sim_full.jsonc",
            id="1.2.0_full",
        ),
    ],
)
@pytest.mark.filterwarnings("ignore::UserWarning")
def test_circulation_alone_migration(older_version_path):
    migration_test(older_version_path)
