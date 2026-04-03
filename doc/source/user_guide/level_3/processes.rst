.. _user_guide_level_3_process :

**********************************
Write pre and post-process scripts
**********************************

In this section, you will learn how to write new **Process** and make them available to configure for a level 2 user.

We will first present the **process pipeline** in Physioblocks.
Then we will see how to write a process that can be integrated in the pipeline.

The processes pipeline
======================

In this section, we will detail the **main phases** of the **pipeline**. 
Then we will first describe main characteristics of the **process**.
Finally, we will see the role of :func:`~physioblocks.simulation.process.run_processes` in the pipeline.


Pipeline Description:
---------------------

The **pipeline** is *a set of processes applied to a dictionary of dataframes*.
User can select dataframes to pass to each process in the pipeline.
The processes **produce dataframes** and **update the global pipeline data** with the results

Main phases of the pipeline
^^^^^^^^^^^^^^^^^^^^^^^^^^^

At each phase of the pipeline, a set of processes is applied to the data.

* **Pre-processes** are run before the simulation starts.
  They typically create data from or transform the simulation initial parameters.
* **Simulation** phase run the model defined by the net.
  It produces a dataframe that is added to the data dictionary with the simulation ``name`` as key (default is ``main``)
* **Post-processes** are run after the simulation completes.
  They create data from or transform the simulation results.
* **Plot-processes** are specialized post-processes that create graphs from data.

The Process:
------------

During the pipeline execution, we execute processes.
Each process is composed from:

* ``run`` method is the core of the process. It performs operations on dataframes.
* ``inputs`` is a list data IDs.
  It determines which data is passed to the ``run`` method among the global data of the pipeline.
* ``outputs`` is a list data IDs.
  It determines which IDs in the global pipeline data are updated with the process result.
* Processes can have additional parameters.
  They are defined as attributes in the process class and can be set by the configuration.

The ``run_processes`` function
------------------------------

The :func:`~physioblocks.simulation.process.run_processes` function executes a set of processes on a input data dictionary.
It is **called at each phase of the pipeline** to run all the processes of a phase.

For each process in the order of definition in the configuration, it: 

    1. Checks the process is properly initialized calling the ``can_run`` property
    2. Checks that all required inputs are available in the data dictionary.
    3. Calls the process run method and updates the data dictionary with the outputs IDs

.. note:: 

    If checks do not pass, the process is skipped and the pipeline continues.
    It allows the user to not fully configure every process and still be able to run the pipeline.
    It is especially useful to configure optional processes that only run when conditions are met.

Writing a process
=================

To create a new **configurable process**, you have to inherit from :class:`~physioblocks.simulation.process.AbstractProcess` and:

1. Register the process type with an ID.
   As we covered in :ref:`previous chapter on blocks<user_guide_level_3_blocks>`, it allows to use the process in a configuration file using the registered key.
2. Define the process specific parameters with annotations and initialize them in the constructor.
3. Implement the run method. 

Here's a basic example:

.. code-block:: python

    from physioblocks.simulation.process import AbstractProcess
    from physioblocks.registers.type_register import register_type
    
    @register_type("my_process")
    class MyProcess(AbstractProcess):
        """My custom process description."""
        
        # Define process-specific parameters
        my_parameter: str
        
        def __init__(self, my_parameter: str, *args, **kwargs):            
            # transmit input and output arguments to the base class 
            super().__init__(*args, **kwargs)

            # Define process-specific parameters
            self.my_parameter = my_parameter
            
        
        def run(self, *dfs) -> list[DataFrame]:
            """Process implementation"""
            # Process the input dataframes
            results = []
            for df in dfs:
                processed_df = df.copy()
                # process the dataframe copy here
                results.append(processed_df)
            return results

.. note::

    Note that we work on dataframes copy.
    We don't want to update the input dataframes in the process,
    the pipeline is in charge of updating the data dictionary according to user configuration.
    (Most of the time you won't have to copy the data frame like in this example since pandas do not modify dataframes directly)

Adding process checkers
-----------------------

**Process checkers** are optional methods that validate whether a process can run or not.
They are registered using the :func:`~physioblocks.simulation.process.run_method_checkers` decorator.
Every checker registered on a process is called when testing the process ``can_run`` property.

The decorator allows to register a function that takes a process and returns a boolean.
To add a checker you will have to:

1. Define a checker function
2. Register it with the decorator

Let's take our previous example and check that a new parameter `my_positive_float` is correctly initialized.

.. code-block:: python

    from __future__ import annotation

    # declare checker function
    def my_positive_checker(process: MyProcess) -> bool:
        return process.my_positive_float >= 0.0

    @register_type("my_process")
    @run_method_checkers(my_positive_checker) # Register the checker
    class MyProcess(AbstractProcess):
        
        # process-specific parameter annotation
        my_positive_float: float

This is a simple example, you can write more **generic checkers** with function factories.
The :func:`~physioblocks.base.function_factories.attribute_checker` is an example of a generic checker factory.
It provides a checker that tests the attribute exists and is initialized for the given parameter name.

Let's use it in our example to check all attributes are initialized.

.. code-block:: python

    from __future__ import annotation

    @register_type("my_process")
    @run_method_checkers(attribute_checker("my_positive_float"), attribute_checker("my_parameter"), my_positive_checker) # Register the checkers
    class MyProcess(AbstractProcess):
        
        # process-specific parameter annotation
        my_positive_float: float
        my_parameter: str

Now we have a process that will only run if all attributes are correctly initialized.

Special processes:
------------------

There are two other types of process inheriting from :class:`~physioblocks.simulation.process.AbstractProcess`

* :class:`~physioblocks.simulation.runtime.AbstractSimulationProcess`: process that has access to its **parent simulation**.
  The simulation parameters is initialized by the simulation when it runs all processes.
  An example of implementation is the :class:`~physioblocks.library.processes.espvr_edpvr_process.EspvrEdpvrProcess`.
* :class:`~physioblocks.simulation.process.AbstractPlotProcess`: process that has ``plot_name`` and ``folder_path`` parameters.
  The parameters are initialized to the **process name and the simulation folder path** respectively before launching the plot processes phase.
  Therefore, users do not have to set them in the configuration.
  The :class:`~physioblocks.library.processes.plot_processes.PlotProcess` and :class:`~physioblocks.library.processes.plot_processes.SubplotProcess` are already implemented in the library and cover most of the needs for plot processes.
