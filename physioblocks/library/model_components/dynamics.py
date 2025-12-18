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
Describes dynamics models.
"""

from dataclasses import dataclass
from typing import Any

import numpy as np
from numpy.typing import NDArray

import physioblocks.utils.math_utils as math_utils
from physioblocks.computing import Expression, ModelComponent, Quantity, diff, mid_point
from physioblocks.computing.assembling import EqSystem
from physioblocks.registers import register_type
from physioblocks.simulation import State, Time
from physioblocks.simulation.solvers import NewtonSolver

# Constant for the spherical dynamics type id
SPHERICAL_DYNAMICS_TYPE_ID = "spherical_dynamics"

SPHERICAL_DYNAMICS_STATIC_DISP_LOCAL_ID = "disp"

_DISP_EPSILON = 1.0e-6
_STATIC_PROBLEM_TOL = 1e-6
_STATIC_PROBLEM_MAX_IT = 10
_STATIC_PROBLEM_DISP_MAG = 0.010
_STATIC_PROBLEM_MIN_PRESSURE_STEP = 1.0


@dataclass
class _SphericalDynamicsStaticModelComponent(ModelComponent):
    """
    ModelComponent containing the quantities and the expressions to solve the
    static problem in the Spherical Dynamics Model in order to initialize the
    displacement and fiber deformation.
    """

    disp: Quantity[np.float64]
    """Displacement"""

    pressure: Quantity[np.float64]
    """pressure"""

    thickness: Quantity[np.float64]
    """thickness"""

    hyperelastic_cst: Quantity[NDArray[np.float64]]
    """hyperelastic constant"""

    inv_radius: Quantity[np.float64]
    """sphere radius"""

    pressure_external: Quantity[np.float64]
    """external pressure"""

    def initialize(self) -> None:
        """
        Initialize block attributes from current quantity values
        """
        self.hyperelastic_cst_01 = (
            self.hyperelastic_cst.current[0] * self.hyperelastic_cst.current[1]
        )
        self.hyperelastic_cst_23 = (
            self.hyperelastic_cst.current[2] * self.hyperelastic_cst.current[3]
        )
        self.thickness_radius_ratio = self.thickness.current * self.inv_radius.current
        self.half_thickness_radius_ratio = 0.5 * self.thickness_radius_ratio

    def dynamics_static_residual(self) -> Any:
        """
        Compute the residual for the dynamics static problem.

        :return: the static problem residual
        :rtype: np.float64
        """
        pressure_external = mid_point(self.pressure_external)

        disp_new_ratio = 1.0 + self.disp.new * self.inv_radius.current
        fluid_volume_diff = np.pow(
            disp_new_ratio
            - np.pow(disp_new_ratio, -2) * self.half_thickness_radius_ratio,
            2,
        ) * (1.0 + np.pow(disp_new_ratio, -3) * self.thickness_radius_ratio)

        j4_new = np.pow(disp_new_ratio, 2)
        j1_new = 2.0 * j4_new + np.pow(disp_new_ratio, -4)

        j4_diff_new = 2.0 * self.inv_radius.current * (disp_new_ratio)
        j1_diff_new = 2.0 * (
            j4_diff_new - 2.0 * self.inv_radius.current * np.pow(disp_new_ratio, -5)
        )

        hyperelastic_potential_diff = 2.0 * (
            (
                self.hyperelastic_cst_01
                * j1_diff_new
                * (j1_new - 3.0)
                * np.exp(self.hyperelastic_cst.current[1] * np.pow(j1_new - 3.0, 2))
            )
            + (
                self.hyperelastic_cst_23
                * j4_diff_new
                * (j4_new - 1.0)
                * np.exp(self.hyperelastic_cst.current[3] * np.pow(j4_new - 1.0, 2))
            )
        )

        passive_stress = self.thickness.current * hyperelastic_potential_diff
        external_stress = (self.pressure.new - pressure_external) * fluid_volume_diff

        return passive_stress - external_stress

    def dynamics_static_residual_ddisp(self) -> Any:
        """
        Compute the partial derivative for disp for the the static problem residual.

        :return: the residual partial derivative for disp
        :rtype: np.float64
        """
        disp_new_ratio = 1.0 + self.disp.new * self.inv_radius.current
        pressure_external = mid_point(self.pressure_external)

        j4_new = np.pow(disp_new_ratio, 2)
        j1_new = 2.0 * j4_new + np.pow(disp_new_ratio, -4)

        j4_diff_new = 2.0 * self.inv_radius.current * (disp_new_ratio)
        j1_diff_new = 2.0 * (
            j4_diff_new - 2.0 * self.inv_radius.current * np.pow(disp_new_ratio, -5)
        )

        j1_diff_diff_new = 4.0 * np.pow(self.inv_radius.current, 2) + 20.0 * np.pow(
            self.inv_radius.current, 2
        ) * np.pow(disp_new_ratio, -6)
        j4_diff_diff_new = 2.0 * np.pow(self.inv_radius.current, 2)

        hyperelastic_potential_diff_diff = 2.0 * (
            self.hyperelastic_cst.current[0]
            * self.hyperelastic_cst.current[1]
            * (
                j1_diff_diff_new * (j1_new - 3.0)
                + np.pow(j1_diff_new, 2)
                + (
                    2.0
                    * self.hyperelastic_cst.current[1]
                    * np.pow(j1_diff_new * (j1_new - 3.0), 2)
                )
            )
            * np.exp(self.hyperelastic_cst.current[1] * np.pow(j1_new - 3.0, 2))
            + self.hyperelastic_cst.current[2]
            * self.hyperelastic_cst.current[3]
            * (
                j4_diff_diff_new * (j4_new - 1.0)
                + np.pow(j4_diff_new, 2)
                + (
                    2.0
                    * self.hyperelastic_cst.current[3]
                    * np.pow(j4_diff_new * (j4_new - 1.0), 2)
                )
            )
            * np.exp(self.hyperelastic_cst.current[3] * np.pow(j4_new - 1.0, 2))
        )

        passive_stress_diff = self.thickness.current * hyperelastic_potential_diff_diff

        fluid_volume_diff_diff = self.inv_radius.current * (
            2.0
            * (
                1.0
                + self.disp.new * self.inv_radius.current
                - np.pow(disp_new_ratio, -2) * self.half_thickness_radius_ratio
            )
            * np.pow(1.0 + np.pow(disp_new_ratio, -3) * self.thickness_radius_ratio, 2)
            - 3.0
            * self.thickness_radius_ratio
            * np.pow(disp_new_ratio, -4)
            * np.pow(
                1.0
                + self.disp.new * self.inv_radius.current
                - np.pow(disp_new_ratio, -2) * self.half_thickness_radius_ratio,
                2,
            )
        )

        ext_stress_diff = (
            self.pressure.new - pressure_external
        ) * fluid_volume_diff_diff

        return passive_stress_diff - ext_stress_diff


_spherical_dynamics_static_residual_expr = Expression(
    1,
    _SphericalDynamicsStaticModelComponent.dynamics_static_residual,
    {
        SPHERICAL_DYNAMICS_STATIC_DISP_LOCAL_ID: _SphericalDynamicsStaticModelComponent.dynamics_static_residual_ddisp  # noqa: E501
    },
)

_SphericalDynamicsStaticModelComponent.declares_internal_expression(
    SPHERICAL_DYNAMICS_STATIC_DISP_LOCAL_ID, _spherical_dynamics_static_residual_expr
)


@dataclass
@register_type(SPHERICAL_DYNAMICS_TYPE_ID)
class SphericalDynamicsModelComponent(ModelComponent):
    r"""
    Implementation of the spherical dynamics model.

    It provides a dynamics on :math:`y` the displacement of a sphere radius.

    **Internal Equation:**

        .. math::

            \frac{P - P_{ext}}{|\Omega_0|} \frac{\partial V(y)}{\partial y}
            - \rho_0 \ddot{y}
            - \frac{\partial W_e(y)}{\partial y}
            - \frac{1}{R_0} \Sigma_v(y,\dot{y})
            - \frac{k_s}{R_0} \Bigl( \frac{y}{R_0}-e_c \Bigr) = 0

    With:

        * :math:`W_e(y)` represents an elastic energy per unit volume given by

            .. math::

                W_e(y) =
                C_0 \exp \Bigl[ C_1 \bigl(2C(y)+C(y)^{-2}-3\bigr)^2 \Bigr]
                + C_2 \exp \Bigl[ C_3 \bigl(C(y)-1\bigr)^2 \Bigr]

            where :math:`(C_0,C_1,C_2,C_3)` denote material parameters of the passive
            constitutive law, and :math:`C(y)= (1+y/R_0)^2` represents the component
            of the right Cauchy-Green deformation tensor along the fiber direction

        * :math:`\Sigma_v(y,\dot{y})` denotes a viscous stress defined by

            .. math::

                \Sigma_v(y,\dot{y}) =
                2 \eta \, \bigl( C(y) + 2 C(y)^{-5} \bigr) \frac{\dot{y}}{R_0}

            with :math:`\eta` a solid viscosity parameter

        * :math:`k_s` denotes a passive elastic modulus

        * :math:`|\Omega_0|` is the total volume of sphere tissue in the reference
          configuration

            .. math::

                |\Omega_0| =
                \frac{4}{3}\pi \Biggl[ \Bigl( R_0+\frac{d_0}{2} \Bigr)^3
                - \Bigl( R_0-\frac{d_0}{2} \Bigr)^3 \Biggr]

            with :math:`d_0` the wall thickness in the reference configuration, and
            factorizing :math:`R_0` from the bracket a Taylor expansion readily gives
            the following approximation that we use in the implementation up to the
            third order in :math:`d_0/2R_0`:

            .. math::

                |\Omega_0| = 4\pi R_0^2 d_0

        * :math:`V(y)` denotes the volume of the sphere, i.e.

            .. math::

                V(y) = \frac{4}{3}\pi \Bigl( R(y)-\frac{d(y)}{2} \Bigr)^3
                = \frac{4}{3}\pi \Bigl( R_0+y-\frac{d_0}{2}C(y)^{-1} \Bigr)^3,

            with :math:`d(y)` the wall thickness in the deformed configuration.

    **Discretised:**

        .. math::

            \frac{P^{n + \frac{1}{2}}
            - P_{ext}^{n + \frac{1}{2}}}{|\Omega_0|} DV^{{n + \frac{1}{2}}\sharp}
            - \rho_0 \Bigl[ \frac{\dot{y}^{n+1}-\dot{y}^n}{\Delta t^n} \Bigr]
            - DW^{{n + \frac{1}{2}}\sharp}
            - \frac{1}{R_0} \Sigma_v(y^{n + \frac{1}{2}},\dot{y}^{n + \frac{1}{2}})
            - \frac{k_s}{R_0} \Bigl(
              \frac{y^{n + \frac{1}{2}}}{R_0}-e_c^{n + \frac{1}{2}} \Bigr) = 0
    """

    disp: Quantity[np.float64]
    """:math:`y` the displacement along the radius."""

    fib_deform: Quantity[np.float64]
    """:math:`e_c` the sphere fiber deformation"""

    pressure: Quantity[np.float64]
    """:math:`P` the pressure in the sphere"""

    pressure_external: Quantity[np.float64]
    """:math:`P_{ext}` the pressure outside the sphere"""

    vel: Quantity[np.float64]
    """:math:`\\dot{y}` the displacement velocity"""

    radius: Quantity[np.float64]
    """:math:`R_0` the initial sphere radius"""

    vol_mass: Quantity[np.float64]
    """:math:`\\rho_0` the volumic mass of the sphere tissu"""

    thickness: Quantity[np.float64]
    """:math:`d_0` the initial thickness of the sphere"""

    damping_coef: Quantity[np.float64]
    """Damping coeff for the viscous coeff :math:`\\eta`"""

    series_stiffness: Quantity[np.float64]
    """:math:`k_s` the series stiffness"""

    hyperelastic_cst: Quantity[NDArray[np.float64]]
    """:math:`(C_0,C_1,C_2,C_3)` the hyperelastic constants"""

    time: Time
    """Simulation time"""

    def initialize(self) -> None:
        """
        Compute initial block quantities (sphere radius, surface, volume, ...) and solve
        the associated static problem to get initial displacement and fiber deformation.
        """
        self.inv_radius = 1.0 / self.radius.current
        self.sphere_surface = 4.0 * np.pi * np.power(self.radius.current, 2)
        self.sphere_volume = 4.0 / 3.0 * np.pi * np.power(self.radius.current, 3)
        self.thickness_radius_ratio = self.thickness.current * self.inv_radius
        self.half_thickness_radius_ratio = 0.5 * self.thickness_radius_ratio
        self.viscous_coef = (
            2.0
            * self.damping_coef.current
            * self.thickness.current
            * np.pow(self.inv_radius, 2)
        )
        self.hyperelastic_cst_01 = (
            self.hyperelastic_cst.current[0] * self.hyperelastic_cst.current[1]
        )
        self.hyperelastic_cst_23 = (
            self.hyperelastic_cst.current[2] * self.hyperelastic_cst.current[3]
        )

        disp_init, fib_deform_init = self._solve_static_problem()

        self.disp.initialize(disp_init)
        self.fib_deform.initialize(fib_deform_init)

    def dynamics_residual(self) -> Any:
        """
        Compute the residual giving a dynamics on `disp`

        :return: the residual
        :rtype: np.float64
        """

        disp_mid = mid_point(self.disp)
        fib_deform_mid = mid_point(self.fib_deform)
        p_mid_point = mid_point(self.pressure)
        pressure_external = mid_point(self.pressure_external)

        disp_diff = diff(self.disp)

        disp_mid_ratio = 1.0 + disp_mid * self.inv_radius
        disp_new_ratio = 1.0 + self.disp.new * self.inv_radius
        disp_cur_ratio = 1.0 + self.disp.current * self.inv_radius

        j4_mid = np.pow(disp_mid_ratio, 2)
        j4_diff_mid = 2.0 * self.inv_radius * disp_mid_ratio

        j1_mid = 2.0 * j4_mid + np.pow(disp_mid_ratio, -4)

        # inertia stress
        inertia_stress = (
            self.vol_mass.current
            * self.thickness.current
            * diff(self.vel)
            * self.time.inv_dt
        )

        # viscous stress
        viscous_diff_vel = (
            self.viscous_coef * j4_mid * (1.0 + 2.0 * np.pow(disp_mid_ratio, -12))
        )
        viscous_stress = viscous_diff_vel * disp_diff * self.time.inv_dt

        # active stress
        active_stress = (
            self.thickness_radius_ratio
            * self.series_stiffness.current
            * (disp_mid * self.inv_radius - fib_deform_mid)
        )
        if np.abs(disp_diff / self.disp.current) > _DISP_EPSILON:
            disp_diff_ratio = disp_diff * self.inv_radius

            # external stress
            fluid_volume_cur = (
                disp_cur_ratio
                - np.pow(disp_cur_ratio, -2) * self.half_thickness_radius_ratio
            )
            fluid_volume_new = (
                disp_new_ratio
                - np.pow(disp_new_ratio, -2) * self.half_thickness_radius_ratio
            )
            fluid_volume_diff3 = (
                disp_diff_ratio
                - math_utils.power_diff(
                    disp_new_ratio, disp_cur_ratio, disp_diff_ratio, -2
                )
                * self.half_thickness_radius_ratio
            )
            fluid_volume_diff = self.sphere_volume * math_utils.power_diff(
                fluid_volume_new, fluid_volume_cur, fluid_volume_diff3, 3
            )

            external_stress = (
                (p_mid_point - pressure_external)
                * fluid_volume_diff
                / (self.sphere_surface * disp_diff)
            )

            # passive stress
            j4_new = np.pow(disp_new_ratio, 2)
            j4_cur = np.pow(disp_cur_ratio, 2)

            j4_diff = math_utils.power_diff(
                disp_new_ratio, disp_cur_ratio, disp_diff_ratio, 2
            )

            j1_new = 2.0 * j4_new + np.pow(disp_new_ratio, -4)
            j1_cur = 2.0 * j4_cur + np.pow(disp_cur_ratio, -4)
            j1_diff = 2.0 * j4_diff + math_utils.power_diff(
                disp_new_ratio, disp_cur_ratio, disp_diff_ratio, -4
            )

            arg_exp_j1_new = self.hyperelastic_cst.current[1] * np.pow(j1_new - 3.0, 2)
            arg_exp_j1_cur = self.hyperelastic_cst.current[1] * np.pow(j1_cur - 3.0, 2)
            arg_exp_j1_diff = self.hyperelastic_cst.current[1] * math_utils.power_diff(
                j1_new - 3.0, j1_cur - 3.0, j1_diff, 2
            )

            arg_exp_j4_new = self.hyperelastic_cst.current[3] * np.pow(j4_new - 1.0, 2)
            arg_exp_j4_cur = self.hyperelastic_cst.current[3] * np.pow(j4_cur - 1.0, 2)
            arg_exp_j4_diff = self.hyperelastic_cst.current[3] * math_utils.power_diff(
                j4_new - 1.0, j4_cur - 1.0, j4_diff, 2
            )

            exp_j1_diff = math_utils.exp_diff(
                arg_exp_j1_new, arg_exp_j1_cur, arg_exp_j1_diff
            )
            exp_j4_diff = math_utils.exp_diff(
                arg_exp_j4_new, arg_exp_j4_cur, arg_exp_j4_diff
            )

            hyperelastic_potential_diff = (
                self.hyperelastic_cst.current[0] * exp_j1_diff
                + self.hyperelastic_cst.current[2] * exp_j4_diff
            )

            passive_stress = (
                self.thickness.current * hyperelastic_potential_diff / disp_diff
            )

        else:
            # external stress
            disp_mid_ratio_adj = np.pow(
                disp_mid_ratio
                - np.pow(disp_mid_ratio, -2) * self.half_thickness_radius_ratio,
                2,
            )
            external_stress = (
                (p_mid_point - pressure_external)
                * disp_mid_ratio_adj
                * (1.0 + np.pow(disp_mid_ratio, -3) * self.thickness_radius_ratio)
            )

            # passive stress
            exp_j1_mid = np.exp(
                self.hyperelastic_cst.current[1] * np.pow(j1_mid - 3.0, 2)
            )
            exp_j4_mid = np.exp(
                self.hyperelastic_cst.current[3] * np.pow(j4_mid - 1.0, 2)
            )

            j1_diff_mid = 2.0 * j4_diff_mid - 4.0 * self.inv_radius * np.pow(
                disp_mid_ratio, -5
            )

            hyperelastic_potential_diff_mid = (
                2.0
                * self.hyperelastic_cst_01
                * j1_diff_mid
                * (j1_mid - 3.0)
                * exp_j1_mid
            ) + (
                2.0
                * self.hyperelastic_cst_23
                * j4_diff_mid
                * (j4_mid - 1.0)
                * exp_j4_mid
            )

            passive_stress = self.thickness.current * hyperelastic_potential_diff_mid

        return (
            inertia_stress
            + passive_stress
            + viscous_stress
            + active_stress
            - external_stress
        )

    def dynamics_residual_ddisp(self) -> Any:
        """
        Compute the partial derivative of the residual for `disp`.

        :return: the residual partial derivative for `disp`
        :rtype: np.float64
        """

        disp_mid = mid_point(self.disp)
        disp_diff = diff(self.disp)
        disp_mid_ratio = 1.0 + disp_mid * self.inv_radius
        disp_cur_ratio = 1.0 + self.disp.current * self.inv_radius
        disp_new_ratio = 1.0 + self.disp.new * self.inv_radius
        pressure_external = mid_point(self.pressure_external)

        p_mid_point = mid_point(self.pressure)

        j4_mid = np.pow(disp_mid_ratio, 2)
        j4_diff_mid = 2.0 * self.inv_radius * (disp_mid_ratio)
        j1_mid = 2.0 * j4_mid + np.pow(disp_mid_ratio, -4)

        # viscous
        viscous_diff_vel = (
            self.viscous_coef * j4_mid * (1.0 + 2.0 * np.pow(disp_mid_ratio, -12))
        )
        viscous_potential_diff_disp_mid = (
            self.viscous_coef
            * disp_diff
            * self.time.inv_dt
            * (
                j4_diff_mid * (1.0 + 2.0 * np.pow(disp_mid_ratio, -12))
                - 24.0 * self.inv_radius * j4_mid * np.pow(disp_mid_ratio, -13)
            )
        )
        viscous_ddisp = (
            0.5 * viscous_potential_diff_disp_mid + self.time.inv_dt * viscous_diff_vel
        )

        # active
        active_ddisp = (
            self.half_thickness_radius_ratio
            * self.series_stiffness.current
            * self.inv_radius
        )

        if np.fabs(disp_diff / self.disp.current) > _DISP_EPSILON:
            # external
            disp_diff_ratio = disp_diff * self.inv_radius
            fluid_volume_term_cur = (
                disp_cur_ratio
                - np.pow(disp_cur_ratio, -2) * self.half_thickness_radius_ratio
            )
            fluid_volume_term_new = (
                disp_new_ratio
                - np.pow(disp_new_ratio, -2) * self.half_thickness_radius_ratio
            )
            fluid_volume_term_diff3 = (
                disp_diff_ratio
                - math_utils.power_diff(
                    disp_new_ratio, disp_cur_ratio, disp_diff_ratio, -2
                )
                * self.half_thickness_radius_ratio
            )
            fluid_volume_diff = self.sphere_volume * math_utils.power_diff(
                fluid_volume_term_new, fluid_volume_term_cur, fluid_volume_term_diff3, 3
            )

            fluid_volume_diff_new = (
                self.sphere_surface
                * np.pow(
                    disp_new_ratio
                    - np.pow(disp_new_ratio, -2) * self.half_thickness_radius_ratio,
                    2,
                )
                * (1.0 + np.pow(disp_new_ratio, -3) * self.thickness_radius_ratio)
            )

            fluid_volume_diff_scheme_diff = (
                (1.0 / self.sphere_surface)
                * (fluid_volume_diff_new * disp_diff - fluid_volume_diff)
                * np.pow(disp_diff, -2)
            )

            external_ddisp = (
                p_mid_point - pressure_external
            ) * fluid_volume_diff_scheme_diff

            # passive
            j4_cur = np.pow(disp_cur_ratio, 2)
            j4_new = np.pow(disp_new_ratio, 2)
            j4_diff_new = 2.0 * self.inv_radius * disp_new_ratio
            j4_diff = math_utils.power_diff(
                disp_new_ratio, disp_cur_ratio, disp_diff_ratio, 2
            )

            j1_new = 2.0 * j4_new + np.pow(disp_new_ratio, -4)
            j1_cur = 2.0 * j4_cur + np.pow(disp_cur_ratio, -4)
            j1_diff_new = 2.0 * j4_diff_new - 4.0 * self.inv_radius * np.pow(
                disp_new_ratio, -5
            )
            j1_diff = 2.0 * j4_diff + math_utils.power_diff(
                disp_new_ratio, disp_cur_ratio, disp_diff_ratio, -4
            )

            arg_exp_j1_cur = self.hyperelastic_cst.current[1] * np.pow(j1_cur - 3.0, 2)
            arg_exp_j1_new = self.hyperelastic_cst.current[1] * np.pow(j1_new - 3.0, 2)
            arg_exp_j1_diff = self.hyperelastic_cst.current[1] * math_utils.power_diff(
                j1_new - 3.0, j1_cur - 3.0, j1_diff, 2
            )
            exp_j1_new = np.exp(arg_exp_j1_new)

            arg_exp_j4_cur = self.hyperelastic_cst.current[3] * np.pow(j4_cur - 1.0, 2)
            arg_exp_j4_new = self.hyperelastic_cst.current[3] * np.pow(j4_new - 1.0, 2)
            arg_exp_j4_diff = self.hyperelastic_cst.current[3] * math_utils.power_diff(
                j4_new - 1.0, j4_cur - 1.0, j4_diff, 2
            )
            exp_j4_new = np.exp(arg_exp_j4_new)

            exp_j4_diff = math_utils.exp_diff(
                arg_exp_j4_new, arg_exp_j4_cur, arg_exp_j4_diff
            )
            exp_j1_diff = math_utils.exp_diff(
                arg_exp_j1_new, arg_exp_j1_cur, arg_exp_j1_diff
            )

            hyperelastic_potential_diff = (
                self.hyperelastic_cst.current[0] * exp_j1_diff
                + self.hyperelastic_cst.current[2] * exp_j4_diff
            )
            hyperelastic_potential_diff_new = (
                2.0
                * self.hyperelastic_cst_01
                * j1_diff_new
                * (j1_new - 3.0)
                * exp_j1_new
            ) + (
                2.0
                * self.hyperelastic_cst_23
                * j4_diff_new
                * (j4_new - 1.0)
                * exp_j4_new
            )
            passive_ddisp = (
                self.thickness.current
                * (
                    hyperelastic_potential_diff_new * disp_diff
                    - hyperelastic_potential_diff
                )
                / np.pow(disp_diff, 2)
            )

        else:
            # external
            disp_mid_ratio_adj = np.pow(
                disp_mid_ratio
                - np.pow(disp_mid_ratio, -2) * self.half_thickness_radius_ratio,
                2,
            )
            fluid_volume_diff_diff_mid = (
                4.0
                * np.pi
                * self.radius.current
                * (
                    2.0
                    * (
                        disp_mid_ratio
                        - np.pow(disp_mid_ratio, -2) * self.half_thickness_radius_ratio
                    )
                    * np.pow(
                        1.0 + np.pow(disp_mid_ratio, -3) * self.thickness_radius_ratio,
                        2,
                    )
                    - (
                        3.0
                        * self.thickness_radius_ratio
                        * np.pow(disp_mid_ratio, -4)
                        * disp_mid_ratio_adj
                    )
                )
            )
            fluid_volume_diff_scheme_diff = (
                1.0 / self.sphere_surface * 0.5 * fluid_volume_diff_diff_mid
            )
            external_ddisp = (
                p_mid_point - pressure_external
            ) * fluid_volume_diff_scheme_diff

            # passive
            exp_j1_mid = np.exp(
                self.hyperelastic_cst.current[1] * np.pow(j1_mid - 3.0, 2)
            )
            exp_j4_mid = np.exp(
                self.hyperelastic_cst.current[3] * np.pow(j4_mid - 1.0, 2)
            )
            j1_diff_mid = 2.0 * j4_diff_mid - 4.0 * self.inv_radius * np.pow(
                disp_mid_ratio, -5
            )
            j4_diff_diff = 2.0 * np.pow(self.inv_radius, 2)
            j1_diff_diff_mid = 4.0 * np.pow(self.inv_radius, 2) + 20.0 * np.pow(
                self.inv_radius, 2
            ) * np.pow(disp_mid_ratio, -6)
            hyperelastic_potential_diff_diff_mid = (
                2.0
                * self.hyperelastic_cst_01
                * (
                    j1_diff_diff_mid * (j1_mid - 3.0)
                    + np.pow(j1_diff_mid, 2)
                    + 2.0
                    * self.hyperelastic_cst.current[1]
                    * np.pow(j1_diff_mid * (j1_mid - 3.0), 2)
                )
                * exp_j1_mid
                + 2.0
                * self.hyperelastic_cst_23
                * (
                    j4_diff_diff * (j4_mid - 1.0)
                    + np.pow(j4_diff_mid, 2)
                    + 2.0
                    * self.hyperelastic_cst.current[3]
                    * np.pow(j4_diff_mid * (j4_mid - 1.0), 2)
                )
                * exp_j4_mid
            )
            passive_ddisp = (
                self.thickness.current * 0.5 * hyperelastic_potential_diff_diff_mid
            )

        return viscous_ddisp + active_ddisp - external_ddisp + passive_ddisp

    def dynamics_residual_dfib_deform(self) -> Any:
        """

        Compute the partial derivative of the residual for `fib_deform`.

        :return: the residual partial derivative for `fib_deform`
        :rtype: np.float64
        """
        # activ stress
        return -self.half_thickness_radius_ratio * self.series_stiffness.current

    def dynamics_residual_dvel(self) -> Any:
        """
        Compute the partial derivative of the residual for `vel`.

        :return: the residual partial derivative for `vel`
        :rtype: np.float64
        """
        # inertia
        return self.vol_mass.current * self.thickness.current * self.time.inv_dt

    def dynamics_residual_dpressure(self) -> Any:
        """
        Compute the partial derivative of the residual for the `pressure`.

        :return: the residual partial derivative for `pressure`
        :rtype: np.float64
        """

        # external
        disp_diff = diff(self.disp)
        disp_mid = mid_point(self.disp)
        disp_mid_ratio = 1.0 + disp_mid * self.inv_radius
        disp_new_ratio = 1.0 + self.disp.new * self.inv_radius
        disp_cur_ratio = 1.0 + self.disp.current * self.inv_radius

        if np.fabs(disp_diff / self.disp.current) > _DISP_EPSILON:
            disp_diff_ratio = disp_diff * self.inv_radius
            fluid_volume_term_cur = (
                disp_cur_ratio
                - np.pow(disp_cur_ratio, -2) * self.half_thickness_radius_ratio
            )
            fluid_volume_term_new = (
                disp_new_ratio
                - np.pow(disp_new_ratio, -2) * self.half_thickness_radius_ratio
            )

            fluid_volume_term_diff3 = (
                disp_diff_ratio
                - math_utils.power_diff(
                    disp_new_ratio, disp_cur_ratio, disp_diff_ratio, -2
                )
                * self.half_thickness_radius_ratio
            )

            fluid_volume_diff = self.sphere_volume * math_utils.power_diff(
                fluid_volume_term_new, fluid_volume_term_cur, fluid_volume_term_diff3, 3
            )
            external_dpressure = -(
                (0.5 * fluid_volume_diff) / (self.sphere_surface * disp_diff)
            )
        else:
            disp_mid_ratio_adj = np.pow(
                disp_mid_ratio
                - np.pow(disp_mid_ratio, -2) * self.half_thickness_radius_ratio,
                2,
            )
            external_dpressure = (
                -0.5
                * disp_mid_ratio_adj
                * (1.0 + np.pow(disp_mid_ratio, -3) * self.thickness_radius_ratio)
            )

        return external_dpressure

    def dynamics_residual_dpressure_external(self) -> Any:
        """
        Compute the partial derivative of the residual `pressure_external`.

        :return: the residual partial derivative `pressure_external`.
        :rtype: np.float64
        """

        disp_diff = diff(self.disp)

        if np.abs(disp_diff / self.disp.current) > _DISP_EPSILON:
            disp_diff_ratio = disp_diff * self.inv_radius
            disp_new_ratio = 1.0 + self.disp.new * self.inv_radius
            disp_cur_ratio = 1.0 + self.disp.current * self.inv_radius

            fluid_volume_cur = (
                disp_cur_ratio
                - np.pow(disp_cur_ratio, -2) * self.half_thickness_radius_ratio
            )
            fluid_volume_new = (
                disp_new_ratio
                - np.pow(disp_new_ratio, -2) * self.half_thickness_radius_ratio
            )
            fluid_volume_diff3 = (
                disp_diff_ratio
                - math_utils.power_diff(
                    disp_new_ratio, disp_cur_ratio, disp_diff_ratio, -2
                )
                * self.half_thickness_radius_ratio
            )
            fluid_volume_diff = self.sphere_volume * math_utils.power_diff(
                fluid_volume_new, fluid_volume_cur, fluid_volume_diff3, 3
            )

            dresidual_dpressure_external = (
                0.5 * fluid_volume_diff / (self.sphere_surface * disp_diff)
            )

        else:
            disp_mid = mid_point(self.disp)
            disp_mid_ratio = 1.0 + disp_mid * self.inv_radius

            disp_mid_ratio_adj = np.pow(
                disp_mid_ratio
                - np.pow(disp_mid_ratio, -2) * self.half_thickness_radius_ratio,
                2,
            )

            dresidual_dpressure_external = (
                0.5
                * disp_mid_ratio_adj
                * (1.0 + np.pow(disp_mid_ratio, -3) * self.thickness_radius_ratio)
            )

        return dresidual_dpressure_external

    def _solve_static_problem(self) -> tuple[np.float64, np.float64]:
        eq_system = EqSystem(1)

        state = State()
        state.add_variable(SPHERICAL_DYNAMICS_STATIC_DISP_LOCAL_ID, 1)
        state[SPHERICAL_DYNAMICS_STATIC_DISP_LOCAL_ID].initialize(self.disp.current)

        static_block = _SphericalDynamicsStaticModelComponent(
            disp=state[SPHERICAL_DYNAMICS_STATIC_DISP_LOCAL_ID],
            pressure=Quantity(self.pressure.current),
            thickness=Quantity(self.thickness.current),
            hyperelastic_cst=Quantity(self.hyperelastic_cst.current),
            inv_radius=Quantity(self.inv_radius),
            pressure_external=Quantity(self.pressure_external.current),
        )
        static_block.initialize()
        static_expression = (
            _SphericalDynamicsStaticModelComponent.get_internal_variable_expression(
                SPHERICAL_DYNAMICS_STATIC_DISP_LOCAL_ID
            )[0]
        )
        eq_system.add_system_part(
            0,
            static_expression.size,
            static_expression.expr_func,
            {
                0: static_expression.expr_gradients[
                    SPHERICAL_DYNAMICS_STATIC_DISP_LOCAL_ID
                ]
            },
            static_block,
        )

        solver = NewtonSolver(
            _STATIC_PROBLEM_TOL,
            _STATIC_PROBLEM_MAX_IT,
        )
        p_test = static_block.pressure.current
        p_step = p_test

        while (
            p_test <= static_block.pressure.current
            and p_test > _STATIC_PROBLEM_MIN_PRESSURE_STEP
        ):
            sol = solver.solve(
                state,
                eq_system,
                {SPHERICAL_DYNAMICS_STATIC_DISP_LOCAL_ID: _STATIC_PROBLEM_DISP_MAG},
            )

            if sol.converged is True:
                state[SPHERICAL_DYNAMICS_STATIC_DISP_LOCAL_ID].initialize(sol.x[0])

                if np.abs(p_test - static_block.pressure.current) < _STATIC_PROBLEM_TOL:
                    break  # disp and fib deform initialized

                p_test = np.min([p_test + p_step, static_block.pressure.current])
                static_block.pressure.update(p_test)

            else:
                # solver did not converged, update pressure
                state.reset_state_vector()
                p_step = p_step * 0.5
                p_test = p_test - p_step
                static_block.pressure.update(p_test)

        disp_init = state[SPHERICAL_DYNAMICS_STATIC_DISP_LOCAL_ID].current
        return disp_init, disp_init * self.inv_radius


# Define the dynamics residual expression and its partial derivatives.
_spherical_dynamics_residual_expr = Expression(
    1,
    SphericalDynamicsModelComponent.dynamics_residual,
    {
        "fib_deform": SphericalDynamicsModelComponent.dynamics_residual_dfib_deform,
        "disp": SphericalDynamicsModelComponent.dynamics_residual_ddisp,
        "vel": SphericalDynamicsModelComponent.dynamics_residual_dvel,
        "pressure": SphericalDynamicsModelComponent.dynamics_residual_dpressure,
        "pressure_external": SphericalDynamicsModelComponent.dynamics_residual_dpressure_external,  # noqa: E501
    },
)

SphericalDynamicsModelComponent.declares_internal_expression(
    "disp", _spherical_dynamics_residual_expr
)
