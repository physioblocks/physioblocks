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

.. _user_guide_level_2_overview:

Overview
========

To launch a simulation, most of the time you will need two configuration files:

    * the **Net Description**
    * the **Simulation Configuration** based on the Net Description

Then the simulation is launched from the simulation configuration as seen in the :ref:`previous chapter <user_guide_level_1>`

Before learning how to write those files, we will introduce here the main PhysioBlocks concepts and how it assembles the global system.

Main concepts
-------------

Here are the main objects object you will have to handle to build **Net Configuration** files.

    * **Net**: a set of **Blocks** connected with **Nodes**.
    * **Block**: it defines a set of **Fluxes** and **Internal Equations** that can be enhanced with **Model Components** if necessary.
    * **Node**: it represents a location in the **Net** where the connected blocks share their **Fluxes**.
      Every node exposes one quantity named **DOF** (degree or freedom) per flux type exchanged at the node.
      The **DOFs** are exposed to every **Block** connected at the **Node**.
    * **Model Components**: they can be added to blocks to concatenante additional **Internal Equations** to blocks.

Assembling process
------------------

Based on the Net layout, we build the **Global System**: 

    * Concatenating equations defined by the **sum of the Fluxes** shared at each **Node**.
    * Concatenating **Internal Equation** provided by **Blocks** and their **Model Components**.

.. tikz:: Assembling process scheme for a simplified net
    :include: ../../schemes/assembling_example_scheme.tex


Now that we have in mind the assembling process of the **Global System** from the **Nets**, the next section will detail how to actually write the JSON configuration files.