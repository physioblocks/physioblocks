# SPDX-FileCopyrightText: Copyright INRIA
#
# SPDX-License-Identifier: LGPL-3.0-only
#
# Copyright INRIA
#
# This file is part of PhysioBlocks, a library mostly developed by the
# [Ananke project-team](https://team.inria.fr/ananke) at INRIA.
#
# Authors:
# - Colin Drieu
# - Dominique Chapelle
# - François Kimmig
# - Philippe Moireau
#
# PhysioBlocks is free software: you can redistribute it and/or modify it under the
# terms of the GNU Lesser General Public License as published by the Free Software
# Foundation, version 3 of the License.
#
# PhysioBlocks is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE. See the GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License along with
# PhysioBlocks. If not, see <https://www.gnu.org/licenses/>.

"""Declare the :class:`~.Net` that describes the global system.

The :class:`Net` defines :class:`Blocks <.Block>`,
:class:`ModelComponents <.ModelComponent>`, Flux and :class:`Nodes <Node>` relations.

See Also
--------
~.Block
    Models describing fluxes expressions.
~.BlockDescription
    Describe the block flux connections in the net.
~.ModelComponent
    Models describing internal equations and saved quantities.
~.ModelComponentDescription
    Describe the model components used as submodels in the net.
"""

from __future__ import annotations

from dataclasses import dataclass
from pprint import pformat
from typing import Any

from physioblocks.description.blocks import (
    ID_SEPARATOR,
    BlockDescription,
)
from physioblocks.description.flux import Dof, FluxDofTypesRegister
from physioblocks.registers.type_register import register_type

# Constant for the net type id
NET_TYPE_ID = "net"

# Constant for the boundary condition type
BOUNDARY_CONDITION_ID = "condition"


@dataclass
@register_type(BOUNDARY_CONDITION_ID)
class BoundaryCondition:
    """Holds boundary condition description.

    Parameters
    ----------
    condition_type : str
        The condition type id
    condition_id : str
        The name of the parameter

    Configuration
    -------------

    The ``condition_type`` must be a flux or DOF type defined in the
    ``flux_dof_definitions`` item of the net.

    .. code-block:: json

        {
            "type": "condition",
            "condition_type": "<str>",  // Flux or DOF type set by the condition
            "condition_id": "<str>"     // Global name of the parameter setting the
                                        // condition value
        }

    """

    condition_type: str
    condition_id: str


