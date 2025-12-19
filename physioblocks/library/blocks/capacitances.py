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

from physioblocks.computing import Block, Expression, Quantity, diff, mid_point
from physioblocks.registers import register_type
from physioblocks.simulation import Time

# C BLOCK Definition


# Constant for the c block type id
C_BLOCK_TYPE_ID = "c_block"

# Constant for the c block dof id
C_BLOCK_PRESSURE_DOF_ID = "pressure"


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

    def flux(self) -> Any:
        """
        Compute the flux at local node 1

        :return: the flux
        :rtype: np.float64
        """
        return -self.capacitance.current * diff(self.pressure) * self.time.inv_dt

    def dflux_dpressure(self) -> Any:
        """
        Compute the flux at local node 1 partial derivative for pressure

        :return: the flux derivative
        :rtype: np.float64
        """
        return -self.capacitance.current * self.time.inv_dt


_c_block_flux_expression = Expression(
    1, CBlock.flux, {C_BLOCK_PRESSURE_DOF_ID: CBlock.dflux_dpressure}
)
CBlock.declares_flux_expression(1, C_BLOCK_PRESSURE_DOF_ID, _c_block_flux_expression)


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

    def flux_1(self) -> Any:
        """
        Computes the outlet flux at local node 1.

        :return: the flux value for current block values
        :rtype: np.float64
        """
        pressure_1 = mid_point(self.pressure_1)
        pressure_2 = mid_point(self.pressure_2)
        return (pressure_2 - pressure_1) / self.resistance.current

    def dflux_1_dpressure_1(self) -> Any:
        """
        Computes the outlet flux at node 1 derivative for pressure_1.

        :return: the flux derivative for pressure_1
        :rtype: np.float64
        """
        return -0.5 / self.resistance.current

    def dflux_1_dpressure_2(self) -> Any:
        """
        Computes the outlet flux at node 1 derivative for pressure_2.

        :return: the flux derivative for pressure_2
        :rtype: np.float64
        """
        return 0.5 / self.resistance.current

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

    def dflux_2_dpressure_1(self) -> Any:
        """
        Computes the outlet flux at node 2 derivative for pressure_1.

        :return: the flux derivative for pressure_1
        :rtype: np.float64
        """
        return 0.5 / self.resistance.current

    def dflux_2_dpressure_2(self) -> Any:
        """
        Computes the outlet flux at node 2 derivative for pressure_2.

        :return: the flux derivative for pressure_2
        :rtype: np.float64
        """
        return (
            -0.5 / self.resistance.current - self.capacitance.current * self.time.inv_dt
        )


# Define the flux expression going in the input node for rc_block
_rc_block_flux_1_expr = Expression(
    1,
    RCBlock.flux_1,
    {
        RC_BLOCK_PRESSURE_1_DOF_ID: RCBlock.dflux_1_dpressure_1,
        RC_BLOCK_PRESSURE_2_DOF_ID: RCBlock.dflux_1_dpressure_2,
    },
)

# Define the flux expression going in the output node for rc_block
_rc_block_flux_2_expr = Expression(
    1,
    RCBlock.flux_2,
    {
        RC_BLOCK_PRESSURE_1_DOF_ID: RCBlock.dflux_2_dpressure_1,
        RC_BLOCK_PRESSURE_2_DOF_ID: RCBlock.dflux_2_dpressure_2,
    },
)

