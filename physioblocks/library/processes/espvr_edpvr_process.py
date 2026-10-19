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
"""Declare a process to compute the ESPVR and EDPVR curves."""

from typing import Any

from pandas import DataFrame

from physioblocks.description.nets import Net
from physioblocks.registers.type_register import register_type
from physioblocks.simulation.base import (
    AbstractSimulationProcess,
    SimulationModelFactory,
    SimulationRange,
)
from physioblocks.simulation.solvers import ConvergenceError

ESPVR_EDPVR_PROCESS_ID = "compute_espvr_edpvr"


@register_type(ESPVR_EDPVR_PROCESS_ID)
class EspvrEdpvrProcess(AbstractSimulationProcess):
    """Compute ESPVR and EDPVR curves for the given net and parameters.

    Parameters
    ----------
    alternative_cavity_id : str
        The id of the alternate model describing the
        asymptotic model of the cavity
    displacement_id : str
        The id of the displacement parameter driving the simulation
    displacement_range : SimulationRange
        The displacement range driving the simulation

    Configuration
    -------------

    .. code-block:: json

        {
            "type": "compute_espvr_edpvr",
            "outputs": ["<str>"],                // Name of the ESPVR and EDPVR output
            "alternative_cavity_id": "<str>",    // Alternative type tag of the
                                                 // asymptotic cavity model
            "displacement_id": "<str>",          // Global name of the displacement
                                                 // driving the simulation
            "displacement_range": "<range type>" // Displacement range
        }

    """

    def __init__(
        self,
        alternative_cavity_id: str,
        displacement_id: str,
        displacement_range: SimulationRange,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        self.alternative_cavity_id = alternative_cavity_id
        self.displacement_id = displacement_id
        self.displacement_range = displacement_range

        super().__init__(*args, **kwargs)

    def run(self) -> list[DataFrame]:
        """Run static simulations driven by the displacement on the asymptotic cavity.

        Returns
        -------
        list[DataFrame]
            the outputs dataframes

        """
        parent_net: Net = self.model_factory.net
        cavity_net = parent_net.get_alternative_net(self.alternative_cavity_id)
        asymptotic_cavity_model_factory = SimulationModelFactory(
            cavity_net, parameters=self.model_factory.parameters.copy()
        )
        sim_model = asymptotic_cavity_model_factory.create_simulation_model()
        results = []
        disp = sim_model.parameters[self.displacement_id]
        disp.initialize(self.displacement_range.start)
        end = self.displacement_range.start + self.displacement_range.length
        while disp <= end:
            sol = sim_model.solver.solve(sim_model.state, sim_model.equation_system)
            if sol.converged is True:
                sim_model.state.set_vector(sol.x)
                sim_model.saved_quantities.update()
            else:
                raise ConvergenceError(
                    "ESPVR-EDPVR process did not converge for "
                    f"displacement: {disp.current}"
                )
            result_line = {self.displacement_id: disp.current}
            result_line.update(
                {
                    variable_id: variable_qty.current
                    for variable_id, variable_qty in sim_model.state.quantities.items()
                }
            )
            result_line.update(
                {
                    saved_qty_id: saved_qty.current
                    for saved_qty_id, saved_qty in sim_model.saved_quantities.items()
                }
            )

            results.append(result_line)
            disp += self.displacement_range.step_size
        return [DataFrame(results)]
