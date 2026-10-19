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
from unittest.mock import MagicMock

import pytest

from physioblocks.computing.models import (
    Block,
    Expression,
    ExpressionDecorator,
    ModelComponent,
    Term,
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
    return Term(DOF_ID, 2)


@pytest.fixture
def expression(term_definition):
    return Expression(2, func, [term_definition])


@pytest.fixture
def other_expression():
    return Expression(2, func)


@pytest.fixture
def expression_type():
    return MagicMock()


class TestExpression:
    def test_constructor_default(self):
        expr = Expression(1, func)
        assert expr.size == 1
        assert expr.expr_func == func
        assert expr.terms == []
        assert expr.expr_gradients == {}

    def test_eq(self, grads):
        expr_1 = Expression(1, func, grads)
        expr_2 = Expression(1, func, grads)
        expr_3 = Expression(1, func)
        expr_4 = Expression(2, func, grads)

        assert expr_1 == expr_1
        assert expr_1 == expr_2
        assert expr_1 != expr_3
        assert expr_1 != expr_4

    @pytest.mark.parametrize(
        "valid_expression",
        [
            pytest.param(Expression(2, func, [Term(DOF_ID, 2, 0)]), id="one_term"),
            pytest.param(
                Expression(
                    2,
                    func,
                    [Term(TERM_A_ID, 1, 0), Term(TERM_B_ID, 1, 1)],
                ),
                id="two_terms",
            ),
            pytest.param(
                Expression(
                    2,
                    func,
                    [Term(TERM_A_ID, 1, 1), Term(TERM_B_ID, 1, 0)],
                ),
                id="two_unsorted_terms",
            ),
        ],
    )
    def test_valid(self, valid_expression: Expression):
        assert valid_expression.valid is True

    @pytest.mark.parametrize(
        "invalid_expression",
        [
            pytest.param(
                Expression(
                    2,
                    func,
                    [Term(TERM_A_ID, 2), Term(TERM_B_ID, 1)],
                ),
                id="too_many_terms",
            ),
            pytest.param(Expression(1, func), id="no_terms"),
            pytest.param(
                Expression(
                    2,
                    func,
                    [Term(DOF_ID, 1)],
                ),
                id="small_term",
            ),
            pytest.param(
                Expression(
                    expression,
                    [Term(TERM_A_ID, 1), Term(TERM_B_ID, 1)],
                ),
                id="repeating_indexes",
            ),
            pytest.param(
                Expression(
                    2,
                    [Term(TERM_A_ID, 1, 1), Term(TERM_B_ID, 1, 2)],
                ),
                id="no_zero_index",
            ),
        ],
    )
    def tests_invalid_expression(self, invalid_expression: Expression):
        assert invalid_expression.valid is False

    def test_get_term(self, expression: Expression, term_definition: Term):
        # one term expression definition
        assert expression.get_term(0) == term_definition
        err_mess = str.format(
            "No term starts at index {0} in expression", 1, expression
        )
        with pytest.raises(KeyError, match=err_mess):
            expression.get_term(1)

        # two terms expression definition
        term_a = Term(TERM_A_ID, 1, 0)
        term_b = Term(TERM_B_ID, 1, 1)
        two_term_expr_definition = Expression(2, func, [term_a, term_b])
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
    @pytest.mark.parametrize(
        "tested_function",
        [
            pytest.param(
                declares_internal_equation, id=declares_internal_equation.__name__
            ),
            pytest.param(declares_saved_quantity, id=declares_saved_quantity.__name__),
        ],
    )
    def test_expression_decorators(
        self, tested_function, reference_function: Callable[..., Any]
    ):
        decorator_factory = tested_function(TERM_X_ID)
        decorated_function = decorator_factory(reference_function)
        assert decorated_function.__name__ is reference_function.__name__
        assert decorated_function() is True

    def test_init_model(self):
        class ModelTest(ModelComponent):
            @declares_internal_equation(TERM_X_ID)
            def method_x(self):
                pass

            @declares_saved_quantity(TERM_A_ID)
            def method_a(self):
                pass

        assert ModelTest.has_internal_variable(TERM_X_ID)
        assert ModelTest.has_saved_quantity(TERM_A_ID)

    def test_raise_value_error(self):
        with pytest.raises(ValueError, match="method_a" and "INTERNAL_EXPRESSION"):

            class ModelTest(ModelComponent):
                @declares_saved_quantity(TERM_A_ID)
                @declares_internal_equation(TERM_X_ID)
                def method_a(self):
                    pass

    def test_register_partial_derivatives(self):
        class ModelTest(ModelComponent):
            @declares_internal_equation(TERM_X_ID)
            def method(self):
                pass

            @method.partial_derivative(TERM_X_ID)
            def partial_derivative(self):
                pass

        assert TERM_X_ID in ModelTest.internal_expressions[0].expr_gradients

    @pytest.mark.parametrize(
        "tested_function",
        [
            pytest.param(
                declares_internal_equation, id=declares_internal_equation.__name__
            ),
            pytest.param(declares_saved_quantity, id=declares_saved_quantity.__name__),
        ],
    )
    def test_add_term(
        self,
        tested_function: Callable[..., Callable[..., ExpressionDecorator]],
        reference_function: Callable[..., Any],
    ):
        term_x_decorator_factory = tested_function(TERM_X_ID)
        term_y_decorator_factory = tested_function(TERM_Y_ID, 2, 1)
        expression_decorator = term_x_decorator_factory(reference_function)
        expression_decorator = term_y_decorator_factory(expression_decorator)

        assert expression_decorator.terms[0] == Term(TERM_X_ID, 1, 0)
        assert expression_decorator.terms[1] == Term(TERM_Y_ID, 2, 1)
        assert expression_decorator.expression.size == 3

    def test_flux_decorator(self, reference_function: Callable[..., Any]):
        expression_decorator_factory = declares_flux(1, TERM_X_ID)
        expression_decorator = expression_decorator_factory(reference_function)

        assert expression_decorator.flux_index == 1
        assert expression_decorator.terms[0] == Term(TERM_X_ID, 1, 0)


class TestModelComponentMetaClass:
    def test_local_ids(self):
        class ModelComponentTest(ModelComponent):
            x: Quantity
            y: Quantity[Any]
            constant: float  # not a local id
            parameter: str  # not a local id

        assert TERM_X_ID in ModelComponentTest.local_ids
        assert TERM_Y_ID in ModelComponentTest.local_ids
        assert "constant" not in ModelComponentTest.local_ids
        assert "parameter" not in ModelComponentTest.local_ids

    def test_init_model_component(self):
        class ModelTest(ModelComponent):
            @declares_internal_equation(TERM_X_ID)
            def method_x(self):
                pass

            @declares_saved_quantity(TERM_A_ID)
            def method_a(self):
                pass

        assert Term(TERM_X_ID, 1, 0) in ModelTest.internal_variables
        assert Term(TERM_A_ID, 1, 0) in ModelTest.saved_quantities

        assert (
            ModelTest.internal_expressions[0].expr_func.__name__
            == ModelTest.method_x.__name__
        )
        assert (
            ModelTest.saved_quantities_expressions[0].expr_func.__name__
            == ModelTest.method_a.__name__
        )

    def test_invalid_expression(self):
        with pytest.raises(ValueError, match="method_ab" and "invalid"):

            class ModelTest(ModelComponent):
                @declares_internal_equation(TERM_A_ID, 1, 0)
                @declares_internal_equation(TERM_B_ID, 1, 0)
                def method_ab(self):
                    pass

    def test_already_registered(self):
        with pytest.raises(KeyError, match="already defined" and TERM_A_ID):

            class ModelTest(ModelComponent):
                @declares_internal_equation(TERM_A_ID)
                def method_internal_a(self):
                    pass

                @declares_saved_quantity(TERM_A_ID)
                def method_saved_a(self):
                    pass


class TestBlockMetaClass:
    def test_init_block(self):
        class BlockTest(Block):
            @declares_flux(1, DOF_ID)
            def method_flux(self):
                pass

        assert DOF_ID not in BlockTest.local_ids
        assert 1 in BlockTest.fluxes_expressions
        assert (
            BlockTest.fluxes_expressions[1].expr_func.__name__
            == BlockTest.method_flux.__name__
        )

    def test_flux_index_already_defined(self):
        with pytest.raises(
            ValueError, match="flux method_flux_1" and "already defined" and "index 1"
        ):

            class BlockTest(Block):
                @declares_flux(1, DOF_ID)
                def method_flux_1(self):
                    pass

                @declares_flux(1, TERM_A_ID)
                def method_flux_2(self):
                    pass
