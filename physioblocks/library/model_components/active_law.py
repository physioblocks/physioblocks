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

from dataclasses import dataclass
from typing import Any

import numpy as np
from numpy.typing import NDArray

from physioblocks.computing import (
    Expression,
    ModelComponent,
    Quantity,
    diff,
    mid_point,
)
from physioblocks.registers import register_type
from physioblocks.simulation import Time

# Constant for the active law type id
ACTIVE_LAW_MACRO_HUXLEY_TWO_MOMENTS_TYPE_ID = "active_law_macro_huxley_two_moments"


@register_type(ACTIVE_LAW_MACRO_HUXLEY_TWO_MOMENTS_TYPE_ID)
@dataclass
class ActiveLawMacroscopicHuxleyTwoMoment(ModelComponent):
    r"""
    Describes the Macroscopic Huxley Two Moment implementation of the ative law.

    **Internal Equations:**

        .. math::

            \dot{K}_c + \bigl(|u|+\alpha|\dot{e}_c|\bigr) \, K_c - n_0(e_c) K_0 |u|_+ = 0

        .. math::

            \dot{\lambda}_c + \frac{1}{2} \bigl(|u|+\alpha|\dot{e}_c|\bigr) \, \lambda_c - \sqrt{K_c} \, \dot{e}_c - \frac{n_0(e_c)}{\sqrt{K_c}} \biggl( T_0 - \frac{K_0\,\lambda_c}{2\sqrt{K_c}} \biggr) |u|_+ = 0


        .. math::

            \lambda_c - T_c/\sqrt{K_c} = 0

    **Discretised:**

        .. math::

            \frac{K_c^{n+1}-K_c^n}{\Delta t^n} + \Bigl(|u^{n+1}|+\alpha\Bigl|\frac{e_c^{n+1}-e_c^n}{\Delta t^n}\Bigr|\Bigr) \, K_c^{n+1} - n_0(e_c^n) K_0 \, |u^{n+1}|_+ = 0

        .. math::

            \frac{\lambda_c^{n+1}-\lambda_c^n}{\Delta t^n} + \frac{1}{2}\Bigl(|u^{n+1}|+\alpha\Bigl|\frac{e_c^{n+1}-e_c^n}{\Delta t^n}\Bigr|\Bigr) \, \lambda_c^{n + \frac{1}{2}} - \sqrt{K_c^{n+1}} \, \frac{e_c^{n+1}-e_c^n}{\Delta t^n} - \frac{n_0(e_c^n)}{\sqrt{K_c^{n+1}}} \biggl( T_0 - \frac{K_0\,\lambda_c^{n + \frac{1}{2}}}{2\sqrt{K_c^{n+1}}} \biggr) |u^{n+1}|_+ = 0

        .. math::

            T_c^{n + \frac{1}{2}\sharp} - \lambda_c^{n + \frac{1}{2}} \sqrt{K_c^{n+1}} = 0
    """  # noqa: E501

    fib_deform: Quantity[np.float64]
    """:math:`e_c` the fiber deformation """

    active_stiffness: Quantity[np.float64]
    """:math:`K_c` the active stiffness"""

    active_energy_sqrt: Quantity[np.float64]
    """:math:`\\lambda_c` the active energy sqrt"""

    active_tension_discr: Quantity[np.float64]
    """:math:`T_c^{n + \\frac{1}{2}\\sharp}` the active tension discretisation"""

    starling_abscissas: Quantity[NDArray[np.float64]]
    """Abscissas of :math:`n_0` the discretized starling function"""

    starling_ordinates: Quantity[NDArray[np.float64]]
    """Ordinates of :math:`n_0` the discretize starling function"""

    activation: Quantity[np.float64]
    """:math:`u` the activation function"""

    crossbridge_stiffness: Quantity[np.float64]
    """:math:`K_0` the crossbridge stiffness"""

    contractility: Quantity[np.float64]
    """:math:`T_0` the contractility"""

    destruction_rate: Quantity[np.float64]
    """the destruction rate"""

    time: Time
    """:math:`t` the simulation time"""

    def active_law_residual(self) -> Any:
        """
        Compute the residual of the active law.

        :return: the residual value
        :rtype: np.array
        """
        starling = np.interp(
            self.fib_deform.current,
            self.starling_abscissas.current,
            self.starling_ordinates.current,
        )
        abs_plus_starling = np.clip(starling, 0.0, None)
        abs_plus_activation = np.clip(self.activation.new, 0.0, None)
        active_stiffness_dynamic_eq = (
            (self.active_stiffness.new - self.active_stiffness.current)
            * self.time.inv_dt
            + self._get_deform_rate() * self.active_stiffness.new
            - abs_plus_starling
            * self.crossbridge_stiffness.current
            * abs_plus_activation
        )
        active_energy_sqrt_dynamic_eq = (
            diff(self.active_energy_sqrt) * self.time.inv_dt
            + 0.5 * self._get_deform_rate() * mid_point(self.active_energy_sqrt)
            - (abs_plus_starling / np.sqrt(self.active_stiffness.new))
            * (
                self.contractility.current
                - (
                    0.5
                    * self.crossbridge_stiffness.current
                    * mid_point(self.active_energy_sqrt)
                    / (np.sqrt(self.active_stiffness.new))
                )
            )
            * abs_plus_activation
            - np.sqrt(self.active_stiffness.new)
            * diff(self.fib_deform)
            * self.time.inv_dt
        )

        active_tension_discr_relation = self.active_tension_discr.new - np.sqrt(
            self.active_stiffness.new
        ) * mid_point(self.active_energy_sqrt)

        return np.array(
            [
                active_stiffness_dynamic_eq,
                active_energy_sqrt_dynamic_eq,
                active_tension_discr_relation,
            ],
        )

    def active_law_residual_dactive_stiffness(self) -> Any:
        """
        Compute the residual partial derivative for the active stiffness

        :return: the partial derivative
        :rtype: np.array
        """
        starling = np.interp(
            self.fib_deform.current,
            self.starling_abscissas.current,
            self.starling_ordinates.current,
        )
        abs_plus_starling = np.clip(starling, 0.0, None)
        abs_plus_activation = np.clip(self.activation.new, 0.0, None)

        active_stiffness_active_law_dactive_stiffness = (
            self.time.inv_dt + self._get_deform_rate()
        )

        active_energy_sqrt_active_law_dactive_stiffness = (
            -abs_plus_activation
            * abs_plus_starling
            * (
                -0.5
                * self.contractility.current
                * np.pow(self.active_stiffness.new, -1.5)
                + (
                    0.5
                    * self.crossbridge_stiffness.current
                    * mid_point(self.active_energy_sqrt)
                    * np.pow(self.active_stiffness.new, -2)
                )
            )
            - 0.5
            * diff(self.fib_deform)
            * self.time.inv_dt
            / np.sqrt(self.active_stiffness.new)
        )

        active_tension_discr_relation_dactive_stiffness = (
            -0.5
            * mid_point(self.active_energy_sqrt)
            / np.sqrt(self.active_stiffness.new)
        )

        return np.array(
            [
                active_stiffness_active_law_dactive_stiffness,
                active_energy_sqrt_active_law_dactive_stiffness,
                active_tension_discr_relation_dactive_stiffness,
            ],
        )

    def active_law_residual_dactive_energy_sqrt(self) -> Any:
        """
        Compute the residual partial derivative for the active energy sqrt

        :return: the partial derivative
        :rtype: np.array
        """
        starling = np.interp(
            self.fib_deform.current,
            self.starling_abscissas.current,
            self.starling_ordinates.current,
        )
        abs_plus_starling = np.clip(starling, 0.0, None)
        abs_plus_activation = np.clip(self.activation.new, 0.0, None)

        active_stiffness_active_law_dactive_energy_sqrt = 0.0

        active_energy_sqrt_active_law_dactive_energy_sqrt = (
            self.time.inv_dt
            + 0.25
            * (
                abs(self.activation.new)
                + self.destruction_rate.current
                * (self.fib_deform.new - self.fib_deform.current)
                * self.time.inv_dt
            )
            + 0.25
            * abs_plus_activation
            * abs_plus_starling
            * self.crossbridge_stiffness.current
            / self.active_stiffness.new
        )

        active_tension_discr_relation_dactive_energy_sqrt = -0.5 * np.sqrt(
            self.active_stiffness.new
        )

        return np.array(
            [
                active_stiffness_active_law_dactive_energy_sqrt,
                active_energy_sqrt_active_law_dactive_energy_sqrt,
                active_tension_discr_relation_dactive_energy_sqrt,
            ],
        )

    def active_law_residual_dfib_deform(self) -> Any:
        """
        Compute the residual partial derivative for the fiber deformation

        :return: the partial derivative
        :rtype: np.array
        """
        active_stiffness_active_law_dfib_deform = (
            self.destruction_rate.current * self.active_stiffness.new * self.time.inv_dt
        )

        active_energy_sqrt_active_law_dfib_deform = -(
            -0.5
            * self.destruction_rate.current
            * mid_point(self.active_energy_sqrt)
            * self.time.inv_dt
            + np.sqrt(self.active_stiffness.new) * self.time.inv_dt
        )

        active_tension_discr_dfib_deform = 0.0

        return np.array(
            [
                active_stiffness_active_law_dfib_deform,
                active_energy_sqrt_active_law_dfib_deform,
                active_tension_discr_dfib_deform,
            ],
        )

    def active_law_residual_dactive_tension(self) -> Any:
        """
        Compute the residual partial derivative for the active tension

        :return: the partial derivative
        :rtype: np.array
        """
        return np.array(
            [0.0, 0.0, 1.0],
        )

    def _get_deform_rate(self) -> Any:
        return np.fabs(self.activation.new) + (
            self.destruction_rate.current
            * np.fabs(diff(self.fib_deform))
            * self.time.inv_dt
        )


