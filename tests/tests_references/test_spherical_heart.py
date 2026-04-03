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

from copy import copy

import pandas

from physioblocks.configuration.aliases import unwrap_aliases
from physioblocks.configuration.functions import load
from physioblocks.io.configuration import read_json
from physioblocks.simulation.runtime import ForwardSimulation
from physioblocks.simulation.time_manager import TIME_QUANTITY_ID
from physioblocks.utils.gradient_test_utils import gradient_test_from_file

from .compare import results_close_to_data

spherical_heart_gradient_path = (
    "tests/tests_references/spherical_heart/spherical_heart_sim_gradient_test.json"
)

spherical_heart_path = "references/spherical_heart_sim.jsonc"
spherical_heart_reference_path = (
    "tests/tests_references/spherical_heart/ref_spherical_heart_sim.csv"
)
spherical_heart_espvr_edpvr_reference_path = (
    "tests/tests_references/spherical_heart/ref_spherical_heart_sim_espvr_edpvr.csv"
)

spherical_heart_respiration_path = "references/spherical_heart_respiration_sim.jsonc"
spherical_heart_respiration_reference_path = (
    "tests/tests_references/spherical_heart/ref_spherical_heart_respiration_sim.csv"
)
spherical_heart_respiration_espvr_edpvr_reference_path = (
    "tests/tests_references/"
    "spherical_heart/ref_spherical_heart_respiration_sim_espvr_edpvr.csv"
)


def test_spherical_heart_gradient():
    assert gradient_test_from_file(spherical_heart_gradient_path)


def test_spherical_heart_ref():
    sim_config = read_json(spherical_heart_path)
    sim_config = unwrap_aliases(sim_config)
    sim: ForwardSimulation = load(sim_config)
    sim.time_manager.duration = 5.0  # Shorten simulation time to avoid test too long
    results = sim.run()

    ref_df = pandas.read_csv(spherical_heart_reference_path)
    ref_espvr_edpvr_df = pandas.read_csv(spherical_heart_espvr_edpvr_reference_path)

    tol_factors = sim.state.magnitudes
    tol_factors["active_law.activation"] = 1.0e1
    tol_factors["valve_atrium.flux"] = 1.0e2
    tol_factors["valve_arterial.flux"] = 1.0e2
    tol_factors["aorta_proximal.blood_pressure"] = 1.0e2
    tol_factors["aorta_distal.blood_pressure"] = 1.0e2
    tol_factors["cavity.blood_pressure"] = 1.0e2
    tol_factors["atrial.blood_pressure"] = 1.0e2
    tol_factors["cavity.volume"] = 1.0e2
    tol_factors["cavity.dynamics.EDPVR"] = 1.0e2
    tol_factors["cavity.dynamics.ESPVR"] = 1.0e2

    assert results_close_to_data(
        results[sim.name].set_index(TIME_QUANTITY_ID),
        ref_df.set_index(TIME_QUANTITY_ID),
        1e-9,
        tol_factors,
        (sim.time_manager.start, sim.time_manager.start + sim.time_manager.duration),
    )
    assert results_close_to_data(
        results["espvr-edpvr"].set_index("cavity.dynamics.disp"),
        ref_espvr_edpvr_df.set_index("cavity.dynamics.disp"),
        1e-9,
        tol_factors,
    )


def test_spherical_heart_respiration_ref():
    sim_config = read_json(spherical_heart_respiration_path)
    sim_config = unwrap_aliases(sim_config)
    # Shorten simulation time to avoid test too long
    sim: ForwardSimulation = load(sim_config)
    sim.time_manager.duration = 5.0
    results = sim.run()

    ref_df = pandas.read_csv(spherical_heart_respiration_reference_path)
    ref_espvr_edpvr_df = pandas.read_csv(
        spherical_heart_respiration_espvr_edpvr_reference_path
    )

    tol_factors = copy(sim.state.magnitudes)
    tol_factors["active_law.activation"] = 1.0e1
    tol_factors["valve_atrium.flux"] = 1.0e2
    tol_factors["valve_arterial.flux"] = 1.0e2
    tol_factors["aorta_proximal.blood_pressure"] = 1.0e2
    tol_factors["aorta_distal.blood_pressure"] = 1.0e2
    tol_factors["cavity.blood_pressure"] = 1.0e2
    tol_factors["atrial.blood_pressure"] = 1.0e2
    tol_factors["cavity.volume"] = 1.0e2
    tol_factors["cavity.dynamics.EDPVR"] = 1.0e2
    tol_factors["cavity.dynamics.ESPVR"] = 1.0e2
    tol_factors["pleural.pressure"] = 1.0e2

    assert results_close_to_data(
        results[sim.name].set_index(TIME_QUANTITY_ID),
        ref_df.set_index(TIME_QUANTITY_ID),
        1e-9,
        tol_factors,
        (sim.time_manager.start, sim.time_manager.start + sim.time_manager.duration),
    )

    assert results_close_to_data(
        results["espvr-edpvr"].set_index("cavity.dynamics.disp"),
        ref_espvr_edpvr_df.set_index("cavity.dynamics.disp"),
        1e-9,
        tol_factors,
    )
