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

import sys
from dataclasses import dataclass
from unittest.mock import patch

import numpy as np
import pytest
import regex as re

from physioblocks.computing.quantities import Quantity
from physioblocks.configuration.base import Configuration, ConfigurationError
from physioblocks.configuration.functions import load, save

DATA_CLASS_OBJECT_ITEM_ID = "data_class_obj"
CONFIGURATION_LABEL = "data_class_obj"
OBJ_KEY = "obj"
PARAM_A_KEY = "a"
PARAM_B_KEY = "b"
WRONG_KEY = "wrong"
PARAM_A_VALUE = "param_a"
PARAM_B_VALUE = 0.1
WRONG_VALUE = "wrong"
SCALAR_REF = 0.0
VECTOR_REF = [0.1, 0.2, 0.3]


@dataclass
class DataClassObj:
    a: str
    b: float

    def __eq__(self, value):
        return (
            isinstance(value, DataClassObj) and value.a == self.a and value.b == self.b
        )


@dataclass
class UnregisteredClassObj:
    pass


@pytest.fixture
def ref_base_object():
    return DataClassObj(PARAM_A_VALUE, PARAM_B_VALUE)


@pytest.fixture
def ref_base_object_config():
    return Configuration(
        DATA_CLASS_OBJECT_ITEM_ID,
        {PARAM_A_KEY: PARAM_A_VALUE, PARAM_B_KEY: PARAM_B_VALUE},
    )


@pytest.fixture
def ref_base_object_config_exception(ref_base_object_config):
    ref_base_object_config[WRONG_KEY] = WRONG_VALUE
    return ref_base_object_config


@pytest.fixture
def ref_dict(ref_base_object: DataClassObj):
    return {OBJ_KEY: ref_base_object}


@pytest.fixture
def ref_dict_config(ref_base_object_config: Configuration) -> Configuration:
    return {
        OBJ_KEY: ref_base_object_config,
    }


@pytest.fixture
def ref_list(ref_base_object: DataClassObj):
    return [ref_base_object]


@pytest.fixture
def ref_list_config(ref_base_object_config: Configuration) -> Configuration:
    return [ref_base_object_config]


@pytest.fixture
def ref_unsorted_configuration(ref_base_object_config):
    return {
        "a": "b",
        "h": {
            "h.a": "a",
            "h.b": "b",
            "h.d": ["h.a", "h.b", "h.c"],
            "h.e": {"h.e.a": "a", "h.e.b": "h.d"},
            "h.c": ref_base_object_config,
        },
        "b": 0.1,
        "c": "h.a",
        "d": "h.b",
        "e": "h.c",
        "f": "h.d",
        "g": "h.e",
    }


@pytest.fixture
def self_referencing_configuration(ref_base_object_config):
    return {"a": "b", "b": "c", "c": "a"}


@pytest.fixture
def deep_self_referencing_configuration(ref_base_object_config):
    return {"a": "b", "b": "c", "c": {"c.a": ["a", "a1", "a2"]}}


@pytest.fixture
def ref_sorted_obj(ref_base_object):
    return {
        "b": 0.1,
        "a": 0.1,
        "h": {
            "h.a": 0.1,
            "h.b": 0.1,
            "h.c": ref_base_object,
            "h.e": {"h.e.a": 0.1, "h.e.b": [0.1, 0.1, ref_base_object]},
            "h.d": [0.1, 0.1, ref_base_object],
        },
        "c": 0.1,
        "d": 0.1,
        "e": ref_base_object,
        "f": [0.1, 0.1, ref_base_object],
        "g": {"h.e.a": 0.1, "h.e.b": [0.1, 0.1, ref_base_object]},
    }


@pytest.fixture
def scalar_qty() -> Quantity:
    return Quantity(0.0)


@pytest.fixture
def vector_qty() -> Quantity:
    return Quantity(VECTOR_REF)


