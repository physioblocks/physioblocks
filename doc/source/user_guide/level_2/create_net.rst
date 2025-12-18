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


.. _how_to_create_net_ref:

Write a net configuration file
==============================

In this section, we will learn **how to write configuration files describing Nets**.

We will first describe the **net description syntax**, then provide example nets description.
The first example concerns how to **create Blocks, Nodes** and **link them in a Net**.
The second will introduce **Model Components**.

Net description syntax
----------------------

The **Net Descriptions** are done in JSON files and have four main components:

1. **Type:** for now, it should always be ``net``. We will detail the use of this field later in the :ref:`alias section <user_guide_level_2_aliases>`.
2. **Flux DOF couples Definitions:** a dictionary of all the **flux types names** in the net matching their **DOF type names**
3. **Nodes:** a list of the Nodes **names** in the net.
4. **Blocks:** a dictionary of all the blocks in the net with their **names**.
   The blocks are defined by their:
    
    a. **Type:** underlying model defining the **Flux and Internal Equations** of the block.
    b. **Flux Type:** flux type exchanged by the block.
       Nodes can receive *any flux type* from blocks.
       They *sum Flux by type* thus providing *one equation per type of flux* they receive.
    c. **Global Ids:** **global names** in the net of the block parameters and variable **local names**.
    d. **Connections:** for every **local node** sharing a flux in the block, their matching **global node** in the net.
    e. **Sub-models:** The **model components** enhancing the Block.

.. note:: 

    An other composant of the Nets are the **Boundary Conditions**, we will cover them in the :ref:`next section <user_guide_level_2_create_simulation>`.

As a first example, we will create a *simple circulation net* configuration file consisting in a *two state windkessel model*.

.. _user_guide_level_2_create_net_example_1 :

Simple circulation net example
------------------------------

This simple example will focus on :

    * creating **nodes**, **blocks**, link them in the **net**
    * change the **blocks** parameters name in the **global system**.

Simple circulation net model
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The model we are going to describe with a **Net** is the following:

.. tikz:: Simple circulation model scheme
    :include: ../../schemes/simple_circulation_model.tex

From a **block-node** perspective, it contains two unit :class:`~physioblocks.library.blocks.capacitances.RCBlock` and three nodes named A, B and C.

.. note::

    Notice that the fluxes are expressed **towards the output of the blocks** to match the block flux definition in the :class:`~physioblocks.library.blocks.capacitances.RCBlock` documentation.

From the :class:`~physioblocks.library.blocks.capacitances.RCBlock` documentation, we get the fluxes described for the block, and can draw the matching block-node diagram.

.. tikz:: Simple circulation system block-node diagram
    :include: ../../schemes/circulation_net_scheme.tex

We will now create a **net configuration file** step by step to represent this diagram.

Declare the net and its nodes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In an empty JSON file, we have to declare the fields:

* ``type``: Set the configuration object type we are writing to define a net
* ``flux_dof_definitions``: Set all the **flux types** and their matching **DOF type**
* ``nodes``: Set the list of node names to "A", "B" and "C".

.. code:: json

    {
        "type": "net",
        "flux_dof_definitions": {"flow": "pressure"},
        "nodes": ["A", "B", "C"]
    }

Declare blocks and add them to the Net
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Like the net, the block itself is represented with a dictionary.
To declare it as a RC block, we set its ``type`` field.
(you should be able to find the correct value to set to type for each block in the :ref:`blocks alias documentation <library_aliases_blocks>`).

We also set the block's flux type to ``flow``, the only available flux type in our net.

.. code:: json
    
    {
        "type": "rc_block",
        "flux_type": "flow"
    }

The block is then added into the ``blocks`` dictionary and named ``RC_1``.
Declare a second block named ``RC_2`` and the configuration file should now look like this:

