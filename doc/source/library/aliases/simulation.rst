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

.. _library_aliases_simulation:

Simulations
===========

Describes avaible aliases to build simulation configuration files.

Time
----

Default Time
^^^^^^^^^^^^

* **Class:** :class:`~physioblocks.simulation.time_manager.TimeManager`
* **Alias name:** ``default_time``

Parameters
""""""""""

    * **step_size**: ``1e-3`` seconds
    * **min_step**: ``6.25e-5`` seconds

The ``duration`` and ``start`` parameters must be set in the file using the alias

Solvers
-------

Newton Solver
^^^^^^^^^^^^^

* **Class:** :class:`~physioblocks.simulation.solvers.NewtonSolver`
* **Alias name:** ``newton_method_solver``

Parameters
""""""""""

    * **tolerance**: ``1e-9``
    * **iteration_max**: ``10``

Forward Simulation
------------------

Default Forward Simulation
^^^^^^^^^^^^^^^^^^^^^^^^^^

* **Class:** :class:`~physioblocks.simulation.runtime.ForwardSimulation`
* **Alias name:** ``default_forward_simulation``

Parameters
""""""""""

    * **time**: Set to the ``default_time`` alias 
    * **solver**: Set to the ``newton_method_solver`` alias

Circulation Alone Forward Simulation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* **Class:** :class:`~physioblocks.simulation.runtime.ForwardSimulation`
* **Alias name:** ``circulation_alone_forward_simulation``

Parameters
""""""""""

    * **type**: Set to the ``default_forward_simulation`` alias.
    * **net**: Set the ``circulation_alone_net`` alias.
      It sets boundaries on:

        * ``proximal``: blood flow boundary condition
        * ``venous``: blood pressure boundary condition

    * Sets default parameters, magnitudes. Especially:

        * ``aorta_proximal.blood_flow`` is a periodic function needing a min and max value.
        * ``heart_rate`` parameter is introduced to set the function periodicity.

Using this alias, you will need to set:

    * **Time:**

        * ``start``
        * ``duration``

    * **Variable Initialisation:**

        * ``aorta_proximal.blood_pressure``
        * ``aorta_distal.blood_pressure``

    * **Parameters:**

        * ``heart_rate``
        * ``aorta_proximal.resistance``
        * ``venous.blood_pressure``
        * ``aorta_proximal.blood_flow.min``
        * ``aorta_proximal.blood_flow.max``


Spherical Heart Forward Simulation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* **Class:** :class:`~physioblocks.simulation.runtime.ForwardSimulation`
* **Alias name:** ``spherical_heart_forward_simulation``

Parameters
""""""""""

    * **type**: Set to the ``default_forward_simulation`` alias.
    * **net**: Set the ``spherical_heart_net`` alias.
      It sets boundaries on:

        * ``atrium``: blood flow boundary condition
        * ``venous``: blood pressure boundary condition

    * Sets default parameters, variables and magnitudes. Especially:

        * ``atrium.blood_flow`` is a periodic function needing a min and max value.
        * ``heart_rate`` parameter is introduced to set the function periodicity.

Using this alias, you will need to set:

    * **Time:**

        * ``start``
        * ``duration``

    * **Variable Initialisation:**

        * ``cavity.blood_pressure``
        * ``aorta_proximal.blood_pressure``
        * ``aorta_distal.blood_pressure``
                
    * **Parameters:**

        * ``heart_radius``
        * ``heart_thickness``
        * ``heart_contractility``
        * ``heart_rate``
        * ``venous.blood_pressure``
        * ``atrial.blood_pressure.min``
        * ``atrial.blood_pressure.max``
        * ``circulation_aorta_distal.resistance``
        * ``circulation_aorta_proximal.resistance``
        * ``cavity.dynamics.hyperelastic_cst``


Spherical Heart with Respiration Forward Simulation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* **Class:** :class:`~physioblocks.simulation.runtime.ForwardSimulation`
* **Alias name:** ``spherical_heart_with_respiration_forward_simulation``

Parameters
""""""""""

    * **type**: Set to the ``default_forward_simulation`` alias.
    * **net**: Set the ``spherical_heart_net`` alias.
      It sets boundaries on:

        * ``atrium``: blood flow boundary condition
        * ``venous``: blood pressure boundary condition

    * Sets default parameters, variables and magnitudes. Especially:

        * ``atrium.blood_flow`` is a periodic function needing a min and max value and a ``heart_rate`` parameter.
        * ``pleural.pressure`` is set to a periodic sinus function, introducing parameters ``respiration.period``, ``pleural.pressure.min``, ``pleural.pressure.max`` 

Using this alias, you will need to set:

    * **Time:**

        * ``start``
        * ``duration``

    * **Variable Initialisation:**

        * ``cavity.blood_pressure``
        * ``aorta_proximal.blood_pressure``
        * ``aorta_distal.blood_pressure``
                
    * **Parameters:**

        * ``heart_radius``
        * ``heart_thickness``
        * ``heart_contractility``
        * ``heart_rate``
        * ``venous.blood_pressure``
        * ``atrial.blood_pressure.min``
        * ``atrial.blood_pressure.max``
        * ``circulation_aorta_distal.resistance``
        * ``circulation_aorta_proximal.resistance``
        * ``cavity.dynamics.hyperelastic_cst``
        * ``respiration.period``
        * ``pleural.pressure.min``
        * ``pleural.pressure.max``