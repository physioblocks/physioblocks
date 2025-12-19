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

from unittest.mock import Mock, patch

import pytest

from physioblocks.computing.quantities import Quantity
from physioblocks.library.functions.watchers import SumBlocksQuantity, WatchQuantity


@pytest.fixture
def scalar_qty() -> Quantity:
    return Quantity(0.1)


def test_eval_watch_quantity(scalar_qty: Quantity):
    func = WatchQuantity(scalar_qty)
    assert func.eval() == pytest.approx(0.1)


@patch("physioblocks.computing.quantities.Quantity")
@patch("physioblocks.description.blocks.Block")
def test_eval_sum_blocks_quantity(mock_block: Mock, mock_qty: Mock):
    mock_qty.current = 0.1
    mock_block.scalar = mock_qty

    block_list = [mock_block, mock_block, mock_block]
    func = SumBlocksQuantity("scalar", block_list)
    assert func.eval() == pytest.approx(0.3)
