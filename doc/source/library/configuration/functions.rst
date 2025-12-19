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

.. _library_configuration_functions:

Functions Configuration
=======================

This sections describes the function configurations items available in the
simulation configuration to initialise parameters or update them each time step.

.. note::
    
    For most of the functions here, the parameters values can be string references to other parameter of the simulation.

    The can also be function configuration items themselves.

Sum Function
------------

* **Class:** :class:`~physioblocks.library.functions.base_operations.Sum`
* **Type name:** ``sum``

Parameters
^^^^^^^^^^

    * **add:** list of element to sum.
    * **subtract:** (Optional) list of element to subtract from the result of the sum.

Examples
^^^^^^^^

Scalar Sum
""""""""""

.. code:: json

    {
        "type": "sum"
        "add": [0.1, 0.2, 0.3],
        "subtract": [0.2]
    } // result 0.4

Vector Sum
""""""""""

.. code:: json

    {
        "type": "sum"
        "add": [[0.1, 0.2, 0.3], [0.9, 0.8, 0.7]]
    } // result [1.0, 1.0, 1.0]

Product Function
----------------

* **Class:** :class:`~physioblocks.library.functions.base_operations.Product`
* **Type name:** ``product``

Parameters
^^^^^^^^^^

    * **factors:** list of element to multiply.
    * **inverses:** (Optional) list of element to divide from the product result.

Examples
^^^^^^^^

Scalar product
""""""""""""""

.. code:: json

    {
        "type": "sum"
        "factors": [1.0, 2.0, 3.0],
        "inverses": [2.0]
    } // result : 3.0

Vector product
""""""""""""""

.. code:: json

    {
        "type": "sum"
        "factors": [[0.1, 0.2, 0.3], [0.9, 0.8, 0.7]]
    } // [0.9, 0.16, 0.27]

.. _library_configuration_functions_watchers:

Watch Quantity Function
-----------------------

* **Class:** :class:`~physioblocks.library.functions.watchers.WatchQuantity`
* **Type name:** ``watch_quantity``

Parameters
^^^^^^^^^^

    * **quantity:** the quantity reference name

Example
^^^^^^^

.. code:: json

    {"type": "watch_quantity", "quantity": "some_parameter_name"}

Sum Blocks Quantity Function
----------------------------

* **Class:** :class:`~physioblocks.library.functions.watchers.SumBlocksQuantity`
* **Type name:** ``sum_blocks_quantity``

Parameters
^^^^^^^^^^

    * **quantity_id:** the quantity reference name
    * **elements:** a list of the blocks names

Example
^^^^^^^

.. code:: json

    {
        "quantity_id": "volume_stored",
        "elements": ["rcr_block_1", "rcr_block_2"]
    } // result: sum of volume_stored in rcr_block_1 and rcr_block_2

Piecewise Linear Function
-------------------------

* **Class:** :class:`~physioblocks.library.functions.piecewise.PiecewiseLinear`
* **Type name:** ``piecewise_linear``

Parameters
^^^^^^^^^^

    * **points_abscissas:** The function abscissas
    * **points_ordinates:** The function ordinates
    * **left_value:** (Optional) Function value when the evaluation point is before the provided abscissas.
    * **right_value:** (Optional) Function value when the evaluation point is after the provided abscissas.

Example
^^^^^^^

.. code:: json

    {
        "type":"piecewise_linear",
        "points_abscissas": [0.0, 0.5, 1.0],
        "points_ordinates": [0.0, 1.0, 4.0],
        "left_value": -1.0,
        "right_value": 0.0
    }

Piecewise Linear Periodic Function
----------------------------------

* **Class:** :class:`~physioblocks.library.functions.piecewise.PiecewiseLinearPeriodic`
* **Type name:** ``piecewise_linear_periodic``

Parameters
^^^^^^^^^^

    * **period:** The function period
    * **points_abscissas:** The function abscissas
    * **points_ordinates:** The function ordinates

Example
^^^^^^^

.. code:: json

    {
        "type":"piecewise_linear_periodic",
        "period":"1.0",
        "points_abscissas": [0.0, 0.5],
        "points_ordinates": [0.0, 1.0]
    }

Rescale Two Phases Function
---------------------------

* **Class:** :class:`~physioblocks.library.functions.piecewise.RescaleTwoPhasesFunction`
* **Type name:** ``rescale_two_phases_function``

Parameters
^^^^^^^^^^

    * **rescaled_period:** The period of the rescale function
    * **reference_function:** The reference function coordinates
    * **alpha:** The proportion of the variation of phase 0
    * **phases:** For each intervals point of the reference, determine if it belong to
      phase 0 or 1.

Examples
^^^^^^^^

.. code:: json

    {
        "type":"rescale_two_phases_function",
        "rescaled_period":"2.5",
        "reference_function": [[0.0, 0.0], [0.25, 1.0], [0.75, 1.0], [1.0, 0.0]],
        "alpha": 0.75,
        "phases": [0, 1, 0]
    }

.. _library_configuration_functions_sinus:

Sinus Offset Function
---------------------

* **Class:** :class:`~physioblocks.library.functions.trigonometric.SinusOffset`
* **Type name:** ``sinus_offset``

Parameters
^^^^^^^^^^

    * **offset_value:** Offset value of the sinus
    * **amplitude:** Peak amplitude of the sinus
    * **frequency:** Frequency of the sinus
    * **phase_shift:** Phase shift of the sinus

Example
^^^^^^^

.. code:: json

    {
        "type":"sinus_offset",
        "offset_value":0.5,
        "amplitude": 1.0,
        "frequency": 0.5,
        "phase_shift": 0.0
    }

First Order Function
--------------------

* **Class:** :class:`~physioblocks.library.functions.first_order.FirstOrder`
* **Type name:** ``first_order``

Parameters
^^^^^^^^^^

    * **times_start:** Start times of first order components
    * **amplitudes:** Amplitudes of first order components
    * **time_constants:** Time constants of first order components
    * **baseline_value:** Baseline value of the function

Examples
^^^^^^^^

.. code:: json

    {
        "type":"first_order",
        "times_start":[0.0, 3.0, 7.0],
        "amplitudes": [1.0, -1.0, 0.5],
        "time_constants": [0.5, 0.8, 0.3],
        "baseline_value": 0.0
    }