.. code:: json

    {
        "type": "net",
        "flux_dof_definitions": {"flow": "pressure"},
        "nodes": ["A", "B", "C"],
        "blocks": {
            "RC_1": {
                "type": "rc_block",
                "flux_type": "flow"
            },
            "RC_2": {
                "type": "rc_block",
                "flux_type": "flow"
            }
        }
    }

Link nodes to blocks
^^^^^^^^^^^^^^^^^^^^

We now have a **net with three nodes** and **two blocks** but no **fluxes** are exchanged at the nodes.
We have to **link the blocks fluxes to the nodes**.

This is done adding the **flux index** in the block matching the **node names** in the ``nodes`` dictionary.
You can find the flux indexes and flux expressions in the :class:`~physioblocks.library.blocks.capacitances.RCBlock` documentation.
Here is the example for ``RC_1``:

.. code:: json
    
    {
        "type": "rc_block",
        "flux_type": "flow",
        "nodes": {
            1: "B",
            2: "A"
        }
    }

.. note::
    
    Notice the RC Block is in **opposite directions** in the documentation and in the above schematic.

If you repeat the process for ``RC_2``, the JSON file should then look like this:

.. code:: json

    {
        "type": "net",
        "flux_dof_definitions": {"flow": "pressure"},
        "nodes": ["A", "B", "C"],
        "blocks": {
            "RC_1": {
                "type": "rc_block",
                "flux_type": "flow",
                "nodes":
                {
                    1: "B",
                    2: "A"
                }
            },
            "RC_2": {
                "type": "rc_block",
                "flux_type": "flow",
                "nodes":
                {
                    1: "C",
                    2: "B"
                }
            }
        }
    }

Here you have a **complete JSON Net Description** of the model.
But the net description notations are not yet consistent with the model notations.
We can update them in the **block definitions**.

Update blocks parameters names
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Default names for the block parameters are ``$BLOCK_NAME$.$LOCAL_PARAMETER_NAME$``.
In the example, the :math:`R_A` resistance is named ``RC_1.resistance``.

You can rename them in the **Block Description**:

.. code:: json

    {
        "type": "rc_block",
        "flux_type": "flow",
        "resistance": "Ra", // Default RC_1.resistance is renamed Ra
        "capacitance": "Ca", // Default RC_1.capacitance is renamed Ca
        "nodes": {
            1: "B",
            2: "A"
        }
    }

If you also rename ``RC_2`` block parameters to match the model name, you get the following configuration file:

.. code:: json

    {
        "type": "net",
        "flux_dof_definitions": {"flow": "pressure"},
        "nodes": ["A", "B", "C"],
        "blocks": {
            "RC_1": {
                "type": "rc_block",
                "flux_type": "flow",
                "resistance": "Ra",
                "capacitance": "Ca",
                "nodes":
                {
                    1: "B",
                    2: "A"
                }
            },
            "RC_2": {
                "type": "rc_block",
                "flux_type": "flow",
                "resistance": "Rb",
                "capacitance": "Cb",
                "nodes":
                {
                    1: "C",
                    2: "B"
                }
            }
        }
    }



You may notice that we did not rename the pressures quantities to ``Pa``, ``Pb`` and ``Pc``.
Those quantities are **DOFs** created by **Global Nodes**.
Their default names are ``$NODE_NAME$.$DOF_TYPE$`` with the DOF type matching the flux type shared at the node.
For example here, the DOF has a ``pressure`` type, so it is named ``A.pressure``.

.. note::

    Notice that the ``A`` and ``B`` nodes only have **one flux** going in.
    
    This is inconsistent with our definition for the nodes where fluxes have to verify **Kirchhoff's law**.
    In the next section we will learn to add **Boundary Conditions** at nodes to complete the system.

You can now define simples nets.
If you want to skip to the :ref:`next section <user_guide_level_2_create_simulation>`, you should already be able to follow the guide using this net JSON configuration.

The next part will provide a more complete example of a net description using model components.

Cardiovascular system net example
---------------------------------

