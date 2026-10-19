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

.. _user_guide_level_2_estimation:

Estimation simulations
======================

The **Estimation Simulation** computes the state at each time step based on the dynamics defined by the model and measurements on the system.

The estimation is based on a generic implementation of an **estimation filter**.
At each time step, an estimation filter: 

1. **Predicts** the state based on the model dynamic. 
2. **Updates** the predicted state based on the measurements. 

Physioblocks provides some **estimation filters** implementations like the :class:`~physioblocks.library.filters.kalman_filter.KalmanFilter` and the :class:`~physioblocks.library.filters.unscented_kalman_filter.UnscentedKalmanFilter`.
We will see in the :ref:`user guide level 3<user_guide_level_3_filters>` how to define new estimation filters to use in configurations. 

In this section, we will build an estimation simulation step by step for the **simple circulation net** of the :ref:`previous sections <user_guide_level_2_create_simulation>`.
Using the node A pressure measurements, we will estimate:

* the **state** of the net: the pressures at nodes A and B
* the resistance ``Rb`` for a wrong initial guess.

Estimate the state
------------------

Let's first see how to estimate the state starting from a wrong initial guess.

In this section, we will:

* generate synthetic measurements
* set the estimation simulation configuration
* read the measurements
* configure the observation operator
* set the state initial guess
* plot the estimated pressures with their confidence intervals.

Synthetic data
""""""""""""""

For the measurements, we use the simulation of the :ref:`complete simple circulation example <user_guide_level_2_create_simulation>` with the 
**simple circulation net** alias defined in the :ref:`aliases section <user_guide_level_2_aliases>`.

We generate them by running the simple circulation example with a ``20.0`` duration.

We update the flow ``A.flow`` entering the net to a pulse with a ``1.0`` second period.
We define it with a :class:`piecewise_linear_periodic <physioblocks.library.functions.piecewise.PiecewiseLinearPeriodic>` function.

.. code:: json

    "time": {
        "type": "range",
        "start": 0.0,
        "length": 20.0,
        "step_size": 0.001
    },
    "parameters": {
        "Ca": 2.0e-10,
        "Ra": 8.0e6,
        "Cb": 1.7e-08,
        "Rb": 1.0e8,
        "C.pressure": 1.6e3,
        "pulse_period": 1.0
    },
    "update_functions": {
        "A.flow": {
            "type": "piecewise_linear_periodic",
            "evaluation_quantities": {"time": "time"},
            "period": "pulse_period",
            "points_abscissas": [0.0, 0.075, 0.134, 0.142, 0.281],
            "points_ordinates": [0.0, 0.0, 0.5e-3, 0.5e-3, 0.0]
        }
    }

To have measurements in the **stable regime** of the system, we then cut the data to use the last 10 cycles of the simulation.
The next figure shows our measurements.

.. raw:: html

    <figure class="align-center">
        <iframe src="estimation/1_synthetic_data/synthetic_data.html"
                width="100%" height="320"
                title="Pressure synthetic measurements at node A"></iframe>
        <figcaption>
            <p><span class="caption-text">Pressure synthetic measurements at node A.</span></p>
        </figcaption>
    </figure>
    

Simulation and filter type
""""""""""""""""""""""""""

We start from the forward simulation configuration we used to generate the measurements:
the net, its boundary conditions, the parameters and the update functions are unchanged.

We update the simulation ``type`` to :class:`estimation_simulation <physioblocks.simulation.estimation.EstimationSimulation>` and choose the filter with ``filter_type``.

We use the :class:`Unscented Kalman Filter (UKF) <physioblocks.library.filters.unscented_kalman_filter.UnscentedKalmanFilter>` implemented in PhysioBlocks.

.. note::
    
    While it is not necessary to use the UKF for a linear problem,
    it will be necessary as soon as we add parameter estimation in the next section.

For every filter, we can set an optional ``filter_options`` field.
There we can set the parameters detailed in each filter's documentation.
We will use default parameters for the UKF so we don't add the field in the configuration.

Finally, we set the ``time`` range to match the measurements.

