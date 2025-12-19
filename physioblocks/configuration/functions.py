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

"""Declares functions to load and save PhysioBlocks object to generic
:class:`~physioblocks.configuration.base.Configuration` objects.

Before using generic :func:`load` and :func:`save` functions on a PhysioBlocks object,
the object type must be registered with the
:func:`~physioblocks.registers.type_register.register_type` decorator.

To define a specific behavior when saving or loading an registered object with the
generic :func:`load` or :func:`save` functions, declare a function decorated with
:func:`~physioblocks.registers.load_function_register.loads` or
:func:`~physioblocks.registers.save_function_register.saves`.

.. note::

    If you want to create a **Configurable Item** for a dataclass type,
    you will not have to register a specific save or load function.

    Registering the type the :func:`~physioblocks.registers.type_register.register_type`
    decorator will suffice to create a configuration item that needs the same parameters
    as the dataclass.

See :doc:`register module <./registers>` to for decorators documentation to
:func:`~physioblocks.registers.type_register.register_type` as well as
:func:`~physioblocks.registers.load_function_register.loads` and
:func:`~physioblocks.registers.save_function_register.saves`.
"""

import functools
from collections.abc import Iterable, Mapping, Sequence
from inspect import signature
from typing import Any, TypeAlias, TypeVar

import numpy as np
from numpy.typing import NDArray

from physioblocks.configuration.base import Configuration, ConfigurationError
from physioblocks.registers.load_function_register import get_load_function, loads
from physioblocks.registers.save_function_register import (
    get_save_function,
    has_save_function,
)
from physioblocks.registers.type_register import (
    get_registered_type,
    get_registered_type_id,
    is_registered,
)

BaseTypes: TypeAlias = float | int | bool | str
"""Type alias for basic types usable in a Configuration File"""


def load(
    configuration: Any,
    configuration_key: str | None = None,
    configuration_object: Any | None = None,
    configuration_type: type[Any] | None = None,
    configuration_references: dict[str, Any] | None = None,
    configuration_sort: bool = False,
) -> Any:
    """
    Generic load an object from the given configuration item.

    The method can load:
      - :class:`~physioblocks.configuration.base.Configuration`: Use the matching
        registered load function.
      - `dict` and `list`: recursivly load values in the collection

    :param configuration: the configuration to load
    :type configuration: Any

    :param configuration_key: (optional) key of the configuration in the parent
      configuration item.
    :type configuration_key: str

    :param configuration_object: (optional) The object to configure.
      If empty, a the object is first instanciated then configured.
    :type configuration_object: Any

    :param configuration_type: (optional) the type of the object to configure.
      If empty, it is determined from the configuration object.
    :type configuration_type: Any

    :param configuration_references: (optional) mapping of configuration item keys
      with already configured objects to use in the current configured object.
    :type configuration_references: dict[str, Any]

    :param configuration_sort: (optional) flag to signal that configuration items
      should be sorted be sorted before they are loaded. Default is False.
    :type configuration_sort: dict[str, Any]

    :return: the configured object
    :rtype: Any
    """
    if (
        isinstance(configuration, str)
        and configuration_references is not None
        and configuration in configuration_references
    ):
        # the value is already in the references:
        return (
            configuration_references[configuration]
            if configuration_type is None
            else configuration_type(configuration_references[configuration])
        )

    elif configuration_type is not None:
        load_func = get_load_function(configuration_type)
        return load_func(
            configuration,
            configuration_key=configuration_key,
            configuration_object=configuration_object,
            configuration_type=configuration_type,
            configuration_references=configuration_references,
            configuration_sort=configuration_sort,
        )
    elif isinstance(configuration, BaseTypes):
        # No load function required
        return configuration

    elif isinstance(configuration, Configuration):
        return load_configuration(
            configuration,
            configuration_key=configuration_key,
            configuration_object=configuration_object,
            configuration_type=configuration_type,
            configuration_references=configuration_references,
            configuration_sort=configuration_sort,
        )
    elif isinstance(configuration, Mapping):
        return load_dict(
            configuration,
            configuration_key=configuration_key,
            configuration_object=configuration_object,
            configuration_type=configuration_type,
            configuration_references=configuration_references,
            configuration_sort=configuration_sort,
        )
    elif isinstance(configuration, Sequence):
        return load_list(
            configuration,
            configuration_key=configuration_key,
            configuration_object=configuration_object,
            configuration_type=configuration_type,
            configuration_references=configuration_references,
            configuration_sort=configuration_sort,
        )

    raise TypeError(
        str.format(
            "Type {0} can not be loaded as a configuration.",
            type(configuration).__name__,
        )
    )


