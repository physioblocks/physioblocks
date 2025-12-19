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

"""
Watcher are useful functions to use to set **Output Functions**
in the configuration.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from physioblocks.base.operators import AbstractBaseOperators
from physioblocks.computing.models import Block
from physioblocks.computing.quantities import Quantity
from physioblocks.registers.type_register import register_type
from physioblocks.simulation import AbstractFunction

# Quantity Watcher function type name
WATCH_QUANTITY_TYPE_ID = "watch_quantity"


@dataclass
@register_type(WATCH_QUANTITY_TYPE_ID)
class WatchQuantity(AbstractFunction, AbstractBaseOperators):
    """
    Return the current value of the watch quantity.
    """

    quantity: Quantity[Any]
    """The quantities to watch"""

    @property
    def operation_value(self) -> Any:
        """
        Value used with base operators.

        :return: the current evaluation of the function
        :rtype: Any
        """
        return self.eval()

    def eval(self) -> Any:
        """Just return the watched quantity current value

        :return: the watched quantity current value
        :rtype: np.float64 | np.ndarray"""
        return self.quantity.current


# Sum Blocks Quantity function type name
SUM_BLOCKS_QUANTITY_TYPE_ID = "sum_blocks_quantity"


@dataclass
@register_type(SUM_BLOCKS_QUANTITY_TYPE_ID)
class SumBlocksQuantity(AbstractFunction, AbstractBaseOperators):
    """Sum the current values of quantities with the given name
    for each the blocks."""

    quantity_id: str
    """block local id of the quantity to sum"""

    elements: Iterable[Block] = field(default_factory=list)
    """the blocks holding the quantity to sum"""

    @property
    def operation_value(self) -> Any:
        """
        Value used with base operators.

        :return: the current evaluation of the function
        :rtype: Any
        """
        return self.eval()

    def eval(self) -> Any:
        """
        Sum the quantities

        :return: the sum of the quantities
        :rtype: Any
        """
        return np.sum(
            [getattr(block, self.quantity_id).current for block in self.elements]
        )
