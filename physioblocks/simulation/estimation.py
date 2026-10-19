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
"""Declare classes to run estimation simulations."""

from __future__ import annotations

import logging
import multiprocessing
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, TypeAlias

import numpy as np
from numpy.typing import NDArray

from physioblocks.computing.quantities import (
    QuantitiesRegistry,
    Quantity,
    QuantityInit,
)
from physioblocks.registers.type_register import get_registered_type, register_type
from physioblocks.simulation.base import (
    AbstractSimulation,
    Result,
    Results,
    SimulationModelFactory,
    format_result,
)
from physioblocks.simulation.functions import (
    AbstractFunction,
    AbstractTransformation,
    SimulationFunctionFactory,
)
from physioblocks.simulation.time_manager import TIME_QUANTITY_ID

_logger = logging.getLogger(__name__)

_TransformFunction: TypeAlias = Callable[[NDArray[np.float64]], NDArray[np.float64]]
_ModelFunction: TypeAlias = Callable[
    [NDArray[np.float64], float, float], NDArray[np.float64]
]
_ObserverFunction: TypeAlias = Callable[
    [NDArray[np.float64], float], NDArray[np.float64]
]

MEASUREMENTS_ID = "measurements"
"""label of measurements in simulation data."""

OBSERVER_ID = "observer"
"""Type name for the observer class."""

FILTER_TYPE_ID = "filter_type"
"""Filter type parameter name"""

FILTER_OPTIONS_ID = "filter_options"
"""Filter options parameter name"""

ESTIMATION_FILTER_ID = "estimation_filter"
"""Type name for the estimation filter."""


@dataclass
class Observer:
    """Hold measurements and observations quantities.

    It can compute observations matching each measurement using the observations
    operators.

    The operators ids should match the observations quantity registry ids.
    Measurements and observations registry vector sizes should match.
    This is not enforced in the class but it is in the factory.

    Parameters
    ----------
    factory : ObserverFactory
        The factory that created the observer
    observations : QuantitiesRegistry
        a registry holding the observation quantities for each measurement.
    measurements : QuantitiesRegistry
        a registry holding the current measurements
    operators : dict[str, AbstractFunction]
        Observation operators. They are functions that compute observations for the
        current state.

    """

    factory: ObserverFactory

    observations: QuantitiesRegistry = field(default_factory=QuantitiesRegistry)

    measurements: QuantitiesRegistry = field(default_factory=QuantitiesRegistry)

    operators: dict[str, AbstractFunction] = field(default_factory=dict)

    def update_observations(self) -> None:
        """Update the observations registry with observation operators.

        Compute the current values of the observations with the operators and set the
        observations registry.
        """
        for observation_id, observation_operator in self.operators.items():
            self.observations[observation_id].initialize(
                observation_operator.eval_current()
            )


OBSERVATION_TYPE_ID = "observation"
MEASUREMENT_PARAMETER_ID = "measurement"
OPERATOR_PARAMETER_ID = "operator"


@dataclass
@register_type(OBSERVATION_TYPE_ID)
class Observation:
    """
    Holds the initial values for observations.

    Parameters
    ----------
    measurement : str
        the id of the measurement matching the observation.
    operator : SimulationFunctionFactory[Any]
        a factory to create the observation operator.
    magnitude : float
        Observation magnitude. Default value is 1.
    stdev : float
        Observation stdev. Default value is 0.

    Configuration
    -------------

    .. code-block:: json

        {
            "type": "observation",
            "measurement": "<str>",             // Name of the matching measurement
            "operator": "<function type>",  // Observation operator
            "magnitude": "<float>",         // Observation magnitude
                                            // (optional, default: 1.0)
            "stdev": "<float>"              // Observation standard deviation
                                            // (optional, default: 0.0)
        }

    """

    measurement: str
    operator: SimulationFunctionFactory[Any]
    magnitude: float = 1.0
    stdev: float = 0.0


