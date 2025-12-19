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

"""Define simple operations to initialize parameters in the configuration."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from physioblocks.base.operators import AbstractBaseOperators
from physioblocks.registers.type_register import register_type
from physioblocks.simulation import AbstractFunction

# Sum funtion type id
SUM_TYPE_ID = "sum"


@dataclass
@register_type(SUM_TYPE_ID)
class Sum(AbstractFunction, AbstractBaseOperators):
    """
    Sum the elements in ``add`` and subtract the elements in ``subtract``.
    """

    add: Iterable[Any] = field(default_factory=list)
    """the values to sum"""

    subtract: Iterable[Any] | None = None
    """the values to subtract"""

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
        Sum the elements in ``add`` and subtract the elements in ``subtract``.

        :return: the sum result
        :rtype: Any
        """

        pos = np.sum(np.array(self.add), axis=0)

        if self.subtract is None:
            return pos

        neg = np.sum(np.array(self.subtract), axis=0)
        return pos - neg


def _multiply(elements: Iterable[Any]) -> Any:
    result = 1.0
    for elem in elements:
        result = np.multiply(result, elem)
    return result


# Product function type name
PRODUCT_TYPE_ID = "product"


@dataclass
@register_type(PRODUCT_TYPE_ID)
class Product(AbstractFunction, AbstractBaseOperators):
    """
    Multiply all values provided in ``factors`` list and divide the
    result with the multiplication of the values in the ``inverses`` list.

    ..note:: It uses the numpy multiply function

    """

    factors: Iterable[Any] = field(default_factory=list)
    """The values to multiply"""

    inverses: Iterable[Any] | None = None
    """The values to inverse then multiply"""

    @property
    def operation_value(self) -> Any:
        """
        Value used with base operators.

        :return: the current evaluation of the function
        :rtype: Any
        """
        return self.eval()

    def eval(self) -> Any:
        product = _multiply(self.factors)
        if self.inverses is None:
            return product
        else:
            inverses_product = _multiply(self.inverses)
            return product / inverses_product
