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

.. _user_guide_level_3_block_definition:

Declare a Block
===============

In this section we will learn to write a :class:`~physioblocks.computing.models.Block` object implementation along with an example from the library: the :class:`~physioblocks.library.blocks.capacitances.RCRBlock` implementation.

First we will summarize the objects we have to declare to implement a :class:`~physioblocks.computing.models.Block` object.
After a quick presentation of the :class:`~physioblocks.library.blocks.capacitances.RCRBlock` object, we will then go through each object definition with an example.

Block Definition
----------------

To define a :class:`~physioblocks.computing.models.Block` object, we have to declare the quantities and the functions needed to compute its **Fluxes**, **Internal Equations** and **Saved Quantities**.

But first, we have to distinguish what belongs to the :class:`~physioblocks.computing.models.Block` type, from what belongs exclusively to the :class:`~physioblocks.computing.models.Block` instance.
The :class:`~physioblocks.computing.models.Block` type holds:

    * **Flux** expressions
    * **Internal Equations** expressions
    * **Saved Quantities** expressions

They are shared among **Blocks** of the same type. The instance of a :class:`~physioblocks.computing.models.Block` however only holds:

    * Actual quantities needed to compute the :class:`~physioblocks.computing.models.Block` expressions

When writing a :class:`~physioblocks.computing.models.Block`, we are first going to declare **block quantities**, then write functions to compute the **block expressions**.
Then we will assign **expressions** combining those functions to the **block type**.

Let's see how to actually write a :class:`~physioblocks.computing.models.Block` with the :class:`~physioblocks.library.blocks.capacitances.RCRBlock` example.

The RCR Block 
-------------

We are represent the following model as a :class:`~physioblocks.computing.models.Block`.

.. tikz:: RCR Block Model
    
    \draw (3,3) node[above]{$P_{1}$} to[R=$R_{1}$, -*] (6,3) node[above]{$P_\text{mid}$}
    (3,3) to[short, *-, i=$Q_{1}$] (0,3) 
    (6,3) to[R=$R_{2}$] (9,3)
    node[below]{$P_{2}$} to[short, *-, i=$Q_{2}$] (12,3)
    (6,3) to[C=$C$] (6,0) node[ground]{};

The block has two fluxes, :math:`Q_{1}` and :math:`Q_{2}`.

.. math::
    
    Q_{1} = \frac{P_\text{mid} - P_{1}}{R_{1}}

.. math::
    
    Q_{2} = \frac{P_\text{mid} - P_{2}}{R_{2}}

The fluxes will be shared at nodes and participate to the dynamics of :math:`P_{1}` and :math:`P_{2}` when summed with the other fluxes at nodes of the net.

.. note:: 

    Fluxes are always expressed **towards the outlets** of the :class:`~physioblocks.computing.models.Block`.

We express the dynamics on :math:`P_\text{mid}` with the relation: 

.. math::
    
    C\dot{P}_\text{mid} - \frac{P_\text{mid} - P_{1}}{R_{1}} - \frac{P_\text{mid} - P_{2}}{R_{2}} = 0

We will add it as a **internal equation** to include :math:`P_\text{mid}` as an **internal variable** in the system.

Finally, we let's say we want to output the volume stored in the capacitance.
We are going to declare a **Saved Quantity**:

.. math::

    V_{\text{stored}} = C P_{\text{mid}}


Flux relations are discretized with a mid-point time scheme for consistency with other fluxes at the nodes.
We get :

.. math::
    
    Q_1^{n + \frac{1}{2}} = \frac{P_{\text{mid}}^{n + \frac{1}{2}} - P_1^{n + \frac{1}{2}}}{R_1}

.. math::
    
    Q_2^{n + \frac{1}{2}} = \frac{P_{\text{mid}}^{n + \frac{1}{2}} - P_2^{n + \frac{1}{2}}}{R_2}

The internal equations reads:

.. math::
    
    C\ \frac{P_{\text{mid}}^{n + 1} - P_{\text{mid}}^{n}}{\Delta t^n} - \frac{P_1^{n + \frac{1}{2}} - P_{\text{mid}}^{n + \frac{1}{2}}}{R_1} + \frac{P_2^{n + \frac{1}{2}} - P_{\text{mid}}^{n + \frac{1}{2}}}{R_2} = 0

For the saved quantity expression, we compute it for each time step at:

.. math::

    V_{\text{stored}}^n = C \ P_{\text{mid}}^n


.. note::

    You may notice that the :class:`~physioblocks.library.blocks.capacitances.RCRBlock` could also be defined in a net connecting two :class:`~physioblocks.library.blocks.capacitances.RCBlock`.
    A :class:`~physioblocks.library.blocks.capacitances.RCRBlock` object is still useful to define only one capacitance parameter.
    It also avoids to define the mid-point as a node if we don't want other block fluxes to connect to it.
    
    For our purpose, it is also a good example because it declares **Fluxes**, **Internal Equations** and **SavedQuantities** while being a simple block.


Creating the RCR Block class
----------------------------

Define the Block quantities
^^^^^^^^^^^^^^^^^^^^^^^^^^^

We will first define all the quantities needed in the block. 
To create the :class:`~physioblocks.computing.models.Block` from a configuration file, we are going to need the :class:`~physioblocks.computing.models.Block` class members to be annotated and the class constructor to match the class members.
This is implemented by making the :class:`~physioblocks.computing.models.Block` class a dataclass with the ``@dataclass`` decorator.

