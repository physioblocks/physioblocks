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
Finally we will add **Boundary Conditions** to the **net description**, set **Functions** to update the simulation parameters, a post-process to convert the results from SI to medical units, and plot the output.

Simulation configuration items
------------------------------

**Simulation configurations** are composed of several **configuration items**:

1. **type:** simulation type
2. **simulation_name:** a name for the simulation.
3. **solver:** solver used at every simulation step
4. **time:** simulation time parameters
5. **net:** net used for the simulation
6. **state:** initial values and order of magnitudes for variables in the global system
7. **parameters:** values of the parameters in the global system
8. **update_functions:** functions updating parameters at each time step
9. **output_functions:** functions computing additional outputs to add to the results.
10. **data:** available data for pre-process and post-processes
11. **preprocesses:** processes to run before launching the simulation
12. **postprocesses:** processes to run on simulation results
13. **plots:** configuration for additional plots of the outputs
14. **simulation_options:** options depending on the simulation type

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
Two simulation types are currently available :
    
* :class:`~physioblocks.simulation.forward.ForwardSimulation`
* :class:`~physioblocks.simulation.estimation.EstimationSimulation`

For now, we will use a :class:`~physioblocks.simulation.forward.ForwardSimulation`.
At each time step, it advances the state using the model described with the :class:`~physioblocks.description.nets.Net`. 
We will learn about the :class:`~physioblocks.simulation.estimation.EstimationSimulation` later.

.. code:: json

    "type": "forward_simulation"

.. note::

    Other **simulation types** may add more objects to configure in the JSON, but the set of configuration objects presented should remain the minimal configuration needed for every type.


Simulation name
^^^^^^^^^^^^^^^

You can give a name to the simulation updating the ``simulation_name`` parameter.
The simulation name main use is to update the name of the result file.
If you do not set a name, default is ``main``.

Solver
^^^^^^

This field define the solver implementation used to run a single simulation step.

The ``type`` parameters of available solver are found in the :mod:`configuration section <physioblocks.simulation.solvers>` of the object documentation.

.. code:: json

    "solver": {
        "type": "newton_solver",
        "tolerance": 1e-9,
        "iteration_max": 2
    }

We set the two solver's parameters:

* ``tolerance`` is the stop criterion for the Newton algorithm.
* ``iteration_max`` is the maximum number of iterations allowed for the Newton algorithm.

.. note::
    
    Concerning our simple example the problem is **linear**, so a **Newton method is not adapted**.
    Still, we should be able to solve the system in two iterations, so ``iteration_max`` is set to 2.

    A better choice would have been the ``linear_solver``, but we wanted to show the Newton solver in the example because it will be useful for most nets.

Time
^^^^

The time configuration object set the range of the simulation.
It is initialized with a :class:`~physioblocks.simulation.base.SimulationRange` object.
Once again, we will find the parameters it needs to set in the :class:`configuration section <physioblocks.simulation.base.SimulationRange>` of the object description.
It needs:

1. **type:** set to ``range`` to declare a :class:`~physioblocks.simulation.base.SimulationRange` object.
2. **start:** start time value
3. **step_size:** duration of each simulation step.
4. **length:** the simulation duration.

.. code:: json

    "time": {
        "type": "range",
        "start": 0.0,
        "length": 30.0,
        "step_size": 0.001
    }

Here we set a 30 seconds simulation starting at 0.0.
The simulation gives the state each 1ms.

Simulation options
^^^^^^^^^^^^^^^^^^

The ``simulation_options`` field holds optional settings of the simulation method.
They are described in the **Configuration** section of each simulation type documentation (:class:`~physioblocks.simulation.forward.ForwardSimulation`, :class:`~physioblocks.simulation.estimation.EstimationSimulation`).

For a forward simulation, the only option is ``min_step``.
It is the minimum step size allowed for the **continuation algorithm**.

If ``min_step`` is not set, it defaults to the time ``step_size``: the continuation algorithm is disabled.

.. code:: json

    "simulation_options": {
        "min_step": 6.25e-5
    }

Here the simulation can divide a time step in parts of minimum length 62.5us (16 times smaller than the 1ms time step) before considering it can not solve the global system for the step.

Net
^^^

This field is the description of the net as seen in the :ref:`previous section <user_guide_level_2_create_net_example_1>`.

State and parameters initialization
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Both objects are dictionaries holding **quantities global names**.

