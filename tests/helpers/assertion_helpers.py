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

from physioblocks.description.nets import Net
from physioblocks.simulation.solvers import AbstractSolver


def assert_net_equals(net_a: Net, net_b: Net) -> None:
    assert isinstance(net_a, Net)
    assert len(net_a.blocks) == len(net_b.blocks)
    for block_id, block in net_a.blocks.items():
        assert block_id in net_b.blocks
        assert type(block) is type(net_b.blocks[block_id])

    assert len(net_a.nodes) == len(net_b.nodes)
    for node_id, node in net_a.nodes.items():
        assert node_id in net_b.nodes
        assert node.dofs == net_b.nodes[node_id].dofs
        assert node.local_nodes == net_b.nodes[node_id].local_nodes


def assert_solvers_equals(solver_a: AbstractSolver, solver_b: AbstractSolver):
    assert solver_a.tolerance == solver_b.tolerance
    assert solver_a.iteration_max == solver_b.iteration_max
