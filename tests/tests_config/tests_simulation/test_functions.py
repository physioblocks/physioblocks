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

from dataclasses import dataclass
from typing import Any
from unittest.mock import patch

import numpy as np
import pytest
from numpy.typing import NDArray

from physioblocks.computing.quantities import Quantity
from physioblocks.configuration.base import Configuration, ConfigurationError
from physioblocks.configuration.functions import load, save
from physioblocks.description.blocks import Block
from physioblocks.simulation.functions import AbstractFunction

FUNC_ID = "func_id"


class BlockTest(Block):
    param: float

    def __init__(self, param: float):
        self.param = param


@dataclass
class FunctionValues(AbstractFunction):
    a: float
    b: int
    c: str
    d: NDArray[np.float64]
    e: np.float64
    f: Quantity[np.float64]
    g: Quantity[NDArray[np.float64]]
    h: list[Quantity]
    i: dict[str, Quantity]


@pytest.fixture
def ref_function_values():
    with patch.multiple(FunctionValues, __abstractmethods__=set()):
        return FunctionValues(
            0.1,
            2,
            "three",
            np.array([0.4, 0.5, 0.6]),
            0.7,
            Quantity(0.8),
            Quantity([0.9, 1.0, 1.1]),
            [
                Quantity(1.2),
                Quantity(1.3),
                Quantity(1.4),
            ],
            {
                "q1": Quantity(1.5),
                "q2": Quantity(1.6),
                "q3": Quantity(1.7),
            },
        )


@pytest.fixture
def ref_config_values():
    config = Configuration(FUNC_ID)
    config.configuration_items = {
        "a": 0.1,
        "b": 2,
        "c": "three",
        "d": [0.4, 0.5, 0.6],
        "e": 0.7,
        "f": 0.8,
        "g": [0.9, 1.0, 1.1],
        "h": [1.2, 1.3, 1.4],
        "i": {"q1": 1.5, "q2": 1.6, "q3": 1.7},
    }
    return config


@dataclass
class FunctionReferences(AbstractFunction):
    a: Quantity[np.float64]
    b: Quantity[NDArray[np.float64]]
    c: list[Quantity]
    d: dict[str, Quantity]
    e: BlockTest
    f: list[BlockTest]
    g: dict[str, BlockTest]


@pytest.fixture
def ref_config_references():
    config = Configuration(FUNC_ID)
    config.configuration_items = {
        "a": "qa",
        "b": "qb",
        "c": ["qc1", "qc2", "qc3"],
        "d": {"q1": "qd1", "q2": "qd2", "q3": "qd3"},
        "e": "ba",
        "f": ["bb1", "bb2"],
        "g": {"b1": "bc1", "b2": "bc2"},
    }

    return config


@pytest.fixture
def quantities():
    return {
        "qa": Quantity(0.1),
        "qb": Quantity(np.array([0.2, 0.3, 0.4])),
        "qc1": Quantity(0.5),
        "qc2": Quantity(0.6),
        "qc3": Quantity(0.7),
        "qd1": Quantity(0.8),
        "qd2": Quantity(0.9),
        "qd3": Quantity(1.0),
    }


@pytest.fixture
def blocks():
    return {
        "ba": BlockTest(1.1),
        "bb1": BlockTest(1.2),
        "bb2": BlockTest(1.3),
        "bc1": BlockTest(1.4),
        "bc2": BlockTest(1.5),
    }


@pytest.fixture
def ref_function_references(quantities, blocks):
    with patch.multiple(FunctionReferences, __abstractmethods__=set()):
        return FunctionReferences(
            quantities["qa"],
            quantities["qb"],
            [
                quantities["qc1"],
                quantities["qc2"],
                quantities["qc3"],
            ],
            {
                "q1": quantities["qd1"],
                "q2": quantities["qd2"],
                "q3": quantities["qd3"],
            },
            blocks["ba"],
            [blocks["bb1"], blocks["bb2"]],
            {"b1": blocks["bc1"], "b2": blocks["bc2"]},
        )


