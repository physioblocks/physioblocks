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


from unittest.mock import MagicMock, patch

import pytest

from physioblocks.computing.models import Term
from physioblocks.computing.quantities import Quantity
from physioblocks.simulation import AbstractSimulation
from physioblocks.simulation.base import (
    SimulationFactory,
    SimulationModel,
    SimulationModelFactory,
    build_blocks,
    build_eq_system,
    build_parameters,
    build_saved_quantities,
    build_state,
    create_models,
)
from physioblocks.simulation.functions import AbstractFunction
from physioblocks.simulation.time_manager import TIME_QUANTITY_ID


class TestSimulationModelFactory:
    def test_create_model_raises_missing_state_key(self):
        model_factory = SimulationModelFactory(state={"missing": MagicMock()})

        with pytest.raises(KeyError, match="missing"):
            model_factory.create_simulation_model()


class TestSimulationModel:
    def test_quantities(self):
        parameter_id = "param"
        variable_id = "variable"
        state_mock = MagicMock(quantities={variable_id: "param"})
        sim_model = SimulationModel(
            MagicMock(),
            MagicMock(),
            parameters={parameter_id: MagicMock},
            state=state_mock,
        )

        assert len(sim_model.quantities) == 3
        assert TIME_QUANTITY_ID in sim_model.quantities
        assert parameter_id in sim_model.quantities
        assert variable_id in sim_model.quantities

    def test_register_param_update(self):
        key = "parameter"
        sim_model = SimulationModel(
            MagicMock(), MagicMock(), parameters={key: MagicMock()}
        )

        sim_model.register_parameter_update(key, MagicMock(spec_set=AbstractFunction))
        assert key in sim_model.update_functions

        sim_model.unregister_parameter_update(key)
        assert key not in sim_model.update_functions

    def test_register_param_update_existing_param(self):
        key = "unregistered_parameter"
        sim_model = SimulationModel(MagicMock(), MagicMock())
        with pytest.raises(KeyError, match=key):
            sim_model.register_parameter_update(
                key, MagicMock(spec_set=AbstractFunction)
            )

    def test_register_param_update_without_abstract_function(self):
        key = "unregistered_parameter"
        sim_model = SimulationModel(
            MagicMock(), MagicMock(), parameters={key: MagicMock()}
        )
        with pytest.raises(TypeError, match=MagicMock.__name__):
            sim_model.register_parameter_update(key, MagicMock())

    def test_update_functions_parameters_without_time(self):
        key = "parameter"
        parameter_mock = MagicMock(spec_set=Quantity)
        sim_model = SimulationModel(
            MagicMock(), MagicMock(), parameters={key: parameter_mock}
        )
        func_mock = MagicMock(spec_set=AbstractFunction)
        sim_model.register_parameter_update(key, func_mock)
        sim_model.update_functions_parameters()
        assert parameter_mock.initialize.called
        assert parameter_mock.update.called
        assert func_mock.eval_current.called is True
        assert func_mock.eval_current.call_count == 1
        assert func_mock.eval_new.called is True
        assert func_mock.eval_new.call_count == 1


