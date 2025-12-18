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

.. _user_guide_level_2 :

*******
Level 2
*******

In this chapter we will learn how to write **JSON configuration files** that can be used with the **PhysioBlocks Launcher**.

We will first look at **PhysioBlocks main objects** and how it is **assembling global system**.
We will then see how to write a JSON describing a **Net** and use it to create a **full simulation configuration**.
Finally, we will see how to **simplify configuration files** using configuration **Aliases**.

.. toctree::
   :glob:
   :maxdepth: 2

   level_2/overview
   level_2/create_net
   level_2/create_simulation
   level_2/aliases