We are now going to see a more complete **Net** example to learn how to:
    
    * Enhance **Blocks Definition** with **Model Components**
    * Define **Blocks parameters and variables** that **share the same quantity**.


Cardiovascular system model
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Given the following cardiovascular model, we can schematize a **Block-Node** layout of the **Net**.

.. tikz:: Simple cardiovascular system model
    :include: ../../schemes/model_heart_circulation_0D.tex

.. tikz:: Simple cardiovascular system Block-Node diagram
    :include: ../../schemes/spherical_heart_net_scheme.tex

.. note:: 

    If you want to launch a simulation of the model, a simulation configuration using the model is in the ``reference`` folder of the PhysioBlocks package.

Every block here has an implementation in the PhysioBlocks library.
See the :ref:`library section of the API Reference <library_blocks>` for descriptions of the fluxes and internal equations shared for each block.
The **type names** to declare the blocks in configurations are described in the :ref:`alias section<library_aliases_blocks>` of the library.

.. note::

    Notice again that nodes in the net match pressures in the model : the **pressures** are the **DOFs** of the net.

Applying the assembling process described in the :ref:`previous section <user_guide_level_2_overview>`, we get **one equation per node** in the **Net**.
They provide a dynamics on the DOFs.

The other equations are the **Blocks and Model Components Internal Equations** that are concatenated to the system.

Especially, the **cavity** only defines a flux based on its deformation.
The model components attached to the cavity block are concatenating equations to the global system to *provide a dynamics on the pressure shared at the ventricle node*.

.. note::

    Notice again that the ``atrial`` and the ``venous`` nodes only have one Flux going in.
    Net definition should be completed with **Boundary Conditions** when creating a simulation configuration.


Create net, nodes and blocks
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

First, let's write the **Net JSON description** of the **Block-Node diagram** without the model components.
Following the process in the last example, we declare:

* the **net type**.
* the **fluxes-DOFs couples** (for the cardiovascular system, we declare a ``"blood_flow": "blood_pressure"`` couple)
* the **nodes names**.
* We refer to the documentation in the :ref:`Llbrary <library>` to:

    * Declare the needed **block types**.
    * Link the **local node indexes** in the blocks to the **global nodes names** in the net.

The JSON file should look like this:

.. code:: json

    {
        "type": "net",
        "flux_dof_definitions": {"blood_flow": "blood_pressure"},
        "nodes": [
            "cavity",
            "atrial",
            "proximal",
            "distal",
            "venous"
        ],
        "blocks": {
            "cavity": {
                "type": "spherical_cavity_block",
                "flux_type": "blood_flow",
                "nodes": {
                    "1": "cavity"
                }
            },
            "valve_atrium": {
                "type": "valve_rl_block",
                "flux_type": "blood_flow",
                "backward_conductance": "conductance_iso",
                "nodes": {
                    "1": "atrial",
                    "2": "cavity"
                }
            },
            "valve_arterial": {
                "type": "valve_rl_block",
                "flux_type": "blood_flow",
                "backward_conductance": "conductance_iso",
                "nodes": {
                    "1": "cavity",
                    "2": "proximal"
                }
            },
            "capacitance_valve": {
                "type": "c_block",
                "flux_type": "blood_flow",
                "nodes": {
                    "1": "cavity"
                }
            },
            "circulation_aorta_proximal": {
                "type": "rc_block",
                "flux_type": "blood_flow",
                "nodes": {
                    "1": "distal",
                    "2": "proximal"
                }
            },
            "circulation_aorta_distal": {
                "type": "rc_block",
                "flux_type": "blood_flow",
                "nodes": {
                    "1": "venous",
                    "2": "distal"
                }
            }
        }
    }

Here we kept default block names for parameters except for the ``backward_conductance`` of both valves.

Notice that we give them the **same id** in both **valve blocks**. 
This will result in both ``backward_conductance`` sharing the **same quantity** (:math:`K_{iso}` in the model).

