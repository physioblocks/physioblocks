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

from collections.abc import Callable
from typing import Any
from unittest.mock import patch

import pytest

from physioblocks.computing.models import (
    BlockMetaClass,
    Expression,
    ExpressionDecorator,
    ExpressionDefinition,
    FluxDecorator,
    InternalEquationDecorator,
    ModelComponentMetaClass,
    SavedQuantityDecorator,
    TermDefinition,
    declares_flux,
    declares_internal_equation,
    declares_saved_quantity,
)
from physioblocks.computing.quantities import Quantity

TERM_A_ID = "a"
TERM_B_ID = "b"
TERM_X_ID = "x"
TERM_Y_ID = "y"
TERM_Z_ID = "z"
UNDEFINED_TERM_ID = "undefined"
FLUX_TYPE = "flux"
DOF_ID = "dof"


def func():
    return 0


@pytest.fixture
def grads():
    return {"var": func}


@pytest.fixture
def term_definition():
    return TermDefinition(DOF_ID, 2)


@pytest.fixture
def expression():
    return Expression(2, func)


@pytest.fixture
def other_expression():
    return Expression(2, func)


@pytest.fixture
def expression_def(expression: Expression, term_definition: TermDefinition):
    return ExpressionDefinition(expression, [term_definition])


class TestExpression:
    def test_constructor(self, grads):
        expr = Expression(1, func, grads)
        assert expr.size == 1
        assert expr.expr_func == func
        assert expr.expr_gradients == grads

    def test_eq(self, grads):
        expr_1 = Expression(1, func, grads)
        expr_2 = Expression(1, func, grads)
        expr_3 = Expression(1, func)
        expr_4 = Expression(2, func, grads)

        assert expr_1 == expr_1
        assert expr_1 == expr_2
        assert expr_1 != expr_3
        assert expr_1 != expr_4


class TestTermDefinition:
    def test_eq(self):
        term_a = TermDefinition(TERM_A_ID, 1)
        term_b = TermDefinition(TERM_B_ID, 1)
        term_c = TermDefinition(TERM_A_ID, 3)

        assert term_a != term_b
        assert term_a == term_c


class TestExpressionDefinition:
    def test_valid(
        self,
        expression_def: ExpressionDefinition,
        term_definition: TermDefinition,
        expression: Expression,
    ):
        # valid expression with one term
        assert expression_def.valid is True

        # valid expression with two terms
        valid_expr = ExpressionDefinition(
            expression, [TermDefinition("a", 1, 0), TermDefinition("b", 1, 1)]
        )
        assert valid_expr.valid is True

        # valid expression with unsorted terms
        valid_expr = ExpressionDefinition(
            expression, [TermDefinition("a", 1, 1), TermDefinition("b", 1, 0)]
        )
        assert valid_expr.valid is True

        # expression with too many terms
        invalid_expression = ExpressionDefinition(
            expression,
            [term_definition, term_definition],
        )
        assert invalid_expression.valid is False

        # expression with no terms
        invalid_expression = ExpressionDefinition(
            expression,
            [],
        )
        assert invalid_expression.valid is False

        # expression with terms too small
        invalid_expression = ExpressionDefinition(
            expression,
            [TermDefinition(DOF_ID, 1)],
        )
        assert invalid_expression.valid is False

        # invalid expression with repeating indexes
        valid_expr = ExpressionDefinition(
            expression, [TermDefinition("a", 1), TermDefinition("b", 1)]
        )
        assert valid_expr.valid is False

        # invalid expression with indexes not starting at zero
        valid_expr = ExpressionDefinition(
            expression, [TermDefinition("a", 1, 1), TermDefinition("b", 1, 2)]
        )
        assert valid_expr.valid is False

    def test_get_term(
        self,
        expression_def: ExpressionDefinition,
        term_definition: TermDefinition,
        expression: Expression,
    ):
        # one term expression definition
        assert expression_def.get_term(0) == term_definition
        err_mess = str.format(
            "No term starts at index {0} in expression", 1, expression
        )
        with pytest.raises(KeyError, match=err_mess):
            expression_def.get_term(1)

        # two terms expression definition
        term_a = TermDefinition("a", 1, 0)
        term_b = TermDefinition("b", 1, 1)
        two_term_expr_definition = ExpressionDefinition(expression, [term_a, term_b])
        assert two_term_expr_definition.get_term(0) == term_a
        assert two_term_expr_definition.get_term(1) == term_b

        err_mess = str.format(
            "No term starts at index {0} in expression", 2, expression
        )
        with pytest.raises(KeyError, match=err_mess):
            two_term_expr_definition.get_term(2)


@pytest.fixture
def reference_function() -> Callable[..., Any]:
    def function_to_decorate() -> bool:
        return True

    return function_to_decorate


