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
from unittest.mock import MagicMock

import numpy as np
import pytest

from physioblocks.computing.models import (
    Block,
    declares_flux,
    declares_internal_equation,
    declares_saved_quantity,
)
from physioblocks.computing.quantities import Quantity
from physioblocks.description.blocks import BlockDescription
from physioblocks.description.nets import Net
from physioblocks.library.blocks.cavity import CAVITY_VOLUME_LOCAL_ID
from physioblocks.library.processes.espvr_edpvr_process import EspvrEdpvrProcess
from physioblocks.simulation.base import (
    QuantityInit,
    SimulationModelFactory,
    SimulationRange,
)
from physioblocks.simulation.solvers import ConvergenceError


@dataclass
class SimpleCavity(Block):
    displacement: Quantity[np.float64]
    pressure: Quantity[np.float64]
    internal_variable: Quantity[np.float64]

    @declares_flux(0, "pressure")
    def compute_flux(self):
        return self.displacement.current - self.pressure.new

    @compute_flux.partial_derivative("pressure")
    def dflux_dpressure(self):
        return -1.0

    @declares_internal_equation("internal_variable")
    def compute_internal_variable(self):
        return self.displacement.current - self.internal_variable.new

    @compute_internal_variable.partial_derivative("internal_variable")
    def dinternal_variable_dinternal_variable(self):
        return -1.0

    @declares_saved_quantity(CAVITY_VOLUME_LOCAL_ID)
    def compute_volume(self):
        return self.displacement.current


@pytest.fixture
def simple_block_description():
    return BlockDescription(
        "cavity", SimpleCavity, "flow", alternative_types={"cavity": SimpleCavity}
    )


@pytest.fixture
def ref_flux_dof_type_register():
    return MagicMock(
        flux_dof_couples={"flow": "pressure"},
        dof_flux_couples={"pressure": "flow"},
    )


@pytest.fixture
def simple_net(simple_block_description: BlockDescription, ref_flux_dof_type_register):
    net = Net(ref_flux_dof_type_register)
    net.add_node("cavity_node")
    net.add_block("cavity", simple_block_description, {0: "cavity_node"})
    return net


@pytest.fixture
def displacement_range():
    return SimulationRange(start=0.1, length=0.2, step_size=0.1)


@dataclass
class DoNotConvergeCavity(Block):
    displacement: Quantity[np.float64]
    internal_variable: Quantity[np.float64]

    @declares_internal_equation("internal_variable")
    def compute_internal_variable(self):
        return self.displacement.current + self.internal_variable.new**2

    @compute_internal_variable.partial_derivative("internal_variable")
    def dinternal_variable_dinternal_variable(self):
        return 2 * self.internal_variable.new


@pytest.fixture
def do_not_converge_net(ref_flux_dof_type_register):
    net = Net(ref_flux_dof_type_register)
    block_desc = BlockDescription(
        "cavity",
        DoNotConvergeCavity,
        "Any",
        alternative_types={"cavity": DoNotConvergeCavity},
    )
    net.add_block("cavity", block_desc, {})
    return net


class TestEspvrEdpvrProcess:
    def test_run_without_parent_simulation(self, displacement_range):
        process = EspvrEdpvrProcess("cavity", "displacement", displacement_range)
        with pytest.raises(AttributeError):
            process.run()

    def test_run(self, simple_net: Net, displacement_range: SimulationRange):
        factory = SimulationModelFactory(
            net=simple_net,
            state={
                "cavity.pressure": QuantityInit(),
                "cavity.internal_variable": QuantityInit(),
            },
            parameters={"cavity.displacement": 0.0},
        )
        process = EspvrEdpvrProcess("cavity", "cavity.displacement", displacement_range)
        process.model_factory = factory
        results = process.run()

        assert len(results) == 1
        assert results[0].columns.size == 4
        assert "cavity.displacement" in results[0]
        assert results[0]["cavity.displacement"].to_list() == pytest.approx(
            [0.1, 0.2, 0.3]
        )
        assert "cavity_node.pressure" in results[0]
        assert results[0]["cavity_node.pressure"].to_list() == pytest.approx(
            [0.1, 0.2, 0.3]
        )
        assert "cavity.internal_variable" in results[0]
        assert results[0]["cavity.internal_variable"].to_list() == pytest.approx(
            [0.1, 0.2, 0.3]
        )
        assert "cavity.volume" in results[0]
        assert results[0]["cavity.volume"].to_list() == pytest.approx([0.1, 0.2, 0.3])

    def test_run_convergence_error(
        self, do_not_converge_net: Net, displacement_range: SimulationRange
    ):
        factory = SimulationModelFactory(
            net=do_not_converge_net,
            state={"cavity.internal_variable": QuantityInit()},
            parameters={"cavity.displacement": 0.0},
        )
        process = EspvrEdpvrProcess("cavity", "cavity.displacement", displacement_range)
        process.model_factory = factory

        with pytest.raises(
            ConvergenceError, match="did not converge" and "displacement: 0.1"
        ):
            process.run()
