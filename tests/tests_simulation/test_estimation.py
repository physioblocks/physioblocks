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

import multiprocessing
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from physioblocks.computing.quantities import QuantitiesRegistry, Quantity, QuantityInit
from physioblocks.simulation.estimation import (
    AbstractFilter,
    EstimationSimulation,
    Observation,
    Observer,
    ObserverFactory,
)
from physioblocks.simulation.functions import SimulationFunctionFactory

QUANTITY_ID = "qty"
MEASUREMENT_ID = "measurement"
FUNCTION_LOCAL_QUANTITY_ID = "x"


@pytest.fixture
def quantities_factories():
    return {QUANTITY_ID: QuantityInit()}


@pytest.fixture
def operators_factories():
    return {
        QUANTITY_ID: SimulationFunctionFactory(
            function_type=MagicMock(),
            evaluation_quantities={FUNCTION_LOCAL_QUANTITY_ID: QUANTITY_ID},
        )
    }


class TestObserverFactory:
    def test_create_observer_references(
        self, quantities_factories, operators_factories
    ):
        ref_quantity = Quantity(0.0)
        observations = {
            QUANTITY_ID: Observation(
                MEASUREMENT_ID, operators_factories[QUANTITY_ID], 10.0, 0.5
            )
        }
        factory = ObserverFactory(observations)
        observer = factory.create_observer({QUANTITY_ID: ref_quantity})

        assert QUANTITY_ID in observer.observations
        assert MEASUREMENT_ID in observer.measurements
        assert (
            observer.observations.magnitudes_vector
            == observer.measurements.magnitudes_vector
        )
        assert (
            observer.observations.stdevs_vector == observer.measurements.stdevs_vector
        )
        assert (
            observer.operators[QUANTITY_ID].argument_quantities[
                FUNCTION_LOCAL_QUANTITY_ID
            ]
            is ref_quantity
        )


@pytest.fixture
def measurements(quantities_factories):
    return QuantitiesRegistry(quantities_factories)


@pytest.fixture
def observations(quantities_factories):
    return QuantitiesRegistry(quantities_factories)


class TestObserver:
    def test_observer_update_observations(self, measurements, observations):
        operator = MagicMock()
        operator.eval_current.return_value = 0.5
        operators = {QUANTITY_ID: operator}

        observer = Observer(MagicMock(), measurements, observations, operators)

        observer.update_observations()
        assert observer.observations[QUANTITY_ID].current == 0.5


class TestFilters:
    @patch.multiple(AbstractFilter, __abstractmethods__=set())
    def test_filter_default_init(self):
        default_filter = AbstractFilter(2, 1, MagicMock(), MagicMock())
        assert np.array_equal(default_filter.model_noise_covariance, np.zeros((2, 2)))
        assert np.array_equal(
            default_filter.measurements_noise_covariance, np.zeros((1, 1))
        )

    @patch.multiple(AbstractFilter, __abstractmethods__=set())
    def test_filter_init_with_noise(self):
        default_filter = AbstractFilter(
            2, 1, MagicMock(), MagicMock(), [1.0, 2.0], [3.0]
        )
        assert np.array_equal(
            default_filter.model_noise_covariance, np.diag([1.0, 4.0])
        )
        assert np.array_equal(
            default_filter.measurements_noise_covariance, np.diag([9.0])
        )


TEST_FILTER_ID = "test_filter"

TYPE_REGISTER = {TEST_FILTER_ID: MagicMock(), MagicMock(): TEST_FILTER_ID}


@patch("physioblocks.registers.type_register.__type_register", new=TYPE_REGISTER)
class TestEstimationSimulation:
    @patch.object(multiprocessing, "Pool", MagicMock())
    def test_default_init(self):
        simulation = EstimationSimulation(
            factory=MagicMock(),
            simulation_name="estimation_test",
            simulation_model=MagicMock(),
            filter_type=TEST_FILTER_ID,
            observer_factory=MagicMock(),
            estimated_parameters=MagicMock(),
        )
        assert simulation.estimation_filter == TYPE_REGISTER[TEST_FILTER_ID]()
        multiprocessing.Pool.assert_not_called()
        assert simulation.min_step == simulation.simulation_model.time_manager.step_size
        assert simulation.time_tolerance == 1e-9

    @patch.object(multiprocessing, "Pool", MagicMock())
    def test_init_parallelized(self):
        EstimationSimulation(
            factory=MagicMock(),
            simulation_name="estimation_test",
            simulation_model=MagicMock(),
            filter_type=TEST_FILTER_ID,
            observer_factory=MagicMock(),
            estimated_parameters=MagicMock(),
            parallelize=True,
        )
        multiprocessing.Pool.assert_called_once()
        assert multiprocessing.cpu_count() in multiprocessing.Pool.call_args[0]

    @patch.object(multiprocessing, "Pool", MagicMock())
    def test_init_parallelize_with_nb_processes(self):
        EstimationSimulation(
            factory=MagicMock(),
            simulation_name="estimation_test",
            simulation_model=MagicMock(),
            filter_type=TEST_FILTER_ID,
            observer_factory=MagicMock(),
            estimated_parameters=MagicMock(),
            parallelize=True,
            nb_processes=7,
        )
        multiprocessing.Pool.assert_called_once()
        assert 7 in multiprocessing.Pool.call_args[0]

    def test_init_raise_key_error(self):
        with pytest.raises(KeyError, match="not a parameter"):
            EstimationSimulation(
                factory=MagicMock(),
                simulation_name="estimation_test",
                simulation_model=MagicMock(),
                filter_type=TEST_FILTER_ID,
                observer_factory=MagicMock(),
                estimated_parameters={"unregistered_qty": MagicMock()},
            )

    def test_init_estimation_register(self, quantities_factories):
        sim_model_mock = MagicMock(parameters=QuantitiesRegistry(quantities_factories))
        model_factory_mock = MagicMock()
        model_factory_mock.create_simulation_model.return_value = sim_model_mock
        simulation = EstimationSimulation(
            factory=MagicMock(),
            simulation_name="estimation_test",
            simulation_model=MagicMock(
                factory=model_factory_mock,
                parameters=QuantitiesRegistry(quantities_factories),
                state=QuantitiesRegistry(quantities_factories),
            ),
            filter_type=TEST_FILTER_ID,
            observer_factory=MagicMock(),
            estimated_parameters=quantities_factories,
        )
        assert QUANTITY_ID in simulation.estimations

    def test_init_transformations_functions(self, quantities_factories):
        transform_function_mock = MagicMock()
        transform_function_mock.eval.return_value = 0.1
        transform_function_mock.eval_inverse.return_value = 0.2
        simulation = EstimationSimulation(
            factory=MagicMock(),
            simulation_name="estimation_test",
            simulation_model=MagicMock(
                state=QuantitiesRegistry(quantities_factories),
            ),
            filter_type=TEST_FILTER_ID,
            observer_factory=MagicMock(),
            estimated_parameters=MagicMock(),
            transformation_operators={QUANTITY_ID: transform_function_mock},
        )
        assert np.array_equal(simulation.transform_function(np.zeros(1)), [0.1])
        assert np.array_equal(simulation.inverse_function(np.zeros(1)), [0.2])