.. code:: json

    {
        "type": "estimation_simulation",
        "filter_type": "unscented_kalman_filter",
        "solver": {"type": "linear_solver"},
        "time": {
            "type": "range",
            "start": 0.0,
            "length": 10.0,
            "step_size": 0.001
        },
        "net": {
            "type": "simple_circulation_net_example",
            "boundaries_conditions": {
                "C": [{
                    "type": "condition",
                    "condition_type": "pressure",
                    "condition_id": "C.pressure"
                }],
                "A": [{
                    "type": "condition",
                    "condition_type": "flow",
                    "condition_id": "A.flow"
                }]
            }
        },
        "parameters": {
            "Ca": 2.0e-10,
            "Ra": 8.0e6,
            "Cb": 1.7e-08,
            "Rb": 1.0e8,
            "C.pressure": 1.6e3,
            "heartbeat_duration": 1.0
        },
        "update_functions": {
            "A.flow": {
                "type": "piecewise_linear_periodic",
                "evaluation_quantities": {"time": "time"},
                "period": "heartbeat_duration",
                "points_abscissas": [0.0, 0.075, 0.134, 0.142, 0.281],
                "points_ordinates": [0.0, 0.0, 0.5e-3, 0.5e-3, 0.0]
            }
        }
    }

Set the measurements
""""""""""""""""""""

The measurements are read from the data field named ``measurements``.
We use a :class:`read_data <physioblocks.configuration.io.DataReader>` configuration object that takes an input csv filepath and read it into a dataframe.

.. code:: json

    "data": {
        "measurements": {
            "type": "read_data",
            "filepath": "path/to/simple_circulation_results.csv"
        }
    }

Let's remember here that the ``data`` field defines the inputs for the preprocesses and postprocesses.
So you can define preprocesses to shape the measurement data.  

If your measurements are not in SI units, you can add a :class:`conversion_process <physioblocks.library.processes.computing_processes.ConvertProcess>` to convert them.
There is also an :class:`interpolation_process <physioblocks.library.processes.computing_processes.InterpolationProcess>` you can use if you ever want to match your measurements to a different simulation time step.

In our case, we will just rename the synthetic pressure to not confuse it with the estimated pressure in the output. 
Lets rename the file's columns with the :class:`rename_process <physioblocks.library.processes.file_processes.RenameProcess>` preprocess. 

.. code:: json

    "preprocesses": {
        "rename_measurements": {
            "type": "rename_process",
            "inputs": ["measurements"],
            "outputs": ["measurements"],
            "mapping": {"A.pressure": "measurement.A.pressure"}
        }
    }