* ``state`` initializes the **variables** of the global system.
  Each variable is set with a ``quantity`` configuration item holding its initial ``value`` and its order of ``magnitude``.
* ``parameters`` only holds the value.

.. code:: json

    "state": {
        "A.pressure": {"type": "quantity", "value": 8e3, "magnitude": 1e5},
        "B.pressure": {"type": "quantity", "value": 8e3, "magnitude": 1e5}
    },
    "parameters": {
        "Ca": 2.0e-10,
        "Ra": 8.0e6,
        "Cb": 1.7e-08,
        "Rb": 1.0e8
    }

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
    
    You can find the **Boundary Condition configuration item** description in the :class:`Configuration section <physioblocks.description.nets.BoundaryCondition>` of the object description.

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

Parameters of the simulation can be set with a **Function Configuration Item**.

Function configuration items have a set of arguments depending on their type.
You can find all the implemented **Configuration Functions** with their configuration in the :mod:`functions module documentation <physioblocks.library.functions>`.

The arguments can either be set to **numerical values** or to string **references to other parameters**.

There are two main categories of functions you can set to the parameters:

1. **Direct relations:** they compute the function value once. The are useful for initialization and conversions.
   They are set in the ``parameters`` dictionary.
2. **Time functions:** they are updated with the current time value at each simulation step. They are able to update a parameter over time.
   They are set in the ``update_functions`` dictionary.

As an example, we are going to update the flow entering the simple circulation net with a periodic function.

Time function configuration definition
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

We want to set the flow entering node A as a sine function:

In the :class:`configuration section <physioblocks.library.functions.trigonometric.SinusOffset>` of the :class:`~physioblocks.library.functions.trigonometric.SinusOffset`,
we find the type and the arguments needed to set the function.

.. code:: json 

    "update_functions": {
        "A.flow": {
            "type": "sinus_offset",
            "evaluation_quantities": {"time": "time"},
            "offset_value": 1.0e-3,
            "amplitude": 1.0e-3,
            "frequency": 1.25,
            "phase_shift": 0.0
        }
    }

The function configuration item is set to the quantity in the ``update_functions`` dictionary.
The ``evaluation_quantities`` field links the function arguments that change during the simulation (here the ``time`` argument) to the global name of a quantity (still ``time``, the global name of the simulation time).

Update functions can be linked to other evaluations quantities than the time, typically the state quantities.
They are still updated every time step, but with the current value of the chosen evaluation quantity.

Direct relations configuration function
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Now let's set the ``period`` of the sine instead of its ``frequency``.
We can use a **direct relation**.

In the :mod:`function module <physioblocks.library.functions>`, we find the :class:`~physioblocks.library.functions.base_operations.Product` object that performs a simple product with terms inversions.

We can use it to set our ``period`` in the ``parameters``:

1. Add a parameter for the sinus ``period`` in the parameter dictionary and set it.
2. Add a parameter that use the direct relation to compute the ``frequency``.
3. Use the parameter with its reference directly in the ``sinus_offset`` function.

.. code:: json

    "parameters": {
        "sin_period": 0.80, // Define the period
        "sin_frequency": {
            "type": "product",
            "factors": [1.0],
            "inverses": ["sin_period"]
        } // Compute the frequency
    },
    "update_functions": {
        "A.flow": {
            "type": "sinus_offset",
            "evaluation_quantities": {"time": "time"},
            "offset_value": 1.0e-3,
            "amplitude": 1.0e-3,
            "frequency": "sin_frequency", // direct reference to the parameter
            "phase_shift": 0.0
        }
    }

Alternatively, we can avoid declaring the ``sin_frequency`` parameter and use the function nested in the other function.