@dataclass
@register_type(OBSERVER_ID)
class ObserverFactory:
    """Factory for observers.

    Parameters
    ----------
    observations : dict[str, Observation]
        initialization values for the observations

    Configuration
    -------------

    .. code-block:: json

        {
            "type": "observer",
            "observations": {               // Observations with their names
                "<str>": "<observation type>"
            }
        }

    """

    observations: dict[str, Observation] = field(default_factory=dict)

    def create_observer(
        self, quantities_references: dict[str, Quantity[Any]]
    ) -> Observer:
        """
        Create an observer from the factory parameters.

        Use the quantities references to set the observation operators quantities.

        Parameters
        ----------
        quantities_references : dict[str, Quantity[Any]]
            the quantities to pass to the observation operators.

        Returns
        -------
        Observer
            the created observer.
        """
        observations_init = {
            obs_id: QuantityInit(
                stdev=observation.stdev, magnitude=observation.magnitude
            )
            for obs_id, observation in self.observations.items()
        }
        observations = QuantitiesRegistry(observations_init)

        measurements_init = {
            observation.measurement: QuantityInit(
                stdev=observation.stdev, magnitude=observation.magnitude
            )
            for observation in self.observations.values()
        }
        measurements = QuantitiesRegistry(measurements_init)

        operators = {
            obs_id: observation.operator.create_function(quantities_references)
            for obs_id, observation in self.observations.items()
        }

        return Observer(self, observations, measurements, operators)


TRANSFORMATION_OPERATORS = "transformation_operators"
"""Parameter name of the transformations to apply constraints on the state and
parameters."""


class AbstractFilter(ABC):
    """Generic filter used in estimation simulation.

    When inheriting the class, you have to define the ``prediction`` and ``update``
    methods of the filter.

    Once initialized, you can call the filter method on the child class to perform one
    prediction and update step.

    Attributes
    ----------
    state_size : int
        The state size
    observer_size : int
        The observations size
    model_function : _ModelFunction
        The function that transforms the state.
        First argument is the state, second is the current time and third the targeted
        time step.
    observation_function : _ObserverFunction
        The function that gives observations values for the state.
        First argument is the state, second is the targeted time step.
    model_noise_covariance : NDArray[np.float64]
        The model noise covariance.
        When not initialized, it is set to a zero matrix the size of the state
    measurements_noise_covariance : NDArray[np.float64]
        The measurement noise covariance.
        When not initialized, it is set to a zero matrix the size of the observations

    Parameters
    ----------
    state_size : int
        The state size
    observer_size : int
        The observations size
    model_function : _ModelFunction
        The function that transforms the state.
    observation_function : _ObserverFunction
        The function that gives observations values for the state.
    model_noise_stdev_vector : NDArray[np.float64] | None
        The model noise standard deviations, used to build the diagonal model noise
        covariance. Default is None.
    measurements_noise_stdev_vector : NDArray[np.float64] | None
        The measurements noise standard deviations, used to build the diagonal
        measurements noise covariance. Default is None.

    """

    state_size: int

    observer_size: int

    model_function: _ModelFunction

    observation_function: _ObserverFunction

    model_noise_covariance: NDArray[np.float64]

    measurements_noise_covariance: NDArray[np.float64]

    def __init__(
        self,
        state_size: int,
        observer_size: int,
        model_function: _ModelFunction,
        observation_function: _ObserverFunction,
        model_noise_stdev_vector: NDArray[np.float64] | None = None,
        measurements_noise_stdev_vector: NDArray[np.float64] | None = None,
    ):
        self.state_size = state_size
        self.observer_size = observer_size
        self.model_function = model_function
        self.observation_function = observation_function

        # Initialize noise covariances
        self.model_noise_covariance = (
            np.diag(model_noise_stdev_vector) ** 2
            if model_noise_stdev_vector is not None
            else np.zeros((state_size, state_size))
        )
        self.measurements_noise_covariance = (
            np.diag(measurements_noise_stdev_vector) ** 2
            if measurements_noise_stdev_vector is not None
            else np.zeros((observer_size, observer_size))
        )

    @abstractmethod
    def prediction(
        self,
        current_time: float,
        new_time: float,
        state_mean: NDArray[np.float64],
        state_covariance: NDArray[np.float64],
    ) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
        """Predict the state with the model.

        Parameters
        ----------
        current_time : float
            the time value of the current step.
        new_time : float
            the time value of the new step.
        state_mean : NDArray[np.float64]
            The current state.
        state_covariance : NDArray[np.float64]
            the current state covariance

        Returns
        -------
        NDArray[np.float64]
            the predicted state
        NDArray[np.float64]
            the predicted covariance
        """

    @abstractmethod
    def update(
        self,
        time: float,
        predicted_state_mean: NDArray[np.float64],
        predicted_state_covariance: NDArray[np.float64],
        measurement: NDArray[np.float64],
    ) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
        """Correct the prediction with the measurements.

        Parameters
        ----------
        time : float
            the updated (or new) time
        predicted_state_mean : NDArray[np.float64]
            the state from the prediction step.
        predicted_state_covariance : NDArray[np.float64]
            the covariance from the prediction step
        measurement : NDArray[np.float64]
            the measurement at updated (or new) time

        Returns
        -------
        NDArray[np.float64]
            the updated state
        NDArray[np.float64]
            the updated covariance
        """

    def filter(
        self,
        current_time: float,
        new_time: float,
        state_mean: NDArray[np.float64],
        state_covariance: NDArray[np.float64],
        measurement: NDArray[np.float64],
    ) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
        """Perform prediction and update steps.

        Parameters
        ----------
        current_time : float
            the time value of the current step.
        new_time : float
            the time value of the new step.
        state_mean : NDArray[np.float64]
            The current state.
        state_covariance : NDArray[np.float64]
            the current state covariance
        measurement : NDArray[np.float64]
            the measurement at the new time

        Returns
        -------
        NDArray[np.float64]
            the estimated state
        NDArray[np.float64]
            the estimated covariance
        """
        predicted_state, predicted_state_covariance = self.prediction(
            current_time, new_time, state_mean, state_covariance
        )
        return self.update(
            new_time, predicted_state, predicted_state_covariance, measurement
        )


