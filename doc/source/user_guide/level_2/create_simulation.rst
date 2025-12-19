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

.. _user_guide_level_2_create_simulation:

Write a simulation configuration file
=====================================

This section details how to create a **simulation configuration** that uses a **net description**.

First, we are going to give more details on the **Configuration Objects** needed in the **Simulation Configuration**.
We will then provide an example configuration for the **simple circulation net** created in the :ref:`previous section <user_guide_level_2_create_net_example_1>`.
Finally we will add **Boundary Conditions** to the **net description** and set **Functions** to update the simulation parameters.

Simulation configuration items
------------------------------

**Simulation configurations** are composed of several **configuration items**:

    1. **type:** simulation type
    2. **solver:** solver used at every simulation step
    3. **time:** simulation time parameters
    4. **net:** net used for the simulation
    5. **variable_initialization:** initial values for variables in the global system
    6. **variables_magnitudes:** order of magnitudes for each variable
    7. **parameters:** values of the parameters in the global system

.. note::

    If you look at any reference simulations provided with the PhysioBlocks package, you may be surprised to not see all these configuration objects or that some objects have incomplete definition.
    It is because the reference files use **Aliases** to simplify the configuration.
    
    We will learn to use **Aliases** in the :ref:`next section<user_guide_level_2_aliases>`

We are going to see how to set up those configuration item with an example.

Simulation configuration example for the simple circulation net
---------------------------------------------------------------

In this example, we are going to write a configuration file to run a **Forward Simulation** with the net
(See :ref:`previous section <user_guide_level_2_create_net_example_1>` for the description of the net).
We will set a **Solver** that uses a **Newton method** for every time step of the simulation.
For now, every parameter will be a constant.

.. note::

    Any of the following configuration objects can be placed in any order in the configuration file.

Simulation type
^^^^^^^^^^^^^^^

This field defines the method used for the simulation.
For now, only :class:`~physioblocks.simulation.runtime.ForwardSimulation` is provided in the library.
You can find its ``type`` in the :ref:`configuration section <library_configuration_simulation>` of the library.

.. code:: json

    "type": "forward_simulation"

.. note::

    Other **simulation types** may add more objects to configure in the JSON, but the set of configuration objects presented should remain the minimal configuration needed for every type.

Solver
^^^^^^

This field define the solver implementation used to run a single simulation step.

For now, only the :class:`~physioblocks.simulation.solvers.NewtonSolver` object is implemented in the current API.
Its ``type`` is found in the :ref:`configuration section <library_configuration_simulation_solvers>` of the library

.. code:: json

    "solver": {
        "type": "newton_solver",
        "tolerance": 1e-9,
        "iteration_max": 2
    }

New solvers can use different parameters and will be documented in the :ref:`configuration section <library_configuration_simulation_solvers>` of the library.
In this case, we set two parameters to the solver:

* ``tolerance`` is the stop criterion for the Newton algorithm.
* ``iteration_max`` is the maximum number of iterations allowed for the Newton algorithm.

.. note::
    
    Concerning our simple example the problem is **linear**, so a **Newton method is not adapted**.
    Still, we should be able to solve the system in two iterations, so ``iteration_max`` is set to 2.


Time
^^^^

The time configuration object defines the simulation's :class:`~physioblocks.simulation.time_manager.TimeManager` object.
Once again, we will find the parameters it needs to set in the :ref:`configuration section <library_configuration_simulation_time>` of the library.
It needs :

    1. **type:** set to ``time`` to declare a :class:`~physioblocks.simulation.time_manager.TimeManager` object.
    2. **start:** start time value
    3. **step_size:** duration of each simulation step.
    4. **min_step:** minimal step size value when dividing a single simulation step into multiple steps.

.. code:: json

    "time": {
        "type": "time",
        "start": 0.0,
        "duration": 30.0,
        "step_size": 0.001,
        "min_step": 6.25e-5
    }

Here we set a 30 seconds simulation starting at 0.0.
The simulation gives the state each 1ms and can divide a time step in parts of minimum lenght 62.5us before considering it can not solve the global system for the step.

Net
^^^

This field is the description of the net as seen in the :ref:`previous section <user_guide_level_2_create_net_example_1>`.

Variables, variable magnitude and parameters initialization
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

All those objects are dictionaries holding **quantities global names** with their value.

.. code:: json

    "variables_initialization": {
        "A.pressure":8e3,
        "B.pressure":8e3
    },
    "variables_magnitudes": {
        "A.pressure":1e5,
        "B.pressure":1e5
    },
    "parameters": {
            "Ca": 2.0e-10,
            "Ra": 8.0e6,
            "Cb": 1.7e-08,     
            "Rb": 1.0e8,
        }
    

.. note:: 

    It can be tedious to find every quantities that needs to be initialized from the net descriptions.
    We will soon add a small module to generate needed parameters and variables keys with an uninitialized values for a given net description.

You may notice several problems with the Net and its parameters:

    * There is no initial value for the **pressure at node C**.
    * There is only **one flow** coming in nodes A and in node C, so **Kirchhoff's laws** are not satisfied at those node.

