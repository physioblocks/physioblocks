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
Module describing a discretized Velocity Law Block.

It defines two residual giving a dynamics on the velocity and acceleration.
"""

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from physioblocks.computing import (
    Expression,
    ModelComponent,
    Quantity,
    diff,
    mid_alpha,
    mid_point,
)
from physioblocks.registers import register_type
from physioblocks.simulation import Time

# Constant for the velocity law hht type name
VELOCITY_LAW_HHT_TYPE_ID = "velocity_law_hht"


@dataclass
@register_type(VELOCITY_LAW_HHT_TYPE_ID)
class VelocityLawHHTModelComponent(ModelComponent):
    r"""
    Velocity law HHT quantities and equation definitions

    Implement the extended version of the **HHT time integration scheme**.
    Velocity and acceleration unknowns are introduced and solved for by

    **Discretised Internal Equations:**

        .. math::

            \frac{\dot{y}^{n+1}-\dot{y}^n}{\Delta t^n}
            - (\tfrac{1}{2}+\alpha)\, \ddot{y}^{n+1}
            - (\tfrac{1}{2}-\alpha)\, \ddot{y}^n = 0

        .. math::

            \frac{y^{n+1}-y^n}{\Delta t^n}
            - \dot{y}^{n + \frac{1}{2}}
            - \frac{\alpha^2}{4}\Delta t^n\, (\ddot{y}^{n+1}-\ddot{y}^n) = 0
    """

    scheme_ts_hht: Quantity[np.float64]
    """:math:`\\alpha` the time shift scheme"""

    accel: Quantity[np.float64]
    """:math:`\\ddot{y}` the acceleration"""

    vel: Quantity[np.float64]
    """:math:`\\dot{y}` the velocity"""

    disp: Quantity[np.float64]
    """:math:`y` the displacement"""

    time: Time
    """:math:`t` the time"""

    def velocity_law_residual(self) -> NDArray[np.float64]:
        """
        Compute the velocity law residual

        :return: the residual value
        :rtype: NDArray[np.float64]
        """
        accel_mid_alpha = mid_alpha(self.accel, self.scheme_ts_hht.current)
        vel_mid_point = mid_point(self.vel)

        return np.array(
            [
                (self.time.inv_dt * diff(self.vel) - accel_mid_alpha),
                (
                    self.time.inv_dt * diff(self.disp)
                    - vel_mid_point
                    - np.power(self.scheme_ts_hht.current, 2)
                    * self.time.dt
                    / 4.0
                    * diff(self.accel)
                ),
            ],
        )

    def velocity_law_residual_daccel(self) -> NDArray[np.float64]:
        """
        Compute the velocity law residual partial derivative for ``accel``

        :return: the partial derivative for accel
        :rtype: NDArray[np.float64]
        """
        return np.array(
            [
                -(0.5 + self.scheme_ts_hht.current),
                -np.power(self.scheme_ts_hht.current, 2) * self.time.dt * 0.25,
            ],
        )

    def velocity_law_residual_dvel(self) -> NDArray[np.float64]:
        """
        Compute the velocity law residual partial derivative for ``vel``

        :return: the partial derivative for vel
        :rtype: NDArray[np.float64]
        """
        return np.array(
            [self.time.inv_dt, -0.5],
        )

    def velocity_law_residual_ddisp(self) -> NDArray[np.float64]:
        """
        Compute the velocity law residual partial derivative for ``disp``

        :return: the partial derivative for disp
        :rtype: NDArray[np.float64]
        """
        return np.array(
            [0.0, self.time.inv_dt],
        )


# Define the residual expression of the velocity law and its partial derivatives
_velocity_law_hht_expression = Expression(
    2,
    VelocityLawHHTModelComponent.velocity_law_residual,
    {
        "accel": VelocityLawHHTModelComponent.velocity_law_residual_daccel,
        "vel": VelocityLawHHTModelComponent.velocity_law_residual_dvel,
        "disp": VelocityLawHHTModelComponent.velocity_law_residual_ddisp,
    },
)

VelocityLawHHTModelComponent.declares_internal_expression(
    "vel", _velocity_law_hht_expression, 1, 0
)
VelocityLawHHTModelComponent.declares_internal_expression(
    "accel", _velocity_law_hht_expression, 1, 1
)
