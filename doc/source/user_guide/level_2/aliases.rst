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

.. _user_guide_level_2_aliases:

Configuration aliases
=====================

The **Aliases** role is to simplify the configuration files enabling to:

* Define re-usable configuration items
* Pre-configure parameters

In this section, we will first detail how to create an **Alias**.
Then we will go through both use cases with an example to simplify the configuration for the example we presented in the :ref:`previous section <user_guide_level_2_create_simulation_full_example>`.

Create a configuration alias
----------------------------

Any **configuration item** can be defined in its own JSON file and will be reusable in **any other configuration**.
To create a configuration alias for any configuration item, you have to:

    1. Write a JSON configuration file describing the item.
    2. Save the file in the ``user_aliases`` folder of your configured ``launcher_directory`` (see :ref:`configure launcher section <user_guide_level_1_launcher_configuration>`).
 
Every alias in the folder (and in sub-folders recursivly) will be loaded when you launch a simulation from this ``launcher_directory``.

.. warning:: 

    File names have to be unique across the alias folder and its sub-folders recursivly.

To **use the alias in any other configuration**, use the filename (without the extension) in the ``type`` of the object you want to initialise with your alias.

You will then be able to:

* **Override** parameters set in the alias
* **Complete** the aliased item with new parameters.

As an example, we are going to use **aliases** to simplify the circulation simulation configuration.

.. note::
    
    Alternatively, you can save an alias anywhere on your computer.
    In this case, instead of its name, use its file full path (with extension) in the ``type`` field.
    It will only be loaded when it is called.

Use re-usable configuration items
---------------------------------

You already used aliased configuration items in the net description.
``rc_block`` configuration item types are aliases for generic :class:`~physioblocks.description.BlockDescription` where:
    
    * the ``model_type`` is set to ``rc_block``.
    * the ``rc_block`` time parameter is renamed to match the global simulation time name.

You can find this alias and all other **provided aliases descriptions** in the :ref:`aliases section<library_aliases>` of the library.

Now let's use another provided alias for to set the simulation type.

Use an alias for the simulation type
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In the :ref:`simulation aliases section<library_aliases_simulation>` of the library, you will find the ``default_forward_simulation`` alias.
This alias set simulation type to ``forward_simulation`` and sets other default parameters.

Let's use it in our configuration file.

.. code:: json

    {
        "type": "default_forward_simulation"
    }

Using the alias in our configuration file sets the:

    * **Solver:** the default solver use a **Newton method**. 
    * **Time:** we use a default time description that sets the step size and the minimum step size.

Consequently, if we want to match our previous configuration, we still have to set some parameters in the simulation configuration.

.. code:: json

    {
        "type": "default_forward_simulation",
        "solver": {
            "iteration_max": 2
        },
        "time": {
            "start": 0.0,
            "duration": 30.0
        }
    }

Notice we only update the values for the parameters that we want to modify or add to the aliased simulation.

.. note:: 

    We did not set the ``type`` field for the ``solver`` and the ``time``.
    It would *overwrite the entire item* and lose alias default values.

Now that we used aliases provided in the PhysioBlocks package, let's write ou own aliases.

Define an alias for the net
^^^^^^^^^^^^^^^^^^^^^^^^^^^

The net we defined in the configuration file could be re-used in other simulations with different boundary conditions.

We can create an alias for *the net without boundary conditions*.
We will then update the alias with new boundary conditions in the simulation configuration.

First, save the net description in a separate JSON file without the boundary conditions.
Your file should contain: 

.. code:: json

    {
        "type": "net",
        "nodes": ["A", "B", "C"],
        "flux_dof_definitions": {"flow": "pressure"},
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
        }
    }

Save the file in your launcher directory ``user_aliases`` folder and name it ``simple_circulation_net_example.json``.
Then, you can use the in the simulation configuration and update the boundaries:

.. code:: json

    net: {
        "type": "simple_circulation_net_example", // we use the alias
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
    }


Full simple circulation simulation example 
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

At this point, the full configuration file should look like this:

.. code:: json

    {
        "type": "default_forward_simulation",
        "solver": {
            "iteration_max": 2
        },
        "time": {
            "start": 0.0,
            "duration": 30.0
        },
        "flux_dof_definitions": {
            "flow": "pressure"
        },
        "net": {
            "type": "simple_circulation_net_example",
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

We are going to further simplify the configuration file using aliases to pre-configure some simulation parameters.

Pre-configure parameters
------------------------

The configuration file we just defined can also be an alias.
We just have to save it in the ``user_aliases`` folder of the launcher directory and use it in any configuration file.

Let's name it ``simple_circulation_net_example_forward_simulation`` and use it in a new configuration file.

.. code:: json

    {
        "type": "simple_circulation_net_example_forward_simulation",
        "time": {
            "duration": 30.0
        },
        "variables_initialization": {
            "A.pressure":8e3,
            "B.pressure":8e3
        },
        "parameters": {
            "Ra": 8.0e6,
            "Rb": 1.0e8,
            "C.pressure": 1.6e3
        }
    }

Here we have the same simulation configuration as before using the alias.

It is up to you to determine which parameters of the configuration should be set by writing them in the higher configuration file.
Here we will only ask for duration, input pressures, resistances and the input flow.
Other parameters are set from the alias.

.. note::

    Notice that it also hide a lot of configuration items (the net, solver, variable magnitudes) in the higher configuration file.

Finally, you can set an alias for a simulation configuration an derive a lot of simple small configuration files from it.
Composing aliases you have a lot of possibilities to define configuration items and re-use them.
If you look into the ``physioblocks/library/aliases`` folder, you will find more examples, documented in the :ref:`alias section <library_aliases>` of the library.

This concludes level 2 user guide documentation.
The next chapter is dedicated to Level 3 use cases. 
We will see how to write blocks and model components in that can be used with PhysioBlocks.
