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


Launch a simulation
===================

In this section we will first **run a minimal simulation** using the PhysioBlocks Launcher and then go trough the description of launcher options.

.. note::

    For all the examples provided, you can use any reference JSON provided with the PhysioBlocks package in the ``references`` folder.

Minimal run
-----------

.. warning::

    Before running a simulation, you will have to configure the launcher as described in the :ref:`previous section <user_guide_level_1_launcher_configuration>`


Here are the instruction **to run the simulation** from a configuration file:

.. code:: bash

    # Your current folder should be a configured launcher folder.
    python -m physioblocks.launcher $PATH_TO_SIMULATION_CONFIG_FILE

.. note::

    You can provide a **configured Laucher Folder** path with the ``-d`` option and it will produce the same results.

The simulations results can be found in the ``simulation/Z`` series of your configured launcher folder.
The simulation creates a folder named with your machine name, the current serie name (default is Z) and the current simulation number.
This folder should contain:

* **a csv file**: the simulation results
* **a log file**: the simulation logs
* **a json file**: a copy of the configuration file you used

.. note::

    A log of main informations about the simulation run is kept in the main **Launcher Log File** located at the root of the **Launcher Folder**.

With the launcher options, we will be able to update simulation informations, destination folder and generated files.

Launcher options
----------------

You can view all the launcher option with ``-h``. We can break the options into four main categories.

Informations options
^^^^^^^^^^^^^^^^^^^^

This options will attach more informations to the simulation.

    * **Serie:** the ``-s`` option allows to provide a serie name for the configuration. The result of the simulation will be saved in the matching series folder.
    * **Message:** the ``-m`` option attaches a message to the current simulation. This message will be written both in the generated log file for the simulation and the launcher directory main log file, associated with the simulation informations.

Log options
^^^^^^^^^^^

These options control the console logs of the simulation.

    * **Verbose:** the ``-v`` option prints the simulation logs to the console.
    * **Log level:** the ``-l`` set the level console logs. Possible options are ``INFO``, ``DEBUG``, ``WARNING``, ``ERROR`` or ``CRITICAL``. Default is ``INFO``.

File format options
^^^^^^^^^^^^^^^^^^^

A single option to update the format of the simulation result.

    * **file extension:** the ``-ext`` option update the result file format. Supported options are currently ``csv`` and ``parquet``

Traces options
^^^^^^^^^^^^^^

Several options are avaible to save basic traces of the simulation results.

    * **Trace:** if set, the ``-t`` create a trace in html of the simulation results.
    * **compare:** the ``--compare`` options takes a path to a reference file.
      If set, a html file tracing the **error between the reference file and the current simulation** is saved along with the results.
      Be careful: It only compare datas with **matching columns names** in the reference and the results files
    * **row_height:**  if the default row size is not adapted, the ``--row_heights`` option set the rows size in the generated graphs.

Update configuration files
--------------------------

In this section, we will detail parameters present in most configuration file.
If you open one of the reference configuration file provided in the ``references`` folder of the PhysioBlocks package, you will find parameters that you can update.

* **type**: the configuration file type. This will be useful at a higher user levels (see section on :ref:`how to write configuration files<user_guide_level_2>` ).
* **time**: here you can update the simulation **start time and duration**.
* **variable_initialization**: Here you can provide the **initial value for the variables** of the model.
  Note that you can initialise them with a float or a string reference to the key of any parameters in the **parameter** configuration entry.
* **parameters**: they are the updatable parameters for the model.
* **output_function**: Your simulation configuration produces results based on the underlying models it uses.
  If you want to add computations to the result file, you can use this entry to add functions to produce the desired output.
  In the :ref:`next section<user_guide_level_2>` we will detail how to use the functions in the configuration files.

For now, you can **update the parameters, variable initialization and the time** in a simulation configuration.
In the next section, we will see how to actually **write configuration files** and learn more about their possibilities in PhysioBlocks.