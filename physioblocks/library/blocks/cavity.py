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

"""
Describes cavity blocks
"""

from dataclasses import dataclass
from typing import Any

import numpy as np

from physioblocks.computing import Block, Expression, Quantity
from physioblocks.registers import register_type
from physioblocks.simulation import Time

# Local id for the volume saved quantity
CAVITY_VOLUME_LOCAL_ID = "volume"

# Local id for the pressure dof in the cavity
CAVITY_PRESSURE_LOCAL_ID = "pressure"

# Local id for the pressure dof in the cavity
CAVITY_DISP_LOCAL_ID = "disp"

# Constant for the cavity block type id
CAVITY_BLOCK_TYPE_ID = "spherical_cavity_block"


@register_type(CAVITY_BLOCK_TYPE_ID)
@dataclass
class SphericalCavityBlock(Block):
    r"""
    Spherical cavity block implementation

    .. tikz:: Spherical Cavity Scheme

        \filldraw [fill=gray!20]  (0, 0) circle [x radius = 3.0+0.2, y radius = 3.0+0.2];
        \draw [thick, dashed] (0, 0) circle [x radius = 3.0, y radius = 3.0];
        \filldraw [fill=red!25] (0, 0) circle [x radius = 3.0-0.2, y radius = 3.0-0.2];
        \filldraw [fill=gray!40] (0, 0) circle [x radius = 1.8 + 0.5, y radius = 1.8 + 0.5];
        \draw [dashed, thick] (0, 0) circle [x radius = 1.8, y radius = 1.8];
        \filldraw [fill=red!25] (0, 0) circle [x radius = 1.8 - 0.5, y radius = 1.8 - 0.5];
        \draw [thick][<->] (0, 0) -- node[above]{$R_0$} (-1.8, 0);
        \draw [thick][<->] (0, 1.8-0.5) -- node[anchor=west, yshift=4]{$d_0$} (0, 1.8+0.5);
        \draw [thick][dashed][<-] (-3.0, 0) -- node[anchor=north]{$y$} (-1.8, 0);
        \draw [thick][<->] (0, 3.0-0.2) -- node[anchor=south, yshift=5]{$d(y)$} (0, 3.0+0.2);
        \draw (3.0+0.2, 0) to[short, -*, i=$Q$]  (5, 0) node[above]{$P$};

    **Node 1:**

        :math:`Q = - \frac {dV(y)}{dt}`

    **Discretised:**

        :math:`Q^{n + \frac{1}{2}} = - \frac {V(y^{n + 1}) - V(y^{n})}{\Delta t^n}`

    .. note::

        Notice that no dynamics is given on the **DOF** in the block.
        **Model components** of the cavity can access the pressure and give it a dynamics.

    """  # noqa: E501

    disp: Quantity[np.float64]
    """Displacement y"""

    radius: Quantity[np.float64]
    """Initial Sphere radius R0"""

    thickness: Quantity[np.float64]
    """Initial thickness d0"""

    time: Time
    """time"""

    def initialize(self) -> None:
        """
        Initialize block attributes from current quantity values
        """
        self.inv_radius = 1.0 / self.radius.current
        self.sphere_volume = (4.0 / 3.0) * np.pi * np.pow(self.radius.current, 3)
        self.sphere_surface = 4.0 * np.pi * np.pow(self.radius.current, 2)
        self.thickness_radius_ratio = self.thickness.current * self.inv_radius
        self.half_thickness_radius_ratio = 0.5 * self.thickness_radius_ratio

    def fluid_volume_current(self) -> Any:
        """
        Compute the current fluid volume in the cavity.

        :return: the fluid volume
        :rtype: np.float64
        """
        disp_cur_ratio = 1.0 + self.disp.current * self.inv_radius
        return self.sphere_volume * np.pow(
            disp_cur_ratio
            - np.pow(disp_cur_ratio, -2) * self.half_thickness_radius_ratio,
            3,
        )

    def fluid_volume_new(self) -> Any:
        """
        Compute the new fluid volume in the cavity.

        :return: the fluid volume
        :rtype: np.float64
        """
        disp_new_ratio = 1.0 + self.disp.new * self.inv_radius
        return self.sphere_volume * np.pow(
            disp_new_ratio
            - np.pow(disp_new_ratio, -2) * self.half_thickness_radius_ratio,
            3,
        )

    def cavity_flux(self) -> Any:
        """
        Compute the ventricule flux at local node 1.

        :return: the flux
        :rtype: np.float64
        """

        cavity_flux = -(
            (self.fluid_volume_new() - self.fluid_volume_current()) * self.time.inv_dt
        )

        return cavity_flux

    def dcavity_flux_ddisp(self) -> Any:
        """
        Compute the partial derivative of the cavity flux for ``disp``

        :return: the flux partial derivative
        :rtype: np.float64
        """

        disp_new_ratio = 1.0 + self.disp.new * self.inv_radius

        return -(
            self.time.inv_dt
            * self.sphere_surface
            * np.pow(
                disp_new_ratio
                - np.pow(disp_new_ratio, -2) * self.half_thickness_radius_ratio,
                2,
            )
            * (1.0 + np.pow(disp_new_ratio, -3) * self.thickness_radius_ratio)
        )


# Define the cavity block flux expression.
_cavity_block_flux_expr = Expression(
    1,
    SphericalCavityBlock.cavity_flux,
    {CAVITY_DISP_LOCAL_ID: SphericalCavityBlock.dcavity_flux_ddisp},
)

SphericalCavityBlock.declares_flux_expression(
    1, CAVITY_PRESSURE_LOCAL_ID, _cavity_block_flux_expr
)


# Define the cavity block volume of fluid expression.
_cavity_block_fluid_volume_expr = Expression(
    1, SphericalCavityBlock.fluid_volume_current
)
SphericalCavityBlock.declares_saved_quantity_expression(
    CAVITY_VOLUME_LOCAL_ID, _cavity_block_fluid_volume_expr
)
