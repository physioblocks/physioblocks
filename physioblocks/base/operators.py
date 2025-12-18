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

"""Define base classe to provide generic base operators"""

from abc import ABC, abstractmethod
from typing import Any

import numpy as np
from numpy.typing import NDArray


class AbstractBaseOperators(ABC):
    """Base class defining behaviors for common operators

    The derived classes should implement the :attr:`operation_value` property
    to return the attribute of the class that will be used with base
    operators.
    """

    @property
    @abstractmethod
    def operation_value(self) -> Any:
        """
        Overwrite in derived class to return the value used by the
        class for the base operators.
        """
        raise NotImplementedError(
            str.format(
                "{0} is not implemented in {1} class.",
                AbstractBaseOperators.operation_value.__name__,
                type(self),
            )
        )

    # Convertion

    def __float__(self) -> float:
        return float(self.operation_value)

    def __array__(
        self, dtype: type | None = None, copy: bool | None = None
    ) -> NDArray[Any]:
        return np.asarray(self.operation_value, dtype=dtype, copy=copy)

    # Compare

    # Equality
    def __eq__(self, other: Any) -> bool:
        compared_value = (
            other.operation_value if isinstance(other, type(self)) else other
        )
        return bool(self.operation_value == compared_value)

    # Greater
    def __ge__(self, other: Any) -> bool:
        if isinstance(other, type(self)):
            return bool(self.operation_value >= other.operation_value)
        return bool(self.operation_value >= other)

    def __gt__(self, other: Any) -> bool:
        if isinstance(other, type(self)):
            return bool(self.operation_value > other.operation_value)
        return bool(self.operation_value > other)

    # Lesser
    def __le__(self, other: Any) -> bool:
        if isinstance(other, type(self)):
            return bool(self.operation_value <= other.operation_value)
        return bool(self.operation_value <= other)

    def __lt__(self, other: Any) -> bool:
        if isinstance(other, type(self)):
            return bool(self.operation_value < other.operation_value)
        return bool(self.operation_value < other)

    # Base Operations

    # Sum
    def __add__(self, other: Any) -> Any:
        if isinstance(other, type(self)):
            return self.operation_value + other.operation_value
        return self.operation_value + other

    def __radd__(self, other: Any) -> Any:
        return other + self.operation_value

    # Subtraction
    def __sub__(self, other: Any) -> Any:
        if isinstance(other, type(self)):
            return self.operation_value - other.operation_value
        return self.operation_value - other

    def __rsub__(self, other: Any) -> Any:
        return other - self.operation_value

    # Oposite
    def __neg__(self) -> Any:
        return -self.operation_value

    # Multiplication
    def __mul__(self, other: Any) -> Any:
        if isinstance(other, type(self)):
            return self.operation_value * other.operation_value
        return self.operation_value * other

    def __rmul__(self, other: Any) -> Any:
        return other * self.operation_value

    # MatMul
    def __matmul__(self, other: Any) -> Any:
        if isinstance(other, type(self)):
            return self.operation_value @ other.operation_value
        return self.operation_value @ other

    def __rmatmul__(self, other: Any) -> Any:
        return other @ self.operation_value

    # Division
    def __truediv__(self, other: Any) -> Any:
        if isinstance(other, type(self)):
            return self.operation_value / other.operation_value
        return self.operation_value / other

    def __rtruediv__(self, other: Any) -> Any:
        return other / self.operation_value

    # Floor Division
    def __floordiv__(self, other: Any) -> Any:
        if isinstance(other, type(self)):
            return self.operation_value // other.operation_value
        return self.operation_value // other

    def __rfloordiv__(self, other: Any) -> Any:
        return other // self.operation_value

    # Modulo
    def __mod__(self, other: Any) -> Any:
        if isinstance(other, type(self)):
            return self.operation_value % other.operation_value
        return self.operation_value % other

    def __rmod__(self, other: Any) -> Any:
        return other % self.operation_value

    # Power
    def __pow__(self, other: Any) -> Any:
        if isinstance(other, type(self)):
            return self.operation_value**other.operation_value
        return self.operation_value**other

    def __rpow__(self, other: Any) -> Any:
        return other**self.operation_value