Configure the observation operator
""""""""""""""""""""""""""""""""""

The :class:`observer <physioblocks.simulation.estimation.ObserverFactory>` object defines the **observations**: they are the model quantities to compare with the measurements.
Each observation sets:

* ``measurement``: the name of the matching measurement column in the data.
* ``operator``: a function computing the observation from the model quantities.
* ``magnitude``: the order of magnitude of the observation,
* ``stdev``: the standard deviation of the measurement noise.

Concerning the observation operator, in our case we measure a quantity directly accessible from the model,
so we use a :class:`watch_quantity <physioblocks.library.functions.watchers.WatchQuantity>` function as the observation operator.

But keep in mind that you can use any :mod:`simulation function <physioblocks.library.functions>` to set the observation operators.
In particular, for simple observations, you can set them combining :class:`product<physioblocks.library.functions.base_operations.Product>` and
:class:`sum<physioblocks.library.functions.base_operations.Sum>` operations.

.. code:: json

    "observer": {
        "type": "observer",
        "observations": {
            "observation.A.pressure": {
                "type": "observation",
                "measurement": "measurement.A.pressure",
                "operator": {
                    "type": "watch_quantity",
                    "evaluation_quantities": {"quantity": "A.pressure"}},
                "magnitude": 1e5,
                "stdev": 0.1
            }
        }
    }

.. note::

    Every quantity is scaled with the magnitude before entering the filter.
    Every standard deviation (observations, state, parameters and model noise) is expressed in the scaled space.
    Meaning that here, a ``stdev`` of ``0.1`` with a ``magnitude`` of ``1e5`` means a standard deviation of 10 kPa.

Estimate the state
""""""""""""""""""

We set the state variables initial uncertainty with the quantities ``stdev`` parameter.
We initialize both pressures to ``0.0``, far from their measured values, with a 5% uncertainty:

.. code:: json

    "state": {
        "A.pressure": {
            "type": "quantity",
            "value": 0.0,
            "magnitude": 1e5,
            "stdev": 0.05
        },
        "B.pressure": {
            "type": "quantity",
            "value": 0.0,
            "magnitude": 1e5,
            "stdev": 0.05
        }
    }

The ``model_noise_stdev`` simulation option sets the model uncertainty at the prediction step.

.. code:: json

    "simulation_options": {
        "model_noise_stdev": {
            "A.pressure": 0.0005,
            "B.pressure": 0.0005
        }
    }


Plot the estimation
"""""""""""""""""""

The :ref:`subplots_estimation <alias_subplots_estimation>` plot traces each estimated quantity with its confidence interval.
When it exists, it also traces the measurement columns named ``measurement.<name>``.
Since we renamed our measurements to the correct format, they will be traced along with the estimations.

.. code:: json

    "plots": {
        "estimation": {
            "type": "subplots_estimation",
            "abscissas": "time",
            "inputs": ["main", "measurements"],
            "subplots": ["A.pressure", "B.pressure"]
        }
    }

State Estimation Results
""""""""""""""""""""""""

The figure below show the first cycle of the simulation (double click to see the full 10 cycles).

.. raw:: html

    <figure class="align-center">
        <iframe src="estimation/2_state_estimation/state_estimation.html"
                width="100%" height="620"
                title="State estimation of the pressures at nodes A and B"></iframe>
        <figcaption>
            <p><span class="caption-text">State estimation of the pressures at nodes A and B.</span></p>
        </figcaption>
    </figure>


We set the model noise so the uncertainty is clearly visible on the graph.
Same for the measurement noise:
it is set so the state do not converge immediately to the measurements and the transition is visible on the first cycle.

Now that we know how the run an estimation simulation to estimate the state,
we will now add a parameter estimation.

Estimate a parameter
--------------------

We can add parameters to the state, thus creating an **extended state** composed from the **state variables** and the **estimated parameters**.

In this section, we will see how to:

* Add a parameter estimation to the simulation
* Add a transformation to constrain extended state quantities

Estimated Parameters
""""""""""""""""""""

To estimate a **parameter**, we move it from the ``parameters`` to the ``estimated_parameters`` field.

Our measurements were generated with a resistance ``Rb = 1.0e8``. 
Let's add a parameter estimation for ``Rb`` with a wrong initial guess to get back the value used to generate the measurements.

.. code:: json

    "estimated_parameters": {
        "Rb": {
            "type": "quantity",
            "value": 5.0e8, // wrong initial guess
            "magnitude": 1e8,
            "stdev": 0.5 // large standard deviation
        }
    }

We also add a model noise for ``Rb`` that is now in the state:

.. code:: json

    "model_noise_stdev": {
        "A.pressure": 1e-4,
        "B.pressure": 1e-4,
        "Rb": 1e-4
    }

.. note::

    Note that we reduced the model noise from earlier on the pressures.
    We also reduce their initial standard deviation to 1%.

Add a transformation
""""""""""""""""""""

The filter may produce values without physical meaning, like a negative resistance.
We can add a **transformation** to constrain the **extended state** quantities in the model:
the filter works on an unbounded value while the model uses a constrained value.

Here we keep ``Rb`` strictly positive using the :class:`power_transform <physioblocks.library.functions.transform.PowerTransform>` transformation.

.. code:: json

    "transformation_operators": {
        "Rb": {"type": "power_transform", "scaling_factor": 1.0e8}
    }

Available transformations are documented in the :mod:`transform module<physioblocks.library.functions.transform>`.

Complete configuration file
"""""""""""""""""""""""""""

