.. SPDX-FileCopyrightText: Copyright INRIA
..
.. SPDX-License-Identifier: LGPL-3.0-only
..
.. Copyright INRIA
..
.. This file is part of PhysioBlocks, a library mostly developed by the
.. [Ananke project-team](https://team.inria.fr/ananke) at INRIA.
..
.. Authors:
.. - Colin Drieu
.. - Dominique Chapelle
.. - François Kimmig
.. - Philippe Moireau
..
.. PhysioBlocks is free software: you can redistribute it and/or modify it under the
.. terms of the GNU Lesser General Public License as published by the Free Software
.. Foundation, version 3 of the License.
..
.. PhysioBlocks is distributed in the hope that it will be useful, but WITHOUT ANY
.. WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
.. PARTICULAR PURPOSE. See the GNU Lesser General Public License for more details.
..
.. You should have received a copy of the GNU Lesser General Public License along with
.. PhysioBlocks. If not, see <https://www.gnu.org/licenses/>.

Nets
====

Describes available net alias.

Simple Circulation Net
----------------------

Describe a simple circulation model useful to run tests.

* **Class:** :class:`~physioblocks.description.nets.Net`
* **Alias name:** ``circulation_alone``

Model
"""""

.. tikz:: Simple circulation model scheme
    :include: ../../schemes/simple_circulation_model_heart.tex


.. tikz:: Simple circulation model Net
    :include: ../../schemes/circulation_net_scheme_heart.tex

Boundaries
""""""""""

To complete the net, you must add boundary conditions on nodes:

    * ``proximal``
    * ``venous``

Variables
"""""""""

Default variable names in the net:

    * ``aorta_proximal.blood_pressure``
    * ``aorta_distal.blood_pressure``
    * ``venous.blood_pressure``

Parameters
""""""""""

Default parameter names in the net:

    * ``aorta_proximal.resistance``
    * ``aorta_proximal.capacitance``
    * ``aorta_distal.resistance``
    * ``aorta_distal.capacitance``

Spherical Heart Circulation Net
-------------------------------

Describe a simple cardiovascular circulation model.

* **Class:** :class:`~physioblocks.description.nets.Net`
* **Alias name:** ``spherical_heart_net``

Model
"""""

.. tikz:: Spherical Heart Circulation Model
    :include: ../../schemes/model_heart_circulation_0D.tex


.. tikz:: Spherical Heart Circulation Net
    :include: ../../schemes/spherical_heart_net_scheme.tex

Boundaries
""""""""""

To complete the net, you must add boundary conditions on nodes:

    * ``atrium``
    * ``venous``

Variables
"""""""""

Default variable names in the net:

    * ``cavity.blood_pressure``
    * ``atrium.blood_pressure``
    * ``aorta_proximal.blood_pressure``
    * ``aorta_distal.blood_pressure``
    * ``venous.blood_pressure``
    * ``valve_atrium.flux``
    * ``valve_arterial.flux``
    * ``cavity.dynamics.disp``
    * ``cavity.velocity_law.vel``
    * ``cavity.velocity_law.accel``
    * ``cavity.rheology.fib_deform``
    * ``cavity.rheology.active_law.active_stiffness``
    * ``cavity.rheology.active_law.active_energy_sqrt``
    * ``cavity.rheology.active_law.active_tension_discr``

Parameters
""""""""""

Default parameter names in the net:

    * Circulation
        * ``aorta_proximal.resistance``
        * ``aorta_proximal.capacitance``
        * ``aorta_distal.resistance``
        * ``aorta_distal.capacitance``
    
    * Valves:
        * ``conductance_iso``
        * ``valve_atrium.inductance``
        * ``valve_atrium.conductance``
        * ``valve_atrium.scheme_ts_flux``
        * ``valve_arterial.inductance``
        * ``valve_arterial.conductance``
        * ``valve_arterial.scheme_ts_flux``
        * ``capacitance_valve.capacitance``

    * Cavity:
        * ``pleural.pressure``

    * Dynamics:
        * ``cavity.dynamics.vol_mass``
        * ``cavity.dynamics.damping_coef``
        * ``cavity.velocity_law.scheme_ts_hht``

    * Rheology:
        * ``cavity.rheology.series_stiffness``
        * ``cavity.rheology.damping_parallel``
        * ``cavity.rheology.active_law.starling_abscissas``
        * ``cavity.rheology.active_law.starling_ordinates``
        * ``cavity.rheology.active_law.destruction_rate``
        * ``cavity.rheology.active_law.crossbridge_stiffness``
        * ``cavity.rheology.active_law.activation``
        
    