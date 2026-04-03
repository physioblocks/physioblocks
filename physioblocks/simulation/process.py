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

"""Define the process class and process update functions."""

from __future__ import annotations

import logging
from abc import ABCMeta, abstractmethod
from collections.abc import Callable, Iterable, Mapping
from pathlib import Path
from typing import Any, TypeVar

from pandas import DataFrame

from physioblocks.base.function_factories import attribute_checker

_logger = logging.getLogger()


class MetaProcess(ABCMeta):
    _run_checkers: list[Callable[..., bool]]

    def __init__(cls, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        cls._run_checkers = []

    def register_run_checker(cls, checker: Callable[[AbstractProcess], bool]) -> None:
        """
        Register a method to check if the process can run.

        :param checker: the method to register
        :type checker: Callable[[AbstractProcess], bool]
        """
        cls._run_checkers.append(checker)

    def get_run_checkers(cls) -> list[Callable[[AbstractProcess], bool]]:
        """
        Get all registered checkers for the class and its base classes.

        :return: List of all run checkers
        :rtype: list[Callable[[AbstractProcess], bool]]
        """
        all_checkers = (
            cls.__base__.get_run_checkers()
            if cls.__base__ is not None and isinstance(cls.__base__, MetaProcess)
            else []
        )
        all_checkers.extend(cls._run_checkers)
        return all_checkers


class AbstractProcess(metaclass=MetaProcess):
    """
    Base class for processes.

    Implement the run method to define the process behavior.
    """

    inputs: list[str]
    """Name of the process inputs"""
    outputs: list[str]
    """Name of the process outputs"""

    def __init__(
        self, inputs: list[str] | None = None, outputs: list[str] | None = None
    ) -> None:
        self.inputs = inputs if inputs is not None else []
        self.outputs = outputs if outputs is not None else []

    def check_inputs(self, data_ids: Iterable[str]) -> bool:
        """
        Check every input has a match in provided list.

        :param data_ids: the list to test for matches
        :type data_ids: Iterable[str]

        :return: True if all inputs are defined in the provided list, False otherwise.
        :rtype: bool
        """

        return all([input_id in data_ids for input_id in self.inputs])

    def select_inputs(self, data: Mapping[str, DataFrame]) -> list[DataFrame]:
        """
        Select the dataframes matching the process inputs among the provided data.

        :param data: the provided dataframes
        :type data: Mapping[str, DataFrame]

        :return: The input dataframes
        :rtype: list[DataFrame]
        """
        return [data.get(input_id) for input_id in self.inputs]

    def format_outputs(self, outputs: list[DataFrame]) -> dict[str, DataFrame]:
        """
        Format the dataframes from the provided data using process outputs.

        :param outputs: the provided dataframes
        :type outputs: list[DataFrame]

        :return: The output dataframes
        :rtype: dict[str, DataFrame]
        """
        return {
            self.outputs[index]: outputs[index]
            for index in range(len(self.outputs))
            if index in range(len(outputs))
        }

    @property
    def can_run(self) -> bool:
        """
        Get if all conditions are met to run the process.

        :return: True if all conditions are met, False otherwise
        :rtype: bool
        """
        return all(
            [checker_method(self) for checker_method in type(self).get_run_checkers()]
        )

    @abstractmethod
    def run(self, *dfs: DataFrame) -> list[DataFrame]:
        """
        Abstract process run method.

        :param dfs: Input dataframes
        :type dfs: DataFrame

        :return: Output dataframes
        :rtype: list[DataFrame]
        """


T = TypeVar("T", bound=type[AbstractProcess])


def run_method_checkers(
    *checkers: Callable[[AbstractProcess], bool],
) -> Callable[[T], T]:
    """
    Decorator to register  functions as checkers for the process class.

    :param process_type: the process
    :type process_type: type[AbstractProcess]

    :param wrapped_method: the method to register
    :type wrapped_method: Callable[[AbstractProcess], bool])
    """

    def class_wrapper(
        wrapped_class: T,
    ) -> T:
        for checker in checkers:
            wrapped_class.register_run_checker(checker)
        return wrapped_class

    return class_wrapper


def run_processes(
    processes: Mapping[str, AbstractProcess], data: dict[str, DataFrame] | None = None
) -> dict[str, DataFrame]:
    """
    Run every process with the provided input data

    :param processes: the processes to run
    :type list[AbstractProcess]:

    :param data: the input dataframes
    :type dict[str, DataFrame]:

    :return: The output dataframes
    :rtype: dict[str, DataFrame]
    """

    if data is None:
        data = {}

    for process_id, process in processes.items():
        if process.can_run is False:
            _logger.info(
                str.format(
                    "Process {0} skipped. Missing conditions: {1}",
                    process_id,
                    [
                        checker.__name__
                        for checker in type(process).get_run_checkers()
                        if checker(process) is False
                    ],
                )
            )
        elif process.check_inputs(data.keys()) is False:
            _logger.info(
                str.format(
                    "Process {0} skipped. Missing inputs in data: {1}",
                    process_id,
                    [input_id for input_id in process.inputs if input_id not in data],
                )
            )
        else:
            inputs = process.select_inputs(data)
            outputs = process.format_outputs(process.run(*inputs))
            data.update(outputs)
            _logger.info(f"Process {process_id} successful.")
            if len(outputs) > 0:
                _logger.info(f"Outputs {[key for key in outputs]} updated.")

    return data


@run_method_checkers(attribute_checker("folder_path"), attribute_checker("plot_name"))
class AbstractPlotProcess(AbstractProcess):
    """Base class for process plotting data"""

    plot_name: str | None
    """the plot name"""

    folder_path: Path | None
    """the folder path where to write the plot"""

    def __init__(
        self,
        plot_name: str | None = None,
        folder_path: Path | None = None,
        *args: Any,
        **kwargs: Any,
    ):
        self.folder_path = folder_path
        self.plot_name = plot_name
        super().__init__(*args, **kwargs)
