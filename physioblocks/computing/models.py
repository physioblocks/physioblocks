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
Declares the **ModelComponents** and the **Block** base classes along with
objects to hold the **Flux**, **Internal Expressions** and **Saved Quantities**
functions.
"""

from __future__ import annotations

import functools
from collections.abc import Callable
from dataclasses import dataclass, field
from inspect import get_annotations
from typing import Any, TypeAlias, get_origin

import numpy as np
from numpy.typing import NDArray

from physioblocks.computing.quantities import Quantity

SystemFunction: TypeAlias = Callable[..., np.float64 | NDArray[np.float64]]
"""Type alias for functions composing the system"""


@dataclass
class Expression:
    """Expression(size:int, expr_func: SystemFunction, expr_gradients: Mapping[str, SystemFunction] = {})
    Store function computing numerical values for terms in the models with the function
    result size.

    Optionally, it can define a set of function to compute the partial derivatives
    for a set of variables.

    Example
    ^^^^^^^

    .. code:: python

        def f1(x1, x2):
            return 0.5 * x1 + 0.8 * x2

        def df1_dx1(x1, x2):
            return 0.5

        def df1_dx2(x1, x2):
            return 0.8

        expression_f1 = Expression(
            1, # size
            f1, # expression function
            {
                "x1": df1_dx1,
                "x2": df1_dx2,
            } # expressions partial derivatives
        )
    """  # noqa: E501

    size: int
    """Size of the result of the function"""

    expr_func: SystemFunction
    """Function to compute the numerical value"""

    expr_gradients: dict[str, SystemFunction] = field(default_factory=dict)
    """
    Collection of functions to compute the derivatives of the expression for
    variables
    """

    def __eq__(self, value: Any) -> bool:
        return bool(
            isinstance(value, Expression)
            and (
                self.size == value.size
                and self.expr_func == value.expr_func
                and self.expr_gradients == value.expr_gradients
            )
        )


class ExpressionDecorator:
    """
    Base class for expression decorators.

    This is a helper that defines expressions decorating methods in a model or block
    class.
    """

    expression: Expression
    """The expression resulting from decorators declarations"""

    def __init__(
        self,
        wrapped_function: Callable[..., Any],
    ):
        """
        :param wrapped_function: The decorated expression function
        :type wrapped_function: Callable
        """
        self.expression = Expression(0, wrapped_function)
        self._terms: list[tuple[str, int, int]] = []
        functools.update_wrapper(self, wrapped_function)

    def register_term(
        self,
        term_name: str,
        term_size: int,
        term_index: int,
    ) -> None:
        """
        Register a new term to the expression decorator

        :param term_name: the term local name.
        :type term_name: str

        :param term_size: The size of the term
        :type term_size: int

        :param term_index: The start index of the term in the expression
        :type term_index: int
        """
        self.expression.size += term_size
        self._terms.append((term_name, term_size, term_index))

    @property
    def terms(self) -> list[tuple[str, int, int]]:
        """
        Get the terms described by the expression.

        :return: list of terms description
        :rtype: list[[tuple[str, int, int]]]
        """
        return self._terms.copy()

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return self.expression.expr_func(*args, **kwargs)

    def partial_derivative(
        self, variable_name: str
    ) -> Callable[..., Callable[..., Any]]:
        """
        Declares a flux partial derivative.

        :param variable_name: the variable local name.
        :type variable_name: str
        """

        def _register(wrapped: Callable[..., Any]) -> Callable[..., Any]:
            self.expression.expr_gradients[variable_name] = wrapped
            return wrapped

        return _register


def _check_expression_decorator_type(
    wrapped_function: Any, new_decorator_type: type[ExpressionDecorator]
) -> None:
    if (
        isinstance(wrapped_function, ExpressionDecorator) is True
        and isinstance(wrapped_function, new_decorator_type) is False
    ):
        raise ValueError(
            str.format(
                "Can not decorate a function of an other type. "
                "Current type is {0}, new type is {1}.",
                type(wrapped_function),
                new_decorator_type,
            )
        )


class InternalEquationDecorator(ExpressionDecorator):
    """
    Define a decorator that identifies internal equation expressions.
    """

    pass


def declares_internal_equation(
    variable_name: str, size: int = 1, starting_index: int = 0
) -> Callable[..., InternalEquationDecorator]:
    """
    Declares a internal equation expression.

    Once the internal equation function is declared, partial derivatives can be added
    using the function name and the local variable name for the partial derivative.

    :param variable_name: the variable name on which the expression provides a dynamic.
    :type variable_name: str

    :param size: the size of the equation. Default is 1
    :type size: int

    :param starting_index: the starting index of the equation line matching the
      variable. Default is 0
    :type starting_index: int

    :raises ValueError: Raises a ValueError if the function is already decorated with
      an expression decorator of an other type.

    Example
    ^^^^^^^

    .. code:: python

        @dataclass
        class SimpleModel(ModelComponent):

            x: Quantity
            a: Quantity

            @declares_internal_equation("x")
            def residual(self):
                return x.new**2 - a.current

            @flux_1.partial_derivative("x")
            def dresidual_dx(self):
                return 2.0 * x.new
    """

    def _create_internal_equation_decorator(
        wrapped: Callable[..., Any],
    ) -> InternalEquationDecorator:
        _check_expression_decorator_type(wrapped, InternalEquationDecorator)

        decorated = (
            wrapped
            if isinstance(wrapped, InternalEquationDecorator)
            else InternalEquationDecorator(wrapped)
        )
        decorated.register_term(variable_name, size, starting_index)
        return decorated

    return _create_internal_equation_decorator


class SavedQuantityDecorator(ExpressionDecorator):
    """
    Define a decorator that identifies saved quantities expressions.
    """

    pass


def declares_saved_quantity(
    quantity_name: str, size: int = 1, starting_index: int = 0
) -> Callable[..., SavedQuantityDecorator]:
    """
    Declares a saved quantity expression.

    :param quantity_name: the local quantity name.
    :type quantity_name: str

    :param size: the size of the expression. Default is 1
    :type size: int

    :param starting_index: the starting index of the expression in the function.
      Default is 0
    :type starting_index: int

    :raises ValueError: Raises a ValueError if the function is already decorated with
      an expression decorator of an other type.

    Example
    ^^^^^^^

    .. code:: python

        @dataclass
        class SimpleModel(ModelComponent):

            a: Quantity
            b: Quantity

            @declares_saved_quantity("a + b")
            def sum(self):
                return a.current + b.current
    """

    def _create_saved_quantity_decorator(
        wrapped: Callable[..., Any],
    ) -> SavedQuantityDecorator:
        _check_expression_decorator_type(wrapped, SavedQuantityDecorator)

        decorator = (
            wrapped
            if isinstance(wrapped, SavedQuantityDecorator)
            else SavedQuantityDecorator(wrapped)
        )
        decorator.register_term(quantity_name, size, starting_index)

        return decorator

    return _create_saved_quantity_decorator


@dataclass(frozen=True)
class TermDefinition:
    """Describe Terms defined in an :class:`~physioblocks.computing.models.Expression`.

    An :class:`~physioblocks.computing.models.Expression` object can define several
    **Terms**.

    Example
    ^^^^^^^

    .. code:: python

        def vector_3d(x1, x2, x3):
            return [x1, x2, x3]

        expression_vector = Expression(
            3, # size
            vector_3d # expression function
        )

        x1_term = Term(
            "x1", # id
            1, # term size
            0 # starting index in vector expression
        )

        x2_term = Term(
            "x2", # id
            1, # term size
            1 # starting index in vector expression
        )

        x3_term = Term(
            "x3", # id
            1, # term size
            2 # starting index in vector expression
        )
    """

    term_id: str
    """Term id"""

    size: int
    """Term size"""

    index: int = 0
    """Starting line of the term index in its expression"""

    def __eq__(self, value: Any) -> bool:
        return isinstance(value, TermDefinition) and self.term_id == value.term_id


@dataclass(frozen=True)
class ExpressionDefinition:
    """ExpressionDefinition(expression: Expression, terms: list[TermDefinition] = [])

    Holds an :class:`~physioblocks.computing.models.Expression` and
    the :class:`~physioblocks.computing.models.TermDefinition` couple.

    Example
    ^^^^^^^

    .. code:: python

        # Expression Definition for the example above:
        >>> definition = ExpressionDefinition(
            expression_vector,
            [
                x1_term,
                x2_term,
                x3_term
            ]
        )
    """

    expression: Expression
    """The expression"""

    terms: list[TermDefinition] = field(default_factory=list)
    """The expressed Terms"""

    @property
    def valid(self) -> bool:
        """Check if the definition is complete, meaning a term is
        associated with each line of the expression and terms do not
        overlap.

        :return: True if the definition is valid, False otherwise
        :rtype: bool


        .. code ::

            # From example above
            >>> definition = ExpressionDefinition(
                expression_vector,
                [
                    x1_term,
                    x2_term,
                    x3_term
                ]
            )
            >>> definition.valid  # True

            >>> overlapping_definition = ExpressionDefinition(
                expression_vector,
                [
                    x1_term,
                    x2_term,
                    x3_term,
                    x1_term # overlapping term on index 0
                ]
            )
            >>> overlapping_definition.valid  # False

            >>> incomplete_definition = ExpressionDefinition(
                expression_vector,
                [
                    x1_term,
                    # missing index 1 term
                    x3_term
                ]
            )
            >>> incomplete_definition.valid  # False

        """
        used_indexes = []
        for term in self.terms:
            for i in range(term.index, term.index + term.size):
                if i in used_indexes:
                    return False
                used_indexes.append(i)

        return len(used_indexes) == self.expression.size and 0 in used_indexes

    def get_term(self, index: int) -> TermDefinition:
        """Get term starting in expression at the given index

        :param index: the first index of the term in the expression.
        :type index: int

        :return: the term definition
        :rtype: TermDefinition

        .. code ::

            # From example above
            >>> definition = ExpressionDefinition(
                expression_vector,
                [
                    x1_term,
                    x2_term,
                    x3_term
                ]
            )
            >>> definition.get_term(0)  # x1_term
            >>> definition.get_term(1)  # x2_term
            >>> definition.get_term(2)  # x3_term

        """
        for term in self.terms:
            if term.index == index:
                return term

        raise KeyError(
            str.format("No term starts at index {0} in expression, {1}", index, self)
        )


ExpressionsCollection: TypeAlias = dict[str, list[ExpressionDefinition]]
"""
Type alias for a collection of expressions.
Keys are the expression types as strings.
Values are a tuple defining the actual expression and a list of Term Definitions it
expresses.
"""


class ModelComponentMetaClass(type):
    """Meta-class for :class:`~physioblocks.computing.models.ModelComponent`.

    Defines the model **Internal Equations** and **Saved Quantities**
    using :class:`~physioblocks.computing.models.Expression` objects.

    * **Internal Equations** are expressing **Internal Variables** with a residual
      equation.
    * **Saved Quantities** are given with a direct relation

    """

    __INTERNAL_EXPRESSION_KEY = "internals"
    __SAVED_QUANTITIES_EXPRESSION_KEY = "saved_quantities"

    _expressions: ExpressionsCollection

    def __init__(cls, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        cls._expressions = {
            cls.__INTERNAL_EXPRESSION_KEY: [],
            cls.__SAVED_QUANTITIES_EXPRESSION_KEY: [],
        }
        for attr in cls.__dict__.values():
            if isinstance(attr, InternalEquationDecorator):
                for term_name, term_size, term_index in attr.terms:
                    cls.declares_internal_expression(
                        term_name,
                        attr.expression,
                        term_size,
                        term_index,
                    )
            elif isinstance(attr, SavedQuantityDecorator):
                for term_name, term_size, term_index in attr.terms:
                    cls.declares_saved_quantity_expression(
                        term_name,
                        attr.expression,
                        term_size,
                        term_index,
                    )

    @staticmethod
    def __is_quantity_type(type_to_test: Any) -> bool:
        if isinstance(type_to_test, type) is False:
            type_to_test = get_origin(type_to_test)
        return issubclass(type_to_test, Quantity) is True

    @property
    def local_ids(cls) -> list[str]:
        """
        Get local parameters ids of the model.

        Every member of the :class:`~physioblocks.computing.models.ModelComponent`
        annotated with :class:`~physioblocks.computing.quantities.Quantity` type
        has a local id.

        :return: the local ids of the parameters
        :rtype: list[str]

        Example
        ^^^^^^^

        .. code:: python

            @dataclass
            class SimpleModel(metaclass=ModelComponentMetaClass):

                x1: Quantity
                x2: Quantity

            SimpleModel.local_ids # ["x1", "x2"]
        """
        annotations = get_annotations(cls)

        # get the quantities local ids
        local_ids = [
            key
            for key, item in annotations.items()
            if ModelComponentMetaClass.__is_quantity_type(item)
        ]

        # add the saved quantities local ids
        local_ids.extend(
            [
                saved_quantity_expr.term_id
                for saved_quantity_expr in cls.saved_quantities
            ]
        )

        return local_ids

    def _get_all_terms(cls, expr_type: str) -> list[TermDefinition]:
        if expr_type not in cls._expressions:
            return []
        # get terms local id and size for all expressions of the given type
        return [
            term_def
            for expression_def in cls._expressions[expr_type]
            for term_def in expression_def.terms
        ]

    def _has_term_defined(cls, tested_id: str, expr_type: str) -> bool:
        """Get if the given id is defined as the given espresstion type

        :param variable_id: the id to test
        :type variable_id: str

        :param expr_type: the expression type to test
        :type expr_type: str

        :return: True if the id defines an expresseion of the given expression type,
          false otherwise
        :rtype: bool
        """
        return any(term.term_id == tested_id for term in cls._get_all_terms(expr_type))

    def _get_all_expressions(cls, expr_type: str) -> list[ExpressionDefinition]:
        # get all expressions of a type with the matching defined terms
        if expr_type not in cls._expressions:
            return []

        return cls._expressions[expr_type].copy()

    def _get_term_expression(
        cls, term_id: str, expression_type: str
    ) -> tuple[Expression, int, int]:
        """Get the expression, the size and the line index in the expression
        of the given given local term id.

        :param term_id: the term id
        :type term_id: str

        :param expression_type: the type of expression of the term
        :type term_id: str

        :return: the expression, the size and line of the term in the expression.
        :rtype: tuple[Expression, int, int]
        """
        if expression_type not in cls._expressions:
            raise KeyError(str.format("No expressions of type {0}.", expression_type))

        for expr_def in cls._expressions[expression_type]:
            for term_def in expr_def.terms:
                if term_def.term_id == term_id:
                    return (expr_def.expression, term_def.size, term_def.index)

        raise KeyError(str.format("No expression defined for {0}.", term_id))

    def _get_all_terms_ids(cls) -> list[str]:
        # get all expressed terms local ids
        return [
            term_def.term_id
            for expr_type in cls._expressions
            for expr_def in cls._expressions[expr_type]
            for term_def in expr_def.terms
        ]

    def _declares_term_expression(
        cls,
        term_id: str,
        expr: Expression,
        expr_type: str,
        size: int | None = None,
        index: int = 0,
    ) -> None:
        """
        Add a term expression to the model definition.

        :param term_id: the local id of the term.
        :type term_id: str

        :param expr: the associated expression
        :type expr: Expression

        :param expr_type: the expression type
        :type expr_type: str

        :param size: the term size
        :type size: int

        :param index: the starting line index of the term in the expression.
        :type index: str
        """
        if size is None:
            size = expr.size

        if index + size > expr.size:
            raise ValueError(
                str.format(
                    "{0} definition of size {1} starting at index {2} exceed "
                    "expression size {3}",
                    term_id,
                    size,
                    index,
                    expr.size,
                )
            )

        # check if a term with the same id is already used
        if term_id in cls._get_all_terms_ids():
            raise KeyError(
                str.format("An expression is already defined for {0}.", term_id)
            )

        # get existing expression definition
        expression_def = None
        for expr_def in cls._expressions[expr_type]:
            if expr_def.expression is expr:
                expression_def = expr_def
                break

        # if not found, create a new one
        if expression_def is None:
            expression_def = ExpressionDefinition(expr, [])
            cls._expressions[expr_type].append(expression_def)

        # Add the term definition to the expression definition
        expression_def.terms.append(TermDefinition(term_id, size, index))
        expression_def.terms.sort(key=lambda term: term.index)

    def declares_internal_expression(
        cls,
        variable_id: str,
        expr: Expression,
        size: int | None = None,
        index: int = 0,
    ) -> None:
        """
        Declares a :class:`~physioblocks.computing.models.Expression` object
        for an **Internal Equation** of the model.

        :param term_id: the local id of the variable associated with the expression
        :type term_id: str

        :param expr: the associated expression
        :type expr: Expression

        :param size: the term size
        :type size: int

        :param index: the starting line index of the term in the expression.
        :type index: str

        Example
        ^^^^^^^

        .. code:: python

            @dataclass
            class SimpleModel(metaclass=ModelComponentMetaClass):

                x1: Quantity
                a: Quantity
                b: Quantity

                def x1_residual(self):
                    return self.a.current * self.x1.new - b.current

                def dx1_residual_dx1(self):
                    return self.a

            x1_expression = Expression(
                1,
                SimpleModel.x1_residual,
                {
                    "x1": SimpleModel.dx1_residual_dx1
                }
            )
            SimpleModel.declare_internal_expression(
                "x1", # term id
                x1_expression, # term expression
                1, # term size
                0 # Term index in the expression
            )

        """
        cls._declares_term_expression(
            variable_id, expr, cls.__INTERNAL_EXPRESSION_KEY, size, index
        )

    @property
    def internal_variables(cls) -> list[TermDefinition]:
        """Get the :class:`~physioblocks.computing.models.TermDefinition`
        object describing **internal Variables**

        :return: the internal variables term definitions
        :rtype: list[TermDefinition]
        """
        return cls._get_all_terms(cls.__INTERNAL_EXPRESSION_KEY)

    @property
    def internal_expressions(cls) -> list[ExpressionDefinition]:
        """Get the all :class:`~physioblocks.computing.models.Expression` object
        describing **Internal Equations** of the model component.

        :return: the internal equation expressions
        :rtype: list[ExpressionDefinition]
        """
        return cls._get_all_expressions(cls.__INTERNAL_EXPRESSION_KEY)

    def get_internal_variable_expression(
        cls, term_id: str
    ) -> tuple[Expression, int, int]:
        """Get the :class:`~physioblocks.computing.models.Expression` for the given
        **Internal Variable** local name.

        :param term_id: the term id
        :type term_id: str

        :return: the expression, its size and the starting index of the
          term in the expression.
        :rtype: tuple[Expression, int, int]
        """
        return cls._get_term_expression(term_id, cls.__INTERNAL_EXPRESSION_KEY)

    def has_internal_variable(cls, variable_id: str) -> bool:
        """Get if the given name match an **Internal Variable** of the
        model component

        :param variable_id: the id to test
        :type variable_id: str

        :return: True if the id defines an **Internal Variable**, False otherwise
        :rtype: bool
        """
        return cls._has_term_defined(variable_id, cls.__INTERNAL_EXPRESSION_KEY)

    def declares_saved_quantity_expression(
        cls, term_id: str, expr: Expression, size: int | None = None, index: int = 0
    ) -> None:
        """
        Add a **Saved Quantity** :class:`~physioblocks.computing.models.Expression`
        object to the model definition.

        :param term_id: the local id of the term.
        :type term_id: str

        :param expr: the associated expression
        :type expr: Expression

        :param size: the term size
        :type size: int

        :param index: the starting line index of the term in the expression.
        :type index: str

        Example
        ^^^^^^^

        .. code:: python

            @dataclass
            class SimpleModel(metaclass=ModelComponentMetaClass):

                x1: Quantity

                def x1_squared(self):
                    return x1.current * x1.current

            x1_squared_expression = Expression(
                1,
                SimpleModel.x1_squared
            )
            SimpleModel.declares_saved_quantity_expression(
                "x1_squared", # term id
                x1_squared_expression, # term expression
                1, # term size
                0 # Term index in the expression
            )
        """
        cls._declares_term_expression(
            term_id, expr, cls.__SAVED_QUANTITIES_EXPRESSION_KEY, size, index
        )

    @property
    def saved_quantities(cls) -> list[TermDefinition]:
        """Get the saved quantities expressed by the model

        :return: the saved quantities local id and size.
        :rtype: list[tuple[str, int]]
        """
        return cls._get_all_terms(cls.__SAVED_QUANTITIES_EXPRESSION_KEY)

    def has_saved_quantity(cls, saved_quantity_id: str) -> bool:
        """Get if the given id is a saved quantity

        :param saved_quantity_id: the id to test
        :type saved_quantity_id: str

        :return: True if the id defines a saved quantity, false otherwise
        :rtype: bool
        """
        return cls._has_term_defined(
            saved_quantity_id, cls.__SAVED_QUANTITIES_EXPRESSION_KEY
        )

    @property
    def saved_quantities_expressions(cls) -> list[ExpressionDefinition]:
        """Get the all saved quantities expressions

        :return: the saved quantities expressions
        :rtype: list[ExpressionDefinition]
        """
        return cls._get_all_expressions(cls.__SAVED_QUANTITIES_EXPRESSION_KEY)

    def get_saved_quantity_expression(cls, term_id: str) -> tuple[Expression, int, int]:
        """Get the expression for the given saved quantity local id.

        :param term_id: the term id
        :type term_id: str

        :return: the expression, the starting index of the term in the expression
          and its size.
        :rtype: tuple[Expression, int, int]
        """
        return cls._get_term_expression(term_id, cls.__SAVED_QUANTITIES_EXPRESSION_KEY)


class ModelComponent(metaclass=ModelComponentMetaClass):
    """
    Holds parameters and define functions to compute
    **Internal Equations** and **Saved Quantities**.
    """

    def initialize(self) -> None:
        """Override this method to define specific for model initialization."""


class FluxDecorator(ExpressionDecorator):
    """
    Define a decorator that identifies flux functions
    """

    pass


def declares_flux(
    index: int, dof_name: str, size: int = 1
) -> Callable[..., FluxDecorator]:
    """
    Declares a flux function.

    Once the flux expression is declared, partial derivatives can be added using the
    flux function name and the local variable name for the partial derivative.

    :param index: the index of the flux in the block.
    :type index: int

    :param dof_name: the matching dof local name
    :type dof_name: str

    :param size: the size of the flux returned by the function
    :type size: int

    :raises ValueError: Raises a ValueError if the function is already decorated with
      an expression decorator of an other type.


    Example
    ^^^^^^^

    .. code:: python

        @dataclass
        class SimpleBlock(Block):

            q_1: Quantity

            # declares a flux shared at local node 1, where the associated dof has the
            # local name "potential_1"
            @declares_flux(1, "potential_1")
            def flux_1(self):
                return q_1.new

            # associate the following function as the partial derivative of "flux_1" for
            # variable "q_1"
            @flux_1.partial_derivative("q_1")
            def dflux_1_dq_1(self):
                return 1.0

    """

    def _create_flux_decorator(wrapped: Callable[..., Any]) -> FluxDecorator:
        if isinstance(wrapped, ExpressionDecorator) is True:
            raise ValueError(
                str.format(
                    "Function already declares an expression, it can not be a flux."
                )
            )

        decorator = (
            wrapped if isinstance(wrapped, FluxDecorator) else FluxDecorator(wrapped)
        )
        decorator.register_term(dof_name, size, index)

        return decorator

    return _create_flux_decorator


class BlockMetaClass(ModelComponentMetaClass):
    """Meta-class for :class:`~physioblocks.computing.models.Block`.

    Extends :class:`~physioblocks.computing.models.ModelComponentMetaClass` type adding
    **Flux** :class:`~physioblocks.computing.models.Expression` to the model definition.

        * Every **Flux** is expressed toward the outside of the **Block**.
        * Every **Local Nodes** index of the **Block** defines one **Flux**.

    .. note::

        :class:`~physioblocks.computing.models.BlockMetaClass` can also define
        **Internal Equations** and **Saved Quantities**
    """

    _fluxes: dict[int, ExpressionDefinition]
    """Stores the flux expressions at each local nodes"""

    def __init__(cls, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        cls._fluxes = {}
        for attr in cls.__dict__.values():
            if isinstance(attr, FluxDecorator):
                for term_name, _term_size, term_index in attr.terms:
                    cls.declares_flux_expression(term_index, term_name, attr.expression)

    def declares_flux_expression(
        cls, node_index: int, variable_id: str, expr: Expression
    ) -> None:
        """
        Add a flux expression defining a block external relation.

        :param node_index: the local node index where the flux is shared
        :type node_index: int

        :param variable_id: the local id of the variable associated to the node.
        :type variable_id: str

        :param expr: the associated expression
        :type expr: Expression

        Example
        ^^^^^^^

        .. code:: python

            @dataclass
            class SimpleBlock(metaclass=BlockMetaClass):

                q0.new: Quantity

                def flux_0(self):
                    return q0.new


                def dflux_0_dq0(self):
                    return 1.0

            flux_0_expression = Expression(
                1,
                SimpleBlock.flux_0,
                {
                    "q0": SimpleBlock.dflux_0_dq0
                }
            )

            SimpleBlock.declares_flux_expression(
                0, # Local Node index,
                "potential_0", # Associated DOF id
                flux_0_expression, # flux expression
            )
        """

        if node_index in cls.nodes:
            raise ValueError(
                str.format(
                    "Flux {0} is already defined for the block node at index {1}.",
                    cls._fluxes[node_index].expression.expr_func.__name__,
                    node_index,
                )
            )

        cls._fluxes[node_index] = ExpressionDefinition(
            expr, [TermDefinition(variable_id, expr.size)]
        )

    @property
    def nodes(cls) -> list[int]:
        """Get all the local nodes indexes.

        :return: The list of indexes.
        :rtype: list[int]
        """
        return [node_index for node_index in cls._fluxes]

    @property
    def fluxes_expressions(cls) -> dict[int, ExpressionDefinition]:
        """Get all the fluxes expressions in the block with the local node where they
        are shared.

        :return: the fluxes exressions ordered by node index.
        :rtype: dict[int, ExpressionDefinition]
        """
        return cls._fluxes.copy()

    @property
    def external_variables_ids(cls) -> list[str]:
        """
        Get local id of variables defined by the flux connecting to a node in the block.

        :return: a list of all local external variables ids.
        :rtype: list[str]
        """
        return [
            term.term_id for expr_def in cls._fluxes.values() for term in expr_def.terms
        ]


class Block(ModelComponent, metaclass=BlockMetaClass):
    """
    Extends :class:`~physioblocks.computing.models.ModelComponent` and declare
    functions to compute **Flux**.
    """