@dataclass
class CanNotConvertFunction(AbstractFunction):
    can_not_convert_float: float
    can_not_convert_object: object


@pytest.fixture
def ref_config_can_not_convert():
    config = Configuration(FUNC_ID)
    config.configuration_items = {
        "can_not_convert_float": "0.1",
        "can_not_convert_object": "some_id",
    }
    return config


@pytest.fixture
def ref_can_not_convert_values():
    with patch.multiple(CanNotConvertFunction, __abstractmethods__=set()):
        return CanNotConvertFunction(object(), object())


@patch(
    "physioblocks.registers.type_register.__type_register",
    new={FunctionValues: FUNC_ID},
)
def test_to_config_values(ref_function_values, ref_config_values):
    config = save(ref_function_values)
    assert config == ref_config_values


@patch(
    "physioblocks.registers.type_register.__type_register",
    new={FunctionReferences: FUNC_ID},
)
def test_to_config_references(
    ref_function_references,
    ref_config_references,
    quantities: dict[str, Any],
    blocks: dict[str, Any],
):
    references = quantities.copy()
    references.update(blocks)
    config = save(ref_function_references, configuration_references=references)
    assert config == ref_config_references


@patch(
    "physioblocks.registers.type_register.__type_register",
    new={FunctionReferences: FUNC_ID},
)
def test_to_config_can_not_configure_block_exception(ref_function_references):
    message = str.format("Can not configure object {0}.", ref_function_references.e)
    with pytest.raises(ConfigurationError, match=message):
        save(ref_function_references)


@patch(
    "physioblocks.registers.type_register.__type_register",
    new={FUNC_ID: FunctionValues},
)
@patch.multiple(FunctionValues, __abstractmethods__=set())
def test_from_config_values(ref_config_values, ref_function_values: FunctionValues):
    func: FunctionValues = load(ref_config_values)
    assert func.a == pytest.approx(ref_function_values.a)
    assert func.b == ref_function_values.b
    assert func.c == ref_function_values.c
    assert func.d == pytest.approx(ref_function_values.d)
    assert func.e == pytest.approx(ref_function_values.e)
    assert func.f == pytest.approx(ref_function_values.f)
    assert func.g == pytest.approx(ref_function_values.g)

    for index in range(0, len(func.h)):
        assert func.h[index] == pytest.approx(ref_function_values.h[index])

    for key in func.i:
        assert func.i[key] == pytest.approx(ref_function_values.i[key])


@patch(
    "physioblocks.registers.type_register.__type_register",
    new={FUNC_ID: FunctionReferences},
)
@patch.multiple(FunctionReferences, __abstractmethods__=set())
def test_from_config_references(
    ref_config_references,
    ref_function_references: FunctionReferences,
    quantities,
    blocks,
):
    references = {}
    references.update(quantities)
    references.update(blocks)

    func: FunctionReferences = load(
        ref_config_references, configuration_references=references
    )
    assert func.a.current == pytest.approx(ref_function_references.a.current)
    assert func.a.new == pytest.approx(ref_function_references.a.new)

    assert func.b.current == pytest.approx(ref_function_references.b.current)
    assert func.b.new == pytest.approx(ref_function_references.b.new)

    for index in range(0, len(func.c)):
        assert func.c[index].current == pytest.approx(
            ref_function_references.c[index].current
        )
        assert func.c[index].new == pytest.approx(ref_function_references.c[index].new)

    for key in func.d:
        assert func.d[key].current == pytest.approx(
            ref_function_references.d[key].current
        )
        assert func.d[key].new == pytest.approx(ref_function_references.d[key].new)

    assert func.e.param == pytest.approx(ref_function_references.e.param)

    for index in range(0, len(func.f)):
        assert func.f[index].param == pytest.approx(
            ref_function_references.f[index].param
        )

    for key in func.g:
        assert func.g[key].param == pytest.approx(ref_function_references.g[key].param)
