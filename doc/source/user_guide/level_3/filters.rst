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

.. _user_guide_level_3_filters:

****************************
Write an estimation filter
****************************

In this section, you will learn how to write new **estimation filters** to use in an :ref:`estimation simulation <user_guide_level_2_estimation>`.

We will first present the objects the simulation passes to the filter.
Then we will see how to write the filter **prediction** and **update** steps.
Finally, we will briefly see how to configure it.

The filter attributes
=====================

A filter inherits from :class:`~physioblocks.simulation.estimation.AbstractFilter`.
When creating the filter, the simulation passes:

* ``model_function(states, current_time, new_time)``: runs the model for one time step and returns the new states.
* ``observation_function(states, time)``: returns the observations for the states.
* ``model_noise_covariance`` and ``measurements_noise_covariance``: the noise covariances built from the configuration.

You can then use those functions and matrices in the filter algorithm.

Vectorized functions
--------------------

The model and observer functions are **vectorized**: they take a set of states as a 2D array (one state per row) and return one result per row.
It is useful for filters working with particles, like the :class:`~physioblocks.library.filters.unscented_kalman_filter.UnscentedKalmanFilter` and its sigma points:
all the particles are evaluated in a single call.

Consequently, if your filter does not need to evaluate several states,
the argument for the ``model_function`` and the ``observation_function`` function still have to be reshaped to a 2D array with a single column (see the example below).

The evaluation of the particles can run in parallel processes setting the ``parallelize`` and ``nb_processes`` simulation options in the configuration.
There is nothing to do on the filter side (see the :class:`~physioblocks.simulation.estimation.EstimationSimulation` parameters documentation).


Writing a filter
================

To create a new **configurable filter**, you have to inherit from :class:`~physioblocks.simulation.estimation.AbstractFilter` and:

1. Register the filter type with an ID.
2. Implement the ``prediction`` method: compute the predicted state and covariance at the new time from the current ones.
3. Implement the ``update`` method: correct the predicted state and covariance with the measurement.

With :math:`n` the state size (``state_size``), :math:`m` the observations size (``observer_size``) and :math:`p` the number of evaluated states,
here are the sizes of the various arrays the filter handles:

.. list-table::
   :header-rows: 1

   * - Array
     - Shape
   * - ``state``
     - ``(n,)``
   * - ``state_covariance`` and ``model_noise_covariance``
     - ``(n, n)``
   * - ``measurement``
     - ``(m,)``
   * - ``measurements_noise_covariance``
     - ``(m, m)``
   * - ``model_function``
     - ``(p, n) -> (p, n)``
   * - ``observation_function``
     - ``(p, n) -> (p, m)``

The ``prediction`` and ``update`` methods receive and must return the state as a 1D array of shape ``(n,)`` and the covariance as a 2D array of shape ``(n, n)``.
If you compute the state as a column vector of shape ``(n, 1)``, flatten it before returning it.

Here is a simple example of a **forward filter**: it runs the model but never corrects it with the measurements.
It is equivalent to the **forward simulation**.

.. code-block:: python

    from physioblocks.registers.type_register import register_type
    from physioblocks.simulation.estimation import AbstractFilter


    @register_type("forward_filter")
    class ForwardOnlyFilter(AbstractFilter):
        """Run the model without correcting it with the measurements."""

        def prediction(self, current_time, new_time, state_mean, state_covariance):
            # The model function takes a set of states: one state per row.
            states = state_mean.reshape(1, -1)
            new_state = self.model_function(states, current_time, new_time)
            return new_state.flatten(), state_covariance + self.model_noise_covariance

        def update(self, time, predicted_state_mean, predicted_state_covariance, measurement):
            # No correction, so we don't use the 'observation_function' or 'measurements_noise_covariance'
            return predicted_state_mean, predicted_state_covariance

Configuring the filter
======================

Select the filter in the simulation configuration with its registered type:

.. code-block:: json

    "filter_type": "forward_filter"

Additional filter parameters are keyword arguments of the filter constructor.
They are set with the ``filter_options`` configuration item.

See the :class:`~physioblocks.library.filters.unscented_kalman_filter.UnscentedKalmanFilter` for an example.

.. note::

    Save your filter in the ``user_library`` folder of your launcher directory to use it in configuration files.
