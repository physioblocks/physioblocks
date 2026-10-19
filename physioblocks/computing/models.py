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

"""Declare classes and methods to describe models."""

from __future__ import annotations

import functools
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from inspect import get_annotations
from types import MethodType
from typing import Any, NamedTuple, TypeAlias, get_origin

import numpy as np
from numpy.typing import NDArray

from physioblocks.computing.quantities import Quantity

ModelFunction: TypeAlias = Callable[..., np.float64 | NDArray[np.float64]]
"""Type alias for functions defining model expressions."""


class Term(NamedTuple):
    """Identify the terms defined in an expression.

    Attributes
    ----------
    term_id : str
        Term id
    term_size : int
        Term size in the expression.
    term_index : int
        Starting line of the term index in the expression

    See Also
    --------
    Expression: an expression can define several terms.
    """

    term_id: str
    term_size: int = 1
    term_index: int = 0

    def __eq__(self, value: Any) -> bool:
        return isinstance(value, Term) and self.term_id == value.term_id


@dataclass
class Expression:
    """Define a function and its partial derivatives for identified terms in the models.

    Attributes
    ----------
    size : int
        Size of the result of the function
    expr_func : ModelFunction
        the expression function
    terms : list[Term]
        The terms defined by the expression
    expr_gradients : dict[str, ModelFunction]
        Collection of functions to compute the derivatives of the expression for
        terms in the expression

    See Also
    --------
    Term: An expression can define several terms.
    ModelFunction: The expression function and partial derivatives type.
    """

    size: int
    expr_func: ModelFunction
    terms: list[Term] = field(default_factory=list)
    expr_gradients: dict[str, ModelFunction] = field(default_factory=dict)

    def __eq__(self, value: Any) -> bool:
        return bool(
            isinstance(value, Expression)
            and (
                self.size == value.size
                and self.expr_func == value.expr_func
                and self.terms == value.terms
                and self.expr_gradients == value.expr_gradients
            )
        )

    @property
    def valid(self) -> bool:
        """Check if the expression definition is complete.

        An expression definition is valid when each line of the
        expression is associated with a term and they don't overlap.

        Returns
        -------
        bool
            `True` if the definition is valid, `False` otherwise
        """
        used_indexes = []
        for term in self.terms:
            for i in range(term.term_index, term.term_index + term.term_size):
                if i in used_indexes:
                    return False
                used_indexes.append(i)

        return len(used_indexes) == self.size and 0 in used_indexes

    def get_term(self, index: int) -> Term:
        """Get term starting at the given index.

        Parameters
        ----------
        index : int
            the first index of the term in the expression.

        Returns
        -------
        Term
            the term definition

        Raises
        ------
        KeyError
            if no term starts at the given index.
        """
        for term in self.terms:
            if term.term_index == index:
                return term

        raise KeyError(
            str.format("No term starts at index {0} in expression, {1}", index, self)
        )


class _ExpressionType(Enum):
    """Expression type enumeration.

    Attributes
    ----------
    INTERNAL_EXPRESSION : int
        Internal expression type id.
    SAVED_QUANTITY_EXPRESSION : int
        Saved quantity expression type id.
    FLUX_EXPRESSION : int
        Flux expression type id.

    """

    INTERNAL_EXPRESSION = 0
    SAVED_QUANTITY_EXPRESSION = 1
    FLUX_EXPRESSION = 2


class ExpressionDecorator:
    """Define decorators to declare terms of an expression.

    Attributes
    ----------
    expression_type : _ExpressionType
        the expression type.
    expression : Expression
        The resulting expression.

    Parameters
    ----------
    expression_type : _ExpressionType
        the expression type.
    wrapped_function : Callable
        the expression function to decorate

    See Also
    --------
    declares_flux : Decorator factory to declare a flux.
    declares_internal_equation : Decorator factory to declare a internal equation.
    declares_saved_quantity : Decorator factory to declare a saved quantity.

    """

    expression_type: _ExpressionType
    expression: Expression

    def __init__(
        self,
        expression_type: _ExpressionType,
        wrapped_function: Callable[..., Any],
    ):
        self.expression_type = expression_type
        self.expression = Expression(0, wrapped_function)
        functools.update_wrapper(self, wrapped_function)

    def register_term(
        self,
        term_name: str,
        term_size: int,
        term_index: int,
    ) -> None:
        """Register a new term to the expression decorator.

        Parameters
        ----------
        term_name : str
            the term local name.
        term_size : int
            The size of the term
        term_index : int
            The start index of the term in the expression
        """
        self.expression.size += term_size
        self.expression.terms.append(Term(term_name, term_size, term_index))
        self.expression.terms.sort(key=lambda term: term.term_index)

    @property
    def terms(self) -> list[Term]:
        """Get the terms described by the expression.

        Returns
        -------
        list[Term]
            list of terms description

        """
        return self.expression.terms.copy()

    def __call__(self, *args: Any, **kwargs: Any) -> Any:  # noqa: D102
        return self.expression.expr_func(*args, **kwargs)

    def __get__(self, instance: Any, owner: type | None = None) -> Any:
        if instance is None:
            return self

        return MethodType(self.expression.expr_func, instance)

    def partial_derivative(
        self, variable_name: str
    ) -> Callable[..., Callable[..., Any]]:
        """Declare a partial derivative of the expression.

        Parameters
        ----------
        variable_name : str
            the variable local name.

        Returns
        -------
        Callable
            the decorated function
        """

        def _register(wrapped: Callable[..., Any]) -> Callable[..., Any]:
            self.expression.expr_gradients[variable_name] = wrapped
            return wrapped

        return _register