class TestExpressionDecorators:
    def test_create_expression_decorator(self, reference_function: Callable[..., Any]):
        decorator = ExpressionDecorator(reference_function)
        assert decorator() is True

    def test_register_terms(self, reference_function: Callable[..., Any]):
        decorator = ExpressionDecorator(reference_function)

        decorator.register_term(TERM_X_ID, 1, 0)
        decorator.register_term(TERM_Y_ID, 2, 1)

        assert decorator.expression.size == 3

        decorator.terms.pop()
        assert decorator.expression.size == 3

    def test_register_partial_derivatives(self, reference_function: Callable[..., Any]):
        decorator = ExpressionDecorator(reference_function)
        register_function = decorator.partial_derivative(TERM_X_ID)
        partial_derivative = register_function(reference_function)

        assert TERM_X_ID in decorator.expression.expr_gradients
        assert decorator.expression.expr_gradients[TERM_X_ID] is reference_function
        assert partial_derivative is reference_function

    def test_internal_equation_decorator(self, reference_function: Callable[..., Any]):
        expression_decorator_factory = declares_internal_equation(TERM_X_ID)
        expression_decorator = expression_decorator_factory(reference_function)

        assert expression_decorator.terms[0] == (TERM_X_ID, 1, 0)

        expression_decorator_factory = declares_internal_equation(TERM_Y_ID, 2, 1)
        expression_decorator = expression_decorator_factory(expression_decorator)

        assert expression_decorator.terms[0] == (TERM_X_ID, 1, 0)
        assert expression_decorator.terms[1] == (TERM_Y_ID, 2, 1)
        assert expression_decorator.expression.size == 3

        with pytest.raises(
            ValueError,
            match=str.format(
                "Can not decorate a function of an other type. "
                "Current type is {0}, new type is {1}.",
                ExpressionDecorator,
                InternalEquationDecorator,
            ),
        ):
            expression_decorator_factory(ExpressionDecorator(reference_function))

    def test_saved_quantity_decorator(self, reference_function: Callable[..., Any]):
        expression_decorator_factory = declares_saved_quantity(TERM_X_ID)
        expression_decorator = expression_decorator_factory(reference_function)

        assert expression_decorator.terms[0] == (TERM_X_ID, 1, 0)

        expression_decorator_factory = declares_saved_quantity(TERM_Y_ID, 2, 1)
        expression_decorator = expression_decorator_factory(expression_decorator)

        assert expression_decorator.terms[0] == (TERM_X_ID, 1, 0)
        assert expression_decorator.terms[1] == (TERM_Y_ID, 2, 1)
        assert expression_decorator.expression.size == 3

        with pytest.raises(
            ValueError,
            match=str.format(
                "Can not decorate a function of an other type. "
                "Current type is {0}, new type is {1}.",
                ExpressionDecorator,
                SavedQuantityDecorator,
            ),
        ):
            expression_decorator_factory(ExpressionDecorator(reference_function))

    def test_flux_decorator(self, reference_function: Callable[..., Any]):
        expression_decorator_factory = declares_flux(0, TERM_X_ID)
        expression_decorator = expression_decorator_factory(reference_function)

        assert expression_decorator.terms[0] == (TERM_X_ID, 1, 0)

        with pytest.raises(
            ValueError,
            match=str.format(
                "Function already declares an expression, it can not be a flux."
            ),
        ):
            expression_decorator_factory(ExpressionDecorator(reference_function))

        expression_decorator_factory = declares_flux(1, TERM_Y_ID)

        with pytest.raises(
            ValueError,
            match=str.format(
                "Function already declares an expression, it can not be a flux."
            ),
        ):
            expression_decorator_factory(expression_decorator)


@pytest.fixture
def model_component_type():
    class ModelComponentTest(metaclass=ModelComponentMetaClass):
        a: Quantity
        x: Quantity
        y: Quantity[Any]
        z: Quantity
        constant: float  # not a local id
        parameter: str  # not a local id

    return ModelComponentTest