.. code:: json

    "parameters": {
        "sin_period": 0.80 // Set the period
    },
    "update_functions": {
        "A.flow": {
            "type": "sinus_offset",
            "evaluation_quantities": {"time": "time"},
            "offset_value": 1.0e-3,
            "amplitude": 1.0e-3,
            "frequency": {
                "type": "product",
                "factors": [1.0],
                "inverses": ["sin_period"]
            }, // Compute and set the frequency
            "phase_shift": 0.0
        }
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

If you want to save a value without updating it, you can simply use a **Watcher Function**.

Let's add a watcher on the parameter ``A.flow`` to save the function value at each time step.

From the :class:`~physioblocks.library.functions.watchers.WatchQuantity` object documentation and its :class:`configuration item description <physioblocks.library.functions.watchers.WatchQuantity>`,
we get is type name and needed arguments.

.. code:: json

    "output_functions": {
        "A.flow": {
            "type": "watch_quantity",
            "evaluation_quantities": {"quantity": "A.flow"}
        }
    }

.. note::
    
    The output key does not have to match the parameter key if you want to rename the parameter in the output file.


Compute a simple expression
^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can also compute outputs with a relation.

In the next example, we use the previously seen ``product`` function to compute the volume stored in the ``RC_1`` capacitance.

.. code:: json

    "output_functions": {
        "Ca.volume_stored": {
            "type": "product",
            "factors": ["Ca", "pressure"],
            "evaluation_quantities": {"pressure": "A.pressure"}
        }
    }

The ``pressure`` factor changes at each time step: we declare it in ``evaluation_quantities`` and set it to ``A.pressure`` to update its value at each evaluation.
The ``Ca`` factor is a reference to a parameter, its value is set once at initialization.

.. note::

    Output functions are only there to display the results and can not be used as a parameter in the simulation.

.. _user_guide_level_2_create_simulation_full_example:

Define a process
----------------

You can run processes before launching the simulation or after running the simulation on the simulation results.

A process does computation on **inputs** data and generate **outputs**.
To run a process, you will have to define:

* inputs with a list of ids of the data to process.
* outputs to define a id for the processed outputs
* parameters depending on the process you use.

You will find the available processes and their needed parameters in the :mod:`process part of the library <physioblocks.library.processes>`.

.. note::

    You can either overwrite inputs with outputs or create new data.
    Every data will be written in its own file named with the data id in the simulation folder.

You can add input data both for preprocesses and postprocesses using the ``data`` field in the simulation configuration.
Use the ``read_data`` configuration object to read a file and load the data.

.. code:: json

    {
        "data":
        {
            "input_data_a": { // input is accessed with this id.
                "type": "read_data",
                "filepath": "path/to/datafile.csv"
            }
        }
    }

.. note::
    
    The simulation results are available for the **post-processes**.
    Their data id is either the **simulation name** or ``main`` if you did not give a name to the simulation.


Add a conversion post-process
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

As an example, we are going to add a post-process that convert simulation results from SI units to medical units.
In particular, we are going to convert:

* pressure from pascals (Pa) to millimeters of mercury (mmHg)
* volumes from cube meters (m3) to milliliters (mL)

.. code:: json

    {
        "postprocesses": {
            "conversion": {
                "type": "conversion_process",
                "conversion_factors": {
                    "A.flow": 1.0e6, // from m3/s to mL/s
                    "Ca.volume_stored": 1.0e6, // from m3 to mL
                    "A.pressure": 0.00750062, // from Pa to mmHg
                    "B.pressure": 0.00750062 // from Pa to mmHg
                },
                "inputs": ["main"],
                "outputs": ["main_medical_units"]
            }
        }
    }

From the :class:`conversion process documentation <physioblocks.library.processes.computing_processes.ConvertProcess>`, we get the process parameters to initialize.
Here we set the conversion factors: for each quantity id to convert, we define a conversion factor.

We use ``main`` as an input to apply the conversion to the simulation results.

We created new data with the ``main_medical_units`` id, a csv file with the name ``main_medical_units.csv`` will be added in the simulation results folder.
An alternative would have been to use ``main`` for the output id.
In that case, the input data would have been overwritten with the result data.

**Processes are called in the order of definition**. If you overwrite data, you can only access the new data in subsequent processes.

.. note:: 

    Notice that processes inputs and outputs parameters are lists.
    You can apply the conversion process on several data defining several inputs ids with matching output ids.


Add plots to the output
-----------------------

You can configure your own plots with the ``plot`` type documented in the :mod:`process part of the library <physioblocks.library.processes>`.
It traces the selected columns (``subplots``) of the input data against the chosen ``abscissas``, each in a different subplot.

.. note:: 

    Notice that plots are processes where you don't have to define outputs.
    You can configure a plot the same way you configure a process.

The following example configures two plots, one to trace the pressures against time,
one to trace every converted value against time.

.. code:: json

    {
        "plots": {
            "pressures": {
                "type": "plot", // Plot the pressures
                "abscissas": "time",
                "subplots": ["A.pressure", "B.pressure"],
                "inputs": ["main_medical_units"]
            },
            "main_medical_units": { // Plot every data in main_medical_units against time,
                "type": "plot",     // each one in a different subplot.
                "abscissas": "time",
                "inputs": ["main_medical_units"]
            }
        }
    }

.. note:: 

    A default plot that traces all the ordinates in ``main`` against time is already configured when you use the ``default_forward_simulation`` simulation type.

The ``plots`` are always called **after** all processes.
Consequently they have access to all data defined with preprocesses and postprocesses.

.. note::
    
    In the second plot, we did not select ``subplots`` ids: every column in the data is plotted.

Plots also have a ``layout`` parameter.
If you are familiar with the plotly library, you can pass a dictionary to this parameter, it will be used with the ``update_layout`` function.
Here is the plotly documentation of the parameters you can set: https://plotly.com/python/reference/layout.

As an example, we can modify the axis title to add the units of the second plot using the layout field: 

.. code:: json

    "main_medical_units": {
        "type": "plot",
        "abscissas": "time",
        "inputs": ["main_medical_units"]
        "layout": {
            "xaxis1_title": "time (s)",
            "yaxis1_title": "pressure (mmHg)",
            "xaxis2_title": "time (s)",
            "yaxis2_title": "pressure (mmHg)",
            "xaxis3_title": "time (s)",
            "yaxis3_title": "flux (mL/s)",
            "xaxis4_title": "time (s)",
            "yaxis4_title": "pressure (mL)"
        }
    }

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
            "type": "range",
            "start": 0.0,
            "length": 30.0,
            "step_size": 0.001
        },
        "simulation_options": {
            "min_step": 6.25e-5
        },
        "net": {
            "type": "net",
            "flux_dof_definitions": {
                "flow": "pressure"
            },
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
        "state": {
            "A.pressure": {
                "type": "quantity",
                "value": 8e3,
                "magnitude": 1e5
            },
            "B.pressure": {
                "type": "quantity",
                "value": 8e3,
                "magnitude": 1e5
            }
        },
        "parameters": {
            "Ca": 2.0e-10,
            "Ra": 8.0e6,
            "Cb": 1.7e-08,
            "Rb": 1.0e8,
            "C.pressure": 1.6e3,
            "sin_period": 0.80
        },
        "update_functions": {
            "A.flow": {
                "type": "sinus_offset",
                "evaluation_quantities": {"time": "time"},
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
            "A.flow": {"type": "watch_quantity", "evaluation_quantities": {"quantity": "A.flow"}},
            "Ca.volume_stored": {
                "type": "product",
                "factors": ["Ca", "pressure"],
                "evaluation_quantities": {"pressure": "A.pressure"}
            }
        },
        // We did not define preprocesses for the simulation.
        // "preprocesses": {}
        "postprocesses": {
            "conversion": {
                "type": "conversion_process",
                "conversion_factors": {
                    "A.flow": 1.0e6, // from m3/s to mL/s
                    "Ca.volume_stored": 1.0e6, // from m3 to mL
                    "A.pressure": 0.00750062, // from Pa to mmHg
                    "B.pressure": 0.00750062 // from Pa to mmHg
                },
                "inputs": ["main"],
                "outputs": ["main_medical_units"]
            }
        },
        "plots": {
            "pressures": {
                "type": "plot",
                "abscissas": "time",
                "subplots": ["A.pressure", "B.pressure"],
                "inputs": ["main_medical_units"]
            },
            "main_medical_units": {
                "type": "plot",
                "abscissas": "time",
                "inputs": ["main_medical_units"],
                "layout": {
                    "xaxis1_title": "time (s)",
                    "yaxis1_title": "pressure (mmHg)",
                    "xaxis2_title": "time (s)",
                    "yaxis2_title": "pressure (mmHg)",
                    "xaxis3_title": "time (s)",
                    "yaxis3_title": "flux (mL/s)",
                    "xaxis4_title": "time (s)",
                    "yaxis4_title": "pressure (mL)"
                }
            }
        }
    }

When launching the simulation configuration file, here is the the second configured plot.

.. raw:: html

    <figure class="align-center">
        <iframe src="create_simulation/simple_circulation/main_medical_units.html"
                width="100%" height="1200"></iframe>
        <figcaption>
            <p><span class="caption-text">Simulations results for the simple circulation net.</span></p>
        </figcaption>
    </figure>


You may notice the configuration files can become quite long quickly for simple nets.
In the next chapter, we will learn to use aliases to **re-use** configuration objects, **pre-configure** existing simulation and overall **simplify** the configuration files.