Here is the complete configuration file for our example:

.. code:: json

    {
        "type": "estimation_simulation",
        "filter_type": "unscented_kalman_filter",
        "solver": {"type": "linear_solver"},
        "time": {
            "type": "range",
            "start": 0.0,
            "length": 10.0,
            "step_size": 0.001
        },
        "simulation_options": {
            "model_noise_stdev": {
                "A.pressure": 1e-4,
                "B.pressure": 1e-4,
                "Rb": 1e-4
            },
            "transformation_operators": {
                "Rb": {"type": "power_transform", "scaling_factor": 1.0e8}
            }
        },
        "net": {
            "type": "simple_circulation_net_example",
            "boundaries_conditions": {
                "C": [{"type": "condition", "condition_type": "pressure", "condition_id": "C.pressure"}],
                "A": [{"type": "condition", "condition_type": "flow", "condition_id": "A.flow"}]
            }
        },
        "state": {
            "A.pressure": {
                "type": "quantity",
                "value": 0.0,
                "magnitude": 1e5,
                "stdev": 0.01
            },
            "B.pressure": {
                "type": "quantity",
                "value": 0.0,
                "magnitude": 1e5,
                "stdev": 0.01
            }
        },
        "estimated_parameters": {
            "Rb": {
                "type": "quantity",
                "value": 5.0e8,
                "magnitude": 1e8,
                "stdev": 0.5
            }
        },
        "parameters": {
            "Ca": 2.0e-10,
            "Ra": 8.0e6,
            "Cb": 1.7e-08,
            "C.pressure": 1.6e3,
            "heartbeat_duration": 1.0
        },
        "update_functions": {
            "A.flow": {
                "type": "piecewise_linear_periodic",
                "evaluation_quantities": {"time": "time"},
                "period": "heartbeat_duration",
                "points_abscissas": [0.0, 0.075, 0.134, 0.142, 0.281],
                "points_ordinates": [0.0, 0.0, 0.5e-3, 0.5e-3, 0.0]
            }
        },
        "data": {
            "measurements": {
                "type": "read_data",
                "filepath": "path/to/simple_circulation_results.csv"
            }
        },
        "preprocesses": {
            "rename_measurements": {
                "type": "rename_process",
                "inputs": ["measurements"],
                "outputs": ["measurements"],
                "mapping": {"A.pressure": "measurement.A.pressure"}
            }
        },
        "observer": {
            "type": "observer",
            "observations": {
                "observation.A.pressure": {
                    "type": "observation",
                    "measurement": "measurement.A.pressure",
                    "operator": {
                        "type": "watch_quantity",
                        "evaluation_quantities": {"quantity": "A.pressure"}
                    },
                    "magnitude": 1e5,
                    "stdev": 1e-4
                }
            }
        },
        "plots": {
            "estimation": {
                "type": "subplots_estimation",
                "abscissas": "time",
                "inputs": ["main", "measurements"],
                "subplots": ["A.pressure", "B.pressure", "Rb"]
            }
        }
    }

Note that we updated the plots to add ``Rb``.
We also set a lower measurement noise than for the first example.

Parameters Estimation Results
"""""""""""""""""""""""""""""

The figure below shows the results for our configuration. 

.. raw:: html

    <figure class="align-center">
        <iframe src="estimation/3_parameter_estimation/estimation_results.html"
            width="100%" height="920">
        </iframe>
        <figcaption>
            <p><span class="caption-text">"Estimation of the resistance Rb in the circulation net."</span></p>
        </figcaption>
    </figure>

    

``Rb`` is starting from our initial guess, then converges to ``1.0e8`` while its confidence interval narrows:
that is the ``Rb`` value used for measurement generation.


This concludes level 2 user guide documentation.
The next chapter is dedicated to Level 3 use cases. 
We will see how to write blocks and model components in that can be used with PhysioBlocks.

If you want to learn to write new :mod:`filter <physioblocks.library.filters>`, or :mod:`simulation functions <physioblocks.library.functions>`,
you will also find this in the :ref:`User Guide Level 3<user_guide_level_3>` section.