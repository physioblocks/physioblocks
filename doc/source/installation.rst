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
Installation
############

Prerequisites
*************

PhysioBlocks only needs a recent python version installed.

Supported python version:
   * 3.10 to 3.14

.. note::

   We recommend using a python virtual environment to install PhysioBlocks.
   You can find more informations about python virtual environment in the documentation : https://docs.python.org/3/library/venv.html

Here are the instructions to create a virtual environment:

.. code:: bash

   # The current folder can be the PhysioBlocks package for example.
   # Create the virtual environment
   python -m venv .venv

   # Activate the virtual environment
   source .venv/bin/activate

   # To deactivate the virtual environment
   deactivate

Base Installation
*****************

This installation allows to use the PhysioBlocks library and the PhysioBlocks launcher.

.. code:: bash

   pip install physioblocks

