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

Installation
************

Base installation
=================

This installation allows to use the PhysioBlocks library and the PhysioBlocks launcher.

From the repository directory: 

.. code:: bash

   pip install -e .

Specific installations
======================

You can add install options to install specific dependencies for PhysioBlocks.

* ``test``: Install dependencies to run tests and code coverage.
* ``doc``: Install dependencies to build the documentation.
* ``quality``: Install dependencies to check code quality.
* ``tox``: Install tox to automatize package tests.

After installing PhysioBlocks with any of those options, you will be able to run the corresponding tests on the package.

Run tests and coverage
----------------------

With a ``test`` option installation, from the repository directory:

.. code:: bash

   coverage run -m pytest
   coverage html

The coverage report will be available in html in the ``htmlcov`` folder.

Log messages while running tests
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To log information or debug messages when running the tests:

1. Always log while running the tests: locally change the pyproject.toml
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

Add the lines defining the ``log_cli`` and ``log_cli_level`` under the ``[tool.pytest.ini_options]`` of the ``pyproject.toml`` file like in the following example:

.. code:: toml

    [tool.pytest.ini_options]
    addopts = "-ra -q"
    testpaths = [ "tests", ]
    log_cli = true
    log_cli_level = "DEBUG"

2. Occasionally log while running the tests: overwrite pytest arguments in the command line
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

Overwrite the ``log_cli`` and ``log_cli_level`` in the command line when running a test.
From the repository directory:

.. code:: bash

   # Example 1: Run all test with debug level logs:
   pytest -o log_cli=true -o log_cli_level=DEBUG

   # Example 2: Run a single test with debug level logs:
   # $TEST_FILE_PATH: the path of the file contening the test
   # $TEST_NAME: the test to run
   pytest $TEST_FILE_PATH -k $TEST_NAME -o log_cli=true -o log_cli_level=DEBUG

Build the documentation
-----------------------

With a ``doc`` option installation, from the repository directory:

.. code:: bash

   cd doc
   make html

The documentation will be available in the ``doc/build`` folder.

Check quality
-------------

With a ``quality`` option installation, from the repository directory:

.. code:: bash

   # Format code with ruff:
   ruff format

   # Check code with ruff:
   ruff check

   # Check typing with mypy:
   mypy PhysioBlocks --strict --ignore-missing-imports


Run the automated package tests
-------------------------------

With a ``tox`` option installation, from the repository directory:

.. code:: bash

   # Runs formater, linter, type checker and tests for several python versions
   tox 