class Node:
    """**Global Node** in a :class:`~.Net` object.

    They hold a set of :class:`~.Dof` and :class:`~.BoundaryCondition`. They define one
    dof per **Flux Type**.

    For every block sharing a flux at the node, it holds its name in the net
    matching the local node index of the flux.

    Different **Flux types** can be shared at the same node, but they will
    not mix (i.e. **Flux** are only summed with the other **Flux** of the same type).
    Consequently, each node adds one equation per **Flux Type**
    to the **Global System**.

    Parameters
    ----------
    flux_dof_register : FluxDofTypesRegister
        the relations between fluxes and dofs types.
    node_id : str
        the name of the node in the net
    """

    _unique_id: str
    _dofs: list[Dof]
    _local_nodes: list[tuple[str, int]]
    _boundary_conditions: list[BoundaryCondition]

    def __init__(self, flux_dof_register: FluxDofTypesRegister, node_id: str) -> None:
        self._unique_id = node_id
        self._dofs = []
        self._local_nodes = []
        self._boundary_conditions = []
        self._flux_type_register = flux_dof_register

    @property
    def name(self) -> str:
        """Get the name of the node in the net.

        Returns
        -------
        str
            the node name
        """
        return self._unique_id

    def has_flux_type(self, flux_type: str) -> bool:
        """Check if the flux type is defined at the node.

        Parameters
        ----------
        flux_type : str
            the flux type to test.

        Returns
        -------
        bool
            True if the flux type is accepted, False otherwise
        """
        for dof in self._dofs:
            matching_flux_type = self._flux_type_register.dof_flux_couples[dof.dof_type]
            if flux_type == matching_flux_type:
                return True
        return False

    def add_dof(self, dof_id: str, dof_type: str) -> None:
        """Create a Dof of the given type at the node.

        Parameters
        ----------
        dof_id : str
            the dof id.
        dof_type : str
            the DOF type.

        Raises
        ------
        ValueError
            if the Dof type is not registered.

        """
        if dof_type not in self._flux_type_register.dof_flux_couples:
            raise ValueError(
                str.format(
                    "Can not create a Dof with unregister dof type {0}",
                    dof_type,
                )
            )

        dof = Dof(dof_id, dof_type)
        self._dofs.append(dof)

    def remove_dof(self, dof_type: str) -> None:
        """Remove the DOF of the given type.

        Parameters
        ----------
        dof_type : str
            the DOF type.

        """
        for dof in self._dofs:
            if dof.dof_type == dof_type:
                self._dofs.remove(dof)
                break

    @property
    def dofs(self) -> list[Dof]:
        """Get all DOFs at the node.

        Returns
        -------
        list[Dof]
            all the DOFs at the node.

        """
        return self._dofs.copy()

    def get_flux_dof(self, flux_type: str) -> Dof:
        """Get the DOF matching the flux type.

        Parameters
        ----------
        flux_type : str
            the flux type.

        Returns
        -------
        Dof
            the DOF

        Raises
        ------
        KeyError
            if no DOF at the node matches the flux type.

        """
        for dof in self._dofs:
            matching_flux_type = self._flux_type_register.dof_flux_couples[dof.dof_type]
            if flux_type == matching_flux_type:
                return dof

        raise KeyError(str.format("No dof matching the flux type {0}", flux_type))

    def get_dof(self, dof_id: str) -> Dof:
        """Get a DOF with the given id.

        Parameters
        ----------
        dof_id : str
            id of the DOF to get

        Returns
        -------
        Dof
            the DOF if it exists

        Raises
        ------
        KeyError
            Error raised when there are no DOFs with the given id at
            the node.

        """
        for dof in self._dofs:
            if dof.dof_id == dof_id:
                return dof
        raise KeyError(str.format("{0} is not defined at node {1}.", dof_id, self.name))

    @property
    def is_boundary(self) -> bool:
        """Check if the node defines a boundary of the net.

        Returns
        -------
        bool
            True if the node is a boundary, False otherwise

        """
        return len(self._boundary_conditions) > 0

    @property
    def boundary_conditions(self) -> list[BoundaryCondition]:
        """Get the boundary conditions at the node.

        Returns
        -------
        list[BoundaryCondition]
            a list of the boundary conditions
        """
        return self._boundary_conditions.copy()

    def add_boundary_condition(
        self, condition_type: str, parameter_id: str
    ) -> BoundaryCondition:
        """Add a boundary condition at the node.

        A DOF or flux type matching the condition type should exist.

        Parameters
        ----------
        condition_type : str
            the flux or potential type
        parameter_id : str
            the condition parameter global name

        Returns
        -------
        BoundaryCondition
            the added boundary condition

        Raises
        ------
        ValueError
            if no DOF or flux type is matching the condition type or when a matching
            type already has a boundary condition.
        """
        matching_dof = [
            dof
            for dof in self._dofs
            if condition_type
            in [
                dof.dof_type,
                self._flux_type_register.dof_flux_couples[dof.dof_type],
            ]
        ]
        if len(matching_dof) != 1:
            raise ValueError(
                str.format(
                    "There are no potential or flux matching type {0} at node {1}.",
                    condition_type,
                    self.name,
                )
            )
        dof = matching_dof[0]
        is_flux_condition = (
            condition_type == self._flux_type_register.dof_flux_couples[dof.dof_type]
        )

        self._check_existing_condition(condition_type, is_flux_condition)

        bc = BoundaryCondition(condition_type, parameter_id)
        self._boundary_conditions.append(bc)

        # In the case of a potential: rename the dof
        if is_flux_condition is False:
            dof.dof_id = parameter_id

        return bc

    def _check_existing_condition(
        self, condition_type: str, is_flux_condition: bool
    ) -> None:
        # Test that the condition type or matching type is not already added at the node
        check_existing_condition = [
            condition.condition_type
            in [
                condition_type,
                self._flux_type_register.flux_dof_couples[condition_type],
            ]
            if is_flux_condition
            else condition.condition_type
            in [
                condition_type,
                self._flux_type_register.dof_flux_couples[condition_type],
            ]
            for condition in self._boundary_conditions
        ]

        if any(check_existing_condition):
            raise ValueError(
                str.format(
                    "A boundary condition on {0} is already added at node {1}.",
                    condition_type,
                    self.name,
                )
            )

    def remove_boundary_condition(self, condition_type: str) -> None:
        """Remove a boundary condition of the matching type.

        Parameters
        ----------
        condition_type : str
            the flux or potential type

        """
        found = False
        for boundary in self._boundary_conditions:
            if boundary.condition_type == condition_type:
                found = True
                break
        if found is True:
            self._boundary_conditions.remove(boundary)

    @property
    def local_nodes(self) -> list[tuple[str, int]]:
        """Get all the local nodes.

        Returns
        -------
        list[tuple[str, int]]
            The list of local nodes

        """
        return self._local_nodes.copy()

    def add_node_local(self, block_id: str, block_node_index: int) -> None:
        """Add a block local node to the global node.

        Parameters
        ----------
        block_id : str
            the block id in the net.
        block_node_index : int
            the local node index in the block

        """
        self._local_nodes.append((block_id, block_node_index))

    def remove_node_local(self, block_id: str, block_node_index: int) -> None:
        """Remove a block local node from the global node.

        Parameters
        ----------
        block_id : str
            the block id in the net.
        block_node_index : int
            the local node index in the block

        """
        self._local_nodes.remove((block_id, block_node_index))

    def has_node_local(self, block_id: str, block_node_index: int) -> bool:
        """Check if a local node is linked to this global node.

        Parameters
        ----------
        block_id : str
            the block id in the net.
        block_node_index : int
            the local node index in the block

        Returns
        -------
        bool
            True if the block local node is linked to this node, False otherwise

        """
        return (block_id, block_node_index) in self._local_nodes


