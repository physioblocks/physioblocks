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

from copy import deepcopy

import pytest

from physioblocks.configuration.base import Configuration

ROOT_ID = "root"
ITEMS_ID = "items"
ITEM_A_ID = "a"
ITEM_B_ID = "b"
TYPE_1_ID = "type_1"
VAL_ID = "val"
TYPE_2_ID = "type_2"
SUB_TYPE_1_ID = "sub_type_2_1"
SUB_TYPE_2_ID = "sub_type_2_2"
FIRST = "first"
SECOND = "second"
WRONG_KEY = "wrong"


@pytest.fixture
def configuration() -> Configuration:
    root_item = Configuration(ROOT_ID)
    root_item[VAL_ID] = True
    root_item[ITEM_A_ID] = [
        Configuration(TYPE_1_ID, {VAL_ID: FIRST}),
        Configuration(TYPE_1_ID, {VAL_ID: SECOND}),
    ]
    child_2 = Configuration(TYPE_2_ID)

    child_2[ITEMS_ID] = [Configuration(SUB_TYPE_1_ID), Configuration(SUB_TYPE_2_ID)]
    root_item[ITEM_B_ID] = child_2

    return root_item


class TestConfiguration:
    def test_get_set_items(self, configuration: Configuration):
        assert ITEM_A_ID in configuration
        assert configuration[VAL_ID] is True
        configuration[VAL_ID] = False
        assert configuration[VAL_ID] is False

        for key in configuration:
            assert key in [VAL_ID, ITEM_A_ID, ITEM_B_ID]

    def test_items(self, configuration: Configuration):
        assert configuration.items() == configuration.configuration_items.items()

    def test_keys(self, configuration: Configuration):
        assert configuration.keys() == configuration.configuration_items.keys()

    def test_equals(self, configuration: Configuration):
        assert configuration != configuration[VAL_ID]
        config_copy = deepcopy(configuration)
        assert configuration == config_copy
        config_ne_label = deepcopy(config_copy)
        config_ne_label.label = "Other"
        assert configuration != config_ne_label
        config_ne_len = deepcopy(config_copy)
        config_ne_len.configuration_items.pop(VAL_ID)
        assert configuration != config_ne_len
        config_ne_key = deepcopy(config_copy)
        config_ne_key.configuration_items.pop(VAL_ID)
        config_ne_key["Other"] = True
        assert configuration != config_ne_key
        config_ne_val = deepcopy(config_copy)
        config_ne_val.configuration_items[VAL_ID] = False
        assert configuration != config_ne_val

    def test_copy(self, configuration: Configuration):
        config_copy = configuration.copy()
        assert configuration is not config_copy
        assert configuration.configuration_items is not config_copy.configuration_items
        assert configuration == config_copy
