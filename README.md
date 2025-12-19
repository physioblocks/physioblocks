# PhysioBlocks

PhysioBlocks allows the simulation of dynamical models of physiological systems.

## User Levels

They are several use cases for PhysioBlocks depending on the user profile:

* __Level 1:__ Configure and run physiological systems simulation (for pre-existing systems)
* __Level 2:__ Create new systems with existing blocks without writing code
* __Level 3:__ Write and add new blocks to the library.

## Principle

* A __Net__ (system) is built from __Nodes__ and __Blocks__ connected by those nodes.
* At each node in the net, connected blocks share __Degrees of Freedom__ (ex: pressure) and send __Fluxes__ that verify Kirchhoff Law.
* __ModelComponents__ concatenate blocks equations to the global system (if necessary, for modularity purposes within the block)

## Interactions

__Level 1:__ Configure and run a simulation : JSON
* Update the model parameters

__Level 2:__ Create Nets : JSON
* Declare the nodes, the blocks, and the block - nodes connections


__Level 3:__ Write and add models to the library: Python
* Declare the quantities to use in the model
* Write the fluxes and equations

## Documentation

Here are the links to the sections of the [full documentation](https://physioblocks.gitlabpages.inria.fr/physioblocks/):
* [Installation](https://physioblocks.gitlabpages.inria.fr/physioblocks/installation.html)
* [User Guide](https://physioblocks.gitlabpages.inria.fr/physioblocks/user_guide.html)
* [Library](https://physioblocks.gitlabpages.inria.fr/physioblocks/library.html)
* [API Reference](https://physioblocks.gitlabpages.inria.fr/physioblocks/api_reference.html)

## Quick start

Complete instructions are available in the [documentation](https://physioblocks.gitlabpages.inria.fr/physioblocks/). This instructions will enable you to launch a reference simulation.

### Installation

This project requires a recent version of python installed.
Then: 
* Clone or download PhysioBlocks.
* With `$PHYSIOBLOCKS_PACKAGE_PATH$` the cloned repository:
```
    cd $PHYSIOBLOCKS_PACKAGE_PATH$
    pip install .
```

### Configuration

To configure PhysioBlocks Launcher:

```
# Create an empty folder where you want to store simulations results.
mkdir $LAUNCHER_FOLDER_PATH$

# Configure the folder
python -m physioblocks.launcher.configure -d $LAUNCHER_FOLDER_PATH$ -v
```

### Launch a simulation

With a Launcher folder configured:

```
# Move to your configured launcher folder
cd $LAUNCHER_FOLDER_PATH$

#  Launch a reference simulation
python -m physioblocks.launcher $PHYSIOBLOCKS_PACKAGE_PATH$/references/spherical_heart_sim.jsonc -v -t

# This can take some time.
```


Results will be available in the `$LAUNCHER_FOLDER_PATH$/simulations/Z` series folder.