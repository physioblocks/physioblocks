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

"""Declare rheology models."""

from dataclasses import dataclass
from typing import Any

import numpy as np

from physioblocks.computing import ModelComponent, Quantity, diff, mid_point
from physioblocks.computing.models import declares_internal_equation
from physioblocks.registers import register_type
from physioblocks.simulation import Time

# Constant for the rheology model type id
RHEOLOGY_FIBER_ADDITIVE_TYPE_ID = "rheology_fiber_additive"


@register_type(RHEOLOGY_FIBER_ADDITIVE_TYPE_ID)
@dataclass
class RheologyFiberAdditiveModelComponent(ModelComponent):
    r"""Declares a Fiber Additive Rheology model implementation.

    Internal Equations
    ------------------

    .. math::

        \mu\dot{e}_c + T_c - k_s \Bigl( \frac{y}{R_0}-e_c \Bigr) = 0


    Discretization
    --------------

    .. math::

        \mu \frac{e_c^{n+1}-e_c^n}{\Delta t^n}
        - k_s \Bigl( \frac{y^{n + \frac{1}{2}}}{R_0}-e_c^{n + \frac{1}{2}} \Bigr)
        + T_c^{{n + \frac{1}{2}}\sharp} = 0

    Parameters
    ----------
    fib_deform : Quantity[np.float64]
        :math:`e_c` the fiber deformation
    disp : Quantity[np.float64]
        :math:`y` the displacement
    active_tension_discr : Quantity[np.float64]
        :math:`T_c^{{n + \frac{1}{2}}\sharp}` the active tension discretization
    radius : Quantity[np.float64]
        :math:`R_0` sphere initial radius
    damping_parallel : Quantity[np.float64]
        :math:`\mu` the damping parallel
    series_stiffness : Quantity[np.float64]
        :math:`k_s` the series stiffness
    time : Time
        :math:`t` the simulation time

    Configuration
    -------------

    .. code-block:: json

        {
            "type": "model_description",
            "model_type": "rheology_fiber_additive",
            "fib_deform": "<str>",       // Fiber deformation global name (internal
                                         // variable) (optional)
            "disp": "<str>",             // Displacement global name (optional)
            "active_tension_discr": "<str>", // Active tension discretization global
                                             // name (optional)
            "radius": "<str>",           // Sphere initial radius global name (optional)
            "damping_parallel": "<str>", // Damping parallel global name (optional)
            "series_stiffness": "<str>", // Series stiffness global name (optional)
            "time": "<str>"              // Simulation time name
        }

    Aliases
    -------

    .. _alias_rheology_fiber_additive:

    **rheology_fiber_additive**
        Aliases :class:`~.ModelComponentDescription`
        (``model_description``) with ``model_type`` set to ``rheology_fiber_additive``
        and the ``time`` quantity bound to the global ``time`` quantity.

        .. code-block:: json

            {
                "type": "rheology_fiber_additive",
                "fib_deform": "<str>",       // Fiber deformation global name (internal
                                             // variable) (optional)
                "disp": "<str>",             // Displacement global name (optional)
                "active_tension_discr": "<str>", // Active tension discretization global
                                                 // name (optional)
                "radius": "<str>",           // Sphere initial radius global name
                                             // (optional)
                "damping_parallel": "<str>", // Damping parallel global name (optional)
                "series_stiffness": "<str>"  // Series stiffness global name (optional)
            }

    """

    fib_deform: Quantity[np.float64]

    disp: Quantity[np.float64]

    active_tension_discr: Quantity[np.float64]

    radius: Quantity[np.float64]

    damping_parallel: Quantity[np.float64]

    series_stiffness: Quantity[np.float64]

    time: Time

    def initialize(self) -> None:
        """Initialize model's radius inverse."""
        self._inv_radius = 1 / self.radius.current

    @declares_internal_equation("fib_deform")
    def fib_deform_equation(self) -> Any:
        """Compute the equation representing the fiber deformation.

        Returns
        -------
        np.float64
            the relation value

        """
        disp_mid_pt = mid_point(self.disp)
        fib_deform_mid_pt = mid_point(self.fib_deform)

        return (
            self.active_tension_discr.new
            + (self.damping_parallel.current * self.time.inv_dt * diff(self.fib_deform))
            - (
                self.series_stiffness.current
                * (disp_mid_pt * self._inv_radius - fib_deform_mid_pt)
            )
        )

    @fib_deform_equation.partial_derivative("fib_deform")
    def dfib_deform_equation_dfib_deform(self) -> Any:
        """Compute the equation partial derivative for ``fib_deform``.

        Returns
        -------
        np.float64
            the partial derivative value

        """
        return (
            self.damping_parallel.current * self.time.inv_dt
            + self.series_stiffness.current * 0.5
        )

    @fib_deform_equation.partial_derivative("disp")
    def dfib_deform_equation_ddisp(self) -> np.float64:
        """Compute the equation partial derivative for ``disp``.

        Returns
        -------
        np.float64
            the partial derivative value

        """
        return -self.series_stiffness.current * self._inv_radius * 0.5

    @fib_deform_equation.partial_derivative("active_tension_discr")
    def dfib_deform_equation_dactive_tension_discr(self) -> Any:
        """Compute the equation partial derivative for the ``active_tension_discr``.

        Returns
        -------
        np.float64
            the partial derivative value

        """
        return 1.0


