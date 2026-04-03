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

"""Test the process classes."""

from pathlib import Path
from unittest.mock import Mock, PropertyMock, patch

from pandas import DataFrame
from pytest import fixture

from physioblocks.simulation.process import (
    AbstractPlotProcess,
    AbstractProcess,
    run_method_checkers,
    run_processes,
)


@fixture
def reference_dataframe_1():
    return DataFrame({"value": [1, 2, 3]})


@fixture
def reference_dataframe_2():
    return DataFrame({"value": [4, 5, 6]})


@fixture
def reference_dataframe_3():
    return DataFrame({"value": [7, 8, 9]})


@patch.multiple(AbstractProcess, __abstractmethods__=set())
class TestAbstractProcess:
    def test_init_with_inputs_and_outputs(self):
        process = AbstractProcess(inputs=["input1", "input2"], outputs=["output1"])
        assert process.inputs == ["input1", "input2"]
        assert process.outputs == ["output1"]

    def test_init_without_inputs_and_outputs(self):
        process = AbstractProcess()
        assert process.inputs == []
        assert process.outputs == []

    def test_check_inputs_all_present(self):
        process = AbstractProcess(inputs=["input1", "input2"])
        assert process.check_inputs(["input1", "input2", "input3"]) is True

    def test_check_inputs_missing_one(self):
        process = AbstractProcess(inputs=["input1", "input2"])
        assert process.check_inputs(["input1", "input3"]) is False

    def test_check_inputs_missing_all(self):
        process = AbstractProcess(inputs=["input1", "input2"])
        assert process.check_inputs(["input3", "input4"]) is False

    def test_check_inputs_empty(self):
        process = AbstractProcess()
        assert process.check_inputs(["input1", "input2"]) is True

    def test_select_inputs(
        self, reference_dataframe_1, reference_dataframe_2, reference_dataframe_3
    ):
        process = AbstractProcess(inputs=["input1", "input2"])
        data = {
            "input1": reference_dataframe_1,
            "input2": reference_dataframe_2,
            "input3": reference_dataframe_3,
        }
        result = process.select_inputs(data)
        assert len(result) == 2
        assert result[0].equals(reference_dataframe_1)
        assert result[1].equals(reference_dataframe_2)

    def test_format_outputs(
        self, reference_dataframe_1, reference_dataframe_2, reference_dataframe_3
    ):
        process = AbstractProcess(outputs=["output1", "output2"])
        outputs = [reference_dataframe_1, reference_dataframe_2, reference_dataframe_3]
        result = process.format_outputs(outputs)
        assert len(result) == 2
        assert result["output1"].equals(reference_dataframe_1)
        assert result["output2"].equals(reference_dataframe_2)

    def test_format_outputs_with_missing_outputs(
        self, reference_dataframe_1, reference_dataframe_2
    ):
        process = AbstractProcess(outputs=["output1", "output2", "output3"])
        outputs = [
            reference_dataframe_1,
            reference_dataframe_2,
        ]
        result = process.format_outputs(outputs)
        assert len(result) == 2
        assert "output1" in result
        assert "output2" in result
        assert "output3" not in result

    def test_format_outputs_with_excess_outputs(
        self, reference_dataframe_1, reference_dataframe_2, reference_dataframe_3
    ):
        process = AbstractProcess(outputs=["output1", "output2"])
        outputs = [
            reference_dataframe_1,
            reference_dataframe_2,
            reference_dataframe_3,
        ]
        result = process.format_outputs(outputs)
        assert len(result) == 2
        assert result["output1"].equals(outputs[0])
        assert result["output2"].equals(outputs[1])

    def test_can_run_without_checkers(self):
        process = AbstractProcess()
        assert process.can_run is True


@patch.multiple(AbstractPlotProcess, __abstractmethods__=set())
class TestAbstractPlotProcess:
    def test_init_with_attributes(self):
        folder_path = Path("./")
        process = AbstractPlotProcess(
            folder_path=folder_path,
            plot_name="test_plot",
            inputs=["input1"],
            outputs=["output1"],
        )
        assert process.folder_path == folder_path
        assert process.plot_name == "test_plot"
        assert process.inputs == ["input1"]
        assert process.outputs == ["output1"]

    def test_init_without_attributes(self):
        process = AbstractPlotProcess()
        assert process.folder_path is None
        assert process.plot_name is None
        assert process.inputs == []
        assert process.outputs == []

    def test_can_run_without_required_attributes(self):
        process = AbstractPlotProcess()
        assert process.can_run is False

    def test_can_run_with_folder_path_only(self):
        folder_path = Path("./")
        process = AbstractPlotProcess(folder_path=folder_path)
        assert process.can_run is False

    def test_can_run_with_plot_name_only(self):
        process = AbstractPlotProcess(plot_name="test_plot")
        assert process.can_run is False

    def test_can_run_with_both_attributes(self):
        folder_path = Path("./")
        process = AbstractPlotProcess(folder_path=folder_path, plot_name="test_plot")
        assert process.can_run is True


