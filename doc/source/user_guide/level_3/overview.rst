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

Overview
========

In this section, we will go over the main PhysioBlocks principles needed to write **Blocks**.

We will first learn about the :class:`~physioblocks.computing.models.Block` and :class:`~physioblocks.description.blocks.BlockDescription` objects and their roles.
We will then present the main **Expressions** that a :class:`~physioblocks.computing.models.Block` object defines.
Finally, we will go through the main differences between **Blocks** and **ModelComponents**

Block vs BlockDescription
--------------------------

:class:`~physioblocks.computing.models.Block` and :class:`~physioblocks.description.blocks.BlockDescription` are two different PhysioBlocks objects.
The combination of the two allows to use blocks in nets.

The :class:`~physioblocks.computing.models.Block` are simple objects, they allow to compute quantities. They :

  1. Declare the **Quantities** they need to perform computations.
  2. Declare the functions to compute the **Fluxes**, **Internal Equations** and **Saved Quantities** from those quantities.


The :class:`~physioblocks.description.blocks.BlockDescription` are generic objects that provide the interface between a block and the net. They:

  1. Hold a reference to a specific :class:`~physioblocks.computing.models.Block` instance.
  2. Hold the **global name** in the net for every **parameter local name** in the block.
  3. Hold the **flux descriptions** and match them with a **global node** in the net.
  4. Extend the block definitions holding model component descriptions.

.. note::

  You will only have to write :class:`~physioblocks.computing.models.Block` implementations, the :class:`~physioblocks.description.blocks.BlockDescription` are generic and already implemented in PhysioBlocks.
  When using the block in a net, it will be associated with a :class:`~physioblocks.description.blocks.BlockDescription`.

Block Definition
----------------

Any :class:`~physioblocks.computing.models.Block` implementation define functions to compute:
    
  * **Fluxes:** terms summed with other fluxes of the same type at the node of the net.
    They are always **expressed toward the outlet of the block**.
    They are always **discretized with a mid-point time scheme** to ensure stability and consistency in the coupling between blocks.
  * **Internal Equations:** (optional) Equations concatenated to the global system.
    They are expressed in a **residual form**.
  * **Saved Quantities:** (Optional) Additional quantities computation **to output in a result file** along with the variables.
    They are computed once at each time step.
  * Fluxes and internal equations **partial derivatives** along every possible variable.

If we take a closer look at this last point, it means that you should define partial derivatives along:

  * **DOFs** quantities of the block
  * **internal variables** quantities of the block
  * any other term that could be a variable in the global system (ie. potential DOFs and internal variables of other blocks)

.. note::

  Before launching a simulation, PhysioBlocks will build the global system based on the layout of the net and its boundary conditions.
  Every expressions you define will not necessarily be used in the system.

  However, block implementations you write should be exhaustive to obtain modular blocks.

ModelComponents and ModelComponentDescription
---------------------------------------------

:class:`~physioblocks.computing.models.ModelComponent` and :class:`~physioblocks.description.blocks.ModelComponentDescription` objects are :class:`~physioblocks.computing.models.Block` and :class:`~physioblocks.description.blocks.BlockDescription` base definitions.
Everything that we say here about blocks is also true for model components, except:

  * Model components do not define fluxes.
  * :class:`~physioblocks.description.blocks.ModelComponentDescription` and :class:`~physioblocks.description.blocks.BlockDescription` objects can only hold :class:`~physioblocks.description.blocks.ModelComponentDescription` sub-models, never a :class:`~physioblocks.description.blocks.BlockDescription` sub-model.

.. note::

  Everything done with model components sub-models can easily be done directly with block internal equations. 
  However, we define model components for modularity purposes.
  It allows to re-use internal equations with different blocks.

Since the :class:`~physioblocks.computing.models.ModelComponent` definition are exactly the same as :class:`~physioblocks.computing.models.Block` definitions minus the flux definition, we will not detail them in the next part.
However, you can find some examples in the PhysioBlocks package ``physioblocks/library/model_components`` module.

In the next part, we will see how to write a :class:`~physioblocks.computing.models.Block` implementation along with an example.