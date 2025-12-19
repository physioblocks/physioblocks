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

.. _library_configuration_net:

Net Configuration
=================

Description of available configuration item to build :class:`~physioblocks.description.nets.Net` object from a configuration file.

Net item
--------

* **Class:** :class:`~physioblocks.description.nets.Net`
* **Type name:** ``net``

Parameters
^^^^^^^^^^

    * **flux_dof_definitions**: Mapping of the flux-dof type couples used in the net.
    * **nodes**: Sequence of the nodes names.
    * **blocks**: Mapping of the blocks with their names.
    * **boundary_conditions**: Mapping of boundary conditions at Nodes.

Example
^^^^^^^

Considering the following **block-node diagram**, with boundary conditions:

    * On the flux at node A
    * On the pressure at node C

.. tikz:: Simple circulation system block-node diagram
    :include: ../../schemes/circulation_net_scheme.tex

We get the following configuration:

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
                    0: "B",
                    1: "A"
                }
            },
            "RC_2": {
                "type": "rc_block",
                "flux_type": "flow",
                "resistance": "Rb",
                "capacitance": "Cb",
                "nodes":
                {
                    0: "C",
                    1: "B"
                }
            }
        },
        "boundaries_conditions": {
            "A": [
                {
                    "type": "condition",
                    "condition_type": "flow",
                    "condition_id": "A.flow"
                }
            ],
            "C": [
                {
                    "type": "condition",
                    "condition_type": "pressure",
                    "condition_id": "C.pressure"
                }
            ]
        }
    }


Model Component Description item
--------------------------------

* **Class:** :class:`~physioblocks.description.blocks.ModelComponentDescription`
* **Type name:** ``model_description``

Parameters
^^^^^^^^^^

    * **model_type**: The name of the underlying model conponent type.
    * **submodels**: (Optional) Mapping of the :class:`~physioblocks.description.nets.ModelComponentDescription` item of the model.
    * **local parameters**: (Optional) For every local name of the model type, you can set a global name. Otherwise a default name is given.

.. note:: 

    Every model type provided in the library declares an **Alias** of the ``model_description`` with the correct ``model_type`` set.
    See the :ref:`Aliases section<library_aliases>` for model component alias documentation.

Example
^^^^^^^

For the description of a **Velocity Law** type.

.. code:: json

    {
        "type": "model_description",
        "model_type": "velocity_law",
        "pos": "global_position_name",
        "vel": "global_velocity_name",
        "acc": "global_acceleration_name",
        "time": "time",
        "submodels":
        {
            "submodel_1": {"optional submodel description goes here"},
            "submodel_2": {"optional submodel description goes here"}
        }
    }

Block Description item
----------------------

* **Class:** :class:`~physioblocks.description.blocks.BlockDescription`
* **Type name:** ``block_description``

Parameters
^^^^^^^^^^

    * **model_type**: The name of the underlying model type.
    * **nodes**: Mapping of the block local nodes ids to net's global node names.
    * **submodels**: (Optional) Mapping of the :class:`~physioblocks.description.nets.ModelComponentDescription` item of the block.
    * **local parameters**: (Optional) For every local name of the model type, you can set a global name. Otherwise a default name is given.

.. note:: 

    Every block type provided in the library declares an **Alias** of the ``block_description`` with the correct ``model_type`` set.
    See the :ref:`Aliases section<library_aliases>` for block alias documentation.

Example
^^^^^^^

For the description of a :class:`~physioblocks.library.blocks.capacitances.RCBlock` type

.. code:: json

    {
        "type": "block_description",
        "model_type": "rc_block",
        "flux_type": "flow",
        "resistance": "R",
        "capacitance": "C",
        "time": "time",
        "submodels":
        {
            "submodel_1": {"optional submodel description goes here"},
            "submodel_2": {"optional submodel description goes here"}
        },
        "nodes":
        {
            0: "global_node_0",
            1: "global_node_1"
        }
    }

.. _library_configuration_net_boundary_condition:

Boundary Condition items
------------------------

* **Class:** :class:`~physioblocks.description.nets.BoundaryCondition`
* **Type name:** ``condition``

Parameters
^^^^^^^^^^

    * **type**: ``condition``
    * **condition_type**: The flux or DOF type of the condition.
    * **condition_id**: The global name of the parameter set by the condition.

.. note::

    The ``condition_type`` used has to be defined in a ``flux_dof_definitions`` parameter of the Net.

Example
^^^^^^^

For the description of a boundary condition of a ``flow`` flux type named ``inlet_flow``: 

.. code:: json
    
    {
        "type": "condition",
        "condition_type": "flow",
        "condition_id": "inlet_flow"
    }

For the description of a boundary condition of a ``pressure`` dof type named ``p_out``: 

.. code:: json
    
    {
        "type": "condition",
        "condition_type": "pressure",
        "condition_id": "p_out"
    }