def _build_transformation_function(
    registries: list[QuantitiesRegistry],
    transformation_functions: dict[str, _TransformFunction],
    inverse: bool = False,
) -> _TransformFunction:
    indexed_transformations: list[tuple[int, int, _TransformFunction]] = []
    total_size = 0
    for registry in registries:
        for qty_id, transformation_function in transformation_functions.items():
            if qty_id in registry:
                start_index = registry.indexes[qty_id] + total_size
                end_index = start_index + registry.quantities[qty_id].size
                indexed_transformations.append(
                    (start_index, end_index, transformation_function)
                )

        total_size += registry.size

    magnitudes_vector = np.concat([reg.magnitudes_vector for reg in registries])

    return (
        _TransformationFunction(indexed_transformations, magnitudes_vector)
        if inverse is False
        else _InverseFunction(indexed_transformations, magnitudes_vector)
    )


@dataclass
class _TransformationFunction:
    indexed_transformations: list[tuple[int, int, _TransformFunction]]
    magnitudes_vector: NDArray[np.float64]

    def __call__(self, vector: NDArray[np.float64]) -> NDArray[np.float64]:
        result = vector * self.magnitudes_vector
        for start_index, end_index, transformation in self.indexed_transformations:
            result[start_index:end_index] = transformation(
                result[start_index:end_index]
            )
        return result


@dataclass
class _InverseFunction:
    indexed_transformations: list[tuple[int, int, _TransformFunction]]
    magnitudes_vector: NDArray[np.float64]

    def __call__(self, vector: NDArray[np.float64]) -> NDArray[np.float64]:
        result = vector.copy()
        for start_index, end_index, transformation in self.indexed_transformations:
            result[start_index:end_index] = transformation(
                vector[start_index:end_index]
            )
        return result / self.magnitudes_vector


def _build_estimations_registry(
    estimation_init: dict[str, QuantityInit],
    reference: QuantitiesRegistry | dict[str, Quantity[Any]],
) -> QuantitiesRegistry:
    estimations = QuantitiesRegistry()
    magnitudes = {}
    stdevs = {}
    for param_id, param_init in estimation_init.items():
        if param_id not in reference:
            raise KeyError(f"{param_id} is not a parameter.")
        reference[param_id].initialize(param_init.value)
        estimations[param_id] = reference[param_id]
        magnitudes[param_id] = param_init.magnitude
        stdevs[param_id] = param_init.stdev

    estimations.set_magnitudes(magnitudes)
    estimations.set_stdevs(stdevs)

    return estimations