def load_configuration(
    configuration: Configuration,
    configuration_key: str | None = None,
    configuration_object: Any | None = None,
    configuration_references: dict[str, Any] | None = None,
    configuration_sort: bool = False,
    *args: Any,
    **kwargs: Any,
) -> Any:
    """
    Specific load function for a
    :class:`~physioblocks.configuration.base.Configuration`: configuration item.

    It recursivly loads any configuration item used in the ``configuration`` parameter.

    :param configuration: the configuration item to load
    :type configuration: Configuration

    :param configuration_key: (optional) key of the configuration in the parent
      configuration item.
    :type configuration_key: str

    :param configuration_object: (optional) The object to configure.
      If empty, a the object is first instanciated then configured.
    :type configuration_object: Any

    :param configuration_type: (optional) the type of the object to configure.
      If empty, it is determined from the configuration object.
    :type configuration_type: Any

    :param configuration_references: (optional) mapping of configuration item keys
      with already configured objects to use in the current configured object.
    :type configuration_references: dict[str, Any]

    :param configuration_sort: (optional) flag to signal that configuration items
      should be sorted be sorted before they are loaded. Default is False.
    :type configuration_sort: dict[str, Any]

    :return: the configured object
    :rtype: Any
    """
    configuration = (
        configuration
        if configuration_sort is False
        else __sort_configuration(configuration)
    )

    new_configuration_type = get_registered_type(configuration.label)
    load_func = get_load_function(new_configuration_type)

    return load_func(
        configuration,
        configuration_key=configuration_key,
        configuration_object=configuration_object,
        configuration_type=new_configuration_type,
        configuration_references=configuration_references,
        configuration_sort=configuration_sort,
    )


def load_dict(
    configuration: Mapping[str, Any],
    configuration_object: dict[str, Any] | None = None,
    configuration_references: dict[str, Any] | None = None,
    configuration_sort: bool = False,
    *args: Any,
    **kwargs: Any,
) -> dict[str, Any]:
    """
    Specific load function for a `Mapping` configuration item.

    It recursivly loads any configuration item used in the mapping values.

    :param configuration: the configuration item to load
    :type configuration: Configuration

    :param configuration_key: (optional) key of the configuration in the parent
      configuration item.
    :type configuration_key: str

    :param configuration_object: (optional) The object to configure.
      If empty, a the object is first instanciated then configured.
    :type configuration_object: Any

    :param configuration_type: (optional) the type of the object to configure.
      If empty, it is determined from the configuration object.
    :type configuration_type: Any

    :param configuration_references: (optional) mapping of configuration item keys
      with already configured objects to use in the current configured object.
    :type configuration_references: dict[str, Any]

    :param configuration_sort: (optional) flag to signal that configuration items
      should be sorted be sorted before they are loaded. Default is False.
    :type configuration_sort: dict[str, Any]

    :return: the configured object
    :rtype: Any
    """
    configuration = (
        configuration
        if configuration_sort is False
        else __sort_configuration(configuration)
    )

    if configuration_object is None:
        configuration_object = {}

    updated_references = (
        configuration_references.copy() if configuration_references is not None else {}
    )
    configuration_values = {}

    for key, value in configuration.items():
        loaded_obj = load(
            value,
            configuration_key=key,
            configuration_object=configuration_object.get(key),
            configuration_type=type(configuration_object.get(key))
            if configuration_object.get(key) is not None
            and not isinstance(configuration_object.get(key), BaseTypes)
            else None,
            configuration_references=updated_references,
            configuration_sort=configuration_sort,
        )
        configuration_values[key] = loaded_obj
        updated_references[key] = loaded_obj
        if isinstance(loaded_obj, Mapping):
            updated_references.update(loaded_obj)

    configuration_object.update(configuration_values)

    return configuration_object


def load_list(
    configuration: Sequence[Any],
    configuration_object: list[Any] | None = None,
    configuration_references: dict[str, Any] | None = None,
    configuration_sort: bool = False,
    *args: Any,
    **kwargs: Any,
) -> Sequence[Any]:
    """
    Specific load function for a `Sequence` configuration item.

    It recursivly loads any configuration item used in the sequence values.

    :param configuration: the configuration item to load
    :type configuration: Configuration

    :param configuration_key: (optional) key of the configuration in the parent
      configuration item.
    :type configuration_key: str

    :param configuration_object: (optional) The object to configure.
      If empty, a the object is first instanciated then configured.
    :type configuration_object: Any

    :param configuration_type: (optional) the type of the object to configure.
      If empty, it is determined from the configuration object.
    :type configuration_type: Any

    :param configuration_references: (optional) mapping of configuration item keys
      with already configured objects to use in the current configured object.
    :type configuration_references: dict[str, Any]

    :param configuration_sort: (optional) flag to signal that configuration items
      should be sorted be sorted before they are loaded. Default is False.
    :type configuration_sort: dict[str, Any]

    :return: the configured object
    :rtype: Any
    """

    if configuration_object is None:
        configuration_object = []

    configuration_values = [
        load(
            configuration[index],
            configuration_object=configuration_object[index]
            if index < len(configuration_object)
            else None,
            configuration_type=type(configuration_object[index])
            if index < len(configuration_object)
            and not isinstance(configuration[index], BaseTypes)
            else None,
            configuration_references=configuration_references,
            configuration_sort=configuration_sort,
        )
        for index in range(0, len(configuration))
    ]

    return configuration_values


