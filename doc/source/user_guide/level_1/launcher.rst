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

The Launcher module
===================

To run a simulation from a **Configuration File**, the **Launcher Module** is the main interface you will have to use.

Functionalities
---------------

The **Launcher** allows to :

* Run a simulation based on a configuration file
* Save results to ``.csv`` or ``.parquet``
* Organize results in series folders
* Create a basic trace for simulation results
* Create a basic trace of the error of the current simulation with a reference file.

.. _user_guide_level_1_launcher_configuration:

Configuration
-------------

To use the PhysioBlocks Launcher, you will have to **configure a directory** where the simulation results are saved.
It will also contains your your own nets and blocks as we will see later in this guide.

To configure a directory for the PhysioBlocks launcher, we will have to run the PhysioBlocks **Launcher Configure Module**.
The configure module creates the folder hierarchy and configuration files needed to run the PhysioBlocks Launcher module.

.. code:: bash

    # First, create a new folder dedicated to the PhysioBlocks launcher
    # where you want to save your simulation results.
    mkdir $MY_PATH/PhysioBlocksLauncher

    # Then run the launcher configure module from the created folder
    cd $MY_PATH/PhysioBlocksLauncher
    python -m physioblocks.launcher.configure -v

The ``-v`` option will produce the output:

.. code::

    INFO:root:Launcher directory created at $MYPATH/PhysioBlocksLauncher.

.. note::

    To avoid deleting existing files, the configure module only accepts empty folders.
    You will get an error message if you try to configure a folder that already contains files.

Alternatively, you can configure a folder at a given path with the ``-d`` arguments


.. code:: bash

    # This produce the same result.
    python -m physioblocks.launcher.configure -d $MY_PATH/PhysioBlocksLauncher -v

Now that we **configured a PhysioBlocks Launcher Folder**, the next part will show how to **run a simulation** and where to find the simulation results.



