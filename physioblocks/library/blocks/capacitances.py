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

"""Module describing capacitance blocks"""

from dataclasses import dataclass
from typing import Any

import numpy as np

from physioblocks.computing import Block, Quantity, diff, mid_point
from physioblocks.computing.models import (
    declares_flux,
    declares_internal_equation,
    declares_saved_quantity,
)
from physioblocks.registers import register_type
from physioblocks.simulation import Time

# C BLOCK Definition


# Constant for the c block type id
C_BLOCK_TYPE_ID = "c_block"

# Constant for the c block pressure local id
C_BLOCK_PRESSURE_ID = "pressure"


@register_type(C_BLOCK_TYPE_ID)
@dataclass
class CBlock(Block):
    r"""
    C Block quantities and flux definitions

    .. tikz:: C Block scheme

        \draw (0,1) to[short, -*, i=$Q$] (0,3) node[right]{$P$}
            (0,1) to[C=$C$] (0,0) node[ground]{};

    **Node 1:**

       :math:`Q = - C\dot{P}`

    **Discretisation:**

    .. math::

        Q^{n + \frac{1}{2}} = - C\ \frac{P^{n + 1} - P^{n}}{\Delta t^n}

    """

    pressure: Quantity[np.float64]
    """Pressure quantity"""

    capacitance: Quantity[np.float64]
    """Block capacitance quantity"""

    time: Time
    """Simulation time"""

    @declares_flux(1, C_BLOCK_PRESSURE_ID)
    def flux(self) -> Any:
        """
        Compute the flux at local node 1

        :return: the flux
        :rtype: np.float64
        """
        return -self.capacitance.current * diff(self.pressure) * self.time.inv_dt

    @flux.partial_derivative(C_BLOCK_PRESSURE_ID)
    def dflux_dpressure(self) -> Any:
        """
        Compute the flux at local node 1 partial derivative for pressure

        :return: the flux derivative
        :rtype: np.float64
        """
        return -self.capacitance.current * self.time.inv_dt


# RC BLOCK Definition

# Constant for the rc block type id
RC_BLOCK_TYPE_ID = "rc_block"

# Constant for the pressure in local id
RC_BLOCK_PRESSURE_1_DOF_ID = "pressure_1"

# Constant for the pressure out local id
RC_BLOCK_PRESSURE_2_DOF_ID = "pressure_2"


@register_type(RC_BLOCK_TYPE_ID)
@dataclass
class RCBlock(Block):
    r"""
    RC Block quantities and fluxes definitions

    .. tikz:: RC Block scheme

        \draw (0,3) node[below]{$P_{1}$} to[short, *-] (1,3);
        \draw (2, 3) to[short, i=$Q_{1}$] (1, 3);
        \draw (2, 3) to[R=$R$] (4,3);
        \draw (4,3) to[C=$C$] (4,0) node[ground]{};
        \draw (4,3) to[short, -*, i=$Q_{2}$] (6,3) node[below]{$P_{2}$};

    **Node 1:**

        :math:`Q_1 = \frac{P_2 - P_1}{R}`

    **Node 2:**

        :math:`Q_2 =  \frac{P_1 - P_2}{R} - C\dot{P_2}`

    **Discretisation:**

    .. math::

        Q_1^{n + \frac{1}{2}} = \frac{P_2^{n + \frac{1}{2}} - P_1^{n + \frac{1}{2}}}{R}

    .. math::

        Q_2^{n + \frac{1}{2}} = \frac{P_1^{n + \frac{1}{2}} - P_2^{n + \frac{1}{2}}}{R}
        - C\ \frac{P_2^{n + 1} - P_2^{n}}{\Delta t^n}

    """

    pressure_1: Quantity[np.float64]
    """Pressure at local node 1 of the block"""

    pressure_2: Quantity[np.float64]
    """Pressure at local node 2 of the block"""

    resistance: Quantity[np.float64]
    """Resistance value of the block"""

    capacitance: Quantity[np.float64]
    """Capacitor value of the block"""

    time: Time
    """The simulation time"""

    @declares_flux(1, RC_BLOCK_PRESSURE_1_DOF_ID)
    def flux_1(self) -> Any:
        """
        Computes the outlet flux at local node 1.

        :return: the flux value for current block values
        :rtype: np.float64
        """
        pressure_1 = mid_point(self.pressure_1)
        pressure_2 = mid_point(self.pressure_2)
        return (pressure_2 - pressure_1) / self.resistance.current

    @flux_1.partial_derivative(RC_BLOCK_PRESSURE_1_DOF_ID)
    def dflux_1_dpressure_1(self) -> Any:
        """
        Computes the outlet flux at node 1 derivative for pressure_1.

        :return: the flux derivative for pressure_1
        :rtype: np.float64
        """
        return -0.5 / self.resistance.current

    @flux_1.partial_derivative(RC_BLOCK_PRESSURE_2_DOF_ID)
    def dflux_1_dpressure_2(self) -> Any:
        """
        Computes the outlet flux at node 1 derivative for pressure_2.

        :return: the flux derivative for pressure_2
        :rtype: np.float64
        """
        return 0.5 / self.resistance.current

    @declares_flux(2, RC_BLOCK_PRESSURE_2_DOF_ID)
    def flux_2(self) -> Any:
        """
        Computes the outlet flux at node 2.

        :return: the flux value for current block values
        :rtype: np.float64
        """
        pressure_1 = mid_point(self.pressure_1)
        pressure_2 = mid_point(self.pressure_2)
        dpressure_2 = diff(self.pressure_2)
        return (
            (pressure_1 - pressure_2) / self.resistance.current
            - self.capacitance.current * self.time.inv_dt * dpressure_2
        )

    @flux_2.partial_derivative(RC_BLOCK_PRESSURE_1_DOF_ID)
    def dflux_2_dpressure_1(self) -> Any:
        """
        Computes the outlet flux at node 2 derivative for pressure_1.

        :return: the flux derivative for pressure_1
        :rtype: np.float64
        """
        return 0.5 / self.resistance.current

    @flux_2.partial_derivative(RC_BLOCK_PRESSURE_2_DOF_ID)
    def dflux_2_dpressure_2(self) -> Any:
        """
        Computes the outlet flux at node 2 derivative for pressure_2.

        :return: the flux derivative for pressure_2
        :rtype: np.float64
        """
        return (
            -0.5 / self.resistance.current - self.capacitance.current * self.time.inv_dt
        )