.. code:: python

    from dataclasses import dataclass
    from physioblocks.computing.model import Block
    from physioblocks.computing.quantities import Quantity
    from physioblocks.simulation.time_manager import Time

    # Dataclass decorator provides a constructor for annotated members.
    @dataclass
    class RCRBlock(Block):
        """
        RCR Block definition.
        """

        # Annotate the needed quantities
        pressure_1: Quantity
        """Pressure at the first local node of the block"""

        pressure_mid: Quantity
        """Pressure at the mid point of the block"""

        pressure_2: Quantity
        """Pressure at the second local node of the block"""

        resistance_1: Quantity
        """Resistance value at the first local node of the block"""

        resistance_2: Quantity
        """Resistance value at the second local node of the block"""

        capacitance: Quantity
        """Capacitance value of the block"""

        time: Time
        """The simulation time"""


Declare functions to compute the fluxes and the internal equations
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

We define methods to compute the :class:`~physioblocks.computing.models.Block` relations as written above in the discretized form.

To make the methods available to build the residual matrix the methods are decorated to identify:
    
    * **Fluxes** with :func:`~physioblocks.computing.models.declares_flux` decorator.
      You will need to set the local node index where the flux is shared as well as the local name in the block of the dof at the node.
      The default flux size is 1 but can be updated.
    * **Internal equations** with :func:`~physioblocks.computing.models.declares_internal_equation` decorator.
      You need to set at least the local name of the variable on which the equation provides a dynamic.
      Default equation size is set to 1 and can be updated.


.. code:: python

    # Flux definition

    @declares_flux(1, "pressure_1")
    def flux_1(self):
        """
        Computes the flux at first node.
        """
        pressure_mid_discr = 0.5 * (self.pressure_mid.new - self.pressure_mid.current)
        pressure_1_discr = 0.5 * (self.pressure_1.new - self.pressure_1.current)
        
        return (pressure_mid_discr - pressure_1_discr) / self.resistance_1.current

    @declares_flux(2, "pressure_2")
    def flux_2(self):
        """
        Computes the flux at second node.
        """
        pressure_mid_discr = 0.5 * (self.pressure_mid.new - self.pressure_mid.current)
        pressure_2_discr = 0.5 * (self.pressure_2.new - self.pressure_2.current)
        
        return (pressure_mid_discr - pressure_2_discr) / self.resistance_2.current

    # Internal Equation definition
    @declares_internal_equation("pressure_mid")
    def residual_pressure_mid(self):
        """
        Computes the rcr block internal equation residual
        """
        pressure_mid_discr = 0.5 * (self.pressure_mid.new - self.pressure_mid.current)
        pressure_1_discr = 0.5 * (self.pressure_1.new - self.pressure_1.current)
        pressure_2_discr = 0.5 * (self.pressure_2.new - self.pressure_2.current)
        
        return (
            self.capacitance * (self.pressure_mid.new - self.pressure_mid.current) * self.time.inv_dt # time quantity also define its inverse.
            - (pressure_1_discr - pressure_mid_discr) / self.resistance_1
            - (pressure_2_discr - pressure_mid_discr) / self.resistance_2
        )

To be able to add output values that are not variables, we identify the saved quantities with :func:`~physioblocks.computing.models.declares_saved_quantity` decorator.

.. code:: python

    # Saved Quantity definition
    @declares_saved_quantities("volume")
    def volume_stored(self):
        """
        Computes volume stored in the capacitance.
        """
        return self.pressure_mid.current * self.capacitance

Declare all flux and internal equations partial derivatives
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

We then have to declare functions to compute fluxes and internal equations partial derivatives.

To make the methods available to build the gradient matrix, the methods are decorated to identify function partial derivative with :func:`~physioblocks.computing.models.ExpressionDecorator.partial_derivative` decorator.
Each decorator associate the function with its the derivation variable local name.

.. code:: python

    # Flux 1 partial derivatives
    @flux_1.partial_derivative("pressure_mid")
    def dflux_1_dpressure_mid(self):
        """
        Computes flux_1 partial derivative for pressure_mid.
        """
        
        return 0.5 / self.resistance_1.current

    @flux_1.partial_derivative("pressure_1")
    def dflux_1_dpressure_1(self):
        """
        Computes flux_1 partial derivative for pressure_1.
        """
        
        return - 0.5 / self.resistance_1.current
        
    # Flux 2 partial derivatives

    @flux_2.partial_derivative("pressure_mid")
    def dflux_2_dpressure_mid(self):
        """
        Computes flux_2 partial derivative for pressure_mid.
        """
        
        return 0.5 / self.resistance_2.current

    @flux_2.partial_derivative("pressure_2")
    def dflux_2_dpressure_2(self):
        """
        Computes flux_2 partial derivative for pressure_2.
        """
        
        return - 0.5 / self.resistance_2.current

    # Internal equation partial derivatives:

    @residual_pressure_mid.partial_derivative("pressure_mid")
    def dresidual_pressure_mid_dpressure_mid(self):
        """
        Computes internal equation partial derivative for pressure_mid.
        """
        
        return (
            self.capacitance * self.time.inv_dt
            + 0.5 / self.resistance_1
            + 0.5 / self.resistance_2
        )

    @residual_pressure_mid.partial_derivative("pressure_1")
    def dresidual_pressure_mid_dpressure_1(self):
        """
        Computes internal equation partial derivative for pressure_1.
        """
        return (
            - 0.5 / self.resistance_1
        )

    @residual_pressure_mid.partial_derivative("pressure_2")
    def dresidual_pressure_mid_dpressure_2(self):
        """
        Computes internal equation partial derivative for pressure_2.
        """
        return (
            - 0.5 / self.resistance_2
        )


Now the :class:`~physioblocks.library.blocks.capacitances.RCRBlock` is completely defined and can be used in a net.

However, if we want to use it with configuration files, a few more steps are required as we are going to see in the next part.