Add model components to blocks
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Based on the :class:`~physioblocks.library.blocks.cavity.SphericalCavityBlock` object documentation, notice the cavity contributes a flux that only depends on the cavity **volume variation** based on ``disp`` (:math:`y` in the model).
We could consider ``disp`` as a parameter and give it a value that varies over time.

But here, we will add **model components** to the cavity to enhance the block with a dynamics on :math:`y` related to the pressure in the Ventricle (ie. the DOF at node ``ventricle`` or :math:`P_V` in the model).

To add a model component to a block, we update the ``submodels`` dictionary of the block.
Every model component is defined with a dictionary where the ``type`` field is set to the wanted model component type.

You will find the description of the model component internal equations in the :ref:`library<library_model_components>` and their type names in the :ref:`alias section<library_aliases_model_components>`.

For our cardiovascular system net, the cavity with sub-models gives:

.. code:: json

    {
        "type": "spherical_cavity_block",
        "flux_type": "blood_flow",
        "submodels": {
            "dynamics": {
                "type": "spherical_dynamics_hht_model",
            },
            "velocity_law": {
                "type": "velocity_law_hht_model",
            },
            "rheology": {
                "type": "rheology_fiber_additive_model",
                "submodels": {
                    "active_law": {
                        "type": "active_law_macro_huxley_two_moments_model",
                    }
                }
            }
        },
        "nodes": {
            "1": "cavity"
        }
    }


Notice that the ``active law`` is itself a submodel of the ``rheology`` model component. 
You can add model components to any block or other model components updating its ``submodels`` entry.

In fact, since it only concatenates internal equations to the global system, you could perfectly add the same model components to *any block sub-models* field and obtain the same results.

Still, the goal here is to have a clear layout for the net while also having *consistent default parameters names*.
It will also allow us to simplify the net using :ref:`aliases <user_guide_level_2_aliases>` as we will see later.

Shared quantities for parameters and variables 
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

At this point, the cavity will still not work as expected.
Here every model component defines its *own parameters and variables*.

We have to make the model component use the **same quantities** for the variables and parameters that are shared.
This is done using **common names** for the parameters and variables across blocks and model components.

For example here, ``disp`` the cavity deformation (:math:`y` in the cavity model) has to be the **same quantity** in both the cavity, the spherical dynamics, the velocity law and the rheology.

Let's complete the cavity definition:

.. code:: json

    {
        "type": "spherical_cavity_block",
        "flux_type": "blood_flow",
        "disp": "cavity.dynamics.disp",
        "radius": "heart_radius",
        "thickness": "heart_thickness",
        "submodels": {
            "dynamics": {
                "type": "spherical_dynamics_hht_model",
                "fib_deform": "cavity.rheology.fib_deform",
                "pressure": "cavity.blood_pressure",
                "pressure_external": "pleural.pressure",
                "vel": "cavity.velocity_law.vel",
                "radius": "heart_radius",
                "thickness": "heart_thickness",
                "series_stiffness": "cavity.rheology.series_stiffness"
            },
            "velocity_law": {
                "type": "velocity_law_hht_model",
                "disp": "cavity.dynamics.disp"
            },
            "rheology": {
                "type": "rheology_fiber_additive_model",
                "disp": "cavity.dynamics.disp",
                "active_tension_discr": "cavity.rheology.active_law.active_tension_discr",
                "radius": "heart_radius",
                "submodels": {
                    "active_law": {
                        "type": "active_law_macro_huxley_two_moments_model",
                        "fib_deform": "cavity.rheology.fib_deform",
                        "contractility": "heart_contractility"
                    }
                }
            }
        },
        "nodes": {
            "1": "cavity"
        }
    }

The next array summarizes every **quantity global name** matching its **local names** as defined in the model components and blocks.