RCBlock.declares_flux_expression(1, RC_BLOCK_PRESSURE_1_DOF_ID, _rc_block_flux_1_expr)
RCBlock.declares_flux_expression(2, RC_BLOCK_PRESSURE_2_DOF_ID, _rc_block_flux_2_expr)

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

    **Discretisation:**

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

    def flux_1(self) -> Any:
        """
        Computes the outlet flux at node 1.

        :return: the flux value
        :rtype: np.float64
        """

        pressure_1_discr = mid_point(self.pressure_1)
        pressure_mid_discr = mid_point(self.pressure_mid)

        return (pressure_mid_discr - pressure_1_discr) / self.resistance_1.current

    def dflux_1_dp_1(self) -> Any:
        """
        Computes the outlet flux at node 1 derivative for pressure_1.

        :return: flux derivative for pressure_1
        :rtype: np.float64
        """

        return -0.5 / self.resistance_1.current

    def dflux_1_dp_mid(self) -> Any:
        """
        Computes the outlet flux at node 1 derivative for pressure_mid.

        :return: flux derivative for pressure_2
        :rtype: np.float64
        """

        return 0.5 / self.resistance_1.current

    def flux_2(self) -> Any:
        """
        Computes the flux at node 2.

        :return: the flux value
        :rtype: np.float64
        """
        pressure_2_discr = mid_point(self.pressure_2)
        pressure_mid_discr = mid_point(self.pressure_mid)

        return (pressure_mid_discr - pressure_2_discr) / self.resistance_2.current

    def dflux_2_dp_mid(self) -> Any:
        """
        Computes the outlet flux at node 2 derivative for pressure_mid.

        :return: flux derivative for pressure_mid
        :rtype: np.float64
        """

        return 0.5 / self.resistance_2.current

    def dflux_2_dp_2(self) -> Any:
        """
        Computes the outlet flux at node 2 derivative for pressure_2.

        :return: flux derivative for pressure_2
        :rtype: np.float64
        """

        return -0.5 / self.resistance_2.current

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

    def pressure_mid_residual_dp_1(self) -> Any:
        """
        Compute the residual derivative for pressure_1

        :return: the residual derivative for pressure_1
        :rtype: np.float64
        """

        return 0.5 / self.resistance_1.current

    def pressure_mid_residual_dp_2(self) -> Any:
        """
        Compute the residual derivative for pressure_2

        :return: the residual derivative for pressure_2
        :rtype: np.float64
        """

        return 0.5 / self.resistance_2.current

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

    def compute_volume_stored(self) -> Any:
        """
        Computes volume stored in the capacitance.

        :return: volume stored in the capacitance
        :rtype: np.float64
        """

        return self.capacitance.current * self.pressure_mid.current


# Define the flux expression going in node 1 for rcr block
_rcr_block_flux_1_expr = Expression(
    1,
    RCRBlock.flux_1,
    {
        RCR_BLOCK_PRESSURE_1_ID: RCRBlock.dflux_1_dp_1,
        RCR_BLOCK_PRESSURE_MID_ID: RCRBlock.dflux_1_dp_mid,
    },
)


# Define the flux expression going in node 2 for rcr block
_rcr_block_flux_2_expr = Expression(
    1,
    RCRBlock.flux_2,
    {
        RCR_BLOCK_PRESSURE_MID_ID: RCRBlock.dflux_2_dp_mid,
        RCR_BLOCK_PRESSURE_2_ID: RCRBlock.dflux_2_dp_2,
    },
)

# Define the residual expression giving the pressure at the mid node
_rcr_block_pressure_mid_residual_expr = Expression(
    1,
    RCRBlock.pressure_mid_residual,
    {
        RCR_BLOCK_PRESSURE_1_ID: RCRBlock.pressure_mid_residual_dp_1,
        RCR_BLOCK_PRESSURE_MID_ID: RCRBlock.pressure_mid_residual_dp_mid,
        RCR_BLOCK_PRESSURE_2_ID: RCRBlock.pressure_mid_residual_dp_2,
    },
)

# Derfine the stored volume saved quantity expression.
_rcr_volume_stored_expr = Expression(1, RCRBlock.compute_volume_stored)


RCRBlock.declares_internal_expression(
    RCR_BLOCK_PRESSURE_MID_ID, _rcr_block_pressure_mid_residual_expr
)

RCRBlock.declares_flux_expression(1, RCR_BLOCK_PRESSURE_1_ID, _rcr_block_flux_1_expr)
RCRBlock.declares_flux_expression(2, RCR_BLOCK_PRESSURE_2_ID, _rcr_block_flux_2_expr)
RCRBlock.declares_saved_quantity_expression(
    RCR_BLOCK_VOLUME_OUTPUT_ID, _rcr_volume_stored_expr
)