In the next section, we will add **Boundary Conditions** on the net, thus completing the example.

Add Boundary conditions on nets
-------------------------------

Boundary conditions configuration item
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

We can add **Boundary Conditions** on the net in a dictionary labeled ``"boundaries_conditions"``.
The keys of the dictionary should be the **node names** where we want to prescribe a **Boundary Condition**, and the value is a **Boundary Condition configuration item** composed of:

    * **type:** set to ``condition`` to declare a **Boundary Condition** configuration object.
    * **condition_type:** set either to a **flux type** to declare a condition on the **flux** entering the node, or to a **DOF type** to set a condition on the dof.
    * **condition_id:** name for the quantity in the parameters.

.. note::
    
    You can find the **Boundary Condition configuration item** description in the :ref:`Configuration section<library_configuration_net_boundary_condition>` of the library

When declaring a condition on the DOF, it becomes a parameter in the global system.
As a result, *the sum of fluxes at the node is not added to the global system*.

When setting a condition on the flux, the flux quantity entering the node has to be set.
The flux value given in the parameters is *summed with the fluxes coming from the blocks* at the node.

We are now going to add two boundary conditions on the flow and the pressure in the example.

Boundary conditions in the simple circulation net example
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

First, let's add a boundary Condition on the **pressure** at node C.

.. code:: json

    "boundaries_conditions": {
        "C": [
            {
                "type": "condition",
                "condition_type": "pressure",
                "condition_id": "C.pressure"
            }
        ]
    }

The ``C.pressure`` value can now be added in the ``parameters`` dictionary.

.. code:: json

    "parameters": {
            "Ca": 2.0e-10,
            "Ra": 8.0e6,
            "Cb": 1.7e-08,     
            "Rb": 1.0e8,
            "C.pressure": 1.6e3
        }

Here we set it to a constant.

.. note::

    Notice that the boundary conditions configuration items consists of a list.
    Since nodes can have fluxes of different types, you can define conditions on *several Fluxes or DOFs types at the same node*.

Now let's add a flow boundary condition on node A:

.. code:: json

    "boundaries_conditions": {
        "C": [
            {
                "type": "condition",
                "condition_type": "pressure",
                "condition_id": "C.pressure"
            }
        ],
        "A": [
            {
                "type": "condition",
                "condition_type": "flow",
                "condition_id": "A.flow"
            }
        ]
    }

.. note:: 

    Notice that condition types match **Flux-Dof couples** definitions of the net.

Now that we declared a boundary condition on the flow at **node A**, we can set its value in ``parameters`` using the identifier ``A.flow``.

In the next part we are going to declare a function in the configuration and as an example, set a function to update the flow value entering **Node A**.

Define Functions in the simulation configuration
------------------------------------------------

Function configuration item
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Every parameter of the simulation can be set to a **Function Configuration Item**.

Function configuration items have a set of arguments depending on their type.
You can find all the implemented **Configuration Functions** in the :ref:`functions section <library_functions>`, and **Configuration Item** description in the :ref:`configuration section <library_configuration_functions>` of the library.

The arguments can either be set to **numerical values** or to string **references to other parameters**.

There are two main categories of functions you can set to the parameters:

    1. **Direct relations:** they compute the function value once. The are useful for initialization and conversions.
    2. **Time functions:** they are updated with the current time value at each simulation step. They are able to update a parameter over time.

As an example, we are going to update the flow entering the simple circulation net with a periodic function.

Time function configuration definition
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

We want to set the flow entering node A as a sine function:

In the :ref:`configuration section <library_configuration_functions_sinus>` of the library, we find the type and the arguments needed to set a :class:`~physioblocks.library.functions.trigonometric.SinusOffset` function.

.. code:: json 

    "A.flow": {
        "type": "sinus_offset",
        "offset_value": 1.0e-3,
        "amplitude": 1.0e-3,
        "frequency": 1.25,
        "phase_shift": 0.0
    }

The function configuration item is directly set to the quantity in the ``parameters`` dictionary.

Direct relations configuration function
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Now let's set the ``period`` of the sine instead of its ``frequency`` in the parameter dictionary.
We can use a **direct relation**.

In the :ref:`function configuration section <library_functions>`, we find the :class:`~physioblocks.library.functions.base_operations.Product` object that performs a simple product with terms inversions.
Its configuration item description can be found in the :ref:`configuration section <library_configuration_functions>` of the library. 

We can use it to set our ``period`` in the ``parameters``:

1. Add a parameter for the sinus ``period`` in the parameter dictionary and set it.
2. Add a parameter that use the direct relation to compute the ``frequency``.
3. Use the parameter with its reference directly in the ``sinus_offset`` function.

.. code:: json

    "sin_period": 0.80, // Define the period
    "sin_frequency": {
        "type": "product",
        "factors": [1.0],
        "inverses": ["sin_period"]
    }, // Compute the frequency
    "A.flow": {
        "type": "sinus_offset",
        "offset_value": 1.0e-3,
        "amplitude": 1.0e-3,
        "frequency": "sin_frequency", // direct reference to the parameter
        "phase_shift": 0.0
    }

Alternatively, we can avoid declaring the ``sin_frequency`` parameter and use the function nested in the other function.

