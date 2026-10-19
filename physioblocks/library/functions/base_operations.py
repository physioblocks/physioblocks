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

from physioblocks.registers.type_register import register_type
from physioblocks.simulation.functions import (
    AbstractFunction,
    AbstractInitializationFunction,
)

# Sum function type id
SUM_TYPE_ID = "sum"


@dataclass
@register_type(SUM_TYPE_ID)
class Sum(AbstractInitializationFunction):
    """Sum the elements in ``add`` and subtract the elements in ``subtract``.

    Mostly useful in the configuration to initialize parameters with reference to other
    parameters.

    Attributes
    ----------
    add : Iterable[Any]
        the values to sum
    subtract : Iterable[Any] | None
        the values to subtract. Default is None.

    Configuration
    -------------

    .. code-block:: json

        {
            "type": "sum",
            "add": ["<float>"],            // Values to sum
            "subtract": ["<float>"]        // Values to subtract
                                           // (optional, default: none)
        }

    """

    add: Iterable[Any] = field(default_factory=list)

    subtract: Iterable[Any] | None = None

    def eval(self, **quantities: Any) -> Any:
        """Sum the elements in ``add`` and subtract the elements in ``subtract``.

        Parameters
        ----------
        quantities: Any
            Keyword arguments providing the value of the quantities

        Returns
        -------
        Any
            the sum result

        """
        positives = [
            quantities[to_add] if isinstance(to_add, str) else to_add
            for to_add in self.add
        ]

        pos = np.sum(np.array(positives), axis=0)

        if self.subtract is None:
            return pos

        negatives = [
            quantities[to_subtract] if isinstance(to_subtract, str) else to_subtract
            for to_subtract in self.subtract
        ]

        neg = np.sum(np.array(negatives), axis=0)
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
class Product(AbstractFunction, AbstractInitializationFunction):
    """Simple configurable Product.

    Multiply all values provided in ``factors`` list and divide the result by the
    product of the values in the ``inverses`` list.

    Mostly useful in the configuration to initialize parameters with reference to other
    parameters.

    .. note:: It uses the numpy multiply function

    Attributes
    ----------
    factors : Iterable[Any]
        The values to multiply
    inverses : Iterable[Any] | None
        The values to inverse then multiply

    Configuration
    -------------

    .. code-block:: json

        {
            "type": "product",
            "factors": ["<float>"],        // Values to multiply
            "inverses": ["<float>"]        // Values dividing the
                                           // product (optional, default: none)
        }

    """

    factors: Iterable[Any] = field(default_factory=list)

    inverses: Iterable[Any] | None = None

    def eval(self, **quantities: Any) -> Any:
        """
        Perform the product.

        Parameters
        ----------
        quantities: Any
            Keyword arguments providing the value of the quantities

        Returns
        -------
        Any
            the product
        """
        current_factors = [
            quantities[factor] if isinstance(factor, str) else factor
            for factor in self.factors
        ]
        product = _multiply(current_factors)
        if self.inverses is None:
            return product
        else:
            current_inverses = [
                quantities[inverse] if isinstance(inverse, str) else inverse
                for inverse in self.inverses
            ]
            inverses_product = _multiply(current_inverses)
            return product / inverses_product