# RCR BLOCK Definition

# Constant for the rcr block type id
RCR_BLOCK_TYPE_ID = "rcr_block"

# Constant for the rcr block volume saved quantity
RCR_BLOCK_VOLUME_OUTPUT_ID = "volume_stored"

# Constant for the rcr block pressure at the mid point
RCR_BLOCK_PRESSURE_MID_ID = "pressure_mid"

# Constant for the rcr block pressure at local node 1
RCR_BLOCK_PRESSURE_1_ID = "pressure_1"

# Constant for the rcr block pressure at local node 2
RCR_BLOCK_PRESSURE_2_ID = "pressure_2"


@register_type(RCR_BLOCK_TYPE_ID)
@dataclass
class RCRBlock(Block):
    r"""
    RCR Block quantities and flux definitions

    .. tikz::

        \draw (-5,3) node[above]{$P_1$} to[short, *-] (-4,3);
        \draw (-3, 3) to[short, i=$Q_1$] (-4,3);
        \draw (-3, 3) to [R=$R_1$]  (0, 3);
        \draw (0, 3) node[above]{$P_{mid}$} to [short, *-, R=$R_2$]  (3, 3);
        \draw (3, 3) to[short, i=$Q_2$] (4, 3);
        \draw (4,3) to[short, -*] (5,3) node[above]{$P_2$};
        \draw (0,3) to[C=$C$] (0,0) node[ground]{};

    **Node 1:**

        :math:`Q_1 = \frac{P_{mid} - P_1}{R_1}`

    **Node 2:**

        :math:`Q_2 = \frac{P_{mid} - P_2}{R_2}`

    **Internal equation:**

        .. math::

            \frac{P_1 - P_{mid}}{R_1} + \frac{P_2 - P_{mid}}{R_2} - C\dot{P}_{mid} = 0

    **Discretization:**

        .. math::

            Q_1^{n + \frac{1}{2}} = \frac{P_{mid}^{n + \frac{1}{2}}
            - P_1^{n + \frac{1}{2}}}{R_1}

        .. math::

            Q_2^{n + \frac{1}{2}} = \frac{P_{mid}^{n + \frac{1}{2}}
            - P_2^{n + \frac{1}{2}}}{R_2}

        .. math::

            \frac{P_1^{n + \frac{1}{2}} - P_{mid}^{n + \frac{1}{2}}}{R_1}
            + \frac{P_2^{n + \frac{1}{2}} - P_{mid}^{n + \frac{1}{2}}}{R_2}
            - C\ \frac{P_{mid}^{n + 1} - P_{mid}^{n}}{\Delta t^n} = 0

    """

    pressure_1: Quantity[np.float64]
    """Pressure at the input of the block"""

    pressure_2: Quantity[np.float64]
    """Pressure at the output of the block"""

    pressure_mid: Quantity[np.float64]
    """Pressure at the output of the block"""

    resistance_1: Quantity[np.float64]
    """Resistance in value of the block"""

    capacitance: Quantity[np.float64]
    """Capacitor value of the block"""

    resistance_2: Quantity[np.float64]
    """Resistance out value of the block"""

    time: Time
    """The simulation time"""

    @declares_flux(1, RCR_BLOCK_PRESSURE_1_ID)
    def flux_1(self) -> Any:
        """
        Computes the outlet flux at node 1.

        :return: the flux value
        :rtype: np.float64
        """

        pressure_1_discr = mid_point(self.pressure_1)
        pressure_mid_discr = mid_point(self.pressure_mid)

        return (pressure_mid_discr - pressure_1_discr) / self.resistance_1.current

    @flux_1.partial_derivative(RCR_BLOCK_PRESSURE_1_ID)
    def dflux_1_dp_1(self) -> Any:
        """
        Computes the outlet flux at node 1 derivative for pressure_1.

        :return: flux derivative for pressure_1
        :rtype: np.float64
        """

        return -0.5 / self.resistance_1.current

    @flux_1.partial_derivative(RCR_BLOCK_PRESSURE_MID_ID)
    def dflux_1_dp_mid(self) -> Any:
        """
        Computes the outlet flux at node 1 derivative for pressure_mid.

        :return: flux derivative for pressure_2
        :rtype: np.float64
        """

        return 0.5 / self.resistance_1.current

    @declares_flux(2, RCR_BLOCK_PRESSURE_2_ID)
    def flux_2(self) -> Any:
        """
        Computes the flux at node 2.

        :return: the flux value
        :rtype: np.float64
        """
        pressure_2_discr = mid_point(self.pressure_2)
        pressure_mid_discr = mid_point(self.pressure_mid)

        return (pressure_mid_discr - pressure_2_discr) / self.resistance_2.current

    @flux_2.partial_derivative(RCR_BLOCK_PRESSURE_MID_ID)
    def dflux_2_dp_mid(self) -> Any:
        """
        Computes the outlet flux at node 2 derivative for pressure_mid.

        :return: flux derivative for pressure_mid
        :rtype: np.float64
        """

        return 0.5 / self.resistance_2.current

    @flux_2.partial_derivative(RCR_BLOCK_PRESSURE_2_ID)
    def dflux_2_dp_2(self) -> Any:
        """
        Computes the outlet flux at node 2 derivative for pressure_2.

        :return: flux derivative for pressure_2
        :rtype: np.float64
        """

        return -0.5 / self.resistance_2.current

    @declares_internal_equation(RCR_BLOCK_PRESSURE_MID_ID)
    def pressure_mid_residual(self) -> Any:
        """
        Compute the residual representing dynamics of the mid node pressure.

        :return: the residual value
        :rtype: np.float64
        """

        p_1_discr = mid_point(self.pressure_1)
        p_mid_discr = mid_point(self.pressure_mid)
        p_2_discr = mid_point(self.pressure_2)

        return (
            +(p_1_discr - p_mid_discr) / self.resistance_1.current
            + (p_2_discr - p_mid_discr) / self.resistance_2.current
            - self.capacitance.current * self.time.inv_dt * diff(self.pressure_mid)
        )

    @pressure_mid_residual.partial_derivative(RCR_BLOCK_PRESSURE_1_ID)
    def pressure_mid_residual_dp_1(self) -> Any:
        """
        Compute the residual derivative for pressure_1

        :return: the residual derivative for pressure_1
        :rtype: np.float64
        """

        return 0.5 / self.resistance_1.current

    @pressure_mid_residual.partial_derivative(RCR_BLOCK_PRESSURE_2_ID)
    def pressure_mid_residual_dp_2(self) -> Any:
        """
        Compute the residual derivative for pressure_2

        :return: the residual derivative for pressure_2
        :rtype: np.float64
        """

        return 0.5 / self.resistance_2.current

    @pressure_mid_residual.partial_derivative(RCR_BLOCK_PRESSURE_MID_ID)
    def pressure_mid_residual_dp_mid(self) -> Any:
        """
        Compute the residual derivative for pressure_mid

        :return: the residual derivative for pressure_mid
        :rtype: np.float64
        """

        return (
            -self.capacitance.current * self.time.inv_dt
            - 0.5 / self.resistance_1.current
            - 0.5 / self.resistance_2.current
        )

    @declares_saved_quantity("volume")
    def compute_volume_stored(self) -> Any:
        """
        Computes volume stored in the capacitance.

        :return: volume stored in the capacitance
        :rtype: np.float64
        """

        return self.capacitance.current * self.pressure_mid.current
