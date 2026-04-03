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


from dataclasses import dataclass
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from pandas import DataFrame

from physioblocks.computing.models import Block
from physioblocks.computing.quantities import Quantity
from physioblocks.description.blocks import BlockDescription
from physioblocks.library.processes.espvr_edpvr_process import EspvrEdpvrProcess
from physioblocks.simulation.runtime import StaticSimulation


@dataclass
class SimpleCavity(Block):
    displacement: Quantity[np.float64]
    parameter: Quantity[np.float64]


@pytest.fixture
def simple_block_description():
    return BlockDescription(
        "cavity", SimpleCavity, "Any", {"displacement": "cavity.displacement"}
    )


class TestEspvrEdpvrProcess:
    def test_init_with_all_parameters(self):
        process = EspvrEdpvrProcess(
            alternative_cavity_id="cavity",
            displacement_id="displacement",
            displacement_min=0.0,
            displacement_max=1.0,
            displacement_step=0.1,
        )
        assert process.alternative_cavity_id == "cavity"
        assert process.displacement_id == "displacement"
        assert process.displacement_min == 0.0
        assert process.displacement_max == 1.0
        assert process.displacement_step == 0.1

    def test_run_without_parent_simulation(self):
        process = EspvrEdpvrProcess(
            alternative_cavity_id="cavity",
            displacement_id="displacement",
            displacement_min=0.0,
            displacement_max=1.0,
            displacement_step=0.1,
        )
        with pytest.raises(AttributeError):
            process.run()

    def test_run_with_invalid_displacement_id(self, simple_block_description):
        process = EspvrEdpvrProcess(
            alternative_cavity_id="cavity",
            displacement_id="invalid_displacement",
            displacement_min=0.0,
            displacement_max=1.0,
            displacement_step=0.1,
        )

        altenative_net_mock = MagicMock()
        altenative_net_mock.blocks = {"cavity": simple_block_description}
        mock_simulation = MagicMock()
        mock_simulation.factory.net.get_alternative_net = MagicMock(
            return_value=altenative_net_mock
        )
        process.parent_simulation = mock_simulation

        with pytest.raises(KeyError, match="not found in simulation quantities"):
            process.run()

    def test_run_with_valid_parameters(self, simple_block_description):
        process = EspvrEdpvrProcess(
            alternative_cavity_id="cavity",
            displacement_id="cavity.displacement",
            displacement_min=0.0,
            displacement_max=1.0,
            displacement_step=0.1,
        )
        altenative_net_mock = MagicMock()
        altenative_net_mock.blocks = {"cavity": simple_block_description}
        mock_simulation = MagicMock()
        mock_simulation.factory.net.get_alternative_net = MagicMock(
            return_value=altenative_net_mock
        )
        mock_simulation.quantities = {"cavity.parameter": Quantity(5.0)}
        process.parent_simulation = mock_simulation

        sim_result = DataFrame({"pressure": [10.0], "volume": [20.0]})

        with patch.multiple(
            StaticSimulation,
            __abstractmethods__=set(),
            run=MagicMock(return_value={"espvr_edpvr": sim_result}),
        ):
            result = process.run()

        assert len(result) == 1
        assert isinstance(result[0], DataFrame)

        assert "cavity.displacement" in result[0].columns
        assert "pressure" in result[0].columns
        assert "volume" in result[0].columns
