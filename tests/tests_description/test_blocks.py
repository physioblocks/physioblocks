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

import pytest

from physioblocks.computing.models import ModelComponent
from physioblocks.description.blocks import (
    ID_SEPARATOR,
    Block,
    BlockDescription,
    ModelComponentDescription,
)

BLOCK_ID = "block"
MODEL_ID = "model"

FLUX_TYPE = "flux_type"
DOF_TYPE = "dof_type"
DOF_ID = "dof_id"

FLUX_TYPE_A = "flux_type_a"
DOF_TYPE_A = "dof_type_a"
FLUX_TYPE_B = "flux_type_b"
DOF_TYPE_B = "dof_type_b"


class TestBlockDescription:
    def test_constructor(self):
        block_desc = BlockDescription(BLOCK_ID, Block, FLUX_TYPE)

        assert block_desc.name == BLOCK_ID
        assert block_desc.described_type == Block
        assert block_desc.flux_type == FLUX_TYPE
        assert block_desc.global_ids == {}
        assert block_desc.submodels == {}

        with pytest.raises(AttributeError):
            block_desc.name = ""

        with pytest.raises(AttributeError):
            block_desc.described_type = None

        with pytest.raises(AttributeError):
            block_desc.global_ids = None

        with pytest.raises(AttributeError):
            block_desc.flux_type = ""

        block_desc.global_ids["a"] = "b"
        assert block_desc.global_ids == {}

        with pytest.raises(AttributeError):
            block_desc.submodels = ""

        block_desc.submodels["a"] = "b"
        assert block_desc.submodels == {}

        # test too many attributes:
        error_msg = str.format("{0} has no attribute named {1}.", "Block", "attr")
        with pytest.raises(AttributeError, match=error_msg):
            block_desc = BlockDescription(
                BLOCK_ID, Block, FLUX_TYPE, {"attr": "error_attr"}
            )

    def test_add_remove_submodels(self):
        block_desc = BlockDescription(BLOCK_ID, Block, FLUX_TYPE)

        model = ModelComponentDescription(MODEL_ID, ModelComponent)
        submodel = block_desc.add_submodel(MODEL_ID, model)

        assert block_desc.submodels[MODEL_ID] == submodel
        assert submodel.name == ID_SEPARATOR.join([BLOCK_ID, MODEL_ID])

        block_desc.remove_submodel(MODEL_ID)
        assert block_desc.submodels == {}
