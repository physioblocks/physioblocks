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

from unittest.mock import MagicMock

import pytest

from physioblocks.description.blocks import (
    BlockDescription,
    ModelComponentDescription,
)

# Constants for testing
BLOCK_ID = "block"
MODEL_A_ID = "model_a"
MODEL_B_ID = "model_b"
FLUX_TYPE = "flux_type"
DOF_ID = "dof_id"
ALTERNATIVE_TYPE_TAG = "alt"
PARAM_A = "a"
PARAM_B = "b"
PARAM_C = "c"
PARAM_D = "d"
SUBMODEL_ID = "submodel"
OTHER_PARAM = "other_param"
ANY_VALUE = "any_value"


@pytest.fixture
def model_a_local_ids():
    return [PARAM_A, PARAM_B]


@pytest.fixture
def term_a_definition():
    return MagicMock(term_id=PARAM_A, size=1, index=0)


@pytest.fixture
def term_b_definition():
    return MagicMock(term_id=PARAM_B, size=1, index=0)


@pytest.fixture
def model_a_type_mock(model_a_local_ids, term_a_definition, term_b_definition):
    model_a_type_mock = MagicMock(
        __name__=MODEL_A_ID,
        local_ids=model_a_local_ids,
        internal_variables=[term_a_definition],
        internal_expressions=[MagicMock(terms=[term_a_definition])],
        saved_quantities=[term_b_definition],
        saved_quantities_expressions=[MagicMock(terms=[term_b_definition])],
    )
    return model_a_type_mock


@pytest.fixture
def model_b_local_ids():
    return [PARAM_C, PARAM_D]


@pytest.fixture
def model_b_type_mock(model_b_local_ids):
    model_a_type_mock = MagicMock(local_ids=model_b_local_ids)
    return model_a_type_mock


@pytest.fixture
def alternative_model_a_local_ids():
    return [PARAM_A]


@pytest.fixture
def alternative_model_a_type_mock(alternative_model_a_local_ids):
    model_a_type_mock = MagicMock(local_ids=alternative_model_a_local_ids)
    return model_a_type_mock


@pytest.fixture
def flux_expression():
    return MagicMock(size=1)


@pytest.fixture
def flux_definition(flux_expression):
    return MagicMock(
        expression=flux_expression,
        terms=[MagicMock(term_id=DOF_ID, size=1, index=0)],
        valid=True,
    )


@pytest.fixture
def block_type_mock(flux_definition):
    return MagicMock(
        local_ids=[DOF_ID],
        fluxes_expressions={
            1: flux_definition,
        },
    )


@pytest.fixture
def alternative_block_type_mock():
    return MagicMock()