class TestSetupFunctions:
    def test_build_state_internal_variables(self):
        block_x_mock = MagicMock(internal_variables=[Term("x", 1, 0)])
        block_y_mock = MagicMock(internal_variables=[Term("y", 2, 1)])
        net_mock = MagicMock(
            blocks={
                "block_x": block_x_mock,
                "block_y": block_y_mock,
            }
        )
        state = build_state(net_mock)

        assert "x" in state
        assert "y" in state
        assert state.size == 3

    def test_build_state_dofs(self):
        node_x_mock = MagicMock(dofs=[MagicMock(dof_id="x")])
        node_y_mock = MagicMock(dofs=[MagicMock(dof_id="y")])
        net_mock = MagicMock(
            nodes={
                "node_x": node_x_mock,
                "node_y": node_y_mock,
            }
        )
        state = build_state(net_mock)

        assert "x" in state
        assert "y" in state
        assert state.size == 2

    def test_build_state_with_dof_boundary(self):
        node_mock = MagicMock(
            is_boundary=True,
            boundary_conditions=[MagicMock()],
            has_flux_type=MagicMock(return_value=False),
        )
        net_mock = MagicMock(
            nodes={
                "node": node_mock,
            }
        )
        state = build_state(net_mock)
        assert state.size == 0

    def test_build_state_with_flux_boundary(self):
        dof_mock = MagicMock(dof_id="x")
        node_mock = MagicMock(
            is_boundary=True,
            boundary_conditions=[MagicMock()],
            has_flux_type=MagicMock(return_value=True),
            get_flux_dof=MagicMock(return_value=dof_mock),
        )
        net_mock = MagicMock(
            nodes={
                "node": node_mock,
            }
        )
        state = build_state(net_mock)
        assert state.size == 1
        assert "x" in state

    def test_build_parameters_block(self):
        block_mock = MagicMock(
            global_ids={"local_a": "global_a", "local_b": "global_b"}
        )
        net_mock = MagicMock(blocks={"block": block_mock})
        state_mock = MagicMock()
        parameters = build_parameters(net_mock, state_mock)

        assert len(parameters) == 2
        assert "global_a" in parameters
        assert "global_b" in parameters

    def test_build_parameters_submodel(self):
        submodel_mock = MagicMock(global_ids={"local_a": "global_a"})
        block_mock = MagicMock(
            global_ids={"local_b": "global_b"}, submodels={"submodel": submodel_mock}
        )
        net_mock = MagicMock(blocks={"block": block_mock})
        state_mock = MagicMock()
        parameters = build_parameters(net_mock, state_mock)

        assert len(parameters) == 2
        assert "global_a" in parameters
        assert "global_b" in parameters

    def test_build_parameters_time(self):
        block_mock = MagicMock(global_ids={"time": TIME_QUANTITY_ID})
        net_mock = MagicMock(blocks={"block": block_mock})
        state_mock = MagicMock()
        parameters = build_parameters(net_mock, state_mock)

        assert len(parameters) == 0

    def test_build_parameters_in_state(self):
        block_mock = MagicMock(global_ids={"local": "global"})
        net_mock = MagicMock(blocks={"block": block_mock})
        state_mock = MagicMock(__contains__=MagicMock(return_value=True))
        parameters = build_parameters(net_mock, state_mock)

        assert len(parameters) == 0

    def test_build_parameters_in_saved_quantity(self):
        block_mock = MagicMock(
            global_ids={"local": "global"}, saved_quantities=[("global", 1)]
        )
        net_mock = MagicMock(blocks={"block": block_mock})
        state_mock = MagicMock()
        parameters = build_parameters(net_mock, state_mock)

        assert len(parameters) == 0

    def test_build_parameters_flux_boundary(self):
        node_mock = MagicMock(
            boundary_conditions=[MagicMock(condition_id="flux")],
            has_flux_type=MagicMock(return_value=True),
        )
        net_mock = MagicMock(nodes={"node": node_mock})
        state_mock = MagicMock()
        parameters = build_parameters(net_mock, state_mock)

        assert len(parameters) == 1
        assert "flux" in parameters

    def test_build_eq_system(self):
        expression_mock = MagicMock(
            size=1, expr_gradients={"x": MagicMock(), "y": MagicMock()}
        )
        state_mock = MagicMock(
            size=2,
            quantities={"x": MagicMock(), "y": MagicMock()},
            indexes={"x": 0, "y": 1},
        )
        eq_system = build_eq_system([(0, expression_mock, {})], state_mock)
        assert eq_system.system_size == 2

    def test_create_models(self):
        description_mock = MagicMock(global_ids={"local_a": "global_a"})
        parameters = {"global_a": "param_a"}
        models = create_models("model", description_mock, parameters)
        assert len(models) == 1
        assert "model" in models
        assert description_mock.described_type.called is True
        assert description_mock.described_type.call_args.kwargs == {
            "local_a": "param_a"
        }

    def test_create_models_with_saved_quantities(self):
        description_mock = MagicMock(
            global_ids={"local_a": "global_a"},
            described_type=MagicMock(saved_quantities=[MagicMock(term_id="local_a")]),
        )
        parameters = {"global_a": "param_a"}
        models = create_models("model", description_mock, parameters)
        assert len(models) == 1
        assert "model" in models
        assert description_mock.described_type.called is True
        assert description_mock.described_type.call_args.kwargs == {}

    def test_create_models_with_submodels(self):
        submodel_mock = MagicMock()
        submodel_mock.name = "submodel"  # trick to update name attribute in magic mock
        description_mock = MagicMock(submodels={"submodel": submodel_mock})
        parameters = MagicMock()
        models = create_models("model", description_mock, parameters)
        assert len(models) == 2
        assert "model" in models
        assert "submodel" in models

    def test_build_blocks(self):
        description_mock = MagicMock()
        net_mock = MagicMock(blocks={"block": description_mock})
        models = build_blocks(net_mock, {})
        assert len(models) == 1
        assert "block" in models

    def test_build_saved_quantities(self):
        saved_quantity_term_mock = Term(
            term_id="model_output", term_size=1, term_index=0
        )
        saved_quantity_expression_def_mock = MagicMock(terms=[saved_quantity_term_mock])
        block_desc_mock = MagicMock(
            saved_quantities_expressions=[saved_quantity_expression_def_mock]
        )
        models = {"block": MagicMock()}
        net_mock = MagicMock(blocks={"block": block_desc_mock})
        saved_quantities = build_saved_quantities(net_mock, models)
        assert "model_output" in saved_quantities

    def test_build_saved_quantities_in_submodels(self):
        saved_quantity_term_mock = Term(
            term_id="submodel_output", term_size=1, term_index=0
        )
        saved_quantity_expression_def_mock = MagicMock(terms=[saved_quantity_term_mock])
        subblock_desc_mock = MagicMock(
            saved_quantities_expressions=[saved_quantity_expression_def_mock]
        )
        subblock_desc_mock.name = "submodel"
        block_desc_mock = MagicMock(submodels={"submodel": subblock_desc_mock})
        models = {"block": MagicMock(), "submodel": MagicMock()}
        net_mock = MagicMock(blocks={"block": block_desc_mock})
        saved_quantities = build_saved_quantities(net_mock, models)
        assert "submodel_output" in saved_quantities


