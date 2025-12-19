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

.. _library_aliases_blocks:

Block Aliases
=============

Capacitances
------------

C Block Alias
"""""""""""""

* **Class:** :class:`~physioblocks.description.blocks.BlockDescription`
* **Alias name:** ``c_block``

Block description of a :class:`~physioblocks.library.blocks.capacitances.CBlock` object with time parameter set.

Parameters
''''''''''

    * **model_type**: ``c_block``
    * **time**: The simulation time global name.


RC Block Alias
""""""""""""""

* **Class:** :class:`~physioblocks.description.blocks.BlockDescription`
* **Alias name:** ``rc_block``

Block description of a :class:`~physioblocks.library.blocks.capacitances.RCBlock` object with time parameter set.

Parameters
''''''''''

    * **model_type**: ``rc_block``
    * **time**: The simulation time global name.


RCR Block Alias
"""""""""""""""

* **Class:** :class:`~physioblocks.description.blocks.BlockDescription`
* **Alias name:** ``rc_block``

Block description of a :class:`~physioblocks.library.blocks.capacitances.RCRBlock` object with time parameter set.

Parameters
''''''''''

    * **model_type**: ``rcr_block``
    * **time**: The simulation time global name.

Valves
------

Valve RL Block Alias
""""""""""""""""""""

* **Class:** :class:`~physioblocks.description.blocks.BlockDescription`
* **Alias name:** ``valve_rl_block``

Block description of a :class:`~physioblocks.library.blocks.valves.ValveRLBlock` object with time parameter set.

Parameters
''''''''''

    * **model_type**: ``valve_rl_block``
    * **time**: The simulation time global name.


Cavities
--------

Spherical Cavity Block Alias
""""""""""""""""""""""""""""

* **Class:** :class:`~physioblocks.description.blocks.BlockDescription`
* **Alias name:** ``spherical_cavity_block``

Block description of a :class:`~physioblocks.library.blocks.cavity.SphericalCavityBlock` object with time parameter set.

Parameters
''''''''''

    * **model_type**: ``spherical_cavity_block``
    * **time**: The simulation time global name.