@loads(bool)
def _bool_load(
    configuration: Any,
    *args: Any,
    **kwargs: Any,
) -> bool:
    if isinstance(configuration, str):
        return configuration.lower() == str(True)
    return bool(configuration)


T = TypeVar("T")


@loads(object)
def _base_load(
    configuration: Any,
    configuration_key: str | None = None,
    configuration_object: T | None = None,
    configuration_type: type[T] | None = None,
    configuration_references: dict[str, Any] | None = None,
    configuration_sort: bool = False,
    *args: Any,
    **kwargs: Any,
) -> T:
    """
    Load function called when no other load function is defined.

    :param configuration: the configuration to load
    :type configuration: Configuration

    :param configuration_object: The object to configure.
      If empty, a new object is created and configured.
    :type configuration_object: Any

    :return: the configured object
    :rtype: Any
    """
    if configuration_type is None and configuration_object is not None:
        configuration_type = type(configuration_object)
    elif configuration_type is None:
        raise ConfigurationError(
            str.format("Missing configuration type for {0}:{1}.", configuration_key)
        )

    config_args: list[Any] = []
    config_kwargs: dict[str, Any] = {}

    if isinstance(configuration, Configuration | Mapping):
        config_kwargs.update(configuration)
    elif isinstance(configuration, str | float | int | bool):
        config_args.append(configuration)
    elif isinstance(configuration, Sequence):
        config_args.extend(configuration)

    # load the values in the provided arguments
    config_args = load(
        config_args,
        configuration_key=configuration_key,
        configuration_references=configuration_references,
        configuration_sort=configuration_sort,
    )
    config_kwargs = load(
        config_kwargs,
        configuration_key=configuration_key,
        configuration_references=configuration_references,
        configuration_sort=configuration_sort,
    )

    if configuration_object is None:
        try:
            configuration_object = configuration_type(*config_args, **config_kwargs)
        except Exception as exception:
            raise ConfigurationError(
                str.format("Error while initialising key {0}", configuration_key)
            ) from exception
    else:
        if len(config_args) == 0:
            for key, value in config_kwargs.items():
                setattr(configuration_object, key, value)
        else:
            raise ConfigurationError(
                str.format(
                    "Can not set arguments {0} to existing object {1}. "
                    "Missing attribute keys.",
                    config_args,
                    configuration_object,
                )
            )

    return configuration_object


@functools.singledispatch
def save(
    obj: Any,
    configuration_references: dict[str, Any] | None = None,
    *args: Any,
    **kwargs: Any,
) -> Any:
    """
    Save an object to a configuration.

    It first check if the object has a ``save`` function registered and use it.

    When no specific ``save`` function is registered for a object type,
    it saves recursivly every annotated parameters of the object class.

    :param obj: the object to save
    :type obj: Any

    :return: the object configuration
    :rtype: Any

    :raise ConfigurationError: raise a Configuration Error when the
      object can not be saved to a configuration.
    """

    # try to replace the object with a reference when possible.
    if configuration_references is not None:
        obj_reference = next(
            (key for key, item in configuration_references.items() if item is obj), None
        )
        if obj_reference is not None:
            return obj_reference

    obj_type = type(obj)

    if has_save_function(obj_type) is True:
        save_func = get_save_function(obj_type)
        return save_func(
            obj, *args, configuration_references=configuration_references, **kwargs
        )
    elif is_registered(obj_type):
        return _base_save_obj(
            obj, *args, configuration_references=configuration_references, **kwargs
        )
    raise ConfigurationError(str.format("Can not configure object {0}.", obj))


def _base_save_obj(obj: Any, *args: Any, **kwargs: Any) -> Configuration:
    obj_type = type(obj)
    type_id = get_registered_type_id(obj_type)

    # get parameters of the constructor
    parameters_ids = _get_init_parameters(obj_type)
    config_parameters = {
        key: save(getattr(obj, key), *args, **kwargs) for key in parameters_ids
    }
    return Configuration(type_id, config_parameters)


