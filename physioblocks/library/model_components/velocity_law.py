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

"""Declare velocity law models."""

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from physioblocks.computing import (
    ModelComponent,
    Quantity,
    diff,
    mid_alpha,
    mid_point,
)
from physioblocks.computing.models import declares_internal_equation
from physioblocks.registers import register_type
from physioblocks.simulation import Time

# Constant for the velocity law hht type name
VELOCITY_LAW_HHT_TYPE_ID = "velocity_law_hht"


@dataclass
@register_type(VELOCITY_LAW_HHT_TYPE_ID)
class VelocityLawHHTModelComponent(ModelComponent):
    r"""Declare a velocity law HHT model.

    Implement the extended version of the **HHT time integration scheme**.

    Internal Equations
    ------------------

    .. math::

        \frac{d\dot{y}}{dt} - \ddot{y} = 0

    .. math::

        \frac{dy}{dt} - \dot{y} = 0

    Discretization
    --------------

    .. math::

        \frac{\dot{y}^{n+1}-\dot{y}^n}{\Delta t^n}
        - (\tfrac{1}{2}+\alpha)\, \ddot{y}^{n+1}
        - (\tfrac{1}{2}-\alpha)\, \ddot{y}^n = 0

    .. math::

        \frac{y^{n+1}-y^n}{\Delta t^n}
        - \dot{y}^{n + \frac{1}{2}}
        - \frac{\alpha^2}{4}\Delta t^n\, (\ddot{y}^{n+1}-\ddot{y}^n) = 0

    Parameters
    ----------
    scheme_ts_hht : Quantity[np.float64]
        :math:`\alpha` the scheme time shift
    accel : Quantity[np.float64]
        :math:`\ddot{y}` the acceleration
    vel : Quantity[np.float64]
        :math:`\dot{y}` the velocity
    disp : Quantity[np.float64]
        :math:`y` the displacement
    time : Time
        :math:`t` the time

    Configuration
    -------------

    .. code-block:: json

        {
            "type": "model_description",
            "model_type": "velocity_law_hht",
            "scheme_ts_hht": "<str>", // Scheme time shift global name (optional)
            "accel": "<str>",         // Acceleration global name (internal variable)
                                      // (optional)
            "vel": "<str>",           // Velocity global name (internal variable)
                                      // (optional)
            "disp": "<str>",          // Displacement global name (optional)
            "time": "<str>"           // Simulation time name
        }

    Aliases
    -------

    .. _alias_velocity_law_hht:

    **velocity_law_hht**
        Aliases :class:`~.ModelComponentDescription`
        (``model_description``) with ``model_type`` set to ``velocity_law_hht`` and the
        ``time`` quantity bound to the global ``time`` quantity.

        .. code-block:: json

            {
                "type": "velocity_law_hht",
                "scheme_ts_hht": "<str>", // Scheme time shift global name (optional)
                "accel": "<str>",         // Acceleration global name (internal
                                          // variable) (optional)
                "vel": "<str>",           // Velocity global name (internal variable)
                                          // (optional)
                "disp": "<str>"           // Displacement global name (optional)
            }

    """

    scheme_ts_hht: Quantity[np.float64]

    accel: Quantity[np.float64]

    vel: Quantity[np.float64]

    disp: Quantity[np.float64]

    time: Time

    @declares_internal_equation("accel", size=1, starting_index=1)
    @declares_internal_equation("vel", size=1, starting_index=0)
    def velocity_law_residual(self) -> NDArray[np.float64]:
        """Compute the velocity law residual.

        Returns
        -------
        NDArray[np.float64]
            the residual value

        """
        accel_mid_alpha = mid_alpha(self.accel, self.scheme_ts_hht.current)
        vel_mid_point = mid_point(self.vel)

        return np.array(
            [
                (self.time.inv_dt * diff(self.vel) - accel_mid_alpha),
                (
                    self.time.inv_dt * diff(self.disp)
                    - vel_mid_point
                    - self.scheme_ts_hht.current**2
                    * self.time.dt
                    / 4.0
                    * diff(self.accel)
                ),
            ],
        )

    @velocity_law_residual.partial_derivative("accel")
    def velocity_law_residual_daccel(self) -> NDArray[np.float64]:
        """Compute the velocity law residual partial derivative for ``accel``.

        Returns
        -------
        NDArray[np.float64]
            the partial derivative for accel

        """
        return np.array(
            [
                -(0.5 + self.scheme_ts_hht.current),
                -(self.scheme_ts_hht.current**2) * self.time.dt * 0.25,
            ],
        )

    @velocity_law_residual.partial_derivative("vel")
    def velocity_law_residual_dvel(self) -> NDArray[np.float64]:
        """Compute the velocity law residual partial derivative for ``vel``.

        Returns
        -------
        NDArray[np.float64]
            the partial derivative for vel

        """
        return np.array(
            [self.time.inv_dt, -0.5],
        )

    @velocity_law_residual.partial_derivative("disp")
    def velocity_law_residual_ddisp(self) -> NDArray[np.float64]:
        """Compute the velocity law residual partial derivative for ``disp``.

        Returns
        -------
        NDArray[np.float64]
            the partial derivative for disp

        """
        return np.array(
            [0.0, self.time.inv_dt],
        )
