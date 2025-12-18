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


Set a configurable Block
========================

Register the Block Type
-----------------------

To make a :class:`~physioblocks.computing.models.Block` object configurable, we have to register the **block type** with a **type name** we can use in the configuration.

This is done with the ``@register_type`` decorator. 

.. note::

    Every ``type`` name we use in configuration files are registered this way.

Let's register our :class:`~physioblocks.library.blocks.capacitances.RCRBlock` from the last example.

.. code:: python

    @dataclass
    @register_type("rcr_block")
    class RCRBlock(Block):

        # Block Definition here

Dynamic Block import at simulation runtime
------------------------------------------

To use the :class:`~physioblocks.computing.models.Block` object in any configuration, it has to be imported when we use the launcher.
Since we don't want to update the launcher module every time new blocks need to be imported, we import the block modules **dynamically**.

Dynamically import Blocks with the launcher
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When you configure a launcher (see the :ref:`level 1 User Guide <user_guide_level_1_launcher_configuration>`), the ``user_library`` folder is created.
Every module in the folder (and in the recursive sub-folders you created with a ``__init__.py`` file at the root) will be imported dynamically.

To use your own :class:`~physioblocks.computing.models.Block` object with the launcher, just drop your block file in the folder.

.. note:: 

    For our example RCR Block is already in the PhysioBlocks library.
    You don't have to copy its definition to the ``user_library`` folder.

.. The following sub-section is not implemented

.. Update the ``user_library`` and ``user_aliases`` location 
.. ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. You can also personalize the folder from where the blocks are imported.

.. In the launcher folder you configured, there is a ``launcher.json`` file.
.. The configuration has two fields each matching a list:

..     * **libraries**: list modules import paths.
..     * **aliases**: list of aliases import paths.

.. You can update those lists to add or modify the path from where the aliases and module are loaded when you run the launcher.

Now that we know how a :class:`~physioblocks.computing.models.Block` object can be used with the launcher, we are going to see how to use it in a net description.

Set up a Block Alias
--------------------

A net actually holds :class:`~physioblocks.description.blocks.BlockDescription` objects and not :class:`~physioblocks.computing.models.Block` objects.
It is the block description that holds the **block type**.

So if we wanted to use our :class:`~physioblocks.computing.models.Block` in a net description file now, it would look like this:

.. code:: json

    {
        "nodes": ["..."],
        "blocks": {
            "block_k": {
                "type": "block_description",
                "model_type": "rcr_block",
                "flux_type": "the flux type definition here",
                "nodes": "..." 
            }
        }
    }

We can simplify the block description saving an alias for your specific **block type**:

.. code:: json

    {
        "type": "block_description",
        "model_type": "rcr_block",
        "time": "time" 
    }

.. note::

    The RCR block has already an alias defined in the PhysioBlocks library.
    Otherwise to use it you would have to save the alias to the ``user_aliases`` folder.

Notice that we also set the time parameter to match the global name for the simulation time in our alias.
The net definition now simplifies:

.. code:: json

    {
        "nodes": ["..."],
        "blocks": {
            "block_k": {
                "type": "rcr_block",
                "flux_type": "the flux type definition here",
                "nodes": "..." 
            }
        }
    }

We now know how to use :class:`~physioblocks.computing.models.Block` we wrote in a net configuration file. 
In the next section, we will see how to test the :class:`~physioblocks.computing.models.Block` objects we created with the ``gradient_test`` module.