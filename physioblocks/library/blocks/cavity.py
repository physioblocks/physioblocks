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

"""Describes cavity blocks."""

from dataclasses import dataclass
from typing import Any

import numpy as np

from physioblocks.computing import Block, Quantity
from physioblocks.computing.models import declares_flux, declares_saved_quantity
from physioblocks.registers import register_type
from physioblocks.simulation import Time

# Local id for the volume saved quantity
CAVITY_VOLUME_LOCAL_ID = "volume"

# Local id for the pressure dof in the cavity
CAVITY_PRESSURE_LOCAL_ID = "pressure"

# Local id for the displacement in the cavity
CAVITY_DISP_LOCAL_ID = "disp"

# Constant for the cavity block type id
CAVITY_BLOCK_TYPE_ID = "spherical_cavity_block"


@register_type(CAVITY_BLOCK_TYPE_ID)
@dataclass
class SphericalCavityBlock(Block):
    r"""Spherical cavity block implementation.

    Scheme
    ------

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

    Fluxes
    ------

    *Node 1:*

    .. math::

        Q = - \frac {dV(y)}{dt}

    Discretization
    --------------

    .. math::

        Q^{n + \frac{1}{2}} = - \frac {V(y^{n + 1}) - V(y^{n})}{\Delta t^n}

    .. note::

        Notice that no dynamics is given on the **DOF** in the block.
        **Model components** of the cavity can access the pressure and provide its dynamic.

    Saved Quantities
    ----------------

    Fluid volume in the cavity:

    .. math::

        V(y) = \frac{4}{3} \pi R_0^3
        (1 + \frac{y}{R_0}
        - \frac{d_0}{ 2 R_0 (1 + \frac{y}{R_0})^2})^3

    Parameters
    ----------
    disp : Quantity[np.float64]
        :math:`y` the displacement
    radius : Quantity[np.float64]
        :math:`R_0` the initial sphere radius
    thickness : Quantity[np.float64]
        :math:`d_0` the initial thickness
    time : Time
        :math:`t` the time

    Configuration
    -------------

    .. code-block:: json

        {
            "type": "block_description",
            "model_type": "spherical_cavity_block",
            "flux_type": "<str>",    // Type of flux exchanged by the block
            "nodes": {"1": "<str>"}, // Net node name of the local node 1
            "disp": "<str>",         // Displacement global name (optional)
            "radius": "<str>",       // Initial sphere radius global name (optional)
            "thickness": "<str>",    // Initial thickness global name (optional)
            "time": "<str>",         // Simulation time global name (optional)
            "volume": "<str>"        // Fluid volume in the cavity global name (optional) (saved quantity)
        }

    Aliases
    -------

    .. _alias_spherical_cavity_block:

    **spherical_cavity_block**
        Aliases :class:`~.BlockDescription`
        (``block_description``) with ``model_type`` set to ``spherical_cavity_block``
        and the ``time`` quantity bound to the global ``time`` quantity.

        .. code-block:: json

            {
                "type": "spherical_cavity_block",
                "flux_type": "<str>",    // Type of flux exchanged by the block
                "nodes": {"1": "<str>"}, // Net node name of the local node 1
                "disp": "<str>",         // Displacement global name (optional)
                "radius": "<str>",       // Initial sphere radius global name (optional)
                "thickness": "<str>",    // Initial thickness global name (optional)
                "volume": "<str>"        // Fluid volume in the cavity global name (optional) (saved quantity)
            }

    """  # noqa: E501

    disp: Quantity[np.float64]

    radius: Quantity[np.float64]

    thickness: Quantity[np.float64]

    time: Time

    def initialize(self) -> None:
        """Initialize block attributes from current quantity values."""
        self.inv_radius = 1.0 / self.radius.current
        self.sphere_volume = (4.0 / 3.0) * np.pi * self.radius.current**3
        self.sphere_surface = 4.0 * np.pi * self.radius.current**2
        self.thickness_radius_ratio = self.thickness.current * self.inv_radius
        self.half_thickness_radius_ratio = 0.5 * self.thickness_radius_ratio

    @declares_saved_quantity(CAVITY_VOLUME_LOCAL_ID)
    def fluid_volume_current(self) -> Any:
        """Compute the current fluid volume in the cavity.

        Returns
        -------
        np.float64
            the fluid volume

        """
        disp_cur_ratio = 1.0 + self.disp.current * self.inv_radius
        return (
            self.sphere_volume
            * (disp_cur_ratio - disp_cur_ratio**-2 * self.half_thickness_radius_ratio)
            ** 3
        )

    def fluid_volume_new(self) -> Any:
        """Compute the new fluid volume in the cavity.

        Returns
        -------
        np.float64
            the fluid volume

        """
        disp_new_ratio = 1.0 + self.disp.new * self.inv_radius
        return (
            self.sphere_volume
            * (disp_new_ratio - disp_new_ratio**-2 * self.half_thickness_radius_ratio)
            ** 3
        )

    @declares_flux(1, CAVITY_PRESSURE_LOCAL_ID)
    def cavity_flux(self) -> Any:
        """Compute the cavity flux at local node 1.

        Returns
        -------
        np.float64
            the flux

        """
        cavity_flux = -(
            (self.fluid_volume_new() - self.fluid_volume_current()) * self.time.inv_dt
        )

        return cavity_flux

    @cavity_flux.partial_derivative(CAVITY_DISP_LOCAL_ID)
    def dcavity_flux_ddisp(self) -> Any:
        """Compute the partial derivative of the cavity flux for ``disp``.

        Returns
        -------
        np.float64
            the flux partial derivative

        """
        disp_new_ratio = 1.0 + self.disp.new * self.inv_radius

        return -(
            self.time.inv_dt
            * self.sphere_surface
            * (disp_new_ratio - disp_new_ratio**-2 * self.half_thickness_radius_ratio)
            ** 2
            * (1.0 + disp_new_ratio**-3 * self.thickness_radius_ratio)
        )