def _declare_expression_decorator(
    decorator_type: type[ExpressionDecorator],
    expression_type: _ExpressionType,
    term_id: str,
    term_size: int,
    term_index: int,
) -> Callable[..., ExpressionDecorator]:
    def decorator(
        wrapped: Callable[..., Any] | ExpressionDecorator,
    ) -> ExpressionDecorator:
        decorated: ExpressionDecorator
        if isinstance(wrapped, ExpressionDecorator):
            if wrapped.expression_type != expression_type:
                raise ValueError(
                    f"{wrapped.expression.expr_func.__name__} is already registered as "
                    f"a {wrapped.expression_type.name}."
                )
            else:
                decorated = wrapped
        else:
            decorated = decorator_type(expression_type, wrapped)

        decorated.register_term(term_id, term_size, term_index)
        return decorated

    return decorator


def declares_internal_equation(
    variable_name: str, size: int = 1, starting_index: int = 0
) -> Callable[..., ExpressionDecorator]:
    """Declare an internal equation expression in the model.

    Once the internal equation function is declared, declare partial derivatives
    with a decorator and the local variable name of the partial derivative.

    Parameters
    ----------
    variable_name : str
        The variable name on which the expression provides a dynamic.
    size : int
        The size of the equation. Default is 1.
    starting_index : int
        The starting index of the equation line matching the variable. Default is 0.

    Returns
    -------
    Callable
        the decorator registering the internal equation.

    Raises
    ------
    ValueError
        if the function is already decorated with an expression decorator of an other
        type.

    Examples
    --------

    .. code:: python

        @dataclass
        class SimpleModel(ModelComponent):

            x: Quantity
            a: float
            b: float

            @declares_internal_equation("x")
            def affine(self):
                return self.x.new * self.a + self.b

            @affine.partial_derivative("x")
            def dresidual_dx(self):
                return self.a


    See Also
    --------
    declares_flux : Decorator factory to declare a flux.
    declares_saved_quantity : Decorator factory to declare a saved quantity.
    """
    return _declare_expression_decorator(
        ExpressionDecorator,
        _ExpressionType.INTERNAL_EXPRESSION,
        variable_name,
        size,
        starting_index,
    )


def declares_saved_quantity(
    quantity_name: str, size: int = 1, starting_index: int = 0
) -> Callable[..., ExpressionDecorator]:
    """Declare a saved quantity expression in the model.

    Parameters
    ----------
    quantity_name : str
        the local quantity name.
    size : int
        the size of the expression. Default is 1
    starting_index : int
        the starting index of the expression in the function.
        Default is 0

    Returns
    -------
    Callable
        the decorator registering the saved quantity.

    Raises
    ------
    ValueError
        if the function is already decorated with an expression decorator of an other
        type.

    Examples
    --------

    .. code:: python

        @dataclass
        class SimpleModel(ModelComponent):

            a: Quantity
            b: Quantity

            @declares_saved_quantity("sum_ab")
            def sum(self):
                return self.a.current + self.b.current

    See Also
    --------
    declares_flux : Decorator factory to declare a flux.
    declares_internal_equation : Decorator factory to declare a internal equation.

    """
    decorator = _declare_expression_decorator(
        ExpressionDecorator,
        _ExpressionType.SAVED_QUANTITY_EXPRESSION,
        quantity_name,
        size,
        starting_index,
    )
    return decorator