class TestModelComponentDescription:
    def test_default_constructor(self, model_a_type_mock):
        model_desc = ModelComponentDescription(MODEL_A_ID, model_a_type_mock)

        assert model_desc.name == MODEL_A_ID
        assert model_desc.described_type == model_a_type_mock
        assert model_desc.global_ids == {
            PARAM_A: f"{MODEL_A_ID}.a",
            PARAM_B: f"{MODEL_A_ID}.b",
        }
        assert model_desc.submodels == {}
        assert model_desc.alternative_types == {}
        assert model_desc.alternative_descriptions == {}
        assert model_desc.internal_variables == [(f"{MODEL_A_ID}.{PARAM_A}", 1)]
        assert model_desc.saved_quantities == [(f"{MODEL_A_ID}.{PARAM_B}", 1)]

    def test_constructor_with_global_ids(self, model_a_type_mock):
        global_ids = {PARAM_A: PARAM_A, PARAM_B: PARAM_B}
        model_desc = ModelComponentDescription(
            MODEL_A_ID, model_a_type_mock, global_ids=global_ids
        )

        assert model_desc.global_ids[PARAM_A] == PARAM_A
        assert model_desc.global_ids[PARAM_B] == PARAM_B

    def test_constructor_with_invalid_global_ids(self, model_a_type_mock):
        with pytest.raises(
            AttributeError, match=f"{MODEL_A_ID} has no attribute named {OTHER_PARAM}"
        ):
            ModelComponentDescription(
                MODEL_A_ID, model_a_type_mock, global_ids={OTHER_PARAM: ANY_VALUE}
            )

    def test_constructor_with_submodels(self, model_a_type_mock, model_b_type_mock):
        submodel_desc = ModelComponentDescription(SUBMODEL_ID, model_b_type_mock)
        model_desc = ModelComponentDescription(
            MODEL_A_ID, model_a_type_mock, submodels={MODEL_B_ID: submodel_desc}
        )

        assert MODEL_B_ID in model_desc.submodels
        assert model_desc.submodels[MODEL_B_ID].described_type == model_b_type_mock
        assert model_desc.submodels[MODEL_B_ID].name == f"{MODEL_A_ID}.{MODEL_B_ID}"
        assert model_desc.submodels[MODEL_B_ID].global_ids == {
            PARAM_C: f"{MODEL_A_ID}.{MODEL_B_ID}.{PARAM_C}",
            PARAM_D: f"{MODEL_A_ID}.{MODEL_B_ID}.{PARAM_D}",
        }

    def test_constructor_with_alternative_types(
        self, model_a_type_mock, alternative_model_a_type_mock
    ):
        model_desc = ModelComponentDescription(
            MODEL_A_ID,
            model_a_type_mock,
            alternative_types={ALTERNATIVE_TYPE_TAG: alternative_model_a_type_mock},
        )

        assert ALTERNATIVE_TYPE_TAG in model_desc.alternative_types
        assert (
            model_desc.alternative_types[ALTERNATIVE_TYPE_TAG]
            == alternative_model_a_type_mock
        )
        assert len(model_desc.alternative_descriptions) == 1
        assert ALTERNATIVE_TYPE_TAG in model_desc.alternative_descriptions
        assert model_desc.alternative_descriptions[ALTERNATIVE_TYPE_TAG].global_ids == {
            PARAM_A: f"{MODEL_A_ID}.a",
        }

    def test_constructor_with_alternative_types_on_submodels(
        self, model_a_type_mock, model_b_type_mock, alternative_model_a_type_mock
    ):
        submodel_desc = ModelComponentDescription(
            MODEL_A_ID,
            model_a_type_mock,
            alternative_types={ALTERNATIVE_TYPE_TAG: alternative_model_a_type_mock},
        )
        model_desc = ModelComponentDescription(
            MODEL_B_ID, model_b_type_mock, submodels={MODEL_A_ID: submodel_desc}
        )
        assert (
            ALTERNATIVE_TYPE_TAG in model_desc.submodels[MODEL_A_ID].alternative_types
        )
        assert (
            model_desc.submodels[MODEL_A_ID].alternative_types[ALTERNATIVE_TYPE_TAG]
            == alternative_model_a_type_mock
        )
        assert len(model_desc.submodels[MODEL_A_ID].alternative_descriptions) == 1

        assert (
            ALTERNATIVE_TYPE_TAG
            in model_desc.submodels[MODEL_A_ID].alternative_descriptions
        )
        assert model_desc.submodels[MODEL_A_ID].alternative_descriptions[
            ALTERNATIVE_TYPE_TAG
        ].global_ids == {
            PARAM_A: f"{MODEL_B_ID}.{MODEL_A_ID}.{PARAM_A}",
        }

    def test_add_submodel(self, model_a_type_mock, model_b_type_mock):
        model_desc = ModelComponentDescription(MODEL_A_ID, model_a_type_mock)
        submodel = model_desc.add_submodel(
            MODEL_B_ID, ModelComponentDescription(MODEL_B_ID, model_b_type_mock)
        )

        assert MODEL_B_ID in model_desc.submodels
        assert submodel.name == f"{MODEL_A_ID}.{MODEL_B_ID}"

    def test_remove_submodel(self, model_a_type_mock, model_b_type_mock):
        submodel = ModelComponentDescription(MODEL_B_ID, model_b_type_mock)
        model_desc = ModelComponentDescription(
            MODEL_A_ID, model_a_type_mock, submodels={MODEL_B_ID: submodel}
        )

        removed = model_desc.remove_submodel(MODEL_B_ID)
        assert removed.name == f"{MODEL_A_ID}.{MODEL_B_ID}"
        assert removed.described_type == submodel.described_type
        assert model_desc.submodels == {}

    def test_rename_global_id(self, model_a_type_mock):
        model_desc = ModelComponentDescription(MODEL_A_ID, model_a_type_mock)
        model_desc.rename_global_id(f"{MODEL_A_ID}.{PARAM_A}", PARAM_A)

        assert model_desc.global_ids[PARAM_A] == PARAM_A

    def test_rename_global_id_in_submodels(self, model_a_type_mock):
        submodel = ModelComponentDescription(MODEL_A_ID, model_a_type_mock)
        submodel.rename_global_id(f"{MODEL_A_ID}.{PARAM_A}", PARAM_A)
        model_desc = ModelComponentDescription(
            MODEL_A_ID, model_a_type_mock, submodels={SUBMODEL_ID: submodel}
        )
        model_desc.rename_global_id(f"{MODEL_A_ID}.{PARAM_A}", PARAM_A)
        model_desc.rename_global_id(PARAM_A, PARAM_C)

        assert model_desc.global_ids[PARAM_A] == PARAM_C
        assert model_desc.submodels[SUBMODEL_ID].global_ids[PARAM_A] == PARAM_C

    def test_rename_global_id_in_alternative_description(self, model_a_type_mock):
        model_desc = ModelComponentDescription(
            MODEL_A_ID,
            model_a_type_mock,
            alternative_types={ALTERNATIVE_TYPE_TAG: model_a_type_mock},
        )
        model_desc.rename_global_id(f"{MODEL_A_ID}.{PARAM_A}", PARAM_B)

        assert model_desc.global_ids[PARAM_A] == PARAM_B
        assert (
            model_desc.alternative_descriptions[ALTERNATIVE_TYPE_TAG].global_ids[
                PARAM_A
            ]
            == PARAM_B
        )

    def test_internal_variables_expressions(self, model_a_type_mock):
        model_desc = ModelComponentDescription(MODEL_A_ID, model_a_type_mock)

        assert len(model_desc.internal_variables) == 1
        assert model_desc.internal_variables[0][0] == f"{MODEL_A_ID}.{PARAM_A}"
        assert model_desc.internal_variables[0][1] == 1

        assert len(model_desc.internal_expressions) == 1
        assert len(model_desc.internal_expressions[0].terms) == 1
        assert (
            model_desc.internal_expressions[0].terms[0].term_id
            == f"{MODEL_A_ID}.{PARAM_A}"
        )
        assert model_desc.internal_expressions[0].terms[0].size == 1
        assert model_desc.internal_expressions[0].terms[0].index == 0

    def test_saved_quantities_expressions(self, model_a_type_mock):
        model_desc = ModelComponentDescription(MODEL_A_ID, model_a_type_mock)

        assert len(model_desc.internal_variables) == 1
        assert model_desc.saved_quantities[0][0] == f"{MODEL_A_ID}.{PARAM_B}"
        assert model_desc.saved_quantities[0][1] == 1

        assert len(model_desc.saved_quantities_expressions) == 1
        assert len(model_desc.saved_quantities_expressions[0].terms) == 1
        assert (
            model_desc.saved_quantities_expressions[0].terms[0].term_id
            == f"{MODEL_A_ID}.{PARAM_B}"
        )
        assert model_desc.saved_quantities_expressions[0].terms[0].size == 1
        assert model_desc.saved_quantities_expressions[0].terms[0].index == 0

    def test_internal_variables_extends_from_submodels(
        self, model_a_type_mock, model_b_type_mock, term_a_definition
    ):
        submodel = ModelComponentDescription(MODEL_A_ID, model_a_type_mock)
        model_desc = ModelComponentDescription(
            MODEL_B_ID, model_b_type_mock, submodels={MODEL_A_ID: submodel}
        )
        assert model_desc.internal_variables == [
            (f"{MODEL_B_ID}.{MODEL_A_ID}.{PARAM_A}", 1)
        ]
        assert len(model_desc.internal_expressions) == 0  # expressions do not extend

    def test_saved_quantities_extends_from_submodels(
        self, model_a_type_mock, model_b_type_mock
    ):
        submodel = ModelComponentDescription(MODEL_A_ID, model_a_type_mock)
        model_desc = ModelComponentDescription(
            MODEL_B_ID, model_b_type_mock, submodels={MODEL_A_ID: submodel}
        )

        assert model_desc.saved_quantities == [
            (f"{MODEL_B_ID}.{MODEL_A_ID}.{PARAM_B}", 1)
        ]
        assert (
            len(model_desc.saved_quantities_expressions) == 0
        )  # expressions do not extend


