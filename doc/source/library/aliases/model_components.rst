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

.. _library_aliases_model_components:

Model Components
================

Velocity Law
------------

Velocity Law HHT
""""""""""""""""

* **Class:** :class:`~physioblocks.description.blocks.ModelComponentDescription`
* **Alias name:** ``velocity_law_hht``

Model Component Description of a :class:`~physioblocks.library.model_components.velocity_law.VelocityLawHHTModelComponent` object with time parameter set.

Parameters
''''''''''

    * **model_type**: ``velocity_law_hht``
    * **time**: The simulation time global name.

Dynamics
--------

Spherical Dynamics
""""""""""""""""""

* **Class:** :class:`~physioblocks.description.blocks.ModelComponentDescription`
* **Alias name:** ``spherical_dynamics``

Model Component Description of a :class:`~physioblocks.library.model_components.dynamics.SphericalDynamicsModelComponent` object with time parameter set.

Parameters
''''''''''

    * **model_type**: ``spherical_dynamics``
    * **time**: The simulation time global name.


Rheology
--------

Rheology Fiber Additive
"""""""""""""""""""""""

* **Class:** :class:`~physioblocks.description.blocks.ModelComponentDescription`
* **Alias name:** ``rheology_fiber_additive``

Model Component Description of a :class:`~physioblocks.library.model_components.rheology.RheologyFiberAdditiveModelComponent` object with time parameter set.

Parameters
''''''''''

    * **model_type**: ``rheology_fiber_additive``
    * **time**: The simulation time global name.

Active law
----------

Active Law Macroscopic Huxley Two Moments
"""""""""""""""""""""""""""""""""""""""""

* **Class:** :class:`~physioblocks.description.blocks.ModelComponentDescription`
* **Alias name:** ``active_law_macro_huxley_two_moments``

Model Component Description of a :class:`~physioblocks.library.model_components.active_law.ActiveLawMacroscopicHuxleyTwoMoment` object with time parameter set.

Parameters
''''''''''

    * **model_type**: ``active_law_macro_huxley_two_moments``
    * **time**: The simulation time global name.
