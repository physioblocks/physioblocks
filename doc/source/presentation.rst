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

############
Presentation
############

PhysioBlocks allows the simulation of dynamical models of physiological systems represented by blocks.

User Levels
===========

There are three use cases for PhysioBlocks depending on the user profile:

* **Level 1:** Configure and run physiological systems simulation (for pre-existing systems)
* **Level 2:** Create new systems with existing blocks without writing code
* **Level 3:** Write and add new blocks to the library.

Principles
==========

* A **Net** (system) is built from **Nodes** and **Blocks** connected by those nodes.
* At each node in the net, connected blocks share **Degrees of Freedom** (ex: pressure) and send **Fluxes** that satisfy the Kirchhoff Law.
* **ModelComponents** concatenate blocks equations governing internal variables to the global system (if necessary, for modularity purposes within the block)

Interactions
============

**Level 1:** Configure and run a simulation : JSON
    * Update the model parameters

**Level 2:** Create Nets : JSON
    * Declare the nodes, the blocks, and the block-nodes connections

**Level 3:** Write and add models to the library: Python
    * Declare the quantities to be used in the model
    * Write the fluxes and internal equations