@save.register
def _save_dict(obj: Mapping, *args: Any, **kwargs: Any) -> dict[str, Any]:  # type: ignore
    """Save specific function for mappings."""
    return {
        key: save(
            value,
            *args,
            **kwargs,
        )
        for key, value in obj.items()
    }


@save.register
def _save_list(obj: Sequence, *args: Any, **kwargs: Any) -> list[Any]:  # type: ignore
    return [
        save(
            value,
            *args,
            **kwargs,
        )
        for value in obj
    ]


@save.register(float)
@save.register(str)
@save.register(int)
def _save_base_types(
    obj: Any,
    configuration_references: dict[str, Any] | None = None,
    *args: Any,
    **kwargs: Any,
) -> Any:
    if configuration_references is not None:
        obj_reference = next(
            (
                key
                for key, item in configuration_references.items()
                if isinstance(item, type(obj)) and item == obj
            ),
            None,
        )
        if obj_reference is not None:
            return obj_reference
    return obj


@save.register
def _save_bool(obj: bool, *args: Any, **kwargs: Any) -> str:
    return str(obj)


@save.register(np.ndarray)
def _save_array(obj: NDArray[Any], *args: Any, **kwargs: Any) -> Any:
    return float(obj) if obj.size == 1 else obj.tolist()


def _get_init_parameters(obj_type: type[T]) -> list[str]:
    # get parameters of the constructor
    obj_cstr_sig = signature(obj_type.__init__)
    # remove first argument (self)
    parameters_ids = list(obj_cstr_sig.parameters.keys())[1:]
    return parameters_ids


def __sort_configuration(configuration: Mapping[str, Any]) -> Any:
    # Sort dict entries based on on their dependencies to initialize most
    # required arguments first
    dependencies_score = __build_dependencies_sorting_score(configuration)
    sorted_values = dict(
        sorted(
            configuration.items(),
            key=lambda item: dependencies_score[item[0]],
        )
    )
    if isinstance(configuration, Configuration):
        return Configuration(configuration.label, sorted_values)
    elif isinstance(configuration, Mapping):
        return sorted_values


def __build_dependencies_sorting_score(
    configuration: Mapping[str, Any],
) -> dict[str, int]:
    dependencies = __build_dependencies(configuration)
    for key, item in dependencies.items():
        __check_dependencies(key, item, dependencies)
    return {key: __get_score(key, dependencies) for key in configuration}


def __check_dependencies(
    key: str,
    dependencies: set[str],
    all_dependencies: Mapping[str, set[str]],
    dependency_chain: list[str] | None = None,
) -> None:
    dependency_chain_copy = (
        dependency_chain.copy() if dependency_chain is not None else []
    )
    if key in dependency_chain_copy:
        raise ConfigurationError(
            str.format("Item {0} is referencing itself: {1}", key, dependency_chain)
        )
    dependency_chain_copy.append(key)
    for dependency_item in dependencies:
        __check_dependencies(
            dependency_item,
            all_dependencies[dependency_item],
            all_dependencies,
            dependency_chain_copy,
        )


def __build_dependencies(configuration: Mapping[str, Any]) -> Mapping[str, set[str]]:
    dependencies: dict[str, set[str]] = {}
    for key, item in configuration.items():
        all_values = __get_all_strings(item)
        dependencies[key] = set.intersection(all_values, configuration.keys())
        for new_key, new_item in configuration.items():
            recursive_keys = __get_recursives_keys(new_item)
            if new_key != key and any(
                [
                    value in recursive_keys
                    for value in all_values
                    if value not in dependencies[key]
                ]
            ):
                dependencies[key].add(new_key)

    return dependencies


def __get_score(item_key: str, dependencies: Mapping[str, set[str]]) -> int:
    score = 1
    for dependencies_key in dependencies[item_key]:
        score += __get_score(dependencies_key, dependencies)
    return score


def __get_recursives_keys(entry: Any) -> set[str]:
    result: set[str] = set()
    if isinstance(entry, str):
        return result
    elif isinstance(entry, Mapping):
        result = result.union(entry.keys())
        result = result.union(__get_recursives_keys(entry.values()))
    elif isinstance(entry, Iterable):
        for value in entry:
            result = result.union(__get_recursives_keys(value))
    return result


def __get_all_strings(entry: Any) -> set[str]:
    result = set()
    if isinstance(entry, str):
        result.add(entry)
    elif isinstance(entry, Mapping):
        result = result.union(__get_all_strings(entry.values()))
    elif isinstance(entry, Iterable):
        for sub_entry in entry:
            entry_set = __get_all_strings(sub_entry)
            result = result.union(entry_set)

    return result