class TestSimulationFactory:
    def test_create_simulation_raise_type_error(self):
        factory = SimulationFactory("sim", object, MagicMock())
        with pytest.raises(
            TypeError, match=object.__name__ and "not" and AbstractSimulation.__name__
        ):
            factory.create_simulation()


@patch.multiple(AbstractSimulation, __abstractmethods__=set())
class TestAbstractSimulation:
    def test_run_simulation_raise_error(self):
        simulation = AbstractSimulation(MagicMock(), "sim", MagicMock())
        simulation.simulation_model.time_manager.duration = 1.0
        with (
            patch.object(simulation, "_initialize", return_value=MagicMock()),
            patch.object(simulation, "run_step", side_effect=Exception()),
            patch.object(simulation.simulation_model.time_manager, "ended", new=False),
        ):
            simulation.run()

        assert "sim" in simulation.processed_data

    def test_register_output_functions(self):
        simulation = AbstractSimulation(MagicMock, "sim", MagicMock())
        simulation.register_output_function(
            "output_func", MagicMock(spec_set=AbstractFunction)
        )

        assert len(simulation.outputs_functions) == 1
        assert "output_func" in simulation.outputs_functions

        simulation.unregister_output_function("output_func")
        assert len(simulation.outputs_functions) == 0
        assert "output_func" not in simulation.outputs_functions

    def test_register_invalid_output_functions(self):
        simulation = AbstractSimulation(MagicMock, "sim", MagicMock())
        with pytest.raises(
            TypeError, match=MagicMock.__name__ and "invalid output function type"
        ):
            simulation.register_output_function("output_func", MagicMock())

    def test_register_existing_output_function(self):
        simulation = AbstractSimulation(MagicMock, "sim", MagicMock())
        simulation.register_output_function(
            "output_func", MagicMock(spec_set=AbstractFunction)
        )
        with pytest.raises(KeyError, match="output_func" and "already defined"):
            simulation.register_output_function(
                "output_func", MagicMock(spec_set=AbstractFunction)
            )

    def test_register_output_function_with_variable_id(self):
        simulation_model_mock = MagicMock(state={"output_func": MagicMock()})
        simulation = AbstractSimulation(MagicMock, "sim", simulation_model_mock)
        with pytest.raises(KeyError, match="output_func" and "already defined"):
            simulation.register_output_function(
                "output_func", MagicMock(spec_set=AbstractFunction)
            )

    def test_register_output_function_with_saved_quantity_id(self):
        simulation_model_mock = MagicMock(saved_quantities={"output_func": MagicMock()})
        simulation = AbstractSimulation(MagicMock, "sim", simulation_model_mock)
        with pytest.raises(KeyError, match="output_func" and "already defined"):
            simulation.register_output_function(
                "output_func", MagicMock(spec_set=AbstractFunction)
            )
