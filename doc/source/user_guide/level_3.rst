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

.. _user_guide_level_3 :

*******
Level 3
*******

In this chapter will learn how to write new **Blocks** and **ModelComponents**.

We will first present the PhysioBlocks objects and main concepts for writing **Fluxes**, **Internal Equations** and **Saved Quantities**.
We will then use the :class:`~physioblocks.library.blocks.capacitances.RCRBlock` implemented in the PhysioBlocks library to provide an example for each object.
Finally, we will see how to make the block available for use in **Nets and Simulation Configurations**.

.. toctree::
   :glob:
   :maxdepth: 2

   level_3/overview
   level_3/block_definition
   level_3/block_configuration
   level_3/block_test