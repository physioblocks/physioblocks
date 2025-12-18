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
Define the **State** that holds simulation variables.
"""

from collections.abc import Callable, Generator, Mapping
from pprint import pformat
from typing import Any

import numpy as np
from numpy.typing import NDArray

from physioblocks.computing.quantities import Quantity

# Constant to identity the state in simulation
STATE_NAME_ID = "state"


class State:
    """
    The **State** holds the variables names, quantities and indexes during the
    simulation.

    Variables quantity values can be accessed individually with their names or index,
    or altogether throught the **State Vector**.
    """

    _variables: dict[str, Quantity[Any]]
    """The variables ids and quantities values"""

    def __init__(self) -> None:
        self._variables = {}

    @property
    def size(self) -> int:
        """
        Get the total size of the state.

        :return: the size of the state
        :rtype: int
        """
        return sum([var_qty.size for var_qty in self._variables.values()])

    @property
    def variables(self) -> dict[str, Quantity[Any]]:
        """
        Get a mapping of variables names and quantities.

        :return: the variables names and quantities.
        :rtype: dict[str, Quantity]
        """
        return self._variables.copy()

    @property
    def state_vector(self) -> NDArray[np.float64]:
        """
        Get the vector of the ``new`` values of the state variable quantities.

        :return: the state vector
        :rtype: NDArray[np.float64]
        """
        if len(self._variables) > 0:
            return np.concatenate(
                [var_qty.new for var_qty in self._variables.values()], axis=None
            )
        else:
            return np.array([])

    def __array__(self) -> NDArray[Any]:
        return self.state_vector

    def __getitem__(self, var_id: str) -> Quantity[Any]:
        """
        Get the variable quantity.

        :param var_id: the variable id.
        :type var_id: str

        :return: the variable quantity
        :rtype: Quantity
        """
        if var_id in self._variables:
            return self._variables[var_id]

        raise KeyError(str.format("State has no variable variable named {0}.", var_id))

    def get(self, key: str) -> Quantity[Any] | None:
        """
        Get the variable quantity with the given key,
        or ``None`` if it is not registered.

        :param key: the variable key
        :type key: str

        :return: the variable or None
        :rtype: Quantity | None
        """
        return self._variables.get(key)

    def update(self, mapping: Mapping[str, Any]) -> None:
        """
        Update the state variable quantities with the values provided in the
        mapping.

        .. note::

            New variables in the mapping are added to the state while existing
            variables quantities are initialised to the given value.

        :param mapping: the values to update the state.
        :type mapping: str
        """
        for key, val in mapping.items():
            self.__setitem__(key, val)

    def __setitem__(self, var_id: str, value: Any) -> None:
        """
        Set the variable quantity value.

        :param var_id: the variable name.
        :type var_id: str

        :param value: the variable quant.
        :type var_id: Quantity

        :raises ValueError: Raises a ValueError if the value is not a Quantity
            or the quantity size is incorrect.
        """

        if var_id not in self._variables:
            self.add_variable(var_id, value)

        if var_id in self._variables:
            if np.asarray(value).size != self._variables[var_id].size:
                raise ValueError(
                    str.format(
                        "Expected size {0} for variable {1}, got {2}.",
                        self._variables[var_id].size,
                        var_id,
                        np.asarray(value).size,
                    )
                )
            else:
                self._variables[var_id].initialize(value)

    def __str__(self) -> str:
        state_dict: dict[str, Any] = {}
        state_dict["Variables"] = {
            self.get_variable_index(var_id): (var_id, "size " + str(var_qty.size))
            for var_id, var_qty in self._variables.items()
        }
        return pformat(state_dict, indent=2, compact=False)

    @property
    def indexes(self) -> dict[str, int]:
        """
        Get a mapping of the variables indexes with their names.

        :return: the variables indexes ordered by variables ids
        :rtype: dict[str, int]
        """
        return {var_id: self.get_variable_index(var_id) for var_id in self._variables}

    def get_variable_index(self, variable_id: str) -> int:
        """
        Get the index of the variable with the given name

        :param variable_id: the variable id
        :rtype: str

        :return: the variable index
        :rtype: int
        """

        index = 0
        for key, value in self._variables.items():
            if variable_id == key:
                return index
            else:
                index += value.size

        raise KeyError(
            str.format("State has no variable variable named {0}.", variable_id)
        )

    def get_variable_size(self, var_id: str) -> int:
        """
        Get the size of the variable with the given name.

        :param var_id: the variable id
        :rtype: str

        :return: the size of the variable
        :rtype: int
        """
        return self._variables[var_id].size

    def get_variable_id(self, var_index: int) -> str:
        """
        Get the variable name with the given index.

        :param var_index: the variable index
        :rtype: int

        :return: the variable id
        :rtype: str
        """
        index = 0
        var_id_iterator = (var_id for var_id in self._variables)
        var_id = next(var_id_iterator, None)

        while index != var_index and var_id is not None:
            index += self._variables[var_id].size
            var_id = next(var_id_iterator, None)

        if var_id is not None:
            return var_id

        raise KeyError(str.format("No variable at index {0}", var_index))

    def __iter__(self) -> Generator[str, None, None]:
        """
        Iterate on the variables names in the state.

        :return: the variable ids
        :rtype: str
        """
        yield from self._variables

    def __contains__(self, key: str) -> bool:
        """
        Checks if the key is in the variables names.

        :param key: The key to test
        :rtype: Any
        """
        return key in self._variables

    def update_state_vector(self, x: NDArray[np.float64]) -> None:
        """
        Update the ``new`` values of the state vector quantities,
        with the given vector.

        :param x: the vector to set.
        :type x: NDArray[np.float64]

        :raise ValueError:
          Raise a ValueError when x and the state vector sizes don't match.
        """
        self.__change_state_vector(Quantity.update, x)

    def reset_state_vector(self) -> None:
        """
        Set the new values to the current value of the state vector quantities.
        """
        for variable in self._variables.values():
            variable.initialize(variable.current)

    def set_state_vector(self, x: NDArray[np.float64]) -> None:
        """
        Set the ``new`` and ``current`` values of the state vector quantities
        with the given vector.

        :param x: the vector to set.
        :type x: NDArray[np.float64]

        :raise ValueError:
          Raise a ValueError when x and the state vector sizes don't match.
        """
        self.__change_state_vector(Quantity.initialize, x)

    def __change_state_vector(
        self, func: Callable[[Quantity[Any], Any], None], x: NDArray[np.float64]
    ) -> None:
        # Checks x and state vector have the same size.
        if x.size != self.size:
            raise ValueError(str.format("State vector size does not match state size."))
        indexes = self.indexes
        for var_id, quantity in self._variables.items():
            var_index = indexes[var_id]
            if quantity.size == 1:
                # assign scalar value
                func(quantity, x[var_index])
            else:
                # assign vector value
                quantity_part = x[var_index : var_index + quantity.size]
                func(quantity, quantity_part)

    def add_variable(self, var_id: str, var_value: Any) -> None:
        """
        Add a variable to the state.

        :param var_id: the name of the variable
        :type var_id: str

        :param value: the initial value of the variable.
        :type size: int
        """

        if var_id in self:
            raise KeyError(str.format("{0} is already registered.", var_id))

        quantity = var_value if isinstance(var_value, Quantity) else Quantity(var_value)
        self._variables[var_id] = quantity

    def remove_variable(self, var_id: str) -> None:
        """
        Remove a variable from the state

        :param var_id: the name of the variable to remove.
        :type var_id: str
        """
        # remove the variable
        if var_id in self._variables:
            self._variables.pop(var_id)