@register_type(NET_TYPE_ID)
class Net:
    """Store the **Blocks** and link them with **nodes**.

    It allows to create the global system.

    * Internal Equations of the blocks and their submodels are concatenated to the
      residual.
    * The fluxes shared at each node are summed by flux type and concatenated to
      the global system.

    Parameters
    ----------
    flux_dof_type_register : FluxDofTypesRegister | None
        Initialization of the flux-dof types register. Default is None.

    Configuration
    -------------

    The net configuration links every block description fluxes to nodes of the net.

    .. code-block:: json

        {
            "type": "net",
            "flux_dof_definitions": {   // Flux type with its matching DOF type
                "<str>": "<str>"        // (optional, default: no flux types)
            },
            "nodes": ["<str>"],         // Names of the nodes
            "blocks": {                 // Block descriptions with their names
                "<str>": {
                    "type": "<block description type id>",
                    "nodes": {          // Net node name for each block local node
                        "<int>": "<str>"
                    }
                }
            },
            "boundaries_conditions": {  // Boundary conditions at each node
                "<str>": ["<condition type>"] // (optional, default: no conditions)
            }
        }

    Example
    -------
    .. tikz:: Simple circulation system block-node diagram
        :include: ../schemes/circulation_net_scheme.tex

    The configure this net with:

    * a flow condition entering node ``A``.
    * a pressure condition at node ``C``.

    We obtain the configuration :

    .. code-block:: json

        {
            "type": "net",
            "flux_dof_definitions": {"flow": "pressure"},
            "nodes": ["A", "B", "C"],
            "blocks": {
                "RC_1": {
                    "type": "rc_block",
                    "flux_type": "flow",
                    "resistance": "Ra",
                    "capacitance": "Ca",
                    "nodes":
                    {
                        "1": "B",
                        "2": "A"
                    }
                },
                "RC_2": {
                    "type": "rc_block",
                    "flux_type": "flow",
                    "resistance": "Rb",
                    "capacitance": "Cb",
                    "nodes":
                    {
                        "1": "C",
                        "2": "B"
                    }
                }
            },
            "boundaries_conditions": {
                "A": [
                    {
                        "type": "condition",
                        "condition_type": "flow",
                        "condition_id": "A.flow"
                    }
                ],
                "C": [
                    {
                        "type": "condition",
                        "condition_type": "pressure",
                        "condition_id": "C.pressure"
                    }
                ]
            }
        }

    See Also
    --------
    BoundaryCondition: Set the boundary conditions at the nodes.
    Node: The nodes in the net.
    ~.BlockDescription: The blocks in the net.
    ~.ModelComponentDescription: The components in the blocks.
    """

    _blocks: dict[str, BlockDescription]
    _nodes: dict[str, Node]

    def __init__(
        self, flux_dof_type_register: FluxDofTypesRegister | None = None
    ) -> None:
        self._nodes = {}
        self._blocks = {}
        self.flux_dof_type_register = (
            flux_dof_type_register
            if flux_dof_type_register is not None
            else FluxDofTypesRegister()
        )

    @property
    def blocks(self) -> dict[str, BlockDescription]:
        """Get all block descriptions in the net.

        Returns
        -------
        dict[str, BlockDescription]
            the blocks descriptions in the net.

        """
        return self._blocks.copy()

    @property
    def nodes(self) -> dict[str, Node]:
        """Get the :class:`~.Node` objects in the net.

        Returns
        -------
        dict[str, Node]
            the nodes in the net.

        """
        return self._nodes.copy()

    @property
    def boundary_conditions(self) -> dict[str, list[BoundaryCondition]]:
        """Get :class:`~.BoundaryCondition` in the net with their matching node name.

        Returns
        -------
        dict[str, list[BoundaryCondition]]
            the net boundaries conditions

        """
        boundaries = {
            node_id: node.boundary_conditions
            for node_id, node in self._nodes.items()
            if node.is_boundary
        }

        return boundaries

    def __str__(self) -> str:
        net_dict: dict[str, Any] = {}
        net_dict["Blocks"] = {
            block_id: block.described_type.__name__
            for block_id, block in self._blocks.items()
        }

        # for each node, the list of block ids at the node and the flux index they share
        net_dict["Nodes"] = {
            node_id: {
                block_id: "flux " + str(flux_index)
                for block_id, flux_index in node.local_nodes
            }
            for node_id, node in self._nodes.items()
        }

        # add boundary condition
        for node_id, node in self._nodes.items():
            if node.is_boundary is True:
                node_boundaries = {
                    bc.condition_id: bc.condition_type
                    for bc in node.boundary_conditions
                }
                net_dict["Nodes"][node_id]["Boundary Conditions"] = node_boundaries

        return pformat(net_dict, indent=2, compact=False)

    def add_node(self, node_id: str) -> Node:
        """Add a new node to the net.

        Parameters
        ----------
        node_id : str
            The node id.

        Returns
        -------
        Node
            the added node

        Raises
        ------
        ValueError
            Raise a ValueError if a node with the same id is already in
            the net.

        """
        if node_id in self._nodes:
            raise ValueError(
                str.format(
                    "There is already a node with id {0} in the net",
                    node_id,
                )
            )

        node = Node(self.flux_dof_type_register, node_id)
        self._nodes[node_id] = node
        return node

    def remove_node(self, node_id: str) -> None:
        """Remove a node from the net.

        .. note::

            It also removes all the blocks linked to the node because their dofs no
            longer exist.

        Parameters
        ----------
        node_id : str
            The node id.

        """
        # Remove all block at the node
        node = self._nodes[node_id]

        for loc_node in node.local_nodes:
            self.remove_block(loc_node[0])

        # Actually remove the node
        self._nodes.pop(node_id)

    def add_block(
        self,
        block_local_id: str,
        block_description: BlockDescription,
        node_ids: dict[int, str],
    ) -> BlockDescription:
        """Add a block description in the net.

        The method returns a copy of the block updated with correct global and dofs ids
        in the net.

        .. note::

            When adding a block to a net, every of its flux should be linked to a node.

        Parameters
        ----------
        block_local_id : str
            the id of the block in the net
        block_description : BlockDescription
            the block to add
        node_ids : dict[int, str]
            a mapping of local node indexes in the block to global nodes
            names in the net.

        Returns
        -------
        BlockDescription
            the added block description

        Raises
        ------
        ValueError
            Exception raised if there is already a block with the given id in
            the net or if the number of linked nodes does not match the block local
            nodes.

        """
        if block_local_id in self._blocks:
            raise ValueError(
                str.format(
                    "Block with id {0} is already defined in the net.",
                    block_local_id,
                )
            )

        if len(block_description.described_type.nodes) != len(node_ids):
            raise ValueError(
                str.format(
                    "Linked node ids list and {0} local nodes list size mismatch.",
                    block_local_id,
                )
            )

        # create a block description copy
        new_block_description = BlockDescription(
            block_local_id,
            block_description.described_type,
            block_description.flux_type,
            block_description.global_ids,
            block_description.submodels,
            block_description.alternative_types,
        )

        # link block local node to global node.
        dof_ids = {}
        for (
            node_index,
            flux_def,
        ) in new_block_description.described_type.fluxes_expressions.items():
            global_node_id = node_ids[node_index]
            global_node = self._nodes[global_node_id]

            # create new dof if necessary
            created_dof_types = [dof.dof_type for dof in global_node.dofs]
            dof_type = self.flux_dof_type_register.flux_dof_couples[
                new_block_description.flux_type
            ]
            new_dof_id = ID_SEPARATOR.join([global_node_id, dof_type])
            # get matching local parameter in the block
            local_dof_id = flux_def.get_term(0).term_id
            dof_ids[local_dof_id] = new_dof_id
            if dof_type not in created_dof_types:
                global_node.add_dof(new_dof_id, dof_type)

            # Add node local to node global
            global_node.add_node_local(new_block_description.name, node_index)

        # Rename block with dof ids
        for local_dof_id, global_dof_id in dof_ids.items():
            if local_dof_id in new_block_description.global_ids:
                new_block_description.rename_global_id(
                    new_block_description.global_ids[local_dof_id], global_dof_id
                )

        self._blocks[block_local_id] = new_block_description

        return new_block_description

    def remove_block(self, block_id: str) -> None:
        """Remove a block from the net.

        Also removes the dofs at the global nodes that no longer exist when this
        block is deleted (the dofs that are not linked to any block when the block
        is removed).

        Parameters
        ----------
        block_id : str
            the block id to remove

        """
        # Remove the block
        self._blocks.pop(block_id)

        # remove the block from nodes local indexes
        for node in self._nodes.values():
            to_remove = []
            for node_block_id, node_local_index in node.local_nodes:
                if node_block_id == block_id:
                    to_remove.append((node_block_id, node_local_index))
            for node_block_id, node_local_index in to_remove:
                node.remove_node_local(node_block_id, node_local_index)

        # If no blocks still links to the block global nodes,
        # remove the dof at this nodes.
        self.__clean_unlinked_dofs()

    def __clean_unlinked_dofs(self) -> None:
        for node in self._nodes.values():
            dof_types_to_remove = []
            for dof in node.dofs:
                dof_flux_type = self.flux_dof_type_register.dof_flux_couples[
                    dof.dof_type
                ]
                blocks_at_node = [local_node[0] for local_node in node.local_nodes]
                if (
                    any(
                        [
                            self._blocks[block_id].flux_type == dof_flux_type
                            for block_id in blocks_at_node
                        ]
                    )
                    is False
                ):
                    dof_types_to_remove.append(dof.dof_type)

            for dof_type in dof_types_to_remove:
                node.remove_dof(dof_type)

    def local_to_global_node_id(self, block_id: str, index_block_node: int) -> str:
        """Get the id of the global node linked to the given local node.

        Parameters
        ----------
        block_id : str
            the id of the block in the net
        index_block_node : int
            the index of the local node in the block

        Returns
        -------
        str
            the global node name

        Raises
        ------
        ValueError
            Raise a ValueError if no global node is linked to the given local node.

        """
        for node_id, node in self._nodes.items():
            if node.has_node_local(block_id, index_block_node):
                return node_id
        raise ValueError(
            str.format(
                "No Global Node is linked to the given local node ({0}:{1})",
                block_id,
                index_block_node,
            )
        )

    def set_boundary(
        self, node_id: str, condition_type: str, parameter_id: str
    ) -> None:
        """Set a :class:`~.BoundaryCondition` in the net.

        Parameters
        ----------
        node_id : str
            the id of the node where to set the boundary condition
        condition_type : str
            the flux or dof type of the condition.
        parameter_id : str
            the condition matching parameter id

        Raises
        ------
        ValueError
            if no dof or several dofs at the node match the condition type.

        """
        node = self._nodes[node_id]
        matching_dof = [
            dof
            for dof in node.dofs
            if condition_type
            in [
                dof.dof_type,
                self.flux_dof_type_register.dof_flux_couples[dof.dof_type],
            ]
        ]
        if len(matching_dof) == 0:
            raise ValueError(
                str.format(
                    "There is no dof matching condition_type {0} at node {1}",
                    condition_type,
                    node_id,
                )
            )
        elif len(matching_dof) > 1:
            raise ValueError(
                str.format(
                    "There are multiple dof matching condition_type {0} at node {1}",
                    condition_type,
                    node_id,
                )
            )

        old_dof_id = matching_dof[0].dof_id
        bc = node.add_boundary_condition(condition_type, parameter_id)

        if (
            bc.condition_id != old_dof_id
            and bc.condition_type in self.flux_dof_type_register.dof_flux_couples
        ):
            # rename potential with the new id in all blocks and models
            for block in self._blocks.values():
                block.rename_global_id(old_dof_id, bc.condition_id)

    def remove_boundary(self, node_id: str, condition_type: str) -> None:
        """Remove a boundary condition from the net.

        Parameters
        ----------
        node_id : str
            the node name where the condition is
        condition_type : str
            the flux or dof type for the condition

        """
        node = self._nodes[node_id]
        node.remove_boundary_condition(condition_type)

    def get_alternative_net(self, alternative_id: str) -> Net:
        """Get the alternative net assembling all blocks tagged with the alternative id.

        If boundary conditions and nodes are linked to the alternative blocks, they are
        recreated in the alternative nets.

        Parameters
        ----------
        alternative_id : str
            the tag of the alternative net.

        Returns
        -------
        Net
            the alternative net

        """
        net = Net(self.flux_dof_type_register)
        for block_id, block_desc in self.blocks.items():
            if alternative_id in block_desc.alternative_types:
                linked_nodes = {}
                alt_desc = block_desc.alternative_descriptions[alternative_id]

                for node_id, node in self.nodes.items():
                    for node_block_id, node_flux_id in node.local_nodes:
                        if (
                            node_block_id == block_id
                            and node_flux_id in alt_desc.fluxes
                        ):
                            linked_nodes[node_flux_id] = node_id

                for node_id in linked_nodes.values():
                    if node_id not in net.nodes:
                        net.add_node(node_id)

                net.add_block(
                    block_id,
                    alt_desc,
                    linked_nodes,
                )

        for node_id, boundary_conditions in self.boundary_conditions.items():
            if node_id in net.nodes:
                for bc in boundary_conditions:
                    if net.nodes[node_id].has_flux_type(
                        bc.condition_type
                    ) or bc.condition_type in [
                        dof.dof_type for dof in net.nodes[node_id].dofs
                    ]:
                        net.set_boundary(node_id, bc.condition_type, bc.condition_id)
        return net
