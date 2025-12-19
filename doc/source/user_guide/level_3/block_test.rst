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

Create Block tests
==================

In the ``gradient_test_utils`` module, we provide functions to test block definitions and net layouts.
They will be useful to debug or to setup non-regression tests.

It is a simple test that compares the **estimated gradient** of the global system with the **computed gradient** from the defined partial derivatives.
While it does not validate your residual function itself, it checks its consistency with the partial derivatives definition.

The gradient test function updates a provided :class:`~physioblocks.simulation.state.State` object with an increment based on the **variables magnitudes**.
It computes the gradient using the defined partial derivatives for the variables in the state.
It then compares it to an estimation based on the computation of the **residual**.

First, we will see how to redirect the logs to print the test information.
We will then go through each function of the module and provide and example.

Setup a logger
--------------

Test output is directed to a logger. Main information and the matching ``loglevel`` are:

    * ``INFO``: the variable names and their indexes in the state
    * ``INFO``: the fluxes and internal expressions function names used at each residual line index
    * ``DEBUG``: the difference between the computed and estimated gradient
    * ``DEBUG``: the name of the variable and position in the gradient if an error is over the threshold

You have to redirect the logs to a the console or a file. Let's see an example with the console.
    
.. code:: python

    import logging
    import sys
    stdout_handler = logging.StreamHandler(sys.stdout)
    add_log_handler(stdout_handler, logging.DEBUG)

Typically, you can set the level to ``INFO`` for a minimal output and ``DEBUG`` for a full ouput of the tests informations.

Test a full net
---------------

``gradient_test_from_file`` function allows to test a net using a full configuration file.
It is useful to check that your net definition is correct.
In this case you don't have to provide a state: it is created from the **Net definition**.

It needs a configuration files, to import every object used in the configuration and to import the aliases you use in the configuration.
You can simply import classes and functions you need for your configuration in your python script, but you can also use the ``dynamic_import_utils`` module to dynamically import the objects you need from your user library.

.. _user_guide_level_3_block_test_dynamic_import:

Dynamic import of the libraries
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Use the ``import_libraries`` function from ``dynamic_import_utils`` module.

It will at least need the path to the base PhysioBlocks library: ``physioblocks/library``.
Then you can add any path to packages you want to load.

.. code:: python

    import_libraries(
        Path("$PHYSIOBLOCKS_PACKAGE_PATH$/physioblocks/library"), 
        Path("$PATH_TO_YOUR_LIBRARY$")
    )

Load the aliases
^^^^^^^^^^^^^^^^

You can load aliases with the ``load_aliases`` function from the PhysioBlocks ``aliases`` module.

It will also need to load the base PhysioBlocks aliases, and your user defined aliases:

.. code:: python

    load_aliases("$PHYSIOBLOCKS_PACKAGE_PATH$/physioblocks/library/aliases")
    load_aliases("$PATH_TO_YOUR_ALIAS_FOLDER$")

Test the Net
^^^^^^^^^^^^

Once you have loaded every object and aliases you need, you can directly use the gradient test function with your configuration file path:

.. code:: python

    assert gradient_test_from_file(FULL_PATH_TO_SIMULATION_CONFIGURATION_FILE)


Test a Block
------------

You can test a single block or model component definition with ``gradient_test_from_model`` function. 
In this case you only test its fluxes and internal equations.

You will have to create a :class:`~physioblocks.simulation.state.State` object containing the variables you want to test and provide **magnitudes** for the variables.
In this case, since you will have to instantiate the block yourself, so you can import it directly.

Let's see an example for the RCR Block:

.. code:: python

    from physioblocks.library.blocks.capacitances import RCRBlock

    # Create the tested block
    rcr_block = RCRBlock(
        pressure_1=Quantity(5230),
        pressure_mid=Quantity(4921),
        pressure_2=Quantity(4624),
        resistance_1=Quantity(1.5e7),
        resistance_2=Quantity(2.1e8),
        capacitance=Quantity(2.3e-8),
        time=Time(0.0),
    )

    # Create a state:
    state = State() # Create a state
    # Create a state variable for each variable you want to test.
    state["pressure_1"] = ref_block.pressure_1 # link variable to quantity in the block
    state["pressure_mid"] = ref_block.pressure_mid
    state["pressure_2"] = ref_block.pressure_2

    # Provide the variables magnitudes
    magnitudes = np.array([1e4, 1e4, 1e4])

    # call the test function
    assert gradient_test_from_model(ref_rcr_block, state, magnitudes)


Test a single expression
------------------------

Alternatively you can also test a single :class:`~physioblocks.computing.models.Expression` object.
In this case, you will still have to provide the state and the variables magnitudes.

From our previous example, let's only test the flux at node 0:

.. code:: python

    from physioblocks.library.blocks.capacitances import RCRBlock

    # Create the tested block
    rcr_block = RCRBlock(
        pressure_1=Quantity(5230),
        pressure_mid=Quantity(4921),
        pressure_2=Quantity(4624),
        resistance_1=Quantity(1.5e7),
        resistance_2=Quantity(2.1e8),
        capacitance=Quantity(2.3e-8),
        time=Time(0.0),
    )

    # Create a state:
    state = State() # Create a state

    # Create a state variable for each variable you want to test.
    state["pressure_1"] = ref_block.pressure_1
    state["pressure_mid"] = ref_block.pressure_mid
    state["pressure_2"] = ref_block.pressure_2

    # Provide the variables magnitude
    magnitudes = np.array([1e4, 1e4, 1e4])

    # call the test function
    assert gradient_test_from_expression(RCRBlock.fluxes_expressions[0].expression, state, magnitudes)
