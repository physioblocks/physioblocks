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

.. _user_guide_level_3_functions:

*****************************
Write a simulation function
*****************************

In this section, you will learn how to write new **simulation functions** and make them available to configure for a level 2 user.

Simulation functions compute a value from quantities of the simulation at each time step.
They are configurable in the simulation configuration file, for example to:

* define a parameter varying in time in the ``update_functions`` field.
* define an **observation operators** of an :ref:`estimation simulation <user_guide_level_2_estimation>`.
* configure outputs in the ``output_functions`` field.

Writing a function
==================

To create a new **configurable function**, you have to inherit from :class:`~physioblocks.simulation.functions.AbstractFunction` and:

1. Register the function type.
   It allows to use the function in a configuration file with the registered key.
2. Define the function **parameters**.
   They are the arguments of the constructor.
   They are initialized **once**, when loading the configuration, and are constant during the simulation.
3. Implement the ``eval`` method.
   Its arguments are the **evaluation quantities**: they receive the current values of simulation quantities at each evaluation.

Here's an example of an affine function:

.. code-block:: python

    from dataclasses import dataclass

    from physioblocks.registers.type_register import register_type
    from physioblocks.simulation.functions import AbstractFunction


    @register_type("affine_function")
    @dataclass
    class AffineFunction(AbstractFunction):
        """Compute an affine function of a quantity."""

        # Parameters: initialized once from the configuration
        a: float
        b: float = 0.0

        # Evaluation quantities: the eval method arguments
        def eval(self, x: float) -> float:
            return self.a * x + self.b


Note that we use a ``@dataclass`` decorator: we avoid writing the constructor to set ``a`` and ``b``.
It is still possible to write the function with a constructor an perform a more complex initialization.
In that case, the arguments of the constructor **must match** the parameters in the configuration.

When evaluating the function ``current`` or ``new`` value,
the value passed to ``x`` will be the ``current`` or ``new`` value of the ``evaluation_quantities`` set to ``x`` at creation.

Let's see how to configure this.

Configuring the function
========================

In the configuration, the function parameters are set with their names.
The ``evaluation_quantities`` item matches each argument of the ``eval`` method with a **global quantity name** of the simulation.
The evaluation quantities can be the time or the state variables of the simulation.

.. note::

    Remember to save your function in the ``user_library`` folder of your launcher directory to use it in configuration files.

Here is an example of the ``affine_function`` configuration where we evaluate the function for a quantity named ``pressure``.

.. code-block:: json

    {
        "type": "affine_function",
        "a": 0.5,
        "b": 2.0,
        "evaluation_quantities": {"x": "pressure"}
    }

See the :mod:`physioblocks.library.functions` module for more examples.