class _ModelComponentMetaClass(type):
    _expressions: list[tuple[Expression, _ExpressionType]]

    def __init__(cls, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        cls._expressions = []
        for attr in cls.__dict__.values():
            if isinstance(attr, ExpressionDecorator) and attr.expression_type in (
                _ExpressionType.INTERNAL_EXPRESSION,
                _ExpressionType.SAVED_QUANTITY_EXPRESSION,
            ):
                cls._add_expression(attr.expression, attr.expression_type)

    @staticmethod
    def __is_quantity_type(type_to_test: Any) -> bool:
        if isinstance(type_to_test, type) is False:
            type_to_test = get_origin(type_to_test)
        return issubclass(type_to_test, Quantity) is True

    @property
    def local_ids(cls) -> list[str]:
        """Get local parameters ids of the model.

        Every member of the :class:`~.ModelComponent` annotated with :class:`~.Quantity`
        type has a local id.

        Returns
        -------
        list[str]
            the local ids of the parameters

        Examples
        --------

        .. code:: python

            @dataclass
            class SimpleModel(metaclass=_ModelComponentMetaClass):

                x1: Quantity
                x2: Quantity

            SimpleModel.local_ids # ["x1", "x2"]

        """
        annotations = get_annotations(cls)

        # get the quantities local ids
        local_ids = [
            key
            for key, item in annotations.items()
            if _ModelComponentMetaClass.__is_quantity_type(item)
        ]

        # add the saved quantities local ids
        local_ids.extend(
            [
                saved_quantity_expr.term_id
                for saved_quantity_expr in cls.saved_quantities
            ]
        )

        return local_ids

    def _get_all_terms(cls, expr_type: _ExpressionType) -> list[Term]:
        # get terms local id and size for all expressions of the given type
        return [
            term_def
            for expression in cls._get_all_expressions(expr_type)
            for term_def in expression.terms
        ]

    def _has_term_defined(cls, tested_id: str, expr_type: _ExpressionType) -> bool:
        """Get if the given id is defined as the given expression type.

        Parameters
        ----------
        tested_id : str
            the id to test
        expr_type : _ExpressionType
            the expression type to test

        Returns
        -------
        bool
            True if the id defines an expression of the given expression type,
            false otherwise

        """
        return any(term.term_id == tested_id for term in cls._get_all_terms(expr_type))

    def _get_all_expressions(cls, expr_type: _ExpressionType) -> list[Expression]:
        # get all expressions of a type with the matching defined terms
        return [
            expr for expr, _expr_type in cls._expressions if _expr_type == expr_type
        ]

    def _get_all_terms_ids(cls) -> list[str]:
        # get all expressed terms local ids
        return [
            term_def.term_id
            for expr_type in _ExpressionType
            for expr_def in cls._get_all_expressions(expr_type)
            for term_def in expr_def.terms
        ]

    def _add_expression(cls, expr: Expression, expr_type: _ExpressionType) -> None:
        if expr.valid is False:
            raise ValueError(
                str.format(
                    "Expression {0} for function {1} is invalid.",
                    expr,
                    expr.expr_func.__name__,
                )
            )

        for term in expr.terms:
            # check if a term with the same id is already used
            if term.term_id in cls._get_all_terms_ids():
                raise KeyError(
                    str.format(
                        "An expression is already defined for {0}.", term.term_id
                    )
                )

        cls._expressions.append((expr, expr_type))

    @property
    def internal_variables(cls) -> list[Term]:
        """Get the terms describing internal variables.

        Returns
        -------
        list[Term]
            the internal variables term definitions

        """
        return cls._get_all_terms(_ExpressionType.INTERNAL_EXPRESSION)

    @property
    def internal_expressions(cls) -> list[Expression]:
        """Get all expressions describing **Internal Equations** of the model.

        Returns
        -------
        list[Expression]
            the internal equation expressions

        """
        return cls._get_all_expressions(_ExpressionType.INTERNAL_EXPRESSION)

    def has_internal_variable(cls, variable_id: str) -> bool:
        """Check if the variable id is an internal variable.

        Parameters
        ----------
        variable_id : str
            the id to test

        Returns
        -------
        bool
            True if the id defines an **Internal Variable**, False otherwise

        """
        return cls._has_term_defined(variable_id, _ExpressionType.INTERNAL_EXPRESSION)

    @property
    def saved_quantities(cls) -> list[Term]:
        """Get the terms describing saved quantities.

        Returns
        -------
        list[Term]
            the saved quantities local id and size.

        """
        return cls._get_all_terms(_ExpressionType.SAVED_QUANTITY_EXPRESSION)

    def has_saved_quantity(cls, saved_quantity_id: str) -> bool:
        """Check if the quantity id is a saved quantity.

        Parameters
        ----------
        saved_quantity_id : str
            the id to test

        Returns
        -------
        bool
            True if the id defines a saved quantity, false otherwise

        """
        return cls._has_term_defined(
            saved_quantity_id, _ExpressionType.SAVED_QUANTITY_EXPRESSION
        )

    @property
    def saved_quantities_expressions(cls) -> list[Expression]:
        """Get all saved quantities expressions.

        Returns
        -------
        list[Expression]
            the saved quantities expressions

        """
        return cls._get_all_expressions(_ExpressionType.SAVED_QUANTITY_EXPRESSION)


class ModelComponent(metaclass=_ModelComponentMetaClass):
    """Define model expressions and quantities.

    Define the model **Internal Equations** and **Saved Quantities** and the quantities
    they need.

    * **Internal Equations** are expressing **Internal Variables** with a residual
      equation.
    * **Saved Quantities** are given with a direct relation

    See Also
    --------
    declares_internal_equation : Decorator factory to declare a internal equation.
    declares_saved_quantity : Decorator factory to declare a saved quantity.
    """

    def initialize(self) -> None:
        """Override this method to define specific model initialization."""


class _FluxExpressionDecorator(ExpressionDecorator):
    flux_index: int = 0


def declares_flux(
    index: int, dof_name: str, size: int = 1
) -> Callable[..., _FluxExpressionDecorator]:
    """Declare a flux expression.

    Once the flux expression is declared, partial derivatives can be added using the
    flux function name and the local variable name for the partial derivative.

    Parameters
    ----------
    index : int
        the local node index where the flux is shared.
    dof_name : str
        the matching dof local name
    size : int
        the size of the flux returned by the function. Default is 1.

    Returns
    -------
    Callable
        the decorator registering the flux.

    Raises
    ------
    ValueError
        if the function is already decorated with an expression decorator of an other
        type.

    Examples
    --------

    .. code:: python

        @dataclass
        class SimpleBlock(Block):

            q_1: Quantity

            # declares a flux shared at local node 1, where the associated dof has the
            # local name "potential_1"
            @declares_flux(1, "potential_1")
            def flux_1(self):
                return self.q_1.new

            # associate the following function as the partial derivative of "flux_1" for
            # variable "q_1"
            @flux_1.partial_derivative("q_1")
            def dflux_1_dq_1(self):
                return 1.0

    """
    expression_decorator = _declare_expression_decorator(
        _FluxExpressionDecorator, _ExpressionType.FLUX_EXPRESSION, dof_name, size, 0
    )

    def flux_expression_decorator(
        wrapped: Callable[..., Any],
    ) -> _FluxExpressionDecorator:
        decorated = expression_decorator(wrapped)
        if isinstance(decorated, _FluxExpressionDecorator):
            decorated.flux_index = index
            return decorated
        raise TypeError(f"{decorated} is not a flux expression decorator.")

    return flux_expression_decorator


class _BlockMetaClass(_ModelComponentMetaClass):
    _fluxes: dict[int, Expression]

    def __init__(cls, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        cls._fluxes = {}
        for attr in cls.__dict__.values():
            if (
                isinstance(attr, _FluxExpressionDecorator)
                and attr.expression_type == _ExpressionType.FLUX_EXPRESSION
            ):
                cls._add_flux_expression(attr.flux_index, attr.expression)

    def _add_flux_expression(cls, node_index: int, expr: Expression) -> None:
        """Add a flux expression defining a block external relation.

        Parameters
        ----------
        node_index : int
            the local node index where the flux is shared
        expr : Expression
            the associated expression
        """
        if node_index in cls.nodes:
            raise ValueError(
                str.format(
                    "Flux {0} is already defined for the block node at index {1}.",
                    cls._fluxes[node_index].expr_func.__name__,
                    node_index,
                )
            )
        cls._fluxes[node_index] = expr

    @property
    def nodes(cls) -> list[int]:
        """Get all the local nodes indexes.

        Returns
        -------
        list[int]
            The list of indexes.

        """
        return [node_index for node_index in cls._fluxes]

    @property
    def fluxes_expressions(cls) -> dict[int, Expression]:
        """Get all local nodes with the fluxes expressions they share.

        Returns
        -------
        dict[int, Expression]
            the fluxes expressions indexed by node index.

        """
        return cls._fluxes.copy()


class Block(ModelComponent, metaclass=_BlockMetaClass):
    """Extend :class:`ModelComponent` and declare fluxes expressions.

    * Every **Flux** is expressed toward the outside of the **Block**.
    * Every **Local Node** index of the **Block** defines one **Flux**.

    .. note::

        Blocks can also define **Internal Equations** and **Saved Quantities**

    See Also
    --------
    ModelComponent: Base class.
    declares_flux : Decorator factory to declare a flux.
    declares_internal_equation : Decorator factory to declare a internal equation.
    declares_saved_quantity : Decorator factory to declare a saved quantity.
    """
