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

from physioblocks.configuration import Configuration
from physioblocks.configuration.constants import CONDITION_NAME_ID, CONDITION_TYPE_ID
from physioblocks.configuration.functions import load, save
from physioblocks.description.nets import BOUNDARY_CONDITION_ID, BoundaryCondition

CONDITION_TYPE = "condition_type"
CONDITION_ID = "condition_id"


@pytest.fixture
def ref_config() -> Configuration:
    config = Configuration(BOUNDARY_CONDITION_ID)

    config[CONDITION_TYPE_ID] = CONDITION_TYPE
    config[CONDITION_NAME_ID] = CONDITION_ID

    return config


@pytest.fixture
def ref_condition() -> BoundaryCondition:
    return BoundaryCondition(CONDITION_TYPE, CONDITION_ID)


class TestBoundaryConditionConfiguration:
    def test_save_boundary_condition_config(
        self, ref_config: Configuration, ref_condition: BoundaryCondition
    ):
        configuration = save(ref_condition)
        assert ref_config == configuration

    def test_load_boundary_condition_config(self, ref_config: Configuration):
        condition = load(ref_config)

        assert isinstance(condition, BoundaryCondition)
        assert condition.condition_id == CONDITION_ID
        assert condition.condition_type == CONDITION_TYPE
