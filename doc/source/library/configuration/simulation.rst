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

.. _library_configuration_simulation:

Simulation Configuration
========================

Description of available configuration item to build :class:`~physioblocks.simulation.runtime.AbstractSimulation` object from a configuration file.

Forward Simulation
------------------

* **Class:** :class:`~physioblocks.simulation.runtime.ForwardSimulation`
* **Type name:** ``forward_simulation``

Parameters
^^^^^^^^^^

    * **solver**: The solver configuration item
    * **net**: The net configuration item
    * **time**: The time manager item
    * **variables_magnitudes**: Mapping of the ``float`` magnitude of the state variables
    * **variables_initialization**: Mapping of the state variables quantity initialization. It accepts:
        
        * ``float``
        * ``str`` to reference a value set in the parameter mapping.
    
    * **parameters**: Mapping for the simulation parameter quantities initilisation. It accepts : 
        
        * ``float``, ``int`` or ``str`` values
        * ``str`` reference to an other value set in the parameter mapping
        * Function configuration items. See the :ref:`functions section<library_configuration_functions>`.


Example
^^^^^^^

    Example for a :class:`~physioblocks.simulation.runtime.ForwardSimulation` object using alias for its solver, net and time manager items.

.. code:: json

    {
        "type": "forward_simulation",
        "solver": {"type": "aliased_solver"},
        "net": {"type": "aliased_net"},
        "time": {"type": "aliased_time_manager"},
        "variables_initialization": {
            "variable_name_1": 1.0,
            "variable_name_2": 20.0,
            "variable_name_3": "global_parameter_name_1",
        },
        "variables_magnitudes": {
            "variable_name_1": 1.0,
            "variable_name_2": 10.0,
            "variable_name_3": 100.0,
        },
        "parameters": {
            "global_parameter_name_1": 101.0,
            "global_parameter_name_2": 1000,
            "global_parameter_name_3": "global_parameter_name_1",
            "global_parameter_name_4": {
                "type": "sum",
                "add": [
                    "global_parameter_name_1",
                    100.0
                ]
            }
        }
    }


.. _library_configuration_simulation_time:

Time manager
------------

* **Class:** :class:`~physioblocks.simulation.time_manager.TimeManager`
* **Type name:** ``time``

Parameters
^^^^^^^^^^

    * **start:** The initial value of the simulation time.
    * **duration:** The simulation duration
    * **step_size:** the time of a single simulation step.
    * **min_step:** the minimum step duration allowed.
      Useful when simulation algorithms can adapt the time step duration.

Example
^^^^^^^

The following example describes a time manager starting at 0.0 for a 10.0 seconds simulation dufration with 0.001s time steps.
the minimum allowed time increment is 0.0001s

.. code:: json

    {
        "type": "time",
        "start": 0.0,
        "duration": 10.0,
        "step_size": 1e-3,
        "min_step": 1e-4
    }

.. _library_configuration_simulation_solvers:

Solvers Configuration
=====================

Description of available configuration item to build :class:`~physioblocks.simulation.solvers.AbstractSolver` object from a configuration file.

Newton Solver
-------------

* **Class:** :class:`~physioblocks.simulation.solvers.NewtonSolver`
* **Type name:** ``newton_solver``

Parameters
^^^^^^^^^^

    * **type**: ``newton_solver``
    * **tolerance:** Relative (to each variables magnitudes) tolerance for the stop criteria of the Newton method.
    * **iteration_max:** Maximum number of iteration of the algorithm allowed to find a solution.

Example
^^^^^^^

The following example describes a newton solver and set its relative tolerance and maximum iterations.

.. code:: json

    {
        "type": "newton_solver",
        "tolerance": 1e-9,
        "iteration_max": 10
    }
