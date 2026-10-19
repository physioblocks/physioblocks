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

"""Define a register to hold :class:`~.SavedQuantities` during the simulation."""

from __future__ import annotations

from collections.abc import Generator, ItemsView, ValuesView
from typing import Any

from physioblocks.computing.models import Expression, ModelComponent
from physioblocks.computing.quantities import Quantity


class SavedQuantities:
    """Register holding saved quantities."""

    _saved_quantities: dict[str, Quantity[Any]]
    _quantities_expressions: dict[str, tuple[Expression, ModelComponent, int, int]]

    def __init__(self) -> None:
        self._saved_quantities = {}
        self._quantities_expressions = {}

    def __contains__(self, quantity_id: str) -> bool:
        return quantity_id in self._saved_quantities

    def __getitem__(self, quantity_id: str) -> Quantity[Any]:
        return self._saved_quantities[quantity_id]

    def items(self) -> ItemsView[str, Quantity[Any]]:
        """
        Get a view on saved quantities key-value pairs.

        Returns
        -------
        ItemsView[str, Quantity[Any]]
            the saved quantities key and value.
        """
        return self._saved_quantities.items()

    def values(self) -> ValuesView[Quantity[Any]]:
        """
        Get a view on SavedQuantity values.

        Returns
        -------
        ValuesView[Quantity[Any]]
            the saved quantities
        """
        return self._saved_quantities.values()

    def __iter__(self) -> Generator[str, None, None]:
        yield from self._saved_quantities

    def update(self) -> None:
        """Update all saved quantities values."""
        for quantity_id, (
            expression,
            model,
            size,
            index,
        ) in self._quantities_expressions.items():
            if size == 1:
                self._saved_quantities[quantity_id].initialize(
                    expression.expr_func(model)
                )
            else:
                self._saved_quantities[quantity_id].initialize(
                    expression.expr_func(model)[index : index + size]  # type: ignore
                )

    def register(
        self,
        quantity_id: str,
        expression: Expression,
        model: ModelComponent,
        size: int,
        index: int,
    ) -> None:
        """Register a **Saved Quantity** with its expression and model.

        Parameters
        ----------
        quantity_id : str
            the global saved quantity name
        expression : Expression
            the expression to use for the quantity
        model : ModelComponent
            the model declaring the expression
        size : int
            the size of the saved quantity
        index : int
            the start index of the saved quantity in the expression result

        """
        self._quantities_expressions[quantity_id] = (expression, model, size, index)
        # initialise quantity to 0
        init_value = [0.0] * size if size > 1 else 0.0
        self._saved_quantities[quantity_id] = Quantity(init_value)

    def unregister(self, quantity_id: str) -> None:
        """Unregister a saved quantity.

        Parameters
        ----------
        quantity_id : str
            the quantity global name to unregister

        """
        self._saved_quantities.pop(quantity_id)
        self._quantities_expressions.pop(quantity_id)