class TestBlockDescription:
    def test_constructor(self, block_type_mock):
        block_desc = BlockDescription(BLOCK_ID, block_type_mock, FLUX_TYPE)
        assert block_desc.flux_type == FLUX_TYPE
        assert len(block_desc.fluxes) == 1
        assert 1 in block_desc.fluxes

    def test_set_attributes_error(self, block_type_mock):
        block_desc = BlockDescription(BLOCK_ID, block_type_mock, FLUX_TYPE)

        with pytest.raises(AttributeError):
            block_desc.flux_type = ""

    def test_constructor_with_alternative_types(
        self, block_type_mock, alternative_block_type_mock, model_a_type_mock
    ):
        alternative_types = {
            ALTERNATIVE_TYPE_TAG: alternative_block_type_mock,
        }
        block_desc = BlockDescription(
            BLOCK_ID, block_type_mock, FLUX_TYPE, alternative_types=alternative_types
        )
        assert block_desc.alternative_types == alternative_types
        assert len(block_desc.alternative_descriptions) == 1
        assert (
            block_desc.alternative_descriptions[ALTERNATIVE_TYPE_TAG].flux_type
            == FLUX_TYPE
        )

    def test_fluxes_expressions(self, block_type_mock):
        block_desc = BlockDescription(BLOCK_ID, block_type_mock, FLUX_TYPE)
        assert len(block_desc.fluxes) == 1
        assert 1 in block_desc.fluxes
        assert block_desc.fluxes[1].size == 1
