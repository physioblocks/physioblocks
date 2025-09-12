# Physioblocks

Physioblocks allows the simulation of dynamical models of physiological systems.

## User Levels

They are several use cases for physioblocks depending on the user profile:

* __Level 1:__ Configure and run physiological systems simulation (for pre-existing systems)
* __Level 2:__ Create new systems with existing blocks without writting code
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