@patch(
    "physioblocks.registers.type_register.__type_register",
    new={
        DATA_CLASS_OBJECT_ITEM_ID: DataClassObj,
        DataClassObj: DATA_CLASS_OBJECT_ITEM_ID,
    },
)
class TestLoad:
    def test_load_base_types(self):
        # load float, int, bool values:
        float_obj = load(1.3)
        assert float_obj == pytest.approx(1.3)
        float_obj = load("1.7", configuration_type=float)
        assert float_obj == pytest.approx(1.7)

        loaded_int_obj = load(3)
        assert loaded_int_obj == 3
        loaded_int_obj = load("1", configuration_type=int)
        assert loaded_int_obj == 1
        loaded_int_obj = load(False, configuration_type=int)
        assert loaded_int_obj == 0

        loaded_bool_obj = load(True)
        assert loaded_bool_obj is True
        loaded_bool_obj = load("False", configuration_type=bool)
        assert loaded_bool_obj is False
        loaded_bool_obj = load(1, configuration_type=bool)
        assert loaded_bool_obj is True

    def test_load_from_reference(self):
        references = {
            "a": "0.1",
            "b": 0,
            "c": "3",
        }
        assert load(
            "a", configuration_type=float, configuration_references=references
        ) == pytest.approx(0.1)
        assert (
            load("b", configuration_type=bool, configuration_references=references)
            is False
        )
        assert load(
            "c", configuration_type=int, configuration_references=references
        ) == pytest.approx(3)

    def test_load_base_object(
        self, ref_base_object_config: Configuration, ref_base_object: DataClassObj
    ):
        # use base load
        base_object = load(ref_base_object_config)
        assert base_object == ref_base_object

    def test_load_base_object_list_args(self, ref_base_object: DataClassObj):
        base_object = load(
            [PARAM_A_VALUE, PARAM_B_VALUE], configuration_type=DataClassObj
        )
        assert base_object == ref_base_object

    def test_load_base_object_dict_args(
        self, ref_base_object_config: Configuration, ref_base_object: DataClassObj
    ):
        base_object = load(
            {PARAM_B_KEY: PARAM_B_VALUE, PARAM_A_KEY: PARAM_A_VALUE},
            configuration_type=DataClassObj,
        )
        assert base_object == ref_base_object

    def test_load_base_object_with_initialized_object(
        self, ref_base_object_config: Configuration, ref_base_object: DataClassObj
    ):
        # use base load with an object to configure
        configuration_object = DataClassObj("", 0.0)
        base_object = load(
            ref_base_object_config, configuration_object=configuration_object
        )
        assert base_object == ref_base_object
        assert configuration_object is base_object

    def test_load_base_object_arg_dict_with_initialized_object(
        self, ref_base_object: DataClassObj
    ):
        # use base load with dict of arguments and an object to configure
        configuration_object = DataClassObj("", 0.0)
        base_object = load(
            {PARAM_B_KEY: PARAM_B_VALUE, PARAM_A_KEY: PARAM_A_VALUE},
            configuration_type=DataClassObj,
            configuration_object=configuration_object,
        )
        assert base_object == ref_base_object
        assert configuration_object is base_object

    def test_load_base_object_arg_list_with_initialized_object_error(self):
        # use base load with dict of arguments and an object to configure
        arg_list = [PARAM_A_VALUE, PARAM_B_VALUE]
        configuration_object = DataClassObj("", 0.0)
        err_msg = str.format(
            "Can not set arguments {0} to existing object {1}. Missing attribute keys.",
            arg_list,
            configuration_object,
        )
        with pytest.raises(ConfigurationError, match=re.escape(err_msg)):
            load(
                arg_list,
                configuration_type=DataClassObj,
                configuration_object=configuration_object,
            )

    def test_load_base_object_from_reference(
        self, ref_base_object_config: Configuration, ref_base_object: DataClassObj
    ):
        references = {DATA_CLASS_OBJECT_ITEM_ID: ref_base_object}
        base_object = load(ref_base_object_config, configuration_references=references)
        assert base_object == ref_base_object

    def test_load_base_object_exception(
        self, ref_base_object_config_exception: Configuration
    ):
        err_msg = str.format("Error while initialising key {0}", WRONG_KEY)
        with pytest.raises(ConfigurationError, match=err_msg):
            load(ref_base_object_config_exception, configuration_key=WRONG_KEY)

        err_msg = str.format(
            "Type {0} can not be loaded as a configuration.",
            UnregisteredClassObj.__name__,
        )
        unregistered_config = UnregisteredClassObj()
        with pytest.raises(TypeError, match=err_msg):
            load(unregistered_config)

    def test_load_dict(self, ref_dict: dict, ref_dict_config: Configuration):
        loaded_dict = load(ref_dict_config)
        assert loaded_dict == ref_dict

        configured_dict = {"a": 0.1, "b": 0.2}
        updated_dict = configured_dict.copy()
        updated_dict.update(ref_dict)
        loaded_dict = load(ref_dict_config, configuration_object=configured_dict)
        assert loaded_dict == updated_dict
        assert sys.getrefcount(loaded_dict) == sys.getrefcount(configured_dict)

    def test_load_list(
        self,
        ref_list: list,
        ref_list_config: Configuration,
        ref_base_object: DataClassObj,
        ref_base_object_config: Configuration,
    ):
        loaded_list = load(ref_list_config)
        assert loaded_list == ref_list

        configured_list = [ref_base_object]
        extended_list_to_load = [
            ref_base_object_config,
            ref_base_object_config,
            0.1,
            0.2,
        ]
        extended_list_ref = [ref_base_object, ref_base_object, 0.1, 0.2]
        loaded_list = load(extended_list_to_load, configuration_object=configured_list)
        assert loaded_list == extended_list_ref
        assert sys.getrefcount(loaded_list) == sys.getrefcount(configured_list)

    def test_load_with_sort(
        self, ref_unsorted_configuration: Configuration, ref_sorted_obj: Configuration
    ):
        loaded_obj = load(
            ref_unsorted_configuration,
            configuration_sort=True,
        )
        assert loaded_obj == ref_sorted_obj

    def test_load_with_sort_self_referencing_config(
        self, self_referencing_configuration
    ):
        err_msg = str.format(
            "Item {0} is referencing itself: {1}", "a", ["a", "b", "c"]
        )
        with pytest.raises(ConfigurationError, match=re.escape(err_msg)):
            load(
                self_referencing_configuration,
                configuration_sort=True,
            )

    def test_load_with_sort_deep_self_referencing_config(
        self, deep_self_referencing_configuration
    ):
        err_msg = str.format(
            "Item {0} is referencing itself: {1}", "a", ["a", "b", "c"]
        )
        with pytest.raises(ConfigurationError, match=re.escape(err_msg)):
            load(
                deep_self_referencing_configuration,
                configuration_sort=True,
            )