# Constant for the asymptotic description of cavity block
CAVITY_BLOCK_ASYMPTOTIC_TYPE_ID = CAVITY_BLOCK_TYPE_ID + "_asymptotic"


@dataclass
@register_type(CAVITY_BLOCK_ASYMPTOTIC_TYPE_ID)
class SphericalCavityBlockAsymptotic(Block):
    r"""Asymptotic description of the spherical cavity block.

    It is defined to use as an alternative block of the Spherical Cavity.
    It doesn't define fluxes to interact with the net, only a saved quantity
    to save the volume updated from the submodels.

    Saved Quantities
    ----------------

    Fluid volume in the cavity

    .. math::

        V(y) = \frac{4}{3} \pi R_0^3
        (1 + \frac{y}{R_0}
        - \frac{d_0}{ 2 R_0 (1 + \frac{y}{R_0})^2})^3

    Parameters
    ----------
    disp : Quantity[np.float64]
        Displacement :math:`y`
    radius : Quantity[np.float64]
        Initial sphere radius :math:`R_0`
    thickness : Quantity[np.float64]
        Initial thickness :math:`d_0`

    Configuration
    -------------

    .. code-block:: json

        {
            "type": "block_description",
            "model_type": "spherical_cavity_block_asymptotic",
            "flux_type": "<str>", // Type of flux exchanged by the block
            "disp": "<str>",      // Displacement global name (optional)
            "radius": "<str>",    // Initial sphere radius global name (optional)
            "thickness": "<str>", // Initial thickness global name (optional)
            "volume": "<str>"     // Fluid volume in the cavity global name (optional) (saved quantity)
        }

    """  # noqa: E501

    disp: Quantity[np.float64]

    radius: Quantity[np.float64]

    thickness: Quantity[np.float64]

    def initialize(self) -> None:
        """Initialize block attributes from current quantity values."""
        self.inv_radius = 1.0 / self.radius.current
        self.sphere_volume = (4.0 / 3.0) * np.pi * self.radius.current**3
        self.sphere_surface = 4.0 * np.pi * self.radius.current**2
        self.thickness_radius_ratio = self.thickness.current * self.inv_radius
        self.half_thickness_radius_ratio = 0.5 * self.thickness_radius_ratio

    @declares_saved_quantity(CAVITY_VOLUME_LOCAL_ID)
    def fluid_volume(self) -> Any:
        """Compute the current fluid volume in the cavity.

        Returns
        -------
        np.float64
            the fluid volume

        """
        disp_ratio = 1.0 + self.disp.current * self.inv_radius
        return (
            self.sphere_volume
            * (disp_ratio - disp_ratio**-2 * self.half_thickness_radius_ratio) ** 3
        )
