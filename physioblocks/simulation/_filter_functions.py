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

from collections.abc import Callable

import numpy as np
from numpy.typing import NDArray

from physioblocks.computing.quantities import QuantitiesRegistry, QuantityInit
from physioblocks.simulation.base import SimulationModel, SimulationModelFactory
from physioblocks.simulation.estimation import (
    Observer,
    ObserverFactory,
    _build_estimations_registry,
)
from physioblocks.simulation.forward import solve_step

_TransformFunction = Callable[[NDArray[np.float64]], NDArray[np.float64]]

sim_model: SimulationModel
estimations: QuantitiesRegistry
observer: Observer
min_step: float
transform_function: _TransformFunction
inverse_function: _TransformFunction


def initialize(
    model_factory: SimulationModelFactory,
    estimations_init: dict[str, QuantityInit],
    observer_factory: ObserverFactory,
    transform_functions: _TransformFunction,
    inverse_functions: _TransformFunction,
    min_step_init: float | None = None,
) -> None:
    global sim_model
    global estimations
    global observer
    global transform_function
    global inverse_function
    global min_step
    sim_model = model_factory.create_simulation_model()

    estimations = _build_estimations_registry(estimations_init, sim_model.parameters)
    observer = observer_factory.create_observer(sim_model.quantities)
    transform_function = transform_functions
    inverse_function = inverse_functions
    min_step = (
        min_step_init if min_step_init is not None else sim_model.time_manager.step_size
    )


def compute_state(
    x: NDArray[np.float64], current_time: float, new_time: float
) -> NDArray[np.float64]:
    """Compute the new state at the given time step.

    Parameters
    ----------
    x : NDArray[np.float64]
        the current state
    current_time : float
        the current time
    new_time : float
        the targeted time

    Returns
    -------
    NDArray[np.float64]
        the new state

    """
    x_physical_space = transform_function(x)
    sim_model.time_manager.time.initialize(current_time)
    sim_model.time_manager.time.update(new_time)
    state_physical_space = x_physical_space[: sim_model.state.size]
    estimations_physical_space = x_physical_space[sim_model.state.size :]

    sim_model.state.set_vector(state_physical_space)
    estimations.set_vector(estimations_physical_space)

    sim_model.update_functions_parameters()

    new_x_physical_space = np.concat(
        [solve_step(sim_model, min_step), estimations_physical_space]
    )

    new_x_filter_space = inverse_function(new_x_physical_space)
    return new_x_filter_space


def compute_observations(
    x: NDArray[np.float64], new_time: np.float64
) -> NDArray[np.float64]:
    """Compute the observations at the given time step.

    The observations are scaled by their magnitude.

    Parameters
    ----------
    x : NDArray[np.float64]
        the current state
    new_time : float
        the targeted time

    Returns
    -------
    NDArray[np.float64]
        the observations scaled by magnitude

    """
    x_physical_space = transform_function(x)

    state_physical_space = x_physical_space[: sim_model.state.size]
    estimations_physical_space = x_physical_space[sim_model.state.size :]
    sim_model.time_manager.time.initialize(new_time)

    sim_model.state.set_vector(state_physical_space)
    estimations.set_vector(estimations_physical_space)

    sim_model.update_functions_parameters()
    sim_model.saved_quantities.update()
    observer.update_observations()

    observations_physical_space = observer.observations.vector
    return observations_physical_space / observer.observations.magnitudes_vector
