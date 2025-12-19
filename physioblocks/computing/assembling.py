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
Allows to build systems that computes residual and gradient from collections
of functions.
"""

from __future__ import annotations

from dataclasses import dataclass
from pprint import pformat
from typing import Any

import numpy as np
from numpy.typing import NDArray

from physioblocks.computing.models import ModelComponent, SystemFunction


@dataclass
class _EqSystemPart:
    """
    Part of the global equation system.

    It computes a term that can be summed in the global system at the provided index.
    """

    line_index: int
    """Index where to sum the part in the global system"""
    res_part_size: int
    """Number of lines in the result of the residual part function"""
    model_component: ModelComponent
    """The model that holds the data use to compute the residual and gradient part"""
    res_func: SystemFunction
    """The function to compute the residual part"""
    column_index: int
    """Start column index of the gradient part"""
    grad_part_size: int
    """Number of colums in the result of the gradient part function"""
    grad_funcs: dict[int, SystemFunction]
    """A collection of fonctions to compute the gradient part for each variables,
    associated with their column index"""

    def compute_residual_part(self) -> np.float64 | NDArray[np.float64]:
        """
        Compute the residual part numerical value.

        Can be a scalar or vector of size _res_part_size.

        :return: the residual part value
        :rtype: np.float64 | NDArray[np.float64]
        """
        return self.res_func(self.model_component)

    def compute_gradient_part(self) -> NDArray[np.float64]:
        """
        Compute the gradient part numerical value.

        It a matrix of size (_res_part_size, _grad_part_size) to sum in the
        global gradient at index (_index, _min_grad_index).

        The numerical values are evaluated where the gradient functions are provided,
        the remaing values are set to 0.

        :return: the gradient part numerical value
        :rtype: np.float64 | NDArray[np.float64]
        """
        grad_part = np.zeros(
            (self.res_part_size, self.grad_part_size),
        )

        for grad_index in self.grad_funcs:
            gradient_func = self.grad_funcs[grad_index]
            grad_colum_index = grad_index - self.column_index
            grad_part[:, grad_colum_index] += gradient_func(self.model_component)

        return grad_part


def _create_eq_system_part(
    residual_index: int,
    residual_size: int,
    residual_func: SystemFunction,
    gradients_func: dict[int, SystemFunction],
    model_component: ModelComponent,
) -> _EqSystemPart:
    """
    Create an equation system part.

    :param index: the line index where to sum the expression in the global
    system
    :type index: int

    :param residual_size: the size of the result of the residual_func
    :type residual_size: int

    :param residual_func: the function to compute the residual part
    :type residual_func: SystemFunction

    :param gradients_func: the functions to compute the gradients parts associated with
    the index of the variable in the state vector

    :param model_component: the model holding the data needed to compute the expression
    :type model_component: ModelComponent

    :return: an equation system part
    :rtype: _EqSystemPart
    """
    grad_part_size = 0
    min_grad_index = 0
    if len(gradients_func) > 0:
        min_grad_index = min(gradients_func.keys())
        grad_part_size = max(gradients_func) - min_grad_index + 1

    return _EqSystemPart(
        residual_index,
        residual_size,
        model_component,
        residual_func,
        min_grad_index,
        grad_part_size,
        gradients_func,
    )


class EqSystem:
    """
    Global Equation system

    Allows to compute the numerical value of the residual and the gradient
    for a :class:`~physioblocks.description.nets.Net`.

    The system is built from a collection of **System Parts**.
    The parts are summed in a global system to compute the numerical value of
    the residual and the gradient.
    """

    _system_size: int
    """The system size, fixed at system creation"""
    _system_parts: list[_EqSystemPart]
    """The collection of system parts"""

    def __init__(self, size: int):
        """
        EqSystem constructor

        :param size: system fixed size
        :type size: int
        """
        self._system_size = size
        self._system_parts = []

    def __str__(self) -> str:
        """
        Get the equation system string representation.

        :return: the equation system string representation
        :rtype: str
        """

        eq_system_dict = {
            index: [
                (eq_part.res_func.__qualname__, "size " + str(eq_part.res_part_size))
                for eq_part in self._system_parts
                if eq_part.line_index == index
            ]
            for index in range(0, self.system_size)
        }

        return pformat(eq_system_dict, indent=2, compact=False)

    @property
    def system_size(self) -> int:
        """
        Get the system size

        :return: the system size
        :rtype: int
        """
        return self._system_size

    def add_system_part(
        self,
        residual_index: int,
        residual_size: int,
        residual_func: SystemFunction,
        gradients_func: dict[int, SystemFunction],
        parameters: Any,
    ) -> None:
        """add_system_part(self, residual_index: int, residual_size: int, residual_func: SystemFunction, gradients_func: dict[int, SystemFunction], parameters: Any)
        Add an equation system part to the global system.

        :param residual_index:
            the line index where to sum the function in the global system
        :type residual_index: int

        :param residual_size: the size of the result of the residual_func
        :type residual_size: int

        :param residual_func: the function to compute the residual part
        :type residual_func: SystemFunction

        :param gradients_func:
            the functions to compute the gradients parts associated with
            the index of the variable in the state vector

        :param parameters: the parameters needed to compute the SystemFunctions
            (both residual and gradient)
            (should be the same type as the argument of the residual_func and the
            gradients_func input type)
        :type parameters: Any

        :raise ValueError: Raises a ValueError when either the size of the residual
            or the gradient part will exceed the global system size.
        """  # noqa: E501

        part = _create_eq_system_part(
            residual_index, residual_size, residual_func, gradients_func, parameters
        )

        if part.line_index + part.res_part_size > self.system_size:
            raise ValueError("The residual part exceed system size")

        if part.column_index + part.grad_part_size > self.system_size:
            raise ValueError("The gradient part exceed system size")

        self._system_parts.append(part)

    def compute_residual(self) -> NDArray[np.float64]:
        """
        Compute the numerical value of the residual.

        :return: the residual
        :rtype: NDArray[np.float64]
        """

        residual = np.zeros(
            shape=self.system_size,
        )

        for part in self._system_parts:
            residual_part = part.compute_residual_part()
            residual_column_index = part.line_index + part.res_part_size
            residual[part.line_index : residual_column_index] += residual_part

        return residual

    def compute_gradient(self) -> NDArray[np.float64]:
        """
        Compute the numerical value of the gradient.

        :return: the gradient
        :rtype: NDArray[np.float64]
        """
        grad = np.zeros(
            shape=(self.system_size, self.system_size),
        )

        for part in self._system_parts:
            if part.grad_part_size > 0:
                gradient_part = part.compute_gradient_part()
                grad[
                    part.line_index : part.line_index + part.res_part_size,
                    part.column_index : part.column_index + part.grad_part_size,
                ] += gradient_part

        return grad
