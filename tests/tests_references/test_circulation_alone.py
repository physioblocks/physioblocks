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

from copy import copy

import pandas as pd

from physioblocks.configuration.aliases import unwrap_aliases
from physioblocks.configuration.functions import load
from physioblocks.io.configuration import read_json
from physioblocks.simulation.runtime import ForwardSimulation
from physioblocks.simulation.time_manager import TIME_QUANTITY_ID
from physioblocks.utils.gradient_test_utils import gradient_test_from_file

from .io import read_reference, results_close_to_data

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
    sim.time_manager.duration = 0.5  # Shorten simulation time to avoid test too long
    results = sim.run()

    ref_df = read_reference(reference_path)
    ref_df = ref_df.set_index(TIME_QUANTITY_ID)

    matching_ids = {data_id: data_id for data_id in results[0] if data_id != "time"}
    tol_factors = copy(sim.magnitudes)
    tol_factors["aorta_proximal.blood_flow"] = 1.0e-6

    results_df = pd.DataFrame(results)
    results_df = results_df.set_index(TIME_QUANTITY_ID)

    assert results_close_to_data(
        results_df,
        ref_df,
        matching_ids,
        1e-9,
        tol_factors,
        (sim.time_manager.start, sim.time_manager.start + sim.time_manager.duration),
    )


def test_circulation_alone_gradient():
    assert gradient_test_from_file(circulation_alone_gradient_test_path)
