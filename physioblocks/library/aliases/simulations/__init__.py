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

"""Simulations, time ranges and solvers aliases.

Aliases
-------

.. _alias_default_time:

**default_time**
    Aliases :class:`~.SimulationRange` (``range``) with its values set from the
    ``time.start``, ``time.step_size`` and ``time.duration`` simulation parameters.

    .. code-block:: json

        {
            "type": "default_time"
        }

    The simulation using the alias must initialize the parameters:

    .. code-block:: json

        {
            "parameters": {
                "time.start": "<float>",      // Starting time
                "time.step_size": "<float>",  // Step size
                "time.duration": "<float>"    // Simulation length
            }
        }

.. _alias_newton_method_solver:

**newton_method_solver**
    Aliases :class:`~.NewtonSolver`
    (``newton_solver``) with a ``1e-9`` tolerance and ``10`` maximum iterations.

    .. code-block:: json

        {
            "type": "newton_method_solver"
        }

.. _alias_default_forward_simulation:

**default_forward_simulation**
    Aliases :class:`~.ForwardSimulation` (``forward_simulation``) with the
    :ref:`default_time <alias_default_time>` time range starting at ``0.0`` with
    ``1e-3`` time steps, the :ref:`newton_method_solver <alias_newton_method_solver>`
    solver, a ``6.25e-5`` minimum step for the continuation algorithm and a
    ``main_plot`` plot of the results against time.

    .. code-block:: json

        {
            "type": "default_forward_simulation",
            "net": "<net type>",          // The simulation net
            "state": {
                "<str>": "<quantity type>"
            },
            "parameters": {
                "time.duration": "<float>",  // Simulation length
                "<str>": "<float | initialization function type>"
            }
        }

.. _alias_default_estimation_simulation:

**default_estimation_simulation**
    Aliases :class:`~.EstimationSimulation` (``estimation_simulation``) with the
    :ref:`default_time <alias_default_time>` time range starting at ``0.0`` with
    ``1e-3`` time steps, the :ref:`newton_method_solver <alias_newton_method_solver>`
    solver, a ``6.25e-5`` minimum step for the continuation algorithm and a
    ``main_plot`` plot of the results against time.

    .. code-block:: json

        {
            "type": "default_estimation_simulation",
            "filter_type": "<str>",       // Type id of the estimation filter
            "net": "<net type>",          // The simulation net
            "observer": "<observer type>", // The observer
            "data": {                     // The measurements
                "measurements": "<data reader type>"
            },
            "state": {
                "<str>": "<quantity type>"
            },
            "estimated_parameters": {
                "<str>": "<quantity type>"
            },
            "parameters": {
                "time.duration": "<float>",  // Simulation duration
                "<str>": "<float | initialization function type>"
            }
        }

.. _alias_circulation_alone_forward_simulation:

**circulation_alone_forward_simulation**
    Aliases :ref:`default_forward_simulation <alias_default_forward_simulation>`
    to simulate the :ref:`circulation_alone_net <alias_circulation_alone_net>`
    net with a linear solver.

    * The ``aorta_proximal.blood_flow`` boundary condition at the ``aorta_proximal``
      node is a periodic two phases function (see :class:`~.RescaleTwoPhasesFunction`)
      between its minimum and maximum values, with a heartbeat duration computed from
      the heart rate. The ``venous.blood_pressure`` boundary condition at the ``venous``
      node is a parameter.
    * The distal capacitance is computed from the distal time constant and
      resistance: ``aorta_distal.capacitance = aorta_distal.time_constant /
      aorta_distal.resistance``.
    * The results are converted to mL/s and mmHg.

    .. code-block:: json

        {
            "type": "circulation_alone_forward_simulation",
            "parameters": {
                "time.duration": "<float>",                       // Simulation length
                "heart_rate": "<float>",                          // Beats per minute
                "aorta_proximal.blood_flow.min": "<float>",       // Minimum blood flow
                "aorta_proximal.blood_flow.max": "<float>",       // Maximum blood flow
                "aorta_proximal.resistance": "<float>",
                "aorta_distal.resistance": "<float>",
                "aorta_distal.time_constant": "<float>",
                "venous.blood_pressure": "<float>",
                "aorta_proximal.blood_pressure.init": "<float>",  // Initial pressure
                "aorta_distal.blood_pressure.init": "<float>"     // Initial pressure
            }
        }

.. _alias_spherical_heart_forward_simulation:

**spherical_heart_forward_simulation**
    Aliases :ref:`default_forward_simulation <alias_default_forward_simulation>`
    to simulate the :ref:`spherical_heart_net <alias_spherical_heart_net>` net.

    * The ``atrial.blood_pressure`` boundary condition at the ``atrial`` node and the
      cavity active law activation are periodic two phases functions (see
      :class:`~.RescaleTwoPhasesFunction`), with a heartbeat duration computed from the
      heart rate. The ``venous.blood_pressure`` boundary condition at the ``venous``
      node is a parameter, and the ``pleural.pressure`` is ``0.0``.
    * It sets default values for the cavity dynamics, rheology, active law,
      valves and circulation parameters, and the state variables magnitudes.
    * The distal capacitance is computed from the distal time constant and
      resistance: ``circulation_aorta_distal.capacitance =
      circulation_aorta_distal.time_constant /
      circulation_aorta_distal.resistance``.
    * The ESPVR and EDPVR curves are computed before the simulation (see
      :class:`~.EspvrEdpvrProcess`), then plotted.
    * The results are converted to medical units.

    .. code-block:: json

        {
            "type": "spherical_heart_forward_simulation",
            "parameters": {
                "time.duration": "<float>",                   // Simulation length
                "heart_rate": "<float>",                      // Beats per minute
                "heart_radius": "<float>",                    // Cavity initial radius
                "heart_thickness": "<float>",         // Cavity initial wall thickness
                "heart_contractility": "<float>",             // Heart contractility
                "cavity.dynamics.hyperelastic_cst": ["<float>"], // C0, C1, C2, C3
                "atrial.blood_pressure.min": "<float>",       // Minimum atrial pressure
                "atrial.blood_pressure.max": "<float>",       // Maximum atrial pressure
                "venous.blood_pressure": "<float>",
                "circulation_aorta_proximal.resistance": "<float>",
                "circulation_aorta_distal.resistance": "<float>",
                "circulation_aorta_distal.time_constant": "<float>",
                "cavity.blood_pressure.init": "<float>",      // Initial pressure
                "aorta_proximal.blood_pressure.init": "<float>", // Initial pressure
                "aorta_distal.blood_pressure.init": "<float>" // Initial pressure
            }
        }


.. _alias_circulation_alone_estimation_ukf:

**circulation_alone_estimation_ukf**
    Aliases :ref:`default_estimation_simulation <alias_default_estimation_simulation>`
    to estimate the ``aorta_distal.resistance`` of the
    :ref:`circulation_alone_net <alias_circulation_alone_net>` net with an
    :class:`~.UnscentedKalmanFilter`.

    * The boundary conditions are the ones of
      :ref:`circulation_alone_forward_simulation
      <alias_circulation_alone_forward_simulation>`.
    * The ``aorta_proximal.blood_pressure`` is observed and compared to the
      ``measurement.aorta_proximal.blood_pressure`` measurement.
    * The estimated resistance is constrained positive values.
    * The measurements in mmHg are read from a file, renamed, interpolated on the
      simulation time steps and converted to Pa before the simulation.
    * The results are converted back to to medical units and plotted.

    .. code-block:: json

        {
            "type": "circulation_alone_estimation_ukf",
            "data": {
                "measurements": {
                    "filepath": "<str>"  // Path to the measurements file
                }
            },
            "preprocesses": {
                "measurements_mapping": {
                    "mapping": {         // Map the measurement name in the file to fit
                        "<str>": "<str>" // the awaited measurement name in the code.
                    }
                }
            },
            "parameters": {
                "time.duration": "<float>",                       // Simulation length
                "heart_rate": "<float>",                          // Beats per minute
                "aorta_proximal.blood_flow.min": "<float>",       // Minimum blood flow
                "aorta_proximal.blood_flow.max": "<float>",       // Maximum blood flow
                "aorta_proximal.resistance": "<float>",
                "venous.blood_pressure": "<float>",
                "aorta_distal.resistance.init": "<float>",        // Initial estimation
                "aorta_proximal.blood_pressure.init": "<float>",  // Initial pressure
                "aorta_distal.blood_pressure.init": "<float>"     // Initial pressure
            }
        }

.. _alias_spherical_heart_estimation_ukf:

**spherical_heart_estimation_ukf**
    Aliases :ref:`default_estimation_simulation
    <alias_default_estimation_simulation>` to estimate the
    ``circulation_aorta_distal.resistance`` and the ``heart_contractility`` of the
    :ref:`spherical_heart_net <alias_spherical_heart_net>` net with an
    :class:`~.UnscentedKalmanFilter`.

    * The boundary conditions, default parameters and pre-processes are the ones of
      :ref:`spherical_heart_forward_simulation
      <alias_spherical_heart_forward_simulation>`.
    * The ``aorta_proximal.blood_pressure`` and ``valve_arterial.flux`` are
      observed and compared to the ``measurement.aorta_proximal.blood_pressure``
      and ``measurement.valve_arterial.flux`` measurements.
    * The estimated parameters are constrained to positive values.
    * The measurements are read from a file, renamed, interpolated on the simulation
      time steps and converted to SI units before the simulation.
    * The results are converted back to medical units, the pressure-volume loop
      and the estimations are plotted.

    .. code-block:: json

        {
            "type": "spherical_heart_estimation_ukf",
            "data": {
                "measurements": {
                    "filepath": "<str>"  // Path to the measurements file
                }
            },
            "preprocesses": {
                "measurements_mapping": {
                    "mapping": {          // Map the measurement name in the file to fit
                        "<str>": "<str>"  // the awaited measurement name in the code.
                    }
                }
            },
            "parameters": {
                "time.duration": "<float>",                   // Simulation duration
                "heart_rate": "<float>",                      // In beats per minute
                "heart_radius": "<float>",                    // Cavity initial radius
                "heart_thickness": "<float>",          // Cavity initial wall thickness
                "cavity.dynamics.hyperelastic_cst": ["<float>"], // C0, C1, C2, C3
                "atrial.blood_pressure.min": "<float>",       // Minimum atrial pressure
                "atrial.blood_pressure.max": "<float>",       // Maximum atrial pressure
                "venous.blood_pressure": "<float>",
                "circulation_aorta_proximal.resistance": "<float>",
                "circulation_aorta_distal.resistance.init": "<float>", // Initial guess
                                                                // for distal resistance
                "heart_contractility.init": "<float>",        // Initial guess
                                                              //for heart contractility
                "cavity.blood_pressure.init": "<float>",      // Initial pressure
                "aorta_proximal.blood_pressure.init": "<float>", // Initial pressure
                "aorta_distal.blood_pressure.init": "<float>" // Initial pressure
            }
        }
"""
