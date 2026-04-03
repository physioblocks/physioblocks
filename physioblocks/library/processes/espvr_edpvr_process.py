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

from typing import Any

from pandas import DataFrame, concat
from rich.progress import Progress

from physioblocks.computing.quantities import Quantity
from physioblocks.description.nets import Net
from physioblocks.registers.type_register import register_type
from physioblocks.simulation.runtime import (
    AbstractSimulation,
    AbstractSimulationProcess,
    StaticSimulation,
)
from physioblocks.simulation.setup import SimulationFactory
from physioblocks.simulation.solvers import NewtonSolver
from physioblocks.simulation.time_manager import TIME_QUANTITY_ID


@register_type("compute_espvr_edpvr")
class EspvrEdpvrProcess(AbstractSimulationProcess):
    """
    Compute ESPVR and EDPVR curves for the given net and parameters.
    """

    parent_simulation: AbstractSimulation

    alternative_cavity_id: str
    displacement: Quantity[Any]
    displacement_min: float
    displacement_max: float
    displacement_step: float

    def __init__(
        self,
        alternative_cavity_id: str,
        displacement_id: str,
        displacement_min: float,
        displacement_max: float,
        displacement_step: float,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        self.alternative_cavity_id = alternative_cavity_id
        self.displacement_id = displacement_id
        self.displacement_min = displacement_min
        self.displacement_max = displacement_max
        self.displacement_step = displacement_step

        super().__init__(*args, **kwargs)

    def run(self) -> list[DataFrame]:
        """
        Run a static simulations piloted on displacement on the asymptotic cavity model
        to compute ESPVR and EDPVR.

        :return: the outputs dataframes
        :rtype: list[DataFrame]
        """

        parent_net: Net = self.parent_simulation.factory.net
        cavity_net = parent_net.get_alternative_net(self.alternative_cavity_id)

        factory = SimulationFactory(
            "espvr_edpvr",
            StaticSimulation,
            NewtonSolver(tolerance=1e-12, iteration_max=10),
            cavity_net,
        )
        sim = factory.create_simulation()

        for qty_id, qty in self.parent_simulation.quantities.items():
            if qty_id in sim.quantities:
                sim.quantities[qty_id].initialize(qty.current)

        if self.displacement_id in sim.quantities:
            displacement_qty = sim.quantities[self.displacement_id]
        else:
            raise KeyError(
                str.format(
                    "{0}: not found in simulation quantities.", self.displacement_id
                )
            )

        # Get variable magnitudes from parent simulation
        variable_magnitudes = {
            qty_id: qty
            for qty_id, qty in self.parent_simulation.state.magnitudes.items()
            if qty_id in sim.state
        }
        sim.state.set_variables_magnitudes(variable_magnitudes)

        results: list[DataFrame] = []

        disp = self.displacement_min

        progress_step_update = (
            100.0
            * self.displacement_step
            / (self.displacement_max - self.displacement_min)
        )
        with Progress() as progress:
            sim_task = progress.add_task(
                str.format("{0}: simulation in progress...", sim.name)
            )
            while disp <= self.displacement_max:
                displacement_qty.initialize(disp)
                result_line = sim.run()
                result_line[sim.name][self.displacement_id] = disp
                results.append(result_line[sim.name])
                disp += self.displacement_step
                progress.advance(sim_task, advance=progress_step_update)

        results_df: DataFrame = concat(results)
        results_df = (
            results_df.drop(columns=TIME_QUANTITY_ID)
            if TIME_QUANTITY_ID in results_df
            else results_df
        )
        return [results_df]
