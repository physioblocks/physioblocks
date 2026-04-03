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


import pandas

from physioblocks.configuration.aliases import unwrap_aliases
from physioblocks.configuration.functions import load
from physioblocks.io.configuration import read_json
from physioblocks.simulation.runtime import ForwardSimulation
from physioblocks.simulation.time_manager import TIME_QUANTITY_ID
from physioblocks.utils.gradient_test_utils import gradient_test_from_file

from .compare import results_close_to_data

reference_path = (
    "tests/tests_references/circulation_alone/ref_circulation_alone_sim.csv"
)
circulation_alone_path = "references/circulation_alone_sim.jsonc"
circulation_alone_gradient_test_path = (
    "tests/tests_references/circulation_alone/circulation_alone_sim_gradient_test.json"
)


def test_circulation_alone_ref():
    sim_config = read_json(circulation_alone_path)
    sim_config = unwrap_aliases(sim_config)
    sim: ForwardSimulation = load(sim_config)
    sim.time_manager.duration = 5.0  # Shorten simulation time to avoid test too long
    results = sim.run()

    ref_df = pandas.read_csv(reference_path)

    tol_factors = {
        "aorta_proximal.blood_flow": 1.0,
        "aorta_proximal.blood_pressure": 1.0e2,
        "aorta_distal.blood_pressure": 1.0e2,
    }

    assert results_close_to_data(
        results[sim.name].set_index(TIME_QUANTITY_ID),
        ref_df.set_index(TIME_QUANTITY_ID),
        1e-9,
        tol_factors,
        (sim.time_manager.start, sim.time_manager.start + sim.time_manager.duration),
    )


def test_circulation_alone_gradient():
    assert gradient_test_from_file(circulation_alone_gradient_test_path)
