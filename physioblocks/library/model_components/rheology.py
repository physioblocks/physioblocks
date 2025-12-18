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
Describes rheology models
"""

from dataclasses import dataclass
from typing import Any

import numpy as np

from physioblocks.computing import Expression, ModelComponent, Quantity, diff, mid_point
from physioblocks.registers import register_type
from physioblocks.simulation import Time

# Constant for the rheology model type id
RHEOLOGY_FIBER_ADDITIVE_TYPE_ID = "rheology_fiber_additive"


@register_type(RHEOLOGY_FIBER_ADDITIVE_TYPE_ID)
@dataclass
class RheologyFiberAdditiveModelComponent(ModelComponent):
    r"""
    Describes a Fiber Additive Rheology model implementation.

    **Internal Equation:**

    .. math::

        \dot{e}_c + T_c - k_s \Bigl( \frac{y}{R_0}-e_c \Bigr) = 0


    **Discretised:**

    .. math::

        \mu \frac{e_c^{n+1}-e_c^n}{\Delta t^n}
        - k_s \Bigl( \frac{y^{n + \frac{1}{2}}}{R_0}-e_c^{n + \frac{1}{2}} \Bigr)
        + T_c^{{n + \frac{1}{2}}\sharp} = 0

    """

    fib_deform: Quantity[np.float64]
    """:math:`e_c` the fiber deformation"""

    disp: Quantity[np.float64]
    """:math:`y` the displacement"""

    active_tension_discr: Quantity[np.float64]
    """:math:`T_c^{{n + \frac{1}{2}}\\sharp}` the active tension discretisation"""

    radius: Quantity[np.float64]
    """:math:`R_0` sphere initial radius"""

    damping_parallel: Quantity[np.float64]
    """:math:`\\mu` the damping parallel"""

    series_stiffness: Quantity[np.float64]
    """:math:`k_s` the series stiffness"""

    time: Time
    """:math:`t` the simulation time"""

    def initialize(self) -> None:
        """
        Initialize model's radius inverse
        """
        self._inv_radius = 1 / self.radius.current

    def fib_deform_equation(self) -> Any:
        """
        Compute the equation representing the fiber deformation.

        :return: the relation value
        :rtype: np.float64
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

    def dfib_deform_equation_dfib_deform(self) -> Any:
        """
        Compute the equation partial derivative for ``fib_deform``

        :return: the partial derivative value
        :rtype: np.float64
        """

        return (
            self.damping_parallel.current * self.time.inv_dt
            + self.series_stiffness.current * 0.5
        )

    def dfib_deform_equation_ddisp(self) -> np.float64:
        """
        Compute the equation partial derivative for ``disp``

        :return: the partial derivative value
        :rtype: np.float64
        """
        return -self.series_stiffness.current * self._inv_radius * 0.5

    def dfib_deform_equation_dactive_tension_discr(self) -> Any:
        """
        Compute the equation partial derivative for the ``active_tension_discr``

        :return: the partial derivative value
        :rtype: np.float64
        """
        return 1.0


# Define the expression of the equation of the model.
_fib_deform_equation_expr = Expression(
    1,
    RheologyFiberAdditiveModelComponent.fib_deform_equation,
    {
        "fib_deform": RheologyFiberAdditiveModelComponent.dfib_deform_equation_dfib_deform,  # noqa: E501
        "disp": RheologyFiberAdditiveModelComponent.dfib_deform_equation_ddisp,
        "active_tension_discr": RheologyFiberAdditiveModelComponent.dfib_deform_equation_dactive_tension_discr,  # noqa: E501
    },
)

RheologyFiberAdditiveModelComponent.declares_internal_expression(
    "fib_deform",
    _fib_deform_equation_expr,
)
