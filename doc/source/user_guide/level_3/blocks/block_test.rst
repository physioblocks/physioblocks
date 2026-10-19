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

The gradient test function updates a provided :class:`~physioblocks.computing.quantities.QuantitiesRegistry` object with an increment based on the **variables magnitudes**.
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
    import physioblocks

    logger = logging.getLogger(physioblocks.__name__)
    logger.addHandler(logging.StreamHandler(sys.stdout))
    logger.setLevel(logging.DEBUG)

Typically, you can set the level to ``INFO`` for a minimal output and ``DEBUG`` for a full ouput of the tests information.

Test a net
----------

``gradient_test_from_file`` function allows to test a net using a configuration file.
It is useful to check that your net definition is correct.
In this case you don't have to provide a state: it is created from the **Net definition**.

The configuration file describes a ``simulation_model_factory`` object rather than a full simulation.
It holds the ``time``, ``net``, ``state`` and ``parameters`` items of a simulation configuration (see :ref:`how to write a simulation configuration <user_guide_level_2_create_simulation>`).

It needs a configuration files, to import every object used in the configuration and to import the aliases you use in the configuration.
You can simply import classes and functions you need for your configuration in your python script, but you can also use the ``dynamic_import_utils`` module to dynamically import the objects you need from your user library.

.. _user_guide_level_3_block_test_dynamic_import:

Dynamic import of the libraries
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Use the ``import_libraries`` function from ``dynamic_import_utils`` module.

It will at least need the path to the base PhysioBlocks library: ``physioblocks/library``.
Then you can add any path to packages you want to load.

.. code:: python

    from pathlib import Path
    from physioblocks.utils.dynamic_import_utils import import_libraries

    import_libraries(
        [
            Path("$PHYSIOBLOCKS_PACKAGE_PATH$/physioblocks/library"),
            Path("$PATH_TO_YOUR_LIBRARY$"),
        ]
    )

.. note::

    The path you add must be in a site directory to be imported correctly.
    If it is not the case, call ``site.addsitedir(PATH_TO_YOUR_LIBRARY)`` before dynamically importing your library or copy your library to an existing site.

Load the aliases
^^^^^^^^^^^^^^^^

You can load aliases with the ``load_aliases`` function from the PhysioBlocks ``io.aliases`` module.

It will also need to load the base PhysioBlocks aliases, and your user defined aliases:

.. code:: python

    from physioblocks.io.aliases import load_aliases

    load_aliases("$PHYSIOBLOCKS_PACKAGE_PATH$/physioblocks/library/aliases")
    load_aliases("$PATH_TO_YOUR_ALIAS_FOLDER$")

Test the Net
^^^^^^^^^^^^

Once you have loaded every object and aliases you need, you can directly use the gradient test function with your configuration file path:

.. code:: python

    from physioblocks.utils.gradient_test_utils import gradient_test_from_file

    assert gradient_test_from_file(FULL_PATH_TO_MODEL_FACTORY_CONFIGURATION_FILE)


Test a Block
------------

You can test a single block or model component definition with ``gradient_test_from_model`` function. 
In this case you only test its fluxes and internal equations.

You will have to create a :class:`~physioblocks.computing.quantities.QuantitiesRegistry` object containing the variables you want to test and provide **magnitudes** for the variables.
In this case, since you will have to instantiate the block yourself, so you can import it directly.

Let's see an example for the RCR Block:

.. code:: python

    from physioblocks.computing.quantities import Quantity, QuantitiesRegistry
    from physioblocks.library.blocks.capacitances import RCRBlock
    from physioblocks.simulation.time_manager import Time
    from physioblocks.utils.gradient_test_utils import gradient_test_from_model

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
    # Set a time step
    rcr_block.time.update(0.001)

    # Create a state:
    state = QuantitiesRegistry() # Create a state
    # Create a state variable for each variable you want to test.
    state["pressure_1"] = rcr_block.pressure_1 # link variable to quantity in the block
    state["pressure_mid"] = rcr_block.pressure_mid
    state["pressure_2"] = rcr_block.pressure_2

    # Provide the variables magnitudes
    state.set_magnitudes(
        {
            "pressure_1": 1e4,
            "pressure_mid": 1e4,
            "pressure_2": 1e4,
        }
    )

    # call the test function
    assert gradient_test_from_model(rcr_block, state)


Test a single expression
------------------------

Alternatively you can also test a single :class:`~physioblocks.computing.models.Expression` object.
In this case, you will still have to provide the state and the variables magnitudes.

From our previous example, let's only test the flux at local node 1.
The block type holds its flux expressions in a dictionary indexed by local node, and the tested block instance provides the parameters of the expression:

.. code:: python

    from physioblocks.computing.quantities import Quantity, QuantitiesRegistry
    from physioblocks.library.blocks.capacitances import RCRBlock
    from physioblocks.simulation.time_manager import Time
    from physioblocks.utils.gradient_test_utils import gradient_test_from_expression

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
    # Set a time step
    rcr_block.time.update(0.001)

    # Create a state:
    state = QuantitiesRegistry() # Create a state

    # Create a state variable for each variable you want to test.
    state["pressure_1"] = rcr_block.pressure_1
    state["pressure_mid"] = rcr_block.pressure_mid
    state["pressure_2"] = rcr_block.pressure_2

    # Provide the variables magnitude
    state.set_magnitudes(
        {
            "pressure_1": 1e4,
            "pressure_mid": 1e4,
            "pressure_2": 1e4,
        }
    )

    # call the test function
    assert gradient_test_from_expression(RCRBlock.fluxes_expressions[1], rcr_block, state)