# Define the expression for the residual of the ActiveLawMacroscopicHuxleyTwoMoment and
# its partial derivatives.
_active_law_macroscopic_huxley_two_moment_residual_expression = Expression(
    3,
    ActiveLawMacroscopicHuxleyTwoMoment.active_law_residual,
    {
        "active_stiffness": ActiveLawMacroscopicHuxleyTwoMoment.active_law_residual_dactive_stiffness,  # noqa: E501
        "active_energy_sqrt": ActiveLawMacroscopicHuxleyTwoMoment.active_law_residual_dactive_energy_sqrt,  # noqa: E501
        "active_tension_discr": ActiveLawMacroscopicHuxleyTwoMoment.active_law_residual_dactive_tension,  # noqa: E501
        "fib_deform": ActiveLawMacroscopicHuxleyTwoMoment.active_law_residual_dfib_deform,  # noqa: E501
    },
)

ActiveLawMacroscopicHuxleyTwoMoment.declares_internal_expression(
    "active_stiffness",
    _active_law_macroscopic_huxley_two_moment_residual_expression,
    1,
    0,
)
ActiveLawMacroscopicHuxleyTwoMoment.declares_internal_expression(
    "active_energy_sqrt",
    _active_law_macroscopic_huxley_two_moment_residual_expression,
    1,
    1,
)
ActiveLawMacroscopicHuxleyTwoMoment.declares_internal_expression(
    "active_tension_discr",
    _active_law_macroscopic_huxley_two_moment_residual_expression,
    1,
    2,
)
