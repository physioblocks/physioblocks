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
Define **Quantities** to represent discretized numeric values along with some
convenience functions to handle them.
"""

from collections.abc import Iterable
from typing import Any, Generic, TypeVar

import numpy as np
from numpy.typing import NDArray

from physioblocks.base.operators import AbstractBaseOperators

T = TypeVar("T", np.float64, NDArray[np.float64])


class Quantity(AbstractBaseOperators, Generic[T]):
    """
    Represent discretized values by holding their current and new numeric values.

    Examples
    ^^^^^^^^

    >>> scalar = Quantity(0.5)
    >>> scalar.current == scalar.new  # 0.5

    >>> vector = Quantity([0.1, 0.2, 0.3])
    >>> vector.current == vector.new  # [0.1, 0.2, 0.3]

    It can also be initialized with numpy arrays

    >>> Quantity(np.ones(3))  # [1, 1, 1]

    Matrixes are flattened when initializing a quantity: it can only
    be a scalar or vector.

    >>> Quantity(np.ones((2, 2)))  # [1, 1, 1, 1]
    """

    _current: T
    """Current value (at step n) of the quantity"""

    _new: T
    """New value (at step n + 1) of the quantity"""

    def __init__(self, value: Any):
        """
        Quantity Constructor

        :param value: Initialization value for the Quantity
        :type value: Any
        """
        if isinstance(value, Quantity):
            self.initialize(value.current)
            self.update(value.new)
        else:
            self.initialize(value)

    @property
    def current(self) -> T:
        """
        Get the current value (at step n) of the quantity

        :return: The current value
        :rtype: np.float64 | NDArray[np.float64]
        """
        return self._current

    @property
    def new(self) -> T:
        """
        Get the new value (at step n + 1) of the quantity

        :return: The new value
        :rtype: np.float64 | NDArray[np.float64]
        """
        return self._new

    @property
    def size(self) -> int:
        """
        Get the vector size of the quantity value (or 1 for scalars)

        :return: The vector size of the quantity
        :rtype: int
        """
        return self.current.size

    def update(self, new: Any) -> None:
        """
        Set the new value (at step n + 1) of the quantity

        :param new: The new value
        :type new: Any

        :raise ValueError: Exception raised if the new value and the quantity
            value are not the same size

        Example
        ^^^^^^^

        .. code:: python

            >>> q = Quantity(0.5)
            >>> q.current  # 0.5
            >>> q.new  # 0.5

            >>> q.update(0.6)
            >>> q.current  # 0.5
            >>> q.new  # 0.6
        """
        new_value = np.array(new) if isinstance(new, Iterable) else np.float64(new)

        if new_value.size != self.size:
            raise ValueError("New value should be the same size as the current value")

        self._new = new_value  # type: ignore

    def initialize(self, value: Any) -> None:
        """
        Set the current and new value of the quantity

        :param value: The value to set
        :type value: Any

        Example
        ^^^^^^^

        .. code:: python

            >>> q = Quantity(0.5)
            >>> q.update(0.6)
            >>> q.current  # 0.5
            >>> q.new  # 0.6

            >>> q.initialize(0.1)
            >>> q.current  # 0.1
            >>> q.new  # 0.1
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
        """
        Value used with base operators.

        Direct operation are allowed and performed on the ``current`` value of the
        quantity.

        :return: the current value
        :rtype: Any


        Example
        ^^^^^^^

        .. code:: python

            >>> q1 = Quantity(1.0)
            >>> q2 = Quantity(2.0)
            >>> q1.update(1.5)

            # Quantity sum is performed on current value:
            >>> q1 + q2  # 3.0

            >>> q1.initialise(1.5)
            >>> q1 + q2  # 3.5

        In place operators call ``initialise`` on the **Quantity**

        Example
        ^^^^^^^

        .. code:: python

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
    """
    Compute the difference between the new and the current value of the given
    **Quantity**

    :param q: The quantity
    :type q: Quantity

    :return: The difference betwen new and current for the quantity
    :rtype: np.float64 | NDArray[np.float64]

    Examples
    ^^^^^^^^

    .. code:: python

        >>> q = Quantity(1.0)
        >>> diff(q)  # 0.0

        >>> q.update(1.1)
        >>> diff(q)  # 0.1

    """
    return q.new - q.current


def mid_alpha(q: Quantity[Any], scheme_time_shift: Any) -> Any:
    """
    Compute the discretized value of the Quantity for a shifted time scheme.

    .. math::

        x^{n+\\alpha} = (\\frac{1}{2} - \\alpha) x^{n} + (\\frac{1}{2} +
        \\alpha) x^{n + 1}

    :param q: The quantity
    :type value: Quantity

    :param scheme_time_shift: the time shift of the scheme.
    :type scheme_time_shift: float

    :raise ValueError: If scheme_time_shift is not a scalar,
      exception raised if scheme_time_shift and q are not the same size.

    :return: the discretized value of the quantity
    :rtype: np.float64 | NDArray[np.float64]

    Example
    ^^^^^^^

    .. code:: python

        >>> q = Quantity(1.0)
        >>> q.update(2.0)
        >>> mid_alpha(q, 0.25)  # 1.75
    """
    return (0.5 - scheme_time_shift) * q.current + (0.5 + scheme_time_shift) * q.new


def mid_point(q: Quantity[Any]) -> Any:
    """
    Compute the discretized value of the Quantity for a mid point time scheme

    .. math::

        x^{n + \\frac{1}{2}} = \\frac{1}{2} (x^{n} + x^{n + 1})

    :param q: Quantity
    :type q: Quantity

    :return: Discretized value of the quantity
    :rtype: np.float64 | NDArray[np.float64]

    Example
    ^^^^^^^

    .. code:: python

        >>> q = Quantity(1.0)
        >>> q.update(2.0)
        >>> mid_point(q)  # 1.5
    """
    return 0.5 * (q.current + q.new)


def sign(q: Quantity[np.float64]) -> float:
    """
    Get 1 if the new value is superior to current value,
    -1 othwerwise

    :param q: the quantity
    :type q: Quantity

    :return: 1 or -1
    :rtype: np.float64
    """
    return -1.0 if diff(q) < 0.0 else 1.0