class TestModelComponentMetaClass:
    def test_declarations(
        self,
        model_component_type: ModelComponentMetaClass,
        expression: Expression,
        other_expression: Expression,
    ):
        model_component_type.declares_saved_quantity_expression(
            TERM_B_ID, expression, 1, 0
        )
        model_component_type.declares_internal_expression(TERM_X_ID, expression, 1, 0)
        model_component_type.declares_internal_expression(TERM_Y_ID, expression, 1, 1)
        model_component_type.declares_internal_expression(
            TERM_Z_ID, other_expression, index=0
        )

        assert model_component_type.local_ids == [
            TERM_A_ID,
            TERM_X_ID,
            TERM_Y_ID,
            TERM_Z_ID,
            TERM_B_ID,
        ]

        assert model_component_type.internal_variables == [
            TermDefinition(TERM_X_ID, 1, 0),
            TermDefinition(TERM_Y_ID, 1, 1),
            TermDefinition(TERM_Z_ID, 2, 0),
        ]
        assert model_component_type.has_saved_quantity(TERM_B_ID) is True
        assert model_component_type.has_internal_variable(TERM_X_ID) is True
        assert model_component_type.has_internal_variable(TERM_Y_ID) is True
        assert model_component_type.has_internal_variable(TERM_Z_ID) is True
        assert model_component_type.has_internal_variable(UNDEFINED_TERM_ID) is False
        assert model_component_type.has_saved_quantity(UNDEFINED_TERM_ID) is False

        assert model_component_type.saved_quantities == [
            TermDefinition(TERM_B_ID, 1, 0)
        ]
        assert len(model_component_type.internal_expressions) == 2
        assert model_component_type.internal_expressions[0].expression is expression
        assert model_component_type.internal_expressions[0].terms == [
            TermDefinition(TERM_X_ID, 1, 0),
            TermDefinition(TERM_Y_ID, 1, 1),
        ]
        assert (
            model_component_type.internal_expressions[1].expression is other_expression
        )
        assert model_component_type.internal_expressions[1].terms == [
            TermDefinition(TERM_Z_ID, 2, 0),
        ]

        assert len(model_component_type.saved_quantities_expressions) == 1
        assert (
            model_component_type.saved_quantities_expressions[0].expression
            == expression
        )
        assert model_component_type.saved_quantities_expressions[0].terms == [
            TermDefinition(TERM_B_ID, 0)
        ]

        assert model_component_type.get_internal_variable_expression(TERM_X_ID) == (
            expression,
            1,
            0,
        )
        assert model_component_type.get_internal_variable_expression(TERM_Y_ID) == (
            expression,
            1,
            1,
        )
        assert model_component_type.get_internal_variable_expression(TERM_Z_ID) == (
            other_expression,
            2,
            0,
        )
        assert model_component_type.get_saved_quantity_expression(TERM_B_ID) == (
            expression,
            1,
            0,
        )

    def test_exceptions(
        self,
        model_component_type: ModelComponentMetaClass,
        expression: Expression,
    ):
        error_msg = str.format("No expression defined for {0}.", TERM_A_ID)
        with pytest.raises(KeyError, match=error_msg):
            model_component_type.get_internal_variable_expression(TERM_A_ID)

        error_msg = str.format("An expression is already defined for {0}.", TERM_A_ID)
        with pytest.raises(KeyError, match=error_msg):
            model_component_type.declares_internal_expression(
                TERM_A_ID, expression, 1, 0
            )
            model_component_type.declares_internal_expression(
                TERM_A_ID, expression, 1, 0
            )

        error_msg = str.format(
            "{0} definition of size {1} starting at index {2} exceed expression size "
            "{3}",
            TERM_X_ID,
            3,
            0,
            expression.size,
        )
        with pytest.raises(ValueError, match=error_msg):
            model_component_type.declares_internal_expression(
                TERM_X_ID, expression, 3, 0
            )

        error_msg = str.format(
            "{0} definition of size {1} starting at index {2} exceed expression "
            "size {3}",
            TERM_X_ID,
            1,
            2,
            expression.size,
        )
        with pytest.raises(ValueError, match=error_msg):
            model_component_type.declares_internal_expression(
                TERM_X_ID, expression, 1, 2
            )

        error_msg = str.format(
            "{0} definition of size {1} starting at index {2} exceed expression "
            "size {3}",
            TERM_X_ID,
            3,
            0,
            expression.size,
        )
        with pytest.raises(ValueError, match=error_msg):
            model_component_type.declares_internal_expression(
                TERM_X_ID, expression, 3, 0
            )

    def test_decorators(self):
        class ModelTest(metaclass=ModelComponentMetaClass):
            @declares_internal_equation(TERM_X_ID)
            def internal_equation_func(self):
                pass

            @declares_saved_quantity(TERM_A_ID)
            def saved_quantity_func(self):
                pass

        assert isinstance(ModelTest.internal_equation_func, InternalEquationDecorator)
        assert isinstance(ModelTest.saved_quantity_func, SavedQuantityDecorator)


@pytest.fixture
def block_type() -> BlockMetaClass:
    class BlockTest(metaclass=BlockMetaClass):
        x: Quantity
        a: Quantity

    return BlockTest


class TestBlockMetaClass:
    def test_declares_flux(
        self,
        block_type: BlockMetaClass,
        expression: ExpressionDefinition,
        expression_def: ExpressionDefinition,
    ):
        block_type.declares_flux_expression(0, DOF_ID, expression)

        assert block_type.nodes == [0]
        assert block_type.local_ids == [TERM_X_ID, TERM_A_ID]
        assert block_type.external_variables_ids == [DOF_ID]
        assert block_type.fluxes_expressions == {0: expression_def}
        assert block_type.fluxes_expressions[0] == expression_def

    def test_exceptions(
        self,
        block_type: BlockMetaClass,
        expression: ExpressionDefinition,
        expression_def: ExpressionDefinition,
    ):
        error_message = str.format(
            "Flux {0} is already defined for the block node at index {1}.",
            func.__name__,
            0,
        )
        with (
            pytest.raises(ValueError, match=error_message),
            patch.object(block_type, attribute="_fluxes", new={0: expression_def}),
        ):
            block_type.declares_flux_expression(0, DOF_ID, expression)
            assert block_type.flux_func.expression.size == 1

    def test_decorators(self):
        class BlockTest(metaclass=BlockMetaClass):
            @declares_flux(0, TERM_X_ID)
            def flux_func(self):
                pass

        assert isinstance(BlockTest.flux_func, FluxDecorator)