class TestRunMethodCheckers:
    def test_decorator_registers_checkers(self):
        def checker1(process: AbstractProcess) -> bool:
            return hasattr(process, "attr_exist")

        def checker2(process: AbstractProcess) -> bool:
            return hasattr(process, "attr_dont_exist")

        @run_method_checkers(checker1, checker2)
        class TestProcess(AbstractProcess):
            attr_exist: int = 1

        assert len(TestProcess.get_run_checkers()) == 2
        assert checker1 in TestProcess.get_run_checkers()
        assert checker2 in TestProcess.get_run_checkers()


class TestRunProcesses:
    def test_run_processes_with_no_data(self):
        processes = {}
        result = run_processes(processes)
        assert result == {}

    def test_run_processes_with_data_no_processes(self, reference_dataframe_1):
        data = {"input1": reference_dataframe_1}
        result = run_processes({}, data)
        assert result == data

    def test_run_processes_with_cannot_run(self):
        with patch.multiple(
            AbstractProcess,
            __abstractmethods__=set(),
            can_run=PropertyMock(return_value=False),
            run=Mock(side_effect=Exception("run method is called")),
        ):
            process = AbstractProcess(outputs=["output1"])
            result = run_processes({"test": process})
            assert "output1" not in result

    def test_run_processes_with_cannot_run_due_to_checkers(self):
        with patch.multiple(
            AbstractProcess,
            __abstractmethods__=set(),
            run=Mock(return_value=[reference_dataframe_1]),
        ):

            @run_method_checkers(lambda p: False)
            class TestProcessWithChecker(AbstractProcess):
                pass

            process = TestProcessWithChecker(outputs=["output1"])
            result = run_processes({"test": process})

            assert "output1" not in result

    def test_run_processes_with_missing_inputs(self, reference_dataframe_1):
        with patch.multiple(
            AbstractProcess,
            __abstractmethods__=set(),
            run=Mock(return_value=[reference_dataframe_1]),
        ):
            process = AbstractProcess(inputs=["input1"], outputs=["output1"])
            result = run_processes({"test": process})
            assert "output1" not in result

    def test_run_processes_with_valid_process(self, reference_dataframe_1):
        with patch.multiple(
            AbstractProcess,
            __abstractmethods__=set(),
            run=Mock(return_value=[reference_dataframe_1]),
        ):
            process = AbstractProcess(outputs=["output1"])
            result = run_processes({"test": process})
            assert "output1" in result
            assert result["output1"].equals(reference_dataframe_1)

    def test_run_processes_multiple_chained_processes(self, reference_dataframe_1):
        class DoublesProcess(AbstractProcess):
            def run(self, *dfs):
                # Double the input dataframe
                return [2 * df for df in dfs]

        process1 = DoublesProcess(inputs=["input1"], outputs=["output1"])
        process2 = DoublesProcess(inputs=["output1"], outputs=["output2"])

        result = run_processes(
            {"p1": process1, "p2": process2}, data={"input1": reference_dataframe_1}
        )
        assert len(result) == 3

        assert "input1" in result
        assert "output1" in result
        assert "output2" in result
        assert result["input1"].equals(reference_dataframe_1)
        assert result["output1"].equals(2 * reference_dataframe_1)
        assert result["output2"].equals(4 * reference_dataframe_1)

    def test_run_processes_overwrites_input(
        self, reference_dataframe_1, reference_dataframe_2
    ):
        with patch.multiple(
            AbstractProcess,
            __abstractmethods__=set(),
            run=Mock(return_value=[reference_dataframe_2]),
        ):
            process = AbstractProcess(inputs=["input1"], outputs=["input1"])

            result = run_processes(
                {"p1": process}, data={"input1": reference_dataframe_1}
            )
            assert len(result) == 1
            assert "input1" in result
            assert result["input1"].equals(reference_dataframe_2)
