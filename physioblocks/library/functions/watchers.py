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

"""Define configurable functions to follow a quantity value."""

from __future__ import annotations

from typing import Any

from physioblocks.base.operators import AbstractBaseOperators
from physioblocks.computing.quantities import Quantity
from physioblocks.registers.type_register import register_type
from physioblocks.simulation import AbstractFunction

# Quantity Watcher function type name
WATCH_QUANTITY_TYPE_ID = "watch_quantity"


@register_type(WATCH_QUANTITY_TYPE_ID)
class WatchQuantity(AbstractFunction, AbstractBaseOperators):
    """Return the value of the watch quantity.

    Configuration
    -------------

    .. code-block:: json

        {
            "type": "watch_quantity",
            "evaluation_quantities": {
                "quantity": "<str>"  // Global name of the watched quantity
            }
        }

    """

    @property
    def operation_value(self) -> Any:
        """Value used with base operators.

        Returns
        -------
        Any
            the current evaluation of the function

        """
        return self.eval_current()

    def eval(self, quantity: Quantity[Any]) -> Quantity[Any]:
        """Get the watched quantity.

        Parameters
        ----------
        quantity : Quantity[Any]
            the watched quantity.

        Returns
        -------
        Quantity[Any]
            the watched quantity

        """
        return quantity
