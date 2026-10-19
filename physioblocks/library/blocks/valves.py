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

"""Module describing Valve Blocks."""

from dataclasses import dataclass
from typing import Any

import numpy as np

from physioblocks.computing import (
    Block,
    Quantity,
    diff,
    mid_alpha,
    mid_point,
)
from physioblocks.computing.models import declares_flux, declares_internal_equation
from physioblocks.registers import register_type
from physioblocks.simulation import Time

# Constant for the valve rl block type id
VALVE_RL_BLOCK_ID = "valve_rl_block"


# Flux through the block
VALVE_RL_BLOCK_FLUX_VAR_ID = "flux"

# Pressure at local node 1
VALVE_RL_BLOCK_PRESSURE_1_DOF_ID = "pressure_1"

# Pressure at local node 2
VALVE_RL_BLOCK_PRESSURE_2_DOF_ID = "pressure_2"


@dataclass
@register_type(VALVE_RL_BLOCK_ID)
class ValveRLBlock(Block):
    r"""Describes valve RL block quantities and flux definitions.

    Scheme
    ------

    .. tikz:: Valve RL Scheme

        \draw (1,2) to[short, i=$Q_2$] (1,1) to[short, -*] (1,0) node[right]{$P_2$};
        \draw (1,2) to[short, L=$L$] (1,4);
        \draw (0,4) -- (2,4);
        \draw (0,4) to[D] (0,6);
        \draw (0,6) to[R=$R_{\text{back}}$] (0,8);
        \draw (2,8) to[D] (2,6);
        \draw (2,6) to[R=$R$] (2,4);
        \draw (0,8) -- (2,8);
        \draw (1,9) to[short, i=$Q$] (1,8);
        \draw (1,9) to[short, i=$Q_1$] (1,10) to [short, -*] (1,10.5)
        node[right]{$P_1$};


    Fluxes
    ------
    *Node 1:*

    .. math::

        Q_1 = - Q

    *Node 2:*

    .. math::

        Q_2 = Q

    Internal Equations
    ------------------

    .. math::

        L\ \dot{Q} + P_2 - P_1 +
        \begin{cases}
        RQ \text{ if Q $>$ 0 } \\
        R_{\text{back}}Q \text{ else }
        \end{cases} = 0

    Discretization
    --------------

    .. math:: Q_1^{{n + \frac{1}{2}}} = - Q^{{n + \frac{1}{2}}}

    .. math:: Q_2^{{n + \frac{1}{2}}} = Q^{{n + \frac{1}{2}}}

    .. math::

        L\ \frac{Q^{n + 1} - Q^{n}}{\Delta t^n}
        + P_2^{n + \frac{1}{2}} - P_1^{n + \frac{1}{2}}
        + \begin{cases}
            RQ^{{n + \theta}} \text{ if } Q^{{n + \theta}} > 0 \\
            R_{\text{back}}Q^{{n + \theta}} \text{ else }
        \end{cases} = 0

    Parameters
    ----------
    flux : Quantity[np.float64]
        :math:`Q` the flux traversing the block
    pressure_1 : Quantity[np.float64]
        :math:`P_1` the pressure at local node 1
    pressure_2 : Quantity[np.float64]
        :math:`P_2` the pressure at local node 2
    inductance : Quantity[np.float64]
        :math:`L` the inductance.
    conductance : Quantity[np.float64]
        :math:`K = \frac{1}{R}` the conductance quantity for positive flux
    backward_conductance : Quantity[np.float64]
        :math:`K_{\text{back}} = \frac{1}{R_{\text{back}}}` the conductance quantity for
        negative flux.
    scheme_ts_flux : Quantity[np.float64]
        :math:`\theta` the scheme time shift for flux
    time : Time
        :math:`t` the simulation time

    Configuration
    -------------

    .. code-block:: json

        {
            "type": "block_description",
            "model_type": "valve_rl_block",
            "flux_type": "<str>",      // Type of flux exchanged by the block
            "nodes": {"1": "<str>", "2": "<str>"}, // Net node names of the local nodes
                                                   // 1 and 2
            "flux": "<str>",           // Flux global name (internal variable) (optional)
            "inductance": "<str>",     // Inductance global name (optional)
            "conductance": "<str>",    // Conductance for positive flux global name (optional)
            "backward_conductance": "<str>", // Conductance for negative flux global name (optional)
            "scheme_ts_flux": "<str>", // time scheme shift for flux global name (optional)
            "time": "<str>"            // Simulation time global name
        }

    Aliases
    -------

    .. _alias_valve_rl_block:

    **valve_rl_block**
        Aliases :class:`~.BlockDescription`
        (``block_description``) with ``model_type`` set to ``valve_rl_block`` and the
        ``time`` quantity bound to the global ``time`` quantity.

        .. code-block:: json

            {
                "type": "valve_rl_block",
                "flux_type": "<str>",      // Type of flux exchanged by the block
                "nodes": {"1": "<str>", "2": "<str>"}, // Net node names of the local
                                                       // nodes 1 and 2
                "flux": "<str>",           // Flux global name (internal variable) (optional)
                "inductance": "<str>",     // Inductance global name (optional)
                "conductance": "<str>",    // Conductance global name for positive flux (optional)
                "backward_conductance": "<str>", // Conductance global name for negative flux (optional)
                "scheme_ts_flux": "<str>"  // Scheme time shift for flux global name (optional)
            }

    """  # noqa: E501

    flux: Quantity[np.float64]

    pressure_1: Quantity[np.float64]

    pressure_2: Quantity[np.float64]

    inductance: Quantity[np.float64]

    conductance: Quantity[np.float64]

    backward_conductance: Quantity[np.float64]

    scheme_ts_flux: Quantity[np.float64]

    time: Time

    def initialize(self) -> None:
        """Initialize block constant values."""
        self.k_0 = (
            2.0
            * (self.conductance.current * self.backward_conductance.current)
            / (self.conductance.current + self.backward_conductance.current)
        )

    @declares_internal_equation(VALVE_RL_BLOCK_FLUX_VAR_ID)
    def flux_residual(self) -> Any:
        """Compute the residual giving the dynamics on the flux in the valve.

        Returns
        -------
        np.float64
            the residual value

        """
        q_mid_alpha = mid_alpha(self.flux, self.scheme_ts_flux.current)
        pressure_1_mid_point = mid_point(self.pressure_1)
        pressure_2_mid_point = mid_point(self.pressure_2)

        conductance = self.conductance.current
        if q_mid_alpha < 0:
            conductance = self.backward_conductance.current

        return (
            self.inductance.current * self.time.inv_dt * diff(self.flux)
            - pressure_1_mid_point
            + pressure_2_mid_point
            + q_mid_alpha / conductance
        )

    @flux_residual.partial_derivative(VALVE_RL_BLOCK_FLUX_VAR_ID)
    def flux_residual_dflux(self) -> Any:
        """Compute the residual partial derivative for ``flux``.

        Returns
        -------
        np.float64
            the residual partial derivative for ``flux``

        """
        q_mid_alpha = mid_alpha(self.flux, self.scheme_ts_flux.current)
        conductance = self.conductance.current
        if q_mid_alpha < 0:
            conductance = self.backward_conductance.current
        elif q_mid_alpha == 0:
            conductance = self.k_0

        return (
            self.inductance.current * self.time.inv_dt
            + (0.5 + self.scheme_ts_flux.current) / conductance
        )

    @flux_residual.partial_derivative(VALVE_RL_BLOCK_PRESSURE_1_DOF_ID)
    def flux_residual_dp1(self) -> Any:
        """Compute the residual partial derivative for ``pressure_1``.

        Returns
        -------
        np.float64
            the residual partial derivative for ``pressure_1``

        """
        return -0.5

    @flux_residual.partial_derivative(VALVE_RL_BLOCK_PRESSURE_2_DOF_ID)
    def flux_residual_dp2(self) -> Any:
        """Compute the residual partial derivative for ``pressure_2``.

        Returns
        -------
        np.float64
            the residual partial derivative for ``pressure_2``

        """
        return 0.5

    @declares_flux(1, VALVE_RL_BLOCK_PRESSURE_1_DOF_ID)
    def flux_1(self) -> Any:
        """Compute the block flux at node 1.

        Returns
        -------
        np.float64
            the block flux at node 1

        """
        return -mid_point(self.flux)

    @flux_1.partial_derivative(VALVE_RL_BLOCK_FLUX_VAR_ID)
    def dflux_1_dflux(self) -> Any:
        """Compute the block flux at node 1 partial derivative for ``flux``.

        Returns
        -------
        np.float64
            the block flux at node 1 partial derivative for ``flux``

        """
        return -0.5

    @declares_flux(2, VALVE_RL_BLOCK_PRESSURE_2_DOF_ID)
    def flux_2(self) -> Any:
        """Compute the block flux at node 2.

        Returns
        -------
        np.float64
            the block flux at node 2

        """
        return mid_point(self.flux)

    @flux_2.partial_derivative(VALVE_RL_BLOCK_FLUX_VAR_ID)
    def dflux_2_dflux(self) -> Any:
        """Compute the block flux at node 2 partial derivative for ``flux``.

        Returns
        -------
        np.float64
            the block flux at node 2 partial derivative for ``flux``

        """
        return 0.5