RHEOLOGY_FIBER_ADDITIVE_ASYMPTOTIC_TYPE_ID = (
    RHEOLOGY_FIBER_ADDITIVE_TYPE_ID + "_asymptotic"
)


@dataclass
@register_type(RHEOLOGY_FIBER_ADDITIVE_ASYMPTOTIC_TYPE_ID)
class RheologyFiberAdditiveModelComponentAsymptotic(ModelComponent):
    r"""Asymptotic description of the rheology model.

    Internal Equations
    ------------------

    .. math::

        T_c - k_s(\frac{y}{R_0} - e_c) = 0

    Parameters
    ----------
    fib_deform : Quantity[np.float64]
        :math:`e_c` the fiber deformation
    disp : Quantity[np.float64]
        :math:`y` the displacement
    active_tension_discr : Quantity[np.float64]
        :math:`T_c` the active tension
    radius : Quantity[np.float64]
        :math:`R_0` sphere initial radius
    series_stiffness : Quantity[np.float64]
        :math:`k_s` the series stiffness

    Configuration
    -------------

    .. code-block:: json

        {
            "type": "model_description",
            "model_type": "rheology_fiber_additive_asymptotic",
            "fib_deform": "<str>",       // Fiber deformation global name (internal
                                         // variable) (optional)
            "disp": "<str>",             // Displacement global name (optional)
            "active_tension_discr": "<str>", // Active tension global name (optional)
            "radius": "<str>",           // Sphere initial radius global name (optional)
            "series_stiffness": "<str>"  // Series stiffness global name (optional)
        }

    """

    fib_deform: Quantity[np.float64]

    disp: Quantity[np.float64]

    active_tension_discr: Quantity[np.float64]

    radius: Quantity[np.float64]

    series_stiffness: Quantity[np.float64]

    def initialize(self) -> None:
        """Initialize model's radius inverse."""
        self._inv_radius = 1 / self.radius.current

    @declares_internal_equation("fib_deform")
    def fib_deform_equation(self) -> Any:
        """Compute the equation representing the fiber deformation.

        Returns
        -------
        np.float64
            the relation value

        """
        return self.active_tension_discr.new - (
            self.series_stiffness.current
            * (self.disp.new * self._inv_radius - self.fib_deform.new)
        )

    @fib_deform_equation.partial_derivative("fib_deform")
    def dfib_deform_equation_dfib_deform(self) -> Any:
        """Compute the equation partial derivative for ``fib_deform``.

        Returns
        -------
        np.float64
            the partial derivative value

        """
        return self.series_stiffness.current

    @fib_deform_equation.partial_derivative("disp")
    def dfib_deform_equation_ddisp(self) -> np.float64:
        """Compute the equation partial derivative for ``disp``.

        Returns
        -------
        np.float64
            the partial derivative value

        """
        return -self.series_stiffness.current * self._inv_radius

    @fib_deform_equation.partial_derivative("active_tension_discr")
    def dfib_deform_equation_dactive_tension_discr(self) -> Any:
        """Compute the equation partial derivative for the ``active_tension_discr``.

        Returns
        -------
        np.float64
            the partial derivative value

        """
        return 1.0