.. code:: json

    "sin_period": 0.80, // Set the period
    "A.flow": {
        "type": "sinus_offset",
        "offset_value": 1.0e-3,
        "amplitude": 1.0e-3,
        "frequency": {
            "type": "product",
            "factors": [1.0],
            "inverses": ["sin_period"]
        }, // Compute and set the frequency
        "phase_shift": 0.0
    }

.. note::

    The ``A.flow`` parameter is updated at the *beginning of every time step*, but the ``sin_frequency`` is only *set once at initialization*.


This example is quite simple but the functionality opens a lot of possibilities to define parameters in the configuration files.

Now that we know how to use functions in the configuration, we are going to use them to output specific quantities in our results along with the variables values at each time steps.

Define output functions
-----------------------

**Quantities** written in the output file for each time step the simulation are:

    * **Variables** in the global system.
    * **Saved Quantities** in the **Blocks** and **Model Components** (if any).

.. note::

    We will learn more about **Saved Quantities** of the **Blocks** and **Model Components** in the :ref:`next chapter<user_guide_level_3_block_definition>` of the user guide.

If you want to add other quantities to your saved results, you can configure functions in the ``output_functions`` field.

The functions defined in this dictionary are updated every time step and their values saved along with other results of the simulation.

Add a watcher function on a quantity
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you want to save a value without modifying it, you can simply use a **Watcher Function**.

Let's add a watcher on the parameter ``C.flow`` to save the function value at each time step.

From the :class:`~physioblocks.library.functions.watchers.WatchQuantity` object documentation and its :ref:`configuration item description <library_configuration_functions_watchers>`,
we get is type name and needed arguments.

.. code:: json

    "output_functions": {
        "A.flow": {"type": "watch_quantity", "quantity": "A.flow"}
    }

.. note::
    
    The output key does not have to match the parameter key if you want to rename the parameter in the output file.


Add a direct relation
^^^^^^^^^^^^^^^^^^^^^

You can also compute outputs with a direct relation.

In the next example, we use the previously seen ``product`` function to compute the volume store in the ``RC_1`` capacitance.

.. code:: json

    "output_functions": {
        "Ca.volume_stored": {"type": "product", "factors": ["Ca", "A.pressure"]}
    }

We emphasize that even if it is a direct relation, since it configured in ``output_functions``, it is computed at each simulation time step.

.. note::

    Output functions are only there to display the results and can not be used as a parameter in the simulation.

.. _user_guide_level_2_create_simulation_full_example:

Complete configuration file example for the simple circulation net
------------------------------------------------------------------

Here is the complete configuration file for our example net:

.. code:: json

    {
        "type": "forward_simulation",
        "solver": {
            "type": "newton_solver",
            "tolerance": 1e-9,
            "iteration_max": 2
        },
        "time": {
            "type": "time",
            "start": 0.0,
            "duration": 30.0,
            "step_size": 0.001,
            "min_step": 6.25e-5
        },
        "flux_dof_definitions": {
            "flow": "pressure"
        },
        "net": {
            "type": "net",
            "nodes": ["A", "B", "C"],
            "blocks": {
                "RC_1": {
                    "type": "rc_block",
                    "flux_type": "flow",
                    "resistance": "Ra",
                    "capacitance": "Ca",
                    "nodes":
                    {
                        "1": "B",
                        "2": "A"
                    }
                },
                "RC_2": {
                    "type": "rc_block",
                    "flux_type": "flow",
                    "resistance": "Rb",
                    "capacitance": "Cb",
                    "nodes":
                    {
                        "1": "C",
                        "2": "B"
                    }
                }
            },
            "boundaries_conditions": {
                "C": [
                    {
                        "type": "condition",
                        "condition_type": "pressure",
                        "condition_id": "C.pressure"
                    }
                ],
                "A": [
                    {
                        "type": "condition",
                        "condition_type": "flow",
                        "condition_id": "A.flow"
                    }
                ]
            }
        },
        "variables_initialization": {
            "A.pressure":8e3,
            "B.pressure":8e3
        },
        "variables_magnitudes": {
            "A.pressure":1e5,
            "B.pressure":1e5
        },
        "parameters": {
            "Ca": 2.0e-10,
            "Ra": 8.0e6,
            "Cb": 1.7e-08,     
            "Rb": 1.0e8,
            "C.pressure": 1.6e3,
            "sin_period": 0.80,
            "A.flow": {
                "type": "sinus_offset",
                "offset_value": 1.0e-3,
                "amplitude": 1.0e-3,
                "frequency": {
                        "type": "product",
                        "factors": [1.0],
                        "inverses": ["sin_period"]
                    },
                "phase_shift": 0.0
            }
        },
        "output_functions":{
            "A.flow": {"type": "watch_quantity", "quantity": "A.flow"},
            "Ca.volume_stored": {"type": "product", "factors": ["Ca", "A.pressure"]}
        }
    }

The configuration files can become quite long quickly for simple nets.
In the next chapter, we will learn to use aliases to **re-use** configuration objects, **pre-configure** existing simulation and overall **simplify** the configuration files.