ESTIMATION_SIM_ID = "estimation_simulation"
"""Type id for estimation simulation"""

OBSERVER_FACTORY_ID = "observer_factory"
"""Parameter name of the observer factory in the estimation simulation"""

ESTIMATED_PARAMETERS_ID = "estimated_parameters"
"""Parameter name of the estimated parameters dictionary."""

FILTER_FACTORY_PARAMETER_ID = "filter_factory"
"""Parameter name of filter factory in the estimation simulation"""

COVARIANCE_LABEL = "covariance"
"""Label for the covariances in simulation results"""

VARIANCE_LABEL = "variance"
"""Label for the variances in simulation results"""

MEASUREMENT_LABEL = "measurement"
"""Label for the measurements in simulation results"""

STDEV_PLUS_LABEL = "stdev_plus"
"""Label for the upper bound (mean + 1.96 stdev) in simulation results"""

STDEV_MIN_LABEL = "stdev_min"
"""Label for the lower bound (mean - 1.96 stdev) in simulation results"""


@register_type(ESTIMATION_SIM_ID)
class EstimationSimulation(AbstractSimulation):
    """Run an estimation simulation.

    Each time step, it runs the estimation filter on the simulation model.

    * The ``prediction`` step of the filter runs the simulation model
      for the current step.
    * The ``update`` step corrects the prediction with the measurements.

    Set the measurements provided to the observer through the data attribute with
    the ``measurements`` id.

    Attributes
    ----------
    estimation_filter : AbstractFilter
        the estimation filter
    observer : Observer
        the simulation observer
    estimations : QuantitiesRegistry
        Ids and initial values for estimated parameters
    transformation_operators : dict[str, AbstractTransformation]
        Transformations putting constraints on particles to respect physiological
        values
    time_tolerance : float
        Absolute time tolerance to consider measurement simulation time equals.
        Default is 1e-9
    min_step : float
        Minimum step size allowed for the continuation algorithm.
        Default is set to the current time step: continuation algorithm is disabled.

    Parameters
    ----------
    filter_type : str
        the registered type id of the estimation filter.
    observer_factory : ObserverFactory
        the factory creating the simulation observer.
    estimated_parameters : dict[str, QuantityInit]
        Ids and initial values for estimated parameters.
    filter_options : dict[str, Any] | None
        additional keyword arguments for the filter. Default is None.
    parallelize : bool
        run the filter state and observation functions in parallel processes.
        Useful for particle filters.
        Default is False.
    nb_processes : int | None
        number of processes when ``parallelize`` is True.
        Default is None (the number of CPUs).
    time_tolerance : float
        see the ``time_tolerance`` attribute. Default is 1e-9.
    min_step : float | None
        see the ``min_step`` attribute. Default is None.
    transformation_operators : dict[str, AbstractTransformation] | None
        see the ``transformation_operators`` attribute. Default is None.
    model_noise_stdev : dict[str, float] | None
        model noise standard deviation for state variables and estimated
        parameters. Default is None.

    Configuration
    -------------

    .. code-block:: json

        {
            "type": "estimation_simulation",
            "simulation_name": "<str>",        // Simulation name
                                               // (optional, default: "main")
            "net": "<net type>",               // The simulation net
            "solver": "<solver type>",         // The solver
                                               // (optional, default: newton_solver)
            "time": "<range type>",            // The simulation time range
            "parameters": {                    // Initialization of each parameter
                "<str>": "<float | initialization function type>"
            },
            "state": {                         // Initialization of each state
                "<str>": "<quantity type>"     // variable
            },
            "estimated_parameters": {          // Initialization of each estimated
                "<str>": "<quantity type>"     // parameter (optional)
            },
            "filter_type": "<str>",            // Type id of the estimation filter
            "filter_options": {},              // Filter options (optional),
                                               // see the filter documentation
            "observer": "<observer type>",     // The observer (optional)
            "update_functions": {              // Function updating each parameter at
                "<str>": "<function type>"     // each time step (optional)
            },
            "output_functions": {              // Function computing each additional
                "<str>": "<function type>"     // output (optional)
            },
            "data": {                          // Input data, with the measurements
                "measurements": "<data reader type>"
            },
            "preprocesses": {                  // Processes run before the simulation
                "<str>": "<process type>"      // (optional)
            },
            "postprocesses": {                 // Processes run after the simulation
                "<str>": "<process type>"      // (optional)
            },
            "plots": {                         // Plots traced by the launcher
                "<str>": "<plot type>"         // (optional)
            },
            "simulation_options": {
                "min_step": "<float>",         // Minimum step of the continuation
                                               // algorithm (optional, default: no
                                               // continuation)
                "time_tolerance": "<float>",   // Absolute tolerance matching the
                                               // measurement times
                                               // (optional, default: 1e-9)
                "parallelize": "<bool>",       // Run filter functions in parallel
                                               // (optional, default: false)
                "nb_processes": "<int>",       // Number of parallel processes
                                               // (optional, default: CPUs count)
                "model_noise_stdev": {         // Model noise standard deviation of
                    "<str>": "<float>"         // state variables and estimated
                },                             // parameters (optional)
                "transformation_operators": {  // Transformation constraining each
                    "<str>": "<transformation type>" // estimated quantity (optional)
                }
            }
        }

    See the :mod:`~physioblocks.library.aliases.simulations` module for estimation
    simulation aliases.

    """

    estimation_filter: AbstractFilter

    observer: Observer

    estimations: QuantitiesRegistry

    transformation_operators: dict[str, AbstractTransformation]

    time_tolerance: float

    min_step: float

    _extended_state: NDArray[np.float64]

    _extended_covariance: NDArray[np.float64]

    def __init__(
        self,
        filter_type: str,
        observer_factory: ObserverFactory,
        estimated_parameters: dict[str, QuantityInit],
        filter_options: dict[str, Any] | None = None,
        parallelize: bool = False,
        nb_processes: int | None = None,
        time_tolerance: float = 1e-9,
        min_step: float | None = None,
        transformation_operators: dict[str, AbstractTransformation] | None = None,
        model_noise_stdev: dict[str, float] | None = None,
        *args: Any,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)

        self.min_step = (
            min_step
            if min_step is not None
            else self.simulation_model.time_manager.step_size
        )

        # Initialize Observer
        self.observer = observer_factory.create_observer(
            self.simulation_model.quantities
        )

        # Initialize estimations
        self.estimations = _build_estimations_registry(
            estimated_parameters, self.simulation_model.parameters
        )

        # Initialize time tolerance when reading measurements
        self.time_tolerance = time_tolerance

        # Initialize transformation function
        transformation_operators = (
            transformation_operators if transformation_operators is not None else {}
        )

        transform_functions = {
            qty_id: transformation.eval
            for qty_id, transformation in transformation_operators.items()
        }
        inverse_functions = {
            qty_id: transformation.eval_inverse
            for qty_id, transformation in transformation_operators.items()
        }

        self.transform_function = _build_transformation_function(
            [self.simulation_model.state, self.estimations], transform_functions
        )
        self.inverse_function = _build_transformation_function(
            [self.simulation_model.state, self.estimations], inverse_functions, True
        )

        # Initialize filter
        extended_state_size = self.simulation_model.state.size + self.estimations.size
        model_noise_stdev = {} if model_noise_stdev is None else model_noise_stdev
        model_noise_stdev_vector = np.zeros(extended_state_size)
        for var_id, var_index in self.simulation_model.state.indexes.items():
            model_noise_stdev_vector[var_index] = model_noise_stdev.get(var_id, 0.0)
        for param_id, param_index in self.estimations.indexes.items():
            model_noise_stdev_vector[self.simulation_model.state.size + param_index] = (
                model_noise_stdev.get(param_id, 0.0)
            )

        filter_factory: type[AbstractFilter] = get_registered_type(filter_type)
        filter_options = {} if filter_options is None else filter_options

        state_function, observation_function = _build_state_observation_functions(
            parallelize,
            self.simulation_model.factory,
            estimated_parameters,
            observer_factory,
            self.transform_function,
            self.inverse_function,
            self.min_step,
            nb_processes,
        )
        self.estimation_filter = filter_factory(
            extended_state_size,
            self.observer.observations.size,
            state_function,
            observation_function,
            model_noise_stdev_vector,
            self.observer.observations.stdevs_vector,
            **filter_options,
        )

        self._extended_state = np.zeros(extended_state_size)
        self._extended_covariance = np.zeros((extended_state_size, extended_state_size))

        self.__covariances_labels: list[str] = []
        self.__stdev_min_labels: list[str] = []
        self.__stdev_plus_labels: list[str] = []

    def _initialize(self) -> Results:
        time_tolerance_log = abs(np.log10(self.time_tolerance))
        self._time_rounding_digits = int(np.ceil(time_tolerance_log))
        rounded_data = self.processed_data[MEASUREMENTS_ID][TIME_QUANTITY_ID].round(
            self._time_rounding_digits
        )
        self.processed_data[MEASUREMENTS_ID][TIME_QUANTITY_ID] = rounded_data
        self.measurements = (
            self.processed_data[MEASUREMENTS_ID].set_index(TIME_QUANTITY_ID).to_dict()
            if MEASUREMENTS_ID in self.processed_data
            else {}
        )
        rounded_time = round(
            self.simulation_model.time_manager.time.current, self._time_rounding_digits
        )
        step_measurements = [
            self.measurements[measurement_id][rounded_time]
            for measurement_id in self.observer.measurements
        ]

        self.observer.measurements.set_vector(np.array(step_measurements))
        scaled_measurement = (
            step_measurements / self.observer.measurements.magnitudes_vector
        )

        state_physical_space = np.concat(
            [self.simulation_model.state.vector, self.estimations.vector]
        )
        self._extended_state = self.inverse_function(state_physical_space)
        self._extended_covariance = np.diag(
            np.concat(
                [
                    self.simulation_model.state.stdevs_vector**2,
                    self.estimations.stdevs_vector**2,
                ]
            )
        )
        self._extended_state, self._extended_covariance = self.estimation_filter.update(
            self.simulation_model.time_manager.time.current,
            self._extended_state,
            self._extended_covariance,
            scaled_measurement,
        )
        state_physical_space = self.transform_function(self._extended_state)
        self.simulation_model.state.set_vector(
            state_physical_space[0 : self.simulation_model.state.size]
        )
        self.estimations.set_vector(
            state_physical_space[self.simulation_model.state.size :]
        )

        self.__covariances_labels = self.__get_covariances_labels()
        self.__stdev_min_labels = [
            label.replace(VARIANCE_LABEL, STDEV_MIN_LABEL)
            for label in self.__covariances_labels
            if label.split(".")[0] == VARIANCE_LABEL
        ]
        self.__stdev_plus_labels = [
            label.replace(VARIANCE_LABEL, STDEV_PLUS_LABEL)
            for label in self.__covariances_labels
            if label.split(".")[0] == VARIANCE_LABEL
        ]

        return super()._initialize()

    def run_step(self) -> None:
        """Run a single simulation step."""
        self.simulation_model.update_functions_parameters()
        rounded_time = round(
            self.simulation_model.time_manager.time.new, self._time_rounding_digits
        )

        step_measurements = [
            self.measurements[measurement_id][rounded_time]
            for measurement_id in self.observer.measurements
        ]
        self.observer.measurements.set_vector(np.array(step_measurements))
        scaled_measurement = (
            step_measurements / self.observer.measurements.magnitudes_vector
        )

        self._extended_state, self._extended_covariance = self.estimation_filter.filter(
            self.simulation_model.time_manager.time.current,
            self.simulation_model.time_manager.time.new,
            self._extended_state,
            self._extended_covariance,
            scaled_measurement,
        )
        state_physical_space = self.transform_function(self._extended_state)

        self.simulation_model.state.set_vector(
            state_physical_space[0 : self.simulation_model.state.size]
        )
        self.estimations.set_vector(
            state_physical_space[self.simulation_model.state.size :]
        )

        self.observer.update_observations()
        self.simulation_model.time_manager.update()

    def _finalize(self) -> None:
        super()._finalize()

        # set initial guess for estimations to the final parameter estimation.
        estimation_init = {
            key: qty.current for key, qty in self.estimations.quantities.items()
        }
        self.factory.simulation_model_factory.parameters.update(estimation_init)
        self.estimations = _build_estimations_registry(
            self.factory.simulation_options["estimated_parameters"],
            self.simulation_model.parameters,
        )

    def _get_current_result(self) -> Result:
        result = super()._get_current_result()

        # Add parameter estimations
        for param_id, param in self.estimations.quantities.items():
            result.update(format_result(param_id, param.current))

        # Save stdev around the mean
        variance = np.diagonal(self._extended_covariance)
        stdev_plus_filter_space = self._extended_state + 1.96 * np.sqrt(variance)
        stdev_min_filter_space = self._extended_state - 1.96 * np.sqrt(variance)
        stdev_plus_physical_space = self.transform_function(stdev_plus_filter_space)
        stdev_min_physical_space = self.transform_function(stdev_min_filter_space)
        stdev_plus_results = dict(
            zip(self.__stdev_plus_labels, stdev_plus_physical_space, strict=True)
        )
        stdev_min_results = dict(
            zip(self.__stdev_min_labels, stdev_min_physical_space, strict=True)
        )
        result.update(stdev_plus_results)
        result.update(stdev_min_results)

        # Add extended state covariances
        covariances = dict(
            zip(
                self.__covariances_labels,
                self._extended_covariance.flatten(),
                strict=True,
            )
        )
        result.update(covariances)

        return result

    def __get_covariances_labels(self) -> list[str]:
        extended_state_ids = (
            self.simulation_model.state.sorted_names + self.estimations.sorted_names
        )
        extended_state_sizes = [
            self.simulation_model.state.quantities[name].size
            if name in self.simulation_model.state.quantities
            else self.estimations.quantities[name].size
            for name in extended_state_ids
        ]
        var_labels = [
            label
            for name, size in zip(extended_state_ids, extended_state_sizes, strict=True)
            for label in (
                [name] if size == 1 else [f"{name}[{i}]" for i in range(size)]
            )
        ]

        return [
            f"{COVARIANCE_LABEL}.{x_label}.{y_label}"
            if x_label != y_label
            else f"{VARIANCE_LABEL}.{x_label}"
            for x_label in var_labels
            for y_label in var_labels
        ]


