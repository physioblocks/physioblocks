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

"""Describes dynamics models."""

from dataclasses import dataclass
from typing import Any, TypeVar

import numpy as np
from numpy.typing import NDArray

from physioblocks.computing import ModelComponent, Quantity, diff, mid_point
from physioblocks.computing.assembling import EqSystem
from physioblocks.computing.models import (
    declares_internal_equation,
    declares_saved_quantity,
)
from physioblocks.computing.quantities import QuantitiesRegistry
from physioblocks.registers import register_type
from physioblocks.simulation import Time
from physioblocks.simulation.solvers import NewtonSolver

# Constant for the spherical dynamics type id
SPHERICAL_DYNAMICS_TYPE_ID = "spherical_dynamics"

SPHERICAL_DYNAMICS_STATIC_DISP_LOCAL_ID = "disp"
SPHERICAL_DYNAMICS_STATIC_FIB_DEFORM_LOCAL_ID = "fib_deform"
SPHERICAL_DYNAMICS_STATIC_PRESSURE_LOCAL_ID = "pressure"
SPHERICAL_DYNAMICS_STATIC_PRESSURE_EXTERNAL_LOCAL_ID = "pressure_external"

_DISP_EPSILON = 1.0e-6
_STATIC_PROBLEM_TOL = 1e-6
_STATIC_PROBLEM_MAX_IT = 10
_STATIC_PROBLEM_DISP_MAG = 0.010
_STATIC_PROBLEM_MIN_PRESSURE_STEP = 1.0


