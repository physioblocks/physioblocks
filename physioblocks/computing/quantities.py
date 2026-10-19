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

"""Define **Quantities** to represent discretized numeric values."""

import logging
from collections.abc import Callable, Generator, Iterable, Mapping
from dataclasses import dataclass, field
from pprint import pformat
from typing import Any, Generic, TypeVar

import numpy as np
from numpy.typing import NDArray

from physioblocks.base.operators import AbstractBaseOperators
from physioblocks.registers.type_register import register_type

_logger = logging.getLogger()

T = TypeVar("T", np.float64, NDArray[np.float64])


class Quantity(AbstractBaseOperators, Generic[T]):
    """Define discretized values by holding their `n` and `n + 1` states.

    Parameters
    ----------
    value : Any
        Initialization value for the Quantity

    Examples
    --------
    >>> scalar = Quantity(0.5)
    >>> scalar.current, scalar.new
    (0.5, 0.5)

    >>> vector = Quantity([0.1, 0.2, 0.3])
    >>> vector.new
    [0.1, 0.2, 0.3]

    It can also be initialized with numpy arrays

    >>> Quantity(np.ones(3))
    [1, 1, 1]

    Matrixes are flattened when initializing a quantity: it can only
    be a scalar or vector.

    >>> Quantity(np.ones((2, 2)))
    [1, 1, 1, 1]

    See Also
    --------
    QuantityInit
        Initialize the quantities in a :class:`QuantitiesRegistry`
    QuantitiesRegistry
        Reference and update a set of :class:`Quantities <Quantity>`.
    """

    _current: T
    _new: T

    def __init__(self, value: Any):
        if isinstance(value, Quantity):
            self.initialize(value.current)
            self.update(value.new)
        else:
            self.initialize(value)

    @property
    def current(self) -> T:
        """Get the current value (at step `n`) of the quantity.

        Returns
        -------
        np.float64 | NDArray[np.float64]
            The current value

        """
        return self._current

    @property
    def new(self) -> T:
        """Get the new value (at step `n + 1`) of the quantity.

        Returns
        -------
        np.float64 | NDArray[np.float64]
            The new value

        """
        return self._new

    @property
    def size(self) -> int:
        """Get the vector size of the quantity value (or 1 for scalars).

        Returns
        -------
        int
            The vector size of the quantity

        """
        return self.current.size

    def update(self, new: Any) -> None:
        """Set the new value (at step n + 1) of the quantity.

        Parameters
        ----------
        new : Any
            The new value

        Raises
        ------
        ValueError
            Exception raised if the new value and the quantity
            value are not the same size

        Examples
        --------
        >>> q = Quantity(0.5)
        >>> q.current
        0.5
        >>> q.new
        0.5

        >>> q.update(0.6)
        >>> q.current
        0.5
        >>> q.new
        0.6

        """
        new_value = np.array(new) if isinstance(new, Iterable) else np.float64(new)

        if new_value.size != self.size:
            raise ValueError("New value should be the same size as the current value")

        self._new = new_value  # type: ignore

    def initialize(self, value: Any) -> None:
        """Set the current and new value of the quantity.

        Parameters
        ----------
        value : Any
            The value to set

        Raises
        ------
        ValueError
            if the value is an empty array.

        Examples
        --------
        >>> q = Quantity(0.5)
        >>> q.update(0.6)
        >>> q.current
        0.5
        >>> q.new
        0.6

        >>> q.initialize(0.1)
        >>> q.current
        0.1
        >>> q.new
        0.1

        """
        if isinstance(value, Iterable):
            array_value = np.array(value, np.float64).flatten()
            if array_value.size != 0:
                self._current = array_value  # type: ignore
            else:
                raise ValueError(
                    str.format("Quantity size can not be 0. Got: {0}", array_value)
                )
        else:
            self._current = np.float64(value)  # type: ignore

        self._new = self._current

    # Base operators

    @property
    def operation_value(self) -> T:
        """Value used with base operators.

        Operation are allowed and performed on the ``current`` value of the
        quantity.

        Returns
        -------
        Any
            the current value

        Examples
        --------
        Quantity sum is performed on current value.

        >>> q1 = Quantity(1.0)
        >>> q2 = Quantity(2.0)
        >>> q1.update(1.5)
        >>> q1 + q2
        3.0
        >>> q1.initialize(1.5)
        >>> q1 + q2
        3.5

        In place operators call ``initialize`` on the **Quantity**

        >>> q1 = Quantity(1.0)
        >>> q1 += 0.5
        >>> q1.current  # 1.5
        >>> q1.new  # 1.5

        """
        return self.current

    # In place Operations

    def __iadd__(self, other: Any) -> "Quantity[Any]":
        self.initialize(self.current + other)
        return self

    def __isub__(self, other: Any) -> "Quantity[Any]":
        self.initialize(self.current - other)
        return self

    def __imul__(self, other: Any) -> "Quantity[Any]":
        self.initialize(self.current * other)
        return self

    def __imatmul__(self, other: Any) -> "Quantity[Any]":
        self.initialize(self.current @ other)
        return self

    def __itruediv__(self, other: Any) -> "Quantity[Any]":
        self.initialize(self.current / other)
        return self

    def __ifloordiv__(self, other: Any) -> "Quantity[Any]":
        self.initialize(self.current // other)
        return self

    def __imod__(self, other: Any) -> "Quantity[Any]":
        self.initialize(self.current % other)
        return self

    def __ipow__(self, other: Any) -> "Quantity[Any]":
        self.initialize(self.current**other)
        return self


def diff(q: Quantity[T]) -> T:
    r"""
    Compute the difference between the :class:`Quantity` new and current values.

    .. math::

        dq = q^{n + 1} - q^{n}

    Parameters
    ----------
    q : Quantity
        The quantity

    Returns
    -------
    np.float64 | NDArray[np.float64]
        The difference between new and current for the quantity

    Examples
    --------
    >>> q = Quantity(1.0)
    >>> diff(q)
    0.0

    >>> q.update(1.1)
    >>> diff(q)
    0.1

    """
    return q.new - q.current


def mid_alpha(q: Quantity[Any], scheme_time_shift: Any) -> Any:
    r"""Compute the discretized value of a :class:`Quantity` for a shifted time scheme.

    .. math::

        q^{n+\alpha} = (\frac{1}{2} - \alpha) q^{n} + (\frac{1}{2} +
        \alpha) q^{n + 1}

    Parameters
    ----------
    q : Quantity
        the quantity
    scheme_time_shift : float
        :math:`\alpha` the time shift of the scheme.

    Returns
    -------
    np.float64 | NDArray[np.float64]
        the discretized value of the quantity

    Raises
    ------
    ValueError
        If ``scheme_time_shift`` is not a scalar and ``scheme_time_shift`` and ``q``
        are not the same size.

    Examples
    --------
    >>> q = Quantity(1.0)
    >>> q.update(2.0)
    >>> mid_alpha(q, 0.25)
    1.75

    """
    return (0.5 - scheme_time_shift) * q.current + (0.5 + scheme_time_shift) * q.new


def mid_point(q: Quantity[Any]) -> Any:
    r"""Compute the discretized value of a :class:`Quantity` for a mid point scheme.

    .. math::

        q^{n + \frac{1}{2}} = \frac{1}{2} (q^{n} + q^{n + 1})

    Parameters
    ----------
    q : Quantity
        Quantity

    Returns
    -------
    np.float64 | NDArray[np.float64]
        Discretized value of the quantity

    Examples
    --------
    >>> q = Quantity(1.0)
    >>> q.update(2.0)
    >>> mid_point(q)
    1.5

    """
    return 0.5 * (q.current + q.new)


def sign(q: Quantity[np.float64]) -> float:
    """Get 1 if the new value is greater than or equal to the current value, else -1.

    Parameters
    ----------
    q : Quantity
        the quantity

    Returns
    -------
    float
        1 or -1

    """
    return -1.0 if diff(q) < 0.0 else 1.0


QUANTITY_ID = "quantity"
"""Type label for quantities initialization type"""


@dataclass
@register_type(QUANTITY_ID)
class QuantityInit:
    """Initialization values for quantities in a quantity registry.

    Attributes
    ----------
    value : Any
        The quantity initialization value.
    stdev : Any
        The quantity standard deviation. It is set relatively to the quantity magnitude.
        Meaning when the magnitude is for instance 100, a 0.1 stdev represent a
        deviation of 10.
    magnitude : Any
        The quantity magnitude.

    See Also
    --------
    QuantitiesRegistry: Use :class:`QuantityInit` to initialize quantities references
        in registries.

    Configuration
    -------------

    .. code-block:: json

        {
            "type": "quantity",
            "value": "<float>",     // Initial value (optional, default: 0.0)
            "stdev": "<float>",     // Standard deviation (optional, default: 0.0)
            "magnitude": "<float>"  // Magnitude (optional, default: 1.0)
        }

    """

    value: Any = field(default=0.0)
    stdev: Any = field(default=0.0)
    magnitude: Any = field(default=1.0)


class QuantitiesRegistry:
    """Holds quantities references along with their magnitudes and standard deviation.

    It can format or set vectors and matrices representing the quantities values.

    Parameters
    ----------
    quantities : dict[str, QuantityInit] | None
        Initial values and names for the quantities. Default is empty.


    See Also
    --------
    Quantity: stored references.
    QuantityInit: for registry initialization.
    """

    _quantities: dict[str, Quantity[Any]]
    _magnitudes: dict[str, float | list[float]]
    _stdevs: dict[str, float | list[float]]
    _indexes: dict[str, int]

    def __init__(self, quantities: dict[str, QuantityInit] | None = None) -> None:
        if quantities is None:
            quantities = {}

        self._quantities = {}
        self._magnitudes = {}
        self._stdevs = {}
        self._indexes = {}
        self._size = 0

        for qty_id, qty in quantities.items():
            self.add_quantity(qty_id, qty.value, qty.magnitude, qty.stdev)

    @property
    def size(self) -> int:
        """Get the size of the vector representing quantities.

        Returns
        -------
        int
            the size of the quantities.

        """
        return self._size

    @property
    def quantities(self) -> dict[str, Quantity[Any]]:
        """Get a mapping of the quantities and their name.

        Returns
        -------
        dict[str, Quantity]
            the quantities names and values.

        """
        return self._quantities.copy()

    @property
    def sorted_names(self) -> list[str]:
        """Get the quantities names in their index order.

        Returns
        -------
        list[str]
            a list of the quantities names.

        """
        return [
            name
            for name, _index in sorted(self.indexes.items(), key=lambda index: index[1])
        ]

    @property
    def magnitudes(self) -> dict[str, Any]:
        """Get a mapping of the quantities names and magnitudes.

        Returns
        -------
        dict[str, Any]
            the quantities names and magnitudes.

        """
        return self._magnitudes.copy()

    @property
    def stdevs(self) -> dict[str, Any]:
        """Get a mapping of the quantities names and stdevs.

        Returns
        -------
        dict[str, Any]
            the quantities names and stdevs.

        """
        return self._stdevs.copy()

    @property
    def vector(self) -> NDArray[np.float64]:
        """Get the vector of the ordered ``new`` values of the quantities.

        Returns
        -------
        NDArray[np.float64]
            a vector representing the quantities

        """
        result = np.zeros(self.size)
        for quantity_id, quantity in self._quantities.items():
            quantity_index = self._indexes[quantity_id]
            result[quantity_index : quantity_index + quantity.size] = quantity.new
        return result

    @property
    def magnitudes_vector(self) -> NDArray[np.float64]:
        """Get a vector of the ordered quantities magnitudes.

        Returns
        -------
        NDArray[np.float64]
            a vector representing the quantities magnitudes.

        """
        if len(self._quantities) > 0:
            return np.concatenate(
                [self._magnitudes[quantity_id] for quantity_id in self._quantities],
                axis=None,
            )
        else:
            return np.array([])

    @magnitudes_vector.setter
    def magnitudes_vector(self, vector: NDArray[np.float64]) -> None:
        """Set a vector of the ordered quantities magnitudes.

        Parameters
        ----------
        vector : NDArray[np.float64]
            a vector representing the quantities magnitudes.

        """
        magnitudes = {
            qty_id: vector[index : index + self.quantities[qty_id].size]
            for qty_id, index in self.indexes.items()
        }
        self.set_magnitudes(magnitudes)

    @property
    def stdevs_vector(self) -> NDArray[np.float64]:
        """Get a vector of the ordered quantities stdevs.

        Returns
        -------
        NDArray[np.float64]
            a vector representing the quantities stdevs.

        """
        if len(self._quantities) > 0:
            return np.concatenate(
                [self._stdevs[quantity_id] for quantity_id in self._quantities],
                axis=None,
            )
        else:
            return np.array([])

    @stdevs_vector.setter
    def stdevs_vector(self, vector: NDArray[np.float64]) -> None:
        """Set a vector of the ordered quantities stdevs.

        Parameters
        ----------
        vector : NDArray[np.float64]
            a vector representing the quantities stdevs.

        """
        stdevs = {
            qty_id: vector[index : index + self.quantities[qty_id].size]
            for qty_id, index in self.indexes.items()
        }
        self.set_stdevs(stdevs)

    @property
    def indexes(self) -> dict[str, int]:
        """Get a mapping of the quantity indexes with their names.

        Returns
        -------
        dict[str, int]
            the indexes matching their quantities ids

        """
        return self._indexes.copy()

    def get_quantity_size(self, quantity_id: str) -> int:
        """Get the size of the quantity with the given name.

        Parameters
        ----------
        quantity_id : str
            the quantity name

        Returns
        -------
        int
            the size of the quantity

        """
        return self._quantities[quantity_id].size

    def get_quantity_id(self, quantity_index: int) -> str:
        """Get the name of the quantity starting at the given index.

        Parameters
        ----------
        quantity_index : int
            the quantity index

        Returns
        -------
        str
            the quantity id

        Raises
        ------
        KeyError
            if no quantity is found at the given index.

        """
        index = 0
        quantity_id_iterator = (quantity_id for quantity_id in self._quantities)
        quantity_id = next(quantity_id_iterator, None)

        while index != quantity_index and quantity_id is not None:
            index += self._quantities[quantity_id].size
            quantity_id = next(quantity_id_iterator, None)

        if quantity_id is not None:
            return quantity_id

        raise KeyError(str.format("No quantity at index {0}", quantity_index))

    def __array__(self, *args: Any, **kwargs: Any) -> NDArray[Any]:
        return np.array(self.vector, *args, **kwargs)

    def __getitem__(self, quantity_id: str) -> Quantity[Any]:
        """Get the registered quantity.

        Parameters
        ----------
        quantity_id : str
            the quantity id.

        Returns
        -------
        Quantity
            the quantity

        Raises
        ------
        KeyError
            if no quantity is registered with the given id.

        """
        if quantity_id in self._quantities:
            return self._quantities[quantity_id]

        raise KeyError(f"No quantity named {quantity_id}.")

    def get(self, key: str) -> Quantity[Any] | None:
        """
        Get the quantity registered with the given key.

        Return ``None`` if the key is not registered.

        Parameters
        ----------
        key : str
            the quantity key

        Returns
        -------
        Quantity | None
            the quantity or None

        """
        return self._quantities.get(key)

    def update(self, mapping: Mapping[str, Any]) -> None:
        """Update the quantities with the values provided in the mapping.

        New quantities in the mapping are added to the collection while existing
        quantities are initialized to the given value.

        Parameters
        ----------
        mapping : Mapping[str, Any]
            the values to update the current collection.

        """
        for key, val in mapping.items():
            self.__setitem__(key, val)

    def __setitem__(self, quantity_id: str, value: Any) -> None:
        """Set the quantity reference in the collection.

        Parameters
        ----------
        quantity_id : str
            the quantity name.
        value : Any
            the quantity value.

        Raises
        ------
        ValueError
            If the value size does not match the quantity size.

        """
        if quantity_id not in self._quantities:
            self.add_quantity(quantity_id, value)

        if quantity_id in self._quantities:
            if np.asarray(value).size != self._quantities[quantity_id].size:
                raise ValueError(
                    f"Expected size {self._quantities[quantity_id].size} \
                    for quantity {quantity_id}, got {np.asarray(value).size}."
                )
            else:
                self._quantities[quantity_id].initialize(value)

    def __iter__(self) -> Generator[str, None, None]:
        """Iterate on the quantity names.

        Yields
        ------
        str
            the quantity names

        """
        yield from self._quantities

    def __contains__(self, key: str) -> bool:
        """Check if the key is registered.

        Parameters
        ----------
        key : str
            The key to test

        Returns
        -------
        bool
            True if the key is registered.
        """
        return key in self._quantities

    def __str__(self) -> str:
        printable_dict: dict[str, Any] = {}
        printable_dict["Quantities"] = {
            self._indexes[quantity_id]: (
                f"{quantity_id}: size {quantity.size}, \
                magnitude: {self._magnitudes[quantity_id]}, \
                stdev: {self._stdevs[quantity_id]}"
            )
            for quantity_id, quantity in self._quantities.items()
        }
        return pformat(printable_dict, indent=2, compact=False)

    def update_vector(self, x: NDArray[np.float64]) -> None:
        """Update the ``new`` values of the quantities vector.

        Parameters
        ----------
        x : NDArray[np.float64]
            the vector to set.

        Raises
        ------
        ValueError
            Raise a ValueError when x and the quantity vector sizes don't match.

        """
        self.__change_vector(Quantity.update, x)

    def reset_vector(self) -> None:
        """Set the new values to the current values of the quantities vector."""
        for quantity in self._quantities.values():
            quantity.initialize(quantity.current)

    def set_vector(self, x: NDArray[np.float64]) -> None:
        """Set the ``new`` and ``current`` values with the given vector.

        Parameters
        ----------
        x : NDArray[np.float64]
            the vector to set.

        Raises
        ------
        ValueError
            if ``x`` and the quantities vector sizes don't match.

        """
        self.__change_vector(Quantity.initialize, x)

    def __change_vector(
        self, func: Callable[[Quantity[Any], Any], None], x: NDArray[np.float64]
    ) -> None:
        if x.size != self.size:
            raise ValueError(
                f"Provided vector size {x.size} does not match quantities "
                f"vector size {self.size}."
            )
        indexes = self.indexes
        for quantity_id, quantity in self._quantities.items():
            quantity_index = indexes[quantity_id]
            # TODO: remove case for size 1 unit test both case
            if quantity.size == 1:
                # assign scalar value
                func(quantity, x[quantity_index])
            else:
                # assign vector value
                quantity_part = x[quantity_index : quantity_index + quantity.size]
                func(quantity, quantity_part)

    @staticmethod
    def __initialize_dict_value(
        quantity_id: str,
        quantity_size: int,
        mapping: dict[str, float | list[float]],
        value: Any | None,
        default_value: float,
    ) -> None:
        if value is None:
            value = (
                default_value if quantity_size == 1 else [default_value] * quantity_size
            )

        if quantity_size == 1 and isinstance(value, float):
            mapping[quantity_id] = value
        elif isinstance(value, float):
            mapping[quantity_id] = [value] * quantity_size
        elif isinstance(value, list) and len(value) == quantity_size:
            mapping[quantity_id] = value
        else:
            raise ValueError("Quantity and value sizes mismatch.")

    def add_quantity(
        self, quantity_id: str, value: Any, magnitude: Any = None, stdev: Any = None
    ) -> None:
        """Add a quantity to the collection.

        If the provided value is a quantity, register the reference.
        Otherwise, a new quantity is created from the provided value.

        Parameters
        ----------
        quantity_id : str
            the name of the quantity
        value : Any
            the initialization value for the quantity.
        magnitude : Any
            the quantity magnitude. Default is 1.0.
        stdev : Any
            the quantity stdev. Default is 0.0.

        Raises
        ------
        KeyError
            If the quantity name is already registered.
        ValueError
            If the magnitude or stdev size is incoherent with the quantity size
        """
        if quantity_id in self:
            raise KeyError(f"{quantity_id} is already registered.")

        quantity = value if isinstance(value, Quantity) else Quantity(value)
        self._quantities[quantity_id] = quantity

        # initialize magnitude and stdev
        QuantitiesRegistry.__initialize_dict_value(
            quantity_id, quantity.size, self._magnitudes, magnitude, 1.0
        )
        QuantitiesRegistry.__initialize_dict_value(
            quantity_id, quantity.size, self._stdevs, stdev, 0.0
        )
        self._indexes[quantity_id] = self.size
        self._size += quantity.size

    def _rebuild_indexes(self) -> None:
        self._size = 0
        for quantity_id, quantity in self._quantities.items():
            self._indexes[quantity_id] = self._size
            self._size += quantity.size

    def remove_quantity(self, quantity_id: str) -> None:
        """Remove a quantity from the collection.

        Parameters
        ----------
        quantity_id : str
            the name of the quantity

        """
        if quantity_id in self._quantities:
            self._quantities.pop(quantity_id)

        if quantity_id in self._magnitudes:
            self._magnitudes.pop(quantity_id)

        if quantity_id in self._stdevs:
            self._stdevs.pop(quantity_id)

        if quantity_id in self._indexes:
            self._indexes.pop(quantity_id)
            self._rebuild_indexes()

    def __set_mapping_values(
        self, values: dict[str, Any], target_mapping: dict[str, Any]
    ) -> None:
        if set(values.keys()).issubset(self._quantities.keys()) is False:
            difference = set(values.keys()).difference(self._quantities.keys())
            raise KeyError(
                str.format("Collection has no quantities named {0}.", difference)
            )

        mismatch_ids = [
            quantity_id
            for quantity_id in values
            if (
                isinstance(values[quantity_id], float)
                and self._quantities[quantity_id].size != 1
            )
            or (
                isinstance(values[quantity_id], list)
                and self._quantities[quantity_id].size != len(values[quantity_id])
            )
        ]

        if len(mismatch_ids) > 0:
            raise ValueError(f"Quantities and values size mismatch for {mismatch_ids}.")

        target_mapping.update(values)

    def set_magnitudes(self, magnitudes: dict[str, Any]) -> None:
        """Set the quantities magnitude with a mapping.

        Parameters
        ----------
        magnitudes : dict[str, Any]
            the quantities magnitudes

        Raises
        ------
        KeyError
            if one or more of the magnitude parameters key is not in the collection.
        ValueError
            if one or more of the magnitude size is not coherent with the quantity size.

        """
        self.__set_mapping_values(magnitudes, self._magnitudes)

    def set_stdevs(self, stdevs: dict[str, Any]) -> None:
        """Set the quantities stdev with a mapping.

        Parameters
        ----------
        stdevs : dict[str, Any]
            the quantities stdevs to set

        Raises
        ------
        KeyError
            if one or more of the stdev parameters key is not in the collection.
        ValueError
            if one or more of the stdev size is not coherent with the quantity size

        """
        self.__set_mapping_values(stdevs, self._stdevs)