@patch(
    "physioblocks.registers.type_register.__type_register",
    new={
        DATA_CLASS_OBJECT_ITEM_ID: DataClassObj,
        DataClassObj: DATA_CLASS_OBJECT_ITEM_ID,
    },
)
class TestSave:
    def test_save_base_object(
        self, ref_base_object_config: Configuration, ref_base_object: DataClassObj
    ):
        config = save(ref_base_object)
        assert config == ref_base_object_config

        def mock_save_function(obj, *args, **kwargs):
            return ref_base_object_config

        with patch(
            "physioblocks.registers.save_function_register.__save_functions_register",
            new={DataClassObj: mock_save_function, mock_save_function: DataClassObj},
        ):
            config = save(ref_base_object)
            assert config == ref_base_object_config

    def test_save_base_object_with_reference(self, ref_base_object: DataClassObj):
        config_key = "config_ref"
        config = save(
            ref_base_object, configuration_references={config_key: ref_base_object}
        )
        assert config == config_key

    def test_save_base_object_configuration_error(self):
        obj = UnregisteredClassObj()
        with pytest.raises(
            ConfigurationError,
            match=re.escape(str.format("Can not configure object {0}.", obj)),
        ):
            save(obj)

    def test_save_dict(self, ref_dict: dict, ref_dict_config: Configuration):
        dict_config = save(ref_dict)
        assert dict_config == ref_dict_config

    def test_save_list(self, ref_list: list, ref_list_config: Configuration):
        list_config = save(ref_list)
        assert list_config == ref_list_config

    def test_save_quantities(self, scalar_qty, vector_qty):
        assert save(scalar_qty) == SCALAR_REF
        assert save(vector_qty) == VECTOR_REF

    def test_save_bool(self):
        assert save(True) == "True"
        assert save(False) == "False"

    def test_save_base_types_with_reference(self):
        references = {"a": 0.1, "b": "str", "c": 3}
        assert save(0.1, configuration_references=references) == "a"
        assert save("str", configuration_references=references) == "b"
        assert save(3, configuration_references=references) == "c"

    def test_save_ndarray(self):
        assert save(np.array(VECTOR_REF)) == VECTOR_REF