==================================================== =============== =================== ============= ===================== =====================
Global Name                                          cavity          dynamics            velocity_law  rheology              active_law
==================================================== =============== =================== ============= ===================== =====================
**cavity.blood_pressure**                                            pressure
pleural.pressure                                                     pressure_external
heart_radius                                         radius          radius                            radius
heart_thickness                                      thickness       thickness 
**cavity.dynamics.disp**                             disp            disp                disp          disp
**cavity.velocity_law.vel**                                          vel                 vel           
**cavity.rheology.fib_deform**                                                                         fib_deform            fib_deform                       
**cavity.rheology.series_stiffness**                                 series_stiffness                  series_stiffness
**cavity.rheology.active_law.active_tension_discr**                                                    active_tension_discr  active_tension_discr
heart_contractility                                                                                                          contractility
==================================================== =============== =================== ============= ===================== =====================

The entries are in bold when the **global name** is the **default name** of the parameter, variable or DOFs, the origin of which is indicated as the first part of the quantity name.

.. note::

    ``cavity.blood_pressure`` is a DOF defined in the net: the pressure point matching :math:`P_V` in the model.
    
    In our net, the pleural pressure is a parameter, but we could increase the net to make it a DOF and provide a dynamics on it. 

Full net description
^^^^^^^^^^^^^^^^^^^^

Finally, the full JSON net description for our model gives: 

.. code:: json

    {
        "type": "net",
        "flux_dof_definitions": {"blood_flow": "blood_pressure"},
        "nodes": [
            "cavity",
            "atrial",
            "proximal",
            "distal",
            "venous"
        ],
        "blocks": {
            "cavity": {
                "type": "spherical_cavity_block",
                "flux_type": "blood_flow",
                "disp": "cavity.dynamics.disp",
                "radius": "heart_radius",
                "thickness": "heart_thickness",
                "submodels": {
                    "dynamics": {
                        "type": "spherical_dynamics_hht_model",
                        "fib_deform": "cavity.rheology.fib_deform",
                        "pressure": "cavity.blood_pressure",
                        "pressure_external": "pleural.pressure",
                        "vel": "cavity.velocity_law.vel",
                        "radius": "heart_radius",
                        "thickness": "heart_thickness",
                        "series_stiffness": "cavity.rheology.series_stiffness"
                    },
                    "velocity_law": {
                        "type": "velocity_law_hht_model",
                        "disp": "cavity.dynamics.disp"
                    },
                    "rheology": {
                        "type": "rheology_fiber_additive_model",
                        "disp": "cavity.dynamics.disp",
                        "active_tension_discr": "cavity.rheology.active_law.active_tension_discr",
                        "radius": "heart_radius",
                        "submodels": {
                            "active_law": {
                                "type": "active_law_macro_huxley_two_moments_model",
                                "fib_deform": "cavity.rheology.fib_deform",
                                "contractility": "heart_contractility"
                            }
                        }
                    }
                },
                "nodes": {
                    "1": "cavity"
                }
            },
            "valve_atrium": {
                "type": "valve_rl_block",
                "flux_type": "blood_flow",
                "backward_conductance": "conductance_iso",
                "nodes": {
                    "1": "atrial",
                    "2": "cavity"
                }
            },
            "valve_arterial": {
                "type": "valve_rl_block",
                "flux_type": "blood_flow",
                "backward_conductance": "conductance_iso",
                "nodes": {
                    "1": "cavity",
                    "2": "proximal"
                }
            },
            "capacitance_valve": {
                "type": "c_block",
                "flux_type": "blood_flow",
                "nodes": {
                    "1": "cavity"
                }
            },
            "circulation_aorta_proximal": {
                "type": "rc_block",
                "flux_type": "blood_flow",
                "nodes": {
                    "1": "proximal"
                    "2": "distal",
                }
            },
            "circulation_aorta_distal": {
                "type": "rc_block",
                "flux_type": "blood_flow",
                "nodes": {
                    "1": "venous",
                    "2": "distal"
                }
            }
        }
    }

Now that we know how to define a net with a JSON file, we are going to see **how to write a simulation configuration** to run a simulation based on a net description.

