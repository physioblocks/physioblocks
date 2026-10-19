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

"""Declare configurable functions used during the simulation."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar

from physioblocks.base.operators import AbstractBaseOperators
from physioblocks.computing.quantities import Quantity
from physioblocks.registers.type_register import register_type

INITIALIZATION_FUNCTION_TYPE_ID = "init_function"


@register_type(INITIALIZATION_FUNCTION_TYPE_ID)
@dataclass
class AbstractInitializationFunction(AbstractBaseOperators):
    """Configurable function to initialize simulation parameters.

    Initialization functions are evaluated once, when loading the simulation
    parameters.

    Configuration
    -------------

    .. code-block:: json

        {
            "type": "<initialization function type id>",
            "<str>": "<any>"  // Function parameters
        }

    """

    @property
    def operation_value(self) -> Any:
        """
        Get the value used with the class base operators.

        Returns
        -------
        Any
            the function result.
        """
        return self.eval()

    @abstractmethod
    def eval(self) -> Any:
        """
        Get the function evaluation with the current parameters.

        Returns
        -------
        Any
            the function result.
        """


ABSTRACT_FUNCTION_TYPE_ID = "abstract_function"


@dataclass
@register_type(ABSTRACT_FUNCTION_TYPE_ID)
class AbstractFunction(ABC):
    """Base class for functions that update quantities during the simulation.

    The function parameters are constant during the simulation. The evaluation
    quantities are updated at each time step: they match the ``eval`` method argument
    names with global quantity names.

    Attributes
    ----------
    argument_quantities : dict[str, Quantity[Any]]
        The needed quantities for the function evaluation

    Configuration
    -------------

    .. code-block:: json

        {
            "type": "<function type id>",
            "evaluation_quantities": {  // Global quantity name for each argument of
                "<str>": "<str>"        // the eval method (optional)
            },
            "<str>": "<any>"            // Function parameters
        }

    """

    argument_quantities: dict[str, Quantity[Any]] = field(
        init=False, default_factory=dict
    )

    @abstractmethod
    def eval(self, *args: Any, **kwargs: Any) -> Any:
        """Overwrite this method to compute the function result."""

    def eval_new(self) -> Any:
        """Get the function evaluation for argument quantities new values."""
        arguments = {
            quantity_id: quantity.new
            for quantity_id, quantity in self.argument_quantities.items()
        }
        return self.eval(**arguments)

    def eval_current(self) -> Any:
        """Get the function evaluation for argument quantities current values."""
        arguments = {
            quantity_id: quantity.current
            for quantity_id, quantity in self.argument_quantities.items()
        }
        return self.eval(**arguments)


class AbstractTransformation(AbstractFunction):
    """Base class for quantities transformation."""

    def __init__(self, *args: Any, **kwds: Any) -> None:
        super().__init__(*args, **kwds)

    @abstractmethod
    def eval(self, *args: Any, **kwargs: Any) -> Any:
        """Overwrite this method to compute the transformation result."""

    @abstractmethod
    def eval_inverse(self, *args: Any, **kwargs: Any) -> Any:
        """Overwrite this method to compute the inverse transformation result."""

    def inverse_new(self) -> Any:
        """Get the inverse evaluation for argument quantities new values."""
        arguments = {
            quantity_id: quantity.new
            for quantity_id, quantity in self.argument_quantities.items()
        }
        return self.eval_inverse(**arguments)

    def inverse_current(self) -> Any:
        """Get the inverse evaluation for argument quantities current values."""
        arguments = {
            quantity_id: quantity.current
            for quantity_id, quantity in self.argument_quantities.items()
        }
        return self.eval_inverse(**arguments)


FunctionType = TypeVar("FunctionType", bound=AbstractFunction)

SIMULATION_FUNCTION_TYPE = "function_type"

SIMULATION_FUNCTION_FACTORY_TYPE_ID = "simulation_function"

SIMULATION_FUNCTION_EVALUATION_QUANTITIES = "evaluation_quantities"


@dataclass
@register_type(SIMULATION_FUNCTION_FACTORY_TYPE_ID)
class SimulationFunctionFactory(Generic[FunctionType]):
    """Factory for simulation functions.

    To create the function, the ``create_function`` method needs the
    ``quantities_references`` keys matching the global ids of the
    ``evaluation_quantities`` values.

    The method selects the needed quantities for the function and instantiates it.

    Parameters
    ----------
    function_type : type[FunctionType]
        The type of function to create.
    evaluation_quantities : dict[str, str]
        The updatable quantities references (typically time or state variable
        quantities). Matches the local name in the function and the global name in
        the simulation.
    function_parameters : dict[str, Any]
        The constant function parameters during the simulation
        (typically floats, str, arrays, etc)

    Configuration
    -------------

    The factory is not configured directly: it is created when loading an
    :class:`~.AbstractFunction` configuration, from the function ``type``, its
    ``evaluation_quantities`` and its other items (the function parameters).

    """

    function_type: type[FunctionType]

    evaluation_quantities: dict[str, str]

    function_parameters: dict[str, Any] = field(default_factory=dict)

    def create_function(
        self, quantities_references: dict[str, Quantity[Any]]
    ) -> FunctionType:
        """
        Create a function from factory parameters and the provided quantities.

        The global ids of evaluation quantities are matched with the quantities
        reference keys.

        The ``quantities_references`` parameter can define more quantities than
        necessary, but all the needed ``evaluation_quantities`` should be defined in it.

        Parameters
        ----------
        quantities_references : dict[str, Quantity[Any]]
            the reference values for the evaluation quantities.

        Returns
        -------
        FunctionType
            the resulting function.

        Raises
        ------
        KeyError
            if an evaluation quantity is missing from the quantities references.
        """
        function_quantities = {
            local_id: quantities_references[global_id]
            for local_id, global_id in self.evaluation_quantities.items()
        }
        sim_function = self.function_type(**self.function_parameters)
        sim_function.argument_quantities = function_quantities
        return sim_function
