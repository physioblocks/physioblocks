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

import os
from dataclasses import dataclass, field
from pathlib import Path

import pandas
import pytest

from physioblocks.configuration.aliases import unwrap_aliases
from physioblocks.configuration.functions import load
from physioblocks.io.configuration import read_json
from physioblocks.simulation.base import AbstractSimulation
from physioblocks.simulation.time_manager import TIME_QUANTITY_ID

from ..tests_references.compare import results_close_to_data


@dataclass
class ReferenceParameters:
    """Parameters for the reference comparison in references tests.

    Parameters
    ----------
    path : str
        the path to the expected results
    name : str
        the name of the reference to compare, default is the loaded simulation
        name.
    index : str
        the column name used to index reference and simulation results.
        Default is the 'time' column.
    interval : tuple[float, float] | None
        the beginning and end of the index range to compare.
        Default is None and means the entire configured simulation range.
    exclude_prefixes : list[str]
        column that start with those prefixes are dropped
        from the comparison. Default is to compare every columns.

    """

    path: str
    name: str | None = None
    index: str = TIME_QUANTITY_ID
    interval: tuple[float, float] | None = None
    exclude_prefixes: list[str] = field(default_factory=list)


@dataclass
class ReferenceCase:
    """Parameters defining the reference test case.

    Parameters
    ----------
    id : str
        the pytest id for this case.
    config_path : str
        the path to the configuration to simulate.
    references : list[ReferenceParameters]
        the reference(s) to compare simulation output against.
    duration : float | None
        shortened simulation duration to run, to avoid
        long-running tests. Default is the configured duration.
    tolerance : float
        maximum accepted difference between reference and result
        relative to each field magnitude. Default is 1e-9.
    magnitudes : dict[str, float] | None
        magnitude of the results to set the relative tolerance.
        Default is one for every field.
    use_state_magnitudes : bool
        Flag to set the tolerances magnitudes from the
        simulation's state magnitudes before updating with ``magnitudes``.
        Default is False.

    """

    id: str
    config_path: str
    references: list[ReferenceParameters]
    duration: float | None = None
    tolerance: float = 1e-9
    magnitudes: dict[str, float] | None = None
    use_state_magnitudes: bool = False


def reference_test(
    case: ReferenceCase,
    artifact_path: str | Path | None = None,
):
    """Test if a reference configuration provides the expected outputs.

    Parameters
    ----------
    case : ReferenceCase
        the case parameters to test
    artifact_path : str | Path | None
        when the comparison fails, write the result at this path.

    """
    sim_config = read_json(case.config_path)
    exec_dir = Path.cwd()
    config_path = Path(case.config_path)
    os.chdir(config_path.parent)

    try:
        sim_config = unwrap_aliases(sim_config)
        sim: AbstractSimulation = load(sim_config)

        if case.duration is not None:
            sim.simulation_model.time_manager.duration = case.duration

        results = sim.run()
    finally:
        os.chdir(exec_dir)

    tol_factors = (
        dict(sim.simulation_model.state.magnitudes) if case.use_state_magnitudes else {}
    )
    if case.magnitudes is not None:
        tol_factors.update(case.magnitudes)

    references_match = True

    for reference_param in case.references:
        result_key = (
            reference_param.name
            if reference_param.name is not None
            else sim.simulation_name
        )
        result_df = results[result_key].set_index(reference_param.index)
        ref_df = pandas.read_csv(reference_param.path).set_index(reference_param.index)

        if reference_param.exclude_prefixes:
            compare_columns = [
                column
                for column in result_df.columns
                if not column.startswith(reference_param.exclude_prefixes)
            ]
            result_df = result_df[compare_columns]
            ref_df = ref_df[[column for column in compare_columns if column in ref_df]]

        reference_output_dir = (
            Path(artifact_path) / result_key if artifact_path is not None else None
        )
        references_match = (
            results_close_to_data(
                result_df,
                ref_df,
                case.tolerance,
                tol_factors,
                reference_param.interval,
                reference_output_dir,
            )
            and references_match
        )

    assert references_match


def get_artifact_path(request: pytest.FixtureRequest) -> Path:
    artifact_path = Path(request.path.parent) / "artifacts"
    test_name = str(request.node.name)
    test_name = test_name.translate(str.maketrans("[]/.", "____"))
    test_name = "_".join(part for part in test_name.split("_") if part != "")
    return artifact_path / test_name


def migration_test(older_version_path):
    """Test if an older version of the configuration still loads.

    Parameters
    ----------
    older_version_path : str
        the path to the older version

    """
    older_version_config = read_json(older_version_path)
    older_version_config = unwrap_aliases(older_version_config)
    with pytest.deprecated_call():
        load(older_version_config)