@dataclass
@register_type(SPHERICAL_DYNAMICS_TYPE_ID)
class SphericalDynamicsModelComponent(ModelComponent):
    r"""Implementation of the spherical dynamics model.

    It provides a dynamics on :math:`y` the displacement of a sphere radius.

    Internal Equations
    ------------------

    .. math::

        \frac{P - P_{ext}}{|\Omega_0|} \frac{\partial V(y)}{\partial y}
        - \rho_0 \ddot{y}
        - \frac{\partial W_e(y)}{\partial y}
        - \frac{1}{R_0} \Sigma_v(y,\dot{y})
        - \frac{k_s}{R_0} \Bigl( \frac{y}{R_0}-e_c \Bigr) = 0

    With:

    * :math:`W_e(y)` represents an elastic energy per unit volume given by:

      :math:`W_e(y) =
      C_0 \exp \Bigl[ C_1 \bigl(2C(y)+C(y)^{-2}-3\bigr)^2 \Bigr]
      + C_2 \exp \Bigl[ C_3 \bigl(C(y)-1\bigr)^2 \Bigr]`

      where :math:`(C_0,C_1,C_2,C_3)` denote material parameters of the passive
      constitutive law, and :math:`C(y)= (1+y/R_0)^2` represents the component
      of the right Cauchy-Green deformation tensor along the fiber direction

    * :math:`\Sigma_v(y,\dot{y})` denotes a viscous stress defined by:

      :math:`\Sigma_v(y,\dot{y}) =
      2 \eta \, \bigl( C(y) + 2 C(y)^{-5} \bigr) \frac{\dot{y}}{R_0}`

      with :math:`\eta` a solid viscosity parameter

    * :math:`k_s` denotes a passive elastic modulus

    * :math:`|\Omega_0|` is the total volume of sphere tissue in the reference
      configuration:

      :math:`|\Omega_0| =
      \frac{4}{3}\pi \Biggl[ \Bigl( R_0+\frac{d_0}{2} \Bigr)^3
      - \Bigl( R_0-\frac{d_0}{2} \Bigr)^3 \Biggr]`

      with :math:`d_0` the wall thickness in the reference configuration, and
      factorizing :math:`R_0` from the bracket a Taylor expansion readily gives
      the following approximation that we use in the implementation up to the
      third order in :math:`d_0/2R_0`:

      :math:`|\Omega_0| = 4\pi R_0^2 d_0`

    * :math:`V(y)` denotes the volume of the sphere:

      :math:`V(y) = \frac{4}{3}\pi \Bigl( R(y)-\frac{d(y)}{2} \Bigr)^3
      = \frac{4}{3}\pi \Bigl( R_0+y-\frac{d_0}{2}C(y)^{-1} \Bigr)^3`

      with :math:`d(y)` the wall thickness in the deformed configuration.

    Discretization
    --------------

    .. math::

        \frac{P^{n + \frac{1}{2}}
        - P_{ext}^{n + \frac{1}{2}}}{|\Omega_0|} DV^{{n + \frac{1}{2}}\sharp}
        - \rho_0 \Bigl[ \frac{\dot{y}^{n+1}-\dot{y}^n}{\Delta t^n} \Bigr]
        - DW^{{n + \frac{1}{2}}\sharp}
        - \frac{1}{R_0} \Sigma_v(y^{n + \frac{1}{2}},\dot{y}^{n + \frac{1}{2}})
        - \frac{k_s}{R_0} \Bigl(
            \frac{y^{n + \frac{1}{2}}}{R_0}-e_c^{n + \frac{1}{2}} \Bigr) = 0

    Parameters
    ----------
    disp : Quantity[np.float64]
        :math:`y` the displacement along the radius.
    fib_deform : Quantity[np.float64]
        :math:`e_c` the sphere fiber deformation
    pressure : Quantity[np.float64]
        :math:`P` the pressure in the sphere
    pressure_external : Quantity[np.float64]
        :math:`P_{ext}` the pressure outside the sphere
    vel : Quantity[np.float64]
        :math:`\dot{y}` the displacement velocity
    radius : Quantity[np.float64]
        :math:`R_0` the initial sphere radius
    vol_mass : Quantity[np.float64]
        :math:`\rho_0` the volumic mass of the sphere tissue
    thickness : Quantity[np.float64]
        :math:`d_0` the initial thickness of the sphere
    damping_coef : Quantity[np.float64]
        :math:`\eta` the solid viscosity (damping) coefficient
    series_stiffness : Quantity[np.float64]
        :math:`k_s` the series stiffness
    hyperelastic_cst : Quantity[NDArray[np.float64]]
        :math:`(C_0,C_1,C_2,C_3)` the hyperelastic constants
    time : Time
        Simulation time

    Configuration
    -------------

    .. code-block:: json

        {
            "type": "model_description",
            "model_type": "spherical_dynamics",
            "disp": "<str>",              // Displacement along the radius global name
                                          // (internal variable) (optional)
            "fib_deform": "<str>",        // Sphere fiber deformation global name
                                          // (optional)
            "pressure": "<str>",          // Pressure in the sphere global name
                                          // (optional)
            "pressure_external": "<str>", // Pressure outside the sphere global name
                                          // (optional)
            "vel": "<str>",               // Displacement velocity global name
                                          // (optional)
            "radius": "<str>",            // Initial sphere radius global name
                                          // (optional)
            "vol_mass": "<str>",          // Volumic mass of the sphere tissue global
                                          // name (optional)
            "thickness": "<str>",         // Initial thickness of the sphere global name
                                          // (optional)
            "damping_coef": "<str>",      // Solid viscosity (damping) coefficient
                                          // global name (optional)
            "series_stiffness": "<str>",  // Series stiffness global name (optional)
            "hyperelastic_cst": "<str>",  // Hyperelastic constants global name
                                          // (optional)
            "time": "<str>"               // Simulation time name
        }

    Aliases
    -------

    .. _alias_spherical_dynamics:

    **spherical_dynamics**
        Aliases :class:`~.ModelComponentDescription`
        (``model_description``) with ``model_type`` set to ``spherical_dynamics`` and
        the ``time`` quantity bound to the global ``time`` quantity.

        .. code-block:: json

            {
                "type": "spherical_dynamics",
                "disp": "<str>",              // Displacement along the radius global
                                              // name (internal variable) (optional)
                "fib_deform": "<str>",        // Sphere fiber deformation global name
                                              // (optional)
                "pressure": "<str>",          // Pressure in the sphere global name
                                              // (optional)
                "pressure_external": "<str>", // Pressure outside the sphere global name
                                              // (optional)
                "vel": "<str>",               // Displacement velocity global name
                                              // (optional)
                "radius": "<str>",            // Initial sphere radius global name
                                              // (optional)
                "vol_mass": "<str>",          // Volumic mass of the sphere tissue
                                              // global name (optional)
                "thickness": "<str>",         // Initial thickness of the sphere global
                                              // name (optional)
                "damping_coef": "<str>",      // Solid viscosity (damping) coefficient
                                              // global name (optional)
                "series_stiffness": "<str>",  // Series stiffness global name (optional)
                "hyperelastic_cst": "<str>"   // Hyperelastic constants global name
                                              // (optional)
            }

    """

    disp: Quantity[np.float64]

    fib_deform: Quantity[np.float64]

    pressure: Quantity[np.float64]

    pressure_external: Quantity[np.float64]

    vel: Quantity[np.float64]

    radius: Quantity[np.float64]

    vol_mass: Quantity[np.float64]

    thickness: Quantity[np.float64]

    damping_coef: Quantity[np.float64]

    series_stiffness: Quantity[np.float64]

    hyperelastic_cst: Quantity[NDArray[np.float64]]

    time: Time

    def initialize(self) -> None:
        """Compute initial block quantities.

        Compute model constants (sphere radius, surface, volume, ...)
        and solve the associated static problem to get initial displacement and fiber
        deformation.
        """
        self.inv_radius = 1.0 / self.radius.current
        self.sphere_surface = 4.0 * np.pi * self.radius.current**2
        self.sphere_volume = 4.0 / 3.0 * np.pi * self.radius.current**3
        self.thickness_radius_ratio = self.thickness.current * self.inv_radius
        self.half_thickness_radius_ratio = 0.5 * self.thickness_radius_ratio
        self.viscous_coef = (
            2.0
            * self.damping_coef.current
            * self.thickness.current
            * self.inv_radius**2
        )
        self.hyperelastic_cst_01 = (
            self.hyperelastic_cst.current[0] * self.hyperelastic_cst.current[1]
        )
        self.hyperelastic_cst_23 = (
            self.hyperelastic_cst.current[2] * self.hyperelastic_cst.current[3]
        )

        disp_init, fib_deform_init = self._solve_static_problem()

        if disp_init < 0 and np.abs(disp_init) > self.radius.current:
            raise ValueError(
                "Displacement is initialized with a negative value that "
                "has an absolute value greater than the sphere radius."
            )

        self.disp.initialize(disp_init)
        self.fib_deform.initialize(fib_deform_init)

    @declares_internal_equation("disp")
    def dynamics_residual(self) -> Any:
        """Compute the residual giving a dynamics on ``disp``.

        Returns
        -------
        np.float64
            the residual

        """
        disp_mid = mid_point(self.disp)
        fib_deform_mid = mid_point(self.fib_deform)
        p_mid_point = mid_point(self.pressure)
        pressure_external = mid_point(self.pressure_external)

        disp_diff = diff(self.disp)

        disp_mid_ratio = 1.0 + disp_mid * self.inv_radius
        disp_new_ratio = 1.0 + self.disp.new * self.inv_radius
        disp_cur_ratio = 1.0 + self.disp.current * self.inv_radius

        j4_mid = disp_mid_ratio**2
        j4_diff_mid = 2.0 * self.inv_radius * disp_mid_ratio

        j1_mid = 2.0 * j4_mid + disp_mid_ratio**-4

        # inertia stress
        inertia_stress = (
            self.vol_mass.current
            * self.thickness.current
            * diff(self.vel)
            * self.time.inv_dt
        )

        # viscous stress
        viscous_diff_vel = (
            self.viscous_coef * j4_mid * (1.0 + 2.0 * disp_mid_ratio**-12)
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
                disp_cur_ratio - disp_cur_ratio**-2 * self.half_thickness_radius_ratio
            )
            fluid_volume_new = (
                disp_new_ratio - disp_new_ratio**-2 * self.half_thickness_radius_ratio
            )
            fluid_volume_diff3 = (
                disp_diff_ratio
                - power_diff(disp_new_ratio, disp_cur_ratio, disp_diff_ratio, -2)
                * self.half_thickness_radius_ratio
            )
            fluid_volume_diff = self.sphere_volume * power_diff(
                fluid_volume_new, fluid_volume_cur, fluid_volume_diff3, 3
            )

            external_stress = (
                (p_mid_point - pressure_external)
                * fluid_volume_diff
                / (self.sphere_surface * disp_diff)
            )

            # passive stress
            j4_new = disp_new_ratio**2
            j4_cur = disp_cur_ratio**2

            j4_diff = power_diff(disp_new_ratio, disp_cur_ratio, disp_diff_ratio, 2)

            j1_new = 2.0 * j4_new + disp_new_ratio**-4
            j1_cur = 2.0 * j4_cur + disp_cur_ratio**-4
            j1_diff = 2.0 * j4_diff + power_diff(
                disp_new_ratio, disp_cur_ratio, disp_diff_ratio, -4
            )

            arg_exp_j1_new = self.hyperelastic_cst.current[1] * (j1_new - 3.0) ** 2
            arg_exp_j1_cur = self.hyperelastic_cst.current[1] * (j1_cur - 3.0) ** 2
            arg_exp_j1_diff = self.hyperelastic_cst.current[1] * power_diff(
                j1_new - 3.0, j1_cur - 3.0, j1_diff, 2
            )

            arg_exp_j4_new = self.hyperelastic_cst.current[3] * (j4_new - 1.0) ** 2
            arg_exp_j4_cur = self.hyperelastic_cst.current[3] * (j4_cur - 1.0) ** 2
            arg_exp_j4_diff = self.hyperelastic_cst.current[3] * power_diff(
                j4_new - 1.0, j4_cur - 1.0, j4_diff, 2
            )

            exp_j1_diff = exp_diff(arg_exp_j1_new, arg_exp_j1_cur, arg_exp_j1_diff)
            exp_j4_diff = exp_diff(arg_exp_j4_new, arg_exp_j4_cur, arg_exp_j4_diff)

            hyperelastic_potential_diff = (
                self.hyperelastic_cst.current[0] * exp_j1_diff
                + self.hyperelastic_cst.current[2] * exp_j4_diff
            )

            passive_stress = (
                self.thickness.current * hyperelastic_potential_diff / disp_diff
            )

        else:
            # external stress
            disp_mid_ratio_adj = (
                disp_mid_ratio - disp_mid_ratio**-2 * self.half_thickness_radius_ratio
            ) ** 2
            external_stress = (
                (p_mid_point - pressure_external)
                * disp_mid_ratio_adj
                * (1.0 + disp_mid_ratio**-3 * self.thickness_radius_ratio)
            )

            # passive stress
            exp_j1_mid = np.exp(self.hyperelastic_cst.current[1] * (j1_mid - 3.0) ** 2)
            exp_j4_mid = np.exp(self.hyperelastic_cst.current[3] * (j4_mid - 1.0) ** 2)

            j1_diff_mid = 2.0 * j4_diff_mid - 4.0 * self.inv_radius * disp_mid_ratio**-5

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

    @dynamics_residual.partial_derivative("disp")
    def dynamics_residual_ddisp(self) -> Any:
        """Compute the partial derivative of the residual for ``disp``.

        Returns
        -------
        np.float64
            the residual partial derivative for ``disp``

        """
        disp_mid = mid_point(self.disp)
        disp_diff = diff(self.disp)
        disp_mid_ratio = 1.0 + disp_mid * self.inv_radius
        disp_cur_ratio = 1.0 + self.disp.current * self.inv_radius
        disp_new_ratio = 1.0 + self.disp.new * self.inv_radius
        pressure_external = mid_point(self.pressure_external)

        p_mid_point = mid_point(self.pressure)

        j4_mid = disp_mid_ratio**2
        j4_diff_mid = 2.0 * self.inv_radius * (disp_mid_ratio)
        j1_mid = 2.0 * j4_mid + disp_mid_ratio**-4

        # viscous
        viscous_diff_vel = (
            self.viscous_coef * j4_mid * (1.0 + 2.0 * disp_mid_ratio**-12)
        )
        viscous_potential_diff_disp_mid = (
            self.viscous_coef
            * disp_diff
            * self.time.inv_dt
            * (
                j4_diff_mid * (1.0 + 2.0 * disp_mid_ratio**-12)
                - 24.0 * self.inv_radius * j4_mid * disp_mid_ratio**-13
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
                disp_cur_ratio - disp_cur_ratio**-2 * self.half_thickness_radius_ratio
            )
            fluid_volume_term_new = (
                disp_new_ratio - disp_new_ratio**-2 * self.half_thickness_radius_ratio
            )
            fluid_volume_term_diff3 = (
                disp_diff_ratio
                - power_diff(disp_new_ratio, disp_cur_ratio, disp_diff_ratio, -2)
                * self.half_thickness_radius_ratio
            )
            fluid_volume_diff = self.sphere_volume * power_diff(
                fluid_volume_term_new, fluid_volume_term_cur, fluid_volume_term_diff3, 3
            )

            fluid_volume_diff_new = (
                self.sphere_surface
                * (
                    disp_new_ratio
                    - disp_new_ratio**-2 * self.half_thickness_radius_ratio
                )
                ** 2
                * (1.0 + disp_new_ratio**-3 * self.thickness_radius_ratio)
            )

            fluid_volume_diff_scheme_diff = (
                (1.0 / self.sphere_surface)
                * (fluid_volume_diff_new * disp_diff - fluid_volume_diff)
                * disp_diff**-2
            )

            external_ddisp = (
                p_mid_point - pressure_external
            ) * fluid_volume_diff_scheme_diff

            # passive
            j4_cur = disp_cur_ratio**2
            j4_new = disp_new_ratio**2
            j4_diff_new = 2.0 * self.inv_radius * disp_new_ratio
            j4_diff = power_diff(disp_new_ratio, disp_cur_ratio, disp_diff_ratio, 2)

            j1_new = 2.0 * j4_new + disp_new_ratio**-4
            j1_cur = 2.0 * j4_cur + disp_cur_ratio**-4
            j1_diff_new = 2.0 * j4_diff_new - 4.0 * self.inv_radius * disp_new_ratio**-5
            j1_diff = 2.0 * j4_diff + power_diff(
                disp_new_ratio, disp_cur_ratio, disp_diff_ratio, -4
            )

            arg_exp_j1_cur = self.hyperelastic_cst.current[1] * (j1_cur - 3.0) ** 2
            arg_exp_j1_new = self.hyperelastic_cst.current[1] * (j1_new - 3.0) ** 2
            arg_exp_j1_diff = self.hyperelastic_cst.current[1] * power_diff(
                j1_new - 3.0, j1_cur - 3.0, j1_diff, 2
            )
            exp_j1_new = np.exp(arg_exp_j1_new)

            arg_exp_j4_cur = self.hyperelastic_cst.current[3] * (j4_cur - 1.0) ** 2
            arg_exp_j4_new = self.hyperelastic_cst.current[3] * (j4_new - 1.0) ** 2
            arg_exp_j4_diff = self.hyperelastic_cst.current[3] * power_diff(
                j4_new - 1.0, j4_cur - 1.0, j4_diff, 2
            )
            exp_j4_new = np.exp(arg_exp_j4_new)

            exp_j4_diff = exp_diff(arg_exp_j4_new, arg_exp_j4_cur, arg_exp_j4_diff)
            exp_j1_diff = exp_diff(arg_exp_j1_new, arg_exp_j1_cur, arg_exp_j1_diff)

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
                / disp_diff**2
            )

        else:
            # external
            disp_mid_ratio_adj = (
                disp_mid_ratio - disp_mid_ratio**-2 * self.half_thickness_radius_ratio
            ) ** 2
            fluid_volume_diff_diff_mid = (
                4.0
                * np.pi
                * self.radius.current
                * (
                    2.0
                    * (
                        disp_mid_ratio
                        - disp_mid_ratio**-2 * self.half_thickness_radius_ratio
                    )
                    * (1.0 + disp_mid_ratio**-3 * self.thickness_radius_ratio) ** 2
                    - (
                        3.0
                        * self.thickness_radius_ratio
                        * disp_mid_ratio**-4
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
            exp_j1_mid = np.exp(self.hyperelastic_cst.current[1] * (j1_mid - 3.0) ** 2)
            exp_j4_mid = np.exp(self.hyperelastic_cst.current[3] * (j4_mid - 1.0) ** 2)
            j1_diff_mid = 2.0 * j4_diff_mid - 4.0 * self.inv_radius * disp_mid_ratio**-5
            j4_diff_diff = 2.0 * self.inv_radius**2
            j1_diff_diff_mid = (
                4.0 * self.inv_radius**2
                + 20.0 * self.inv_radius**2 * disp_mid_ratio**-6
            )
            hyperelastic_potential_diff_diff_mid = (
                2.0
                * self.hyperelastic_cst_01
                * (
                    j1_diff_diff_mid * (j1_mid - 3.0)
                    + j1_diff_mid**2
                    + 2.0
                    * self.hyperelastic_cst.current[1]
                    * (j1_diff_mid * (j1_mid - 3.0)) ** 2
                )
                * exp_j1_mid
                + 2.0
                * self.hyperelastic_cst_23
                * (
                    j4_diff_diff * (j4_mid - 1.0)
                    + j4_diff_mid**2
                    + 2.0
                    * self.hyperelastic_cst.current[3]
                    * (j4_diff_mid * (j4_mid - 1.0)) ** 2
                )
                * exp_j4_mid
            )
            passive_ddisp = (
                self.thickness.current * 0.5 * hyperelastic_potential_diff_diff_mid
            )

        return viscous_ddisp + active_ddisp - external_ddisp + passive_ddisp

    @dynamics_residual.partial_derivative("fib_deform")
    def dynamics_residual_dfib_deform(self) -> Any:
        """Compute the partial derivative of the residual for ``fib_deform``.

        Returns
        -------
        np.float64
            the residual partial derivative for ``fib_deform``

        """
        # active stress
        return -self.half_thickness_radius_ratio * self.series_stiffness.current

    @dynamics_residual.partial_derivative("vel")
    def dynamics_residual_dvel(self) -> Any:
        """Compute the partial derivative of the residual for ``vel``.

        Returns
        -------
        np.float64
            the residual partial derivative for ``vel``

        """
        # inertia
        return self.vol_mass.current * self.thickness.current * self.time.inv_dt

    @dynamics_residual.partial_derivative("pressure")
    def dynamics_residual_dpressure(self) -> Any:
        """Compute the partial derivative of the residual for the ``pressure``.

        Returns
        -------
        np.float64
            the residual partial derivative for ``pressure``

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
                disp_cur_ratio - disp_cur_ratio**-2 * self.half_thickness_radius_ratio
            )
            fluid_volume_term_new = (
                disp_new_ratio - disp_new_ratio**-2 * self.half_thickness_radius_ratio
            )

            fluid_volume_term_diff3 = (
                disp_diff_ratio
                - power_diff(disp_new_ratio, disp_cur_ratio, disp_diff_ratio, -2)
                * self.half_thickness_radius_ratio
            )

            fluid_volume_diff = self.sphere_volume * power_diff(
                fluid_volume_term_new, fluid_volume_term_cur, fluid_volume_term_diff3, 3
            )
            external_dpressure = -(
                (0.5 * fluid_volume_diff) / (self.sphere_surface * disp_diff)
            )
        else:
            disp_mid_ratio_adj = (
                disp_mid_ratio - disp_mid_ratio**-2 * self.half_thickness_radius_ratio
            ) ** 2
            external_dpressure = (
                -0.5
                * disp_mid_ratio_adj
                * (1.0 + disp_mid_ratio**-3 * self.thickness_radius_ratio)
            )

        return external_dpressure

    @dynamics_residual.partial_derivative("pressure_external")
    def dynamics_residual_dpressure_external(self) -> Any:
        """Compute the partial derivative of the residual ``pressure_external``.

        Returns
        -------
        np.float64
            the residual partial derivative ``pressure_external``.

        """
        disp_diff = diff(self.disp)

        if np.abs(disp_diff / self.disp.current) > _DISP_EPSILON:
            disp_diff_ratio = disp_diff * self.inv_radius
            disp_new_ratio = 1.0 + self.disp.new * self.inv_radius
            disp_cur_ratio = 1.0 + self.disp.current * self.inv_radius

            fluid_volume_cur = (
                disp_cur_ratio - disp_cur_ratio**-2 * self.half_thickness_radius_ratio
            )
            fluid_volume_new = (
                disp_new_ratio - disp_new_ratio**-2 * self.half_thickness_radius_ratio
            )
            fluid_volume_diff3 = (
                disp_diff_ratio
                - power_diff(disp_new_ratio, disp_cur_ratio, disp_diff_ratio, -2)
                * self.half_thickness_radius_ratio
            )
            fluid_volume_diff = self.sphere_volume * power_diff(
                fluid_volume_new, fluid_volume_cur, fluid_volume_diff3, 3
            )

            dresidual_dpressure_external = (
                0.5 * fluid_volume_diff / (self.sphere_surface * disp_diff)
            )

        else:
            disp_mid = mid_point(self.disp)
            disp_mid_ratio = 1.0 + disp_mid * self.inv_radius

            disp_mid_ratio_adj = (
                disp_mid_ratio - disp_mid_ratio**-2 * self.half_thickness_radius_ratio
            ) ** 2

            dresidual_dpressure_external = (
                0.5
                * disp_mid_ratio_adj
                * (1.0 + disp_mid_ratio**-3 * self.thickness_radius_ratio)
            )

        return dresidual_dpressure_external

    def _solve_static_problem(self) -> tuple[np.float64, np.float64]:
        eq_system = EqSystem(1)

        state = QuantitiesRegistry()
        state.add_quantity(
            SPHERICAL_DYNAMICS_STATIC_DISP_LOCAL_ID, 1, _STATIC_PROBLEM_DISP_MAG
        )
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
        static_expression = _SphericalDynamicsStaticModelComponent.internal_expressions[
            0
        ]
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
            sol = solver.solve(state, eq_system)

            if sol.converged is True:
                state[SPHERICAL_DYNAMICS_STATIC_DISP_LOCAL_ID].initialize(sol.x[0])

                if np.abs(p_test - static_block.pressure.current) < _STATIC_PROBLEM_TOL:
                    break  # disp and fib deform initialized

                p_test = np.min([p_test + p_step, static_block.pressure.current])
                static_block.pressure.update(p_test)

            else:
                # solver did not converged, update pressure
                state.reset_vector()
                p_step = p_step * 0.5
                p_test = p_test - p_step
                static_block.pressure.update(p_test)

        disp_init = state[SPHERICAL_DYNAMICS_STATIC_DISP_LOCAL_ID].current
        return disp_init, disp_init * self.inv_radius


@dataclass
class _SphericalDynamicsStaticModelComponent(ModelComponent):
    """Declare the static problem associated with SphericalDynamicsModelComponent.

    We use this model to initialize the spherical dynamic displacement.

    Parameters
    ----------
    disp : Quantity[np.float64]
        Displacement
    pressure : Quantity[np.float64]
        pressure
    thickness : Quantity[np.float64]
        thickness
    hyperelastic_cst : Quantity[NDArray[np.float64]]
        hyperelastic constant
    inv_radius : Quantity[np.float64]
        inverse of the sphere radius
    pressure_external : Quantity[np.float64]
        external pressure

    """

    disp: Quantity[np.float64]

    pressure: Quantity[np.float64]

    thickness: Quantity[np.float64]

    hyperelastic_cst: Quantity[NDArray[np.float64]]

    inv_radius: Quantity[np.float64]

    pressure_external: Quantity[np.float64]

    def initialize(self) -> None:
        """Initialize block attributes from current quantity values."""
        self.hyperelastic_cst_01 = (
            self.hyperelastic_cst.current[0] * self.hyperelastic_cst.current[1]
        )
        self.hyperelastic_cst_23 = (
            self.hyperelastic_cst.current[2] * self.hyperelastic_cst.current[3]
        )
        self.thickness_radius_ratio = self.thickness.current * self.inv_radius.current
        self.half_thickness_radius_ratio = 0.5 * self.thickness_radius_ratio

    @declares_internal_equation("disp")
    def dynamics_static_residual(self) -> Any:
        """Compute the residual for the dynamics static problem.

        Returns
        -------
        np.float64
            the static problem residual

        """
        pressure_external = mid_point(self.pressure_external)

        disp_new_ratio = 1.0 + self.disp.new * self.inv_radius.current
        fluid_volume_diff = (
            disp_new_ratio - disp_new_ratio**-2 * self.half_thickness_radius_ratio
        ) ** 2 * (1.0 + disp_new_ratio**-3 * self.thickness_radius_ratio)

        j4_new = disp_new_ratio**2
        j1_new = 2.0 * j4_new + disp_new_ratio**-4

        j4_diff_new = 2.0 * self.inv_radius.current * (disp_new_ratio)
        j1_diff_new = 2.0 * (
            j4_diff_new - 2.0 * self.inv_radius.current * disp_new_ratio**-5
        )

        hyperelastic_potential_diff = 2.0 * (
            (
                self.hyperelastic_cst_01
                * j1_diff_new
                * (j1_new - 3.0)
                * np.exp(self.hyperelastic_cst.current[1] * (j1_new - 3.0) ** 2)
            )
            + (
                self.hyperelastic_cst_23
                * j4_diff_new
                * (j4_new - 1.0)
                * np.exp(self.hyperelastic_cst.current[3] * (j4_new - 1.0) ** 2)
            )
        )

        passive_stress = self.thickness.current * hyperelastic_potential_diff
        external_stress = (self.pressure.new - pressure_external) * fluid_volume_diff

        return passive_stress - external_stress

    @dynamics_static_residual.partial_derivative("disp")
    def dynamics_static_residual_ddisp(self) -> Any:
        """Compute the partial derivative for disp for the static problem residual.

        Returns
        -------
        np.float64
            the residual partial derivative for disp

        """
        disp_new_ratio = 1.0 + self.disp.new * self.inv_radius.current
        pressure_external = mid_point(self.pressure_external)

        j4_new = disp_new_ratio**2
        j1_new = 2.0 * j4_new + disp_new_ratio**-4

        j4_diff_new = 2.0 * self.inv_radius.current * (disp_new_ratio)
        j1_diff_new = 2.0 * (
            j4_diff_new - 2.0 * self.inv_radius.current * disp_new_ratio**-5
        )

        j1_diff_diff_new = (
            4.0 * self.inv_radius.current**2
            + 20.0 * self.inv_radius.current**2 * disp_new_ratio**-6
        )
        j4_diff_diff_new = 2.0 * self.inv_radius.current**2

        hyperelastic_potential_diff_diff = 2.0 * (
            self.hyperelastic_cst.current[0]
            * self.hyperelastic_cst.current[1]
            * (
                j1_diff_diff_new * (j1_new - 3.0)
                + j1_diff_new**2
                + (
                    2.0
                    * self.hyperelastic_cst.current[1]
                    * (j1_diff_new * (j1_new - 3.0)) ** 2
                )
            )
            * np.exp(self.hyperelastic_cst.current[1] * (j1_new - 3.0) ** 2)
            + self.hyperelastic_cst.current[2]
            * self.hyperelastic_cst.current[3]
            * (
                j4_diff_diff_new * (j4_new - 1.0)
                + j4_diff_new**2
                + (
                    2.0
                    * self.hyperelastic_cst.current[3]
                    * (j4_diff_new * (j4_new - 1.0)) ** 2
                )
            )
            * np.exp(self.hyperelastic_cst.current[3] * (j4_new - 1.0) ** 2)
        )

        passive_stress_diff = self.thickness.current * hyperelastic_potential_diff_diff

        fluid_volume_diff_diff = self.inv_radius.current * (
            2.0
            * (
                1.0
                + self.disp.new * self.inv_radius.current
                - disp_new_ratio**-2 * self.half_thickness_radius_ratio
            )
            * (1.0 + disp_new_ratio**-3 * self.thickness_radius_ratio) ** 2
            - 3.0
            * self.thickness_radius_ratio
            * disp_new_ratio**-4
            * (
                1.0
                + self.disp.new * self.inv_radius.current
                - disp_new_ratio**-2 * self.half_thickness_radius_ratio
            )
            ** 2
        )

        ext_stress_diff = (
            self.pressure.new - pressure_external
        ) * fluid_volume_diff_diff

        return passive_stress_diff - ext_stress_diff


SPHERICAL_DYNAMICS_ASYMPTOTIC_TYPE_ID = SPHERICAL_DYNAMICS_TYPE_ID + "_asymptotic"


@dataclass
@register_type(SPHERICAL_DYNAMICS_ASYMPTOTIC_TYPE_ID)
class SphericalDynamicsAsymptoticModelComponent(ModelComponent):
    r"""Asymptotic description of the dynamics.

    Allows to save the ESPVR (End Systolic Pressure-Volume Relationship)
    and EDPVR (End Diastolic Pressure-Volume Relationship).

    Saved Quantities
    ----------------

    The ESPVR:

    .. math::

        P(V) = |\Omega_0|
        (\frac{\partial V(y)}{\partial y})^{-1}
        (\frac{\partial W_e(y)}{\partial y}
        + \frac{k_s}{R_0} \Bigl( \frac{y}{R_0}-e_c \Bigr))

    The EDPVR:

    .. math::

        P(V) = |\Omega_0|
        (\frac{\partial V(y)}{\partial y})^{-1}
        (\frac{\partial W_e(y)}{\partial y})

    With:

    * :math:`W_e(y)` represents an elastic energy per unit volume given by:

      :math:`W_e(y) =
      C_0 \exp \Bigl[ C_1 \bigl(2C(y)+C(y)^{-2}-3\bigr)^2 \Bigr]
      + C_2 \exp \Bigl[ C_3 \bigl(C(y)-1\bigr)^2 \Bigr]`

      where :math:`(C_0,C_1,C_2,C_3)` denote material parameters of the
      passive constitutive law, and :math:`C(y)= (1+y/R_0)^2` represents the
      component of the right Cauchy-Green deformation tensor along the fiber
      direction.

    * :math:`k_s` denotes a passive elastic modulus

    * :math:`|\Omega_0|` is the total volume of sphere tissue in the reference
      configuration:

      :math:`|\Omega_0| = 4\pi R_0^2 d_0`

    * :math:`V(y)` denotes the volume of the sphere:

      :math:`V(y) = \frac{4}{3}\pi \Bigl( R_0+y-\frac{d_0}{2}C(y)^{-1} \Bigr)^3`

    Parameters
    ----------
    disp : Quantity[np.float64]
        Displacement :math:`y`
    fib_deform : Quantity[np.float64]
        fiber deformation  :math:`e_c`
    thickness : Quantity[np.float64]
        thickness  :math:`d_0`
    series_stiffness : Quantity[np.float64]
        series stiffness  :math:`k_s`
    hyperelastic_cst : Quantity[NDArray[np.float64]]
        hyperelastic constant :math:`(C_0,C_1,C_2,C_3)`
    radius : Quantity[np.float64]
        sphere radius :math:`R_0`

    Configuration
    -------------

    .. code-block:: json

        {
            "type": "model_description",
            "model_type": "spherical_dynamics_asymptotic",
            "disp": "<str>",             // Displacement global name (optional)
            "fib_deform": "<str>",       // Fiber deformation global name (optional)
            "thickness": "<str>",        // Thickness global name (optional)
            "series_stiffness": "<str>", // Series stiffness global name (optional)
            "hyperelastic_cst": "<str>", // Hyperelastic constant global name (optional)
            "radius": "<str>",           // Sphere radius global name (optional)
            "EDPVR": "<str>",            // End Diastolic Pressure-Volume Relationship
                                         // global name (optional) (saved quantity)
            "ESPVR": "<str>"             // End Systolic Pressure-Volume Relationship
                                         // global name (optional) (saved quantity)
        }

    """

    disp: Quantity[np.float64]

    fib_deform: Quantity[np.float64]

    thickness: Quantity[np.float64]

    series_stiffness: Quantity[np.float64]

    hyperelastic_cst: Quantity[NDArray[np.float64]]

    radius: Quantity[np.float64]

    def initialize(self) -> None:
        """Initialize block constants from current quantity values."""
        self.inv_radius = 1 / self.radius
        self.squared_radius = self.radius**2
        self.hyperelastic_cst_01 = (
            self.hyperelastic_cst.current[0] * self.hyperelastic_cst.current[1]
        )
        self.hyperelastic_cst_23 = (
            self.hyperelastic_cst.current[2] * self.hyperelastic_cst.current[3]
        )
        self.sphere_volume = 4.0 * np.pi * self.radius.current**2 * self.thickness

    def _get_fluid_volume_diff_ratio(self) -> Any:
        disp_radius_sum = self.radius + self.disp.current
        return (
            np.pi
            * (-self.squared_radius * self.thickness + 2 * disp_radius_sum**3) ** 2
            * (self.squared_radius * self.thickness + disp_radius_sum**3)
            / disp_radius_sum**7
        )

    def _get_hyperelastic_potential_diff(self, disp_ratio: float) -> Any:
        return (
            self.hyperelastic_cst_01
            * (8 * disp_ratio / self.radius - 8 / (self.radius * disp_ratio**5))
            * (2 * disp_ratio**2 - 3 + disp_ratio ** (-4))
            * np.exp(
                self.hyperelastic_cst.current[1]
                * (2 * disp_ratio**2 - 3 + disp_ratio ** (-4)) ** 2
            )
            + 4
            * self.hyperelastic_cst_23
            * disp_ratio
            * (disp_ratio**2 - 1)
            * np.exp(self.hyperelastic_cst.current[3] * (disp_ratio**2 - 1) ** 2)
            / self.radius
        )

    @declares_saved_quantity("EDPVR")
    def compute_pressure_edpvr(self) -> Any:
        """
        Compute the End Diastolic Pressure-Volume Relationship.

        Returns
        -------
        Any
            the EDPVR.
        """
        disp_ratio = 1.0 + self.disp.current * self.inv_radius
        fluid_volume_diff = self._get_fluid_volume_diff_ratio()
        hyperelastic_potential_diff = self._get_hyperelastic_potential_diff(disp_ratio)
        passive_stress = hyperelastic_potential_diff

        return passive_stress * self.sphere_volume / fluid_volume_diff

    @declares_saved_quantity("ESPVR")
    def compute_pressure_espvr(self) -> Any:
        """
        Compute the End Systolic Pressure-Volume Relationship.

        Returns
        -------
        Any
            the ESPVR.
        """
        disp_ratio = 1.0 + self.disp.current * self.inv_radius
        fluid_volume_diff = self._get_fluid_volume_diff_ratio()
        hyperelastic_potential_diff = self._get_hyperelastic_potential_diff(disp_ratio)
        passive_stress = hyperelastic_potential_diff
        active_stress = (
            self.series_stiffness
            * self.inv_radius
            * (self.disp.current * self.inv_radius - self.fib_deform.current)
        )
        return (passive_stress + active_stress) * self.sphere_volume / fluid_volume_diff


T = TypeVar("T", float, NDArray[np.float64])


def exp_diff(a: T, b: T, diff: T) -> Any:
    r"""Compute the exponential difference between the parameters.

    This method has better numerical accuracy when a and b are close using the
    relationship:

    .. math::

        e^a - e^b = 2\ e^{\frac{a + b}{2}}\ \text{sinh}(\frac{a - b}{2})

    Parameters
    ----------
    a : float | NDArray[np.float64]
        value of a
    b : float | NDArray[np.float64]
        value of b
    diff : float | NDArray[np.float64]
        value of a - b

    Returns
    -------
    float | NDArray[np.float64]
        exponential difference value

    """
    return np.exp(0.5 * (a + b)) * 2.0 * np.sinh(0.5 * diff)


def power_diff(a: T, b: T, diff: T, n: int) -> T:
    r"""Compute :math:`a^n - b^n`.

    This method has better numerical accuracy when a and b are close using the
    relationship:

    .. math::

        a^n - b^n = (a-b) \sum_{i = 0}^{n -1}{a^i b^{n-1-i}}

    For :math:`n < 0` with :math:`m = -n`, the following transformation is used:

    .. math::

        \frac{1}{a^m} - \frac{1}{b^m} = -\frac{a^m-b^m}{(ab)^m}

    Parameters
    ----------
    a : float | NDArray[np.float64]
        value of a
    b : float | NDArray[np.float64]
        value of b
    diff : float | NDArray[np.float64]
        value of :math:`a - b`
    n : int
        the power

    Returns
    -------
    float | NDArray[np.float64]
        the a and b power n difference value

    """
    if n < 0:
        return -power_diff(a, b, diff, -n) / ((a * b) ** -n)
    elif n > 0:
        return diff * sum((a**_i) * (b ** (n - _i - 1)) for _i in range(n))
    else:
        return a**n - b**n