def _build_state_observation_functions(
    parallelize: bool,
    model_factory: SimulationModelFactory,
    estimations_init: dict[str, QuantityInit],
    observer_factory: ObserverFactory,
    transform_function: _TransformFunction,
    inverse_function: _TransformFunction,
    min_step: float,
    nb_processes: int | None = None,
) -> tuple[
    _ModelFunction,
    _ObserverFunction,
]:
    import physioblocks.simulation._filter_functions as _filter_functions

    if parallelize is False:
        _filter_functions.initialize(
            model_factory,
            estimations_init,
            observer_factory,
            transform_function,
            inverse_function,
            min_step,
        )
        return (
            np.vectorize(
                _filter_functions.compute_state, excluded=[1, 2], signature="(n) -> (n)"
            ),
            np.vectorize(
                _filter_functions.compute_observations,
                excluded=[1],
                signature="(n) -> (m)",
            ),
        )
    else:
        _nb_processes = (
            nb_processes if nb_processes is not None else multiprocessing.cpu_count()
        )
        _pool = multiprocessing.Pool(
            _nb_processes,
            initializer=_filter_functions.initialize,
            initargs=[
                model_factory,
                estimations_init,
                observer_factory,
                transform_function,
                inverse_function,
                min_step,
            ],
        )

        def compute_state_parallel(
            x: NDArray[np.float64], current_time: float, new_time: float
        ) -> NDArray[np.float64]:
            pool_arguments = [
                [x[_index], current_time, new_time] for _index in range(x.shape[0])
            ]
            return np.array(
                _pool.starmap(_filter_functions.compute_state, pool_arguments)
            )

        def compute_observation_parallel(
            x: NDArray[np.float64], new_time: float
        ) -> NDArray[np.float64]:
            pool_arguments = [[x[_index], new_time] for _index in range(x.shape[0])]
            return np.array(
                _pool.starmap(_filter_functions.compute_observations, pool_arguments)
            )

        return compute_state_parallel, compute_observation_parallel
