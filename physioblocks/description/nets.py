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

"""
Define the :class:`~.Net` object that organises
:class:`~physioblocks.description.blocks.BlockDescription` and
:class:`~.Node` to describe the global system.
"""

from __future__ import annotations

from dataclasses import dataclass
from pprint import pformat
from typing import Any

from physioblocks.description.blocks import (
    ID_SEPARATOR,
    BlockDescription,
    ModelComponentDescription,
)
from physioblocks.description.flux import Dof, get_flux_dof_register
from physioblocks.registers.type_register import register_type

# Get all defined flux types
_flux_type_register = get_flux_dof_register()

# Constant for the net type id
NET_TYPE_ID = "net"

# Constant for the boundary condition type
BOUNDARY_CONDITION_ID = "condition"


@dataclass
@register_type(BOUNDARY_CONDITION_ID)
class BoundaryCondition:
    """
    Holds boundary condition description.
    """

    condition_type: str
    """The condition type id"""
    condition_id: str
    """The name of the parameter"""


class Node:
    """
    **Global Node** in a :class:`~.Net` object.

    They hold a set of :class:`~physioblocks.description.flux.Dof` and
    :class:`~.BoundaryCondition`. They define one
    dof per **Flux Type**.

    For every block sharing a flux at the node, it holds its name in the net
    matching the local node index of the flux.

    Different **Flux types** can be shared at the same node, but they will
    not mix (.ie **Flux** are only summed with the other **Flux** of the same type).
    Consequently, each node adds one equation per **Flux Type**
    to the **Global System**.

    :param node_id: the name of the node in the net
    :type node_id: str
    """

    _unique_id: str
    """the node id in the net"""

    _dofs: list[Dof]
    """the DOFs of the fluxes at the node"""

    _local_nodes: list[tuple[str, int]]
    """the ids of the blocks and their local node present at the global node"""

    _boundary_conditions: list[BoundaryCondition]
    """boundary condition types at the node (empty if the node is not a boundary)"""

    def __init__(self, node_id: str) -> None:
        self._unique_id = node_id
        self._dofs = []
        self._local_nodes = []
        self._boundary_conditions = []

    @property
    def name(self) -> str:
        """
        Get the name of the node in the net

        :return: the node name
        :rtype: str
        """
        return self._unique_id

    def has_flux_type(self, flux_type: str) -> bool:
        """
        Check if the flux type is defined at the node.

        :return: True if the flux type is accepted, False otherwise
        :rtype: bool
        """
        for dof in self._dofs:
            matching_flux_type = _flux_type_register.dof_flux_couples[dof.dof_type]
            if flux_type == matching_flux_type:
                return True
        return False

    def add_dof(self, dof_id: str, dof_type: str) -> None:
        """
        Create a :class:`~physioblocks.description.flux.Dof` object of the given type
        at the node.

        :param dof_id: the dof id.
        :type dof_id: str

        :param dof_type: the DOF type.
        :type dof_type: str

        :raise ValueError: raises a Value Error if the Dof type is not registered.
        """
        if dof_type not in _flux_type_register.dof_flux_couples:
            raise ValueError(
                str.format(
                    "Can not create a Dof with unregister dof type {0}",
                    dof_type,
                )
            )

        dof = Dof(dof_id, dof_type)
        self._dofs.append(dof)

    def remove_dof(self, dof_type: str) -> None:
        """
        Remove the DOF of the given type.

        :param dof_type: the DOF type.
        :type dof_type: str
        """
        for dof in self._dofs:
            if dof.dof_type == dof_type:
                self._dofs.remove(dof)
                break

    @property
    def dofs(self) -> list[Dof]:
        """
        Get all DOFs at the node.

        :return: all the DOFs at the node.
        :rtype: list[Dof]
        """
        return self._dofs.copy()

    def get_flux_dof(self, flux_type: str) -> Dof:
        """
        Get the DOF matching the flux type.

        :param flux_type: the flux type.
        :type flux_type: str

        :return: the DOF
        :rtype: Dof
        """
        for dof in self._dofs:
            matching_flux_type = _flux_type_register.dof_flux_couples[dof.dof_type]
            if flux_type == matching_flux_type:
                return dof

        raise KeyError(str.format("No dof matching the flux type {0}", flux_type))

    def get_dof(self, dof_id: str) -> Dof:
        """
        Get a DOF with the given id.

        :param dof_id: id of the DOF to get
        :type dof_id: str

        :raise KeyError: Error raised when there are no DOFs with the given id at
          the node.

        :return: the DOF if it exists
        :rtype: Dof
        """
        for dof in self._dofs:
            if dof.dof_id == dof_id:
                return dof
        raise KeyError(str.format("{0} is not defined at node {1}.", dof_id, self.name))

    @property
    def is_boundary(self) -> bool:
        """
        Check if the node is defines a boundary of the net.

        :return: True if the node is a boundary, False otherwise
        :rtype: bool
        """
        return len(self._boundary_conditions) > 0

    @property
    def boundary_conditions(self) -> list[BoundaryCondition]:
        """
        Get the boundary conditions at the node.

        This is a list of string representing the boundary condition
        types add the node.

        :return: a list the boundaries conditions
        :rtype: list[str]
        """
        return self._boundary_conditions.copy()

    def add_boundary_condition(
        self, condition_type: str, parameter_id: str
    ) -> BoundaryCondition:
        """
        Add a boundary condition at the node.

        A DOF or flux type matching the condition type should exist.

        :param condition_type: the flux or potential type
        :type condition_type: str

        :param parameter_id: the condition parameter global name
        :type parameter: str

        :raise ValueError: Raises a ValueError when no DOF or flux type is
          matching the condition type or when a matching type already has a boundary
          condition
        """
        matching_dof = [
            dof
            for dof in self._dofs
            if condition_type
            in [
                dof.dof_type,
                _flux_type_register.dof_flux_couples[dof.dof_type],
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
            condition_type == _flux_type_register.dof_flux_couples[dof.dof_type]
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
                _flux_type_register.flux_dof_couples[condition_type],
            ]
            if is_flux_condition
            else condition.condition_type
            in [
                condition_type,
                _flux_type_register.dof_flux_couples[condition_type],
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
        """
        Remove a boundary condition of the matching type.

        :param condition_type: the flux or potential type
        :type condition_type: str
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
        """
        Get all the local nodes.

        :return: The list of local nodes
        :rtype: list[tuple[str, int]]
        """
        return self._local_nodes.copy()

    def add_node_local(self, block_id: str, block_node_index: int) -> None:
        """
        Add a block local node to the global node.

        :param block_id: the block id in the net.
        :type block_id: int

        :param block_node_index: the local node index in the block
        :type block_node_index: int
        """
        self._local_nodes.append((block_id, block_node_index))

    def remove_node_local(self, block_id: str, block_node_index: int) -> None:
        """
        Remove a block local node from the global node.

        :param block_id: the block id in the net.
        :type block_id: str

        :param block_node_index: the local node index in the block
        :type block_node_index: int
        """
        self._local_nodes.remove((block_id, block_node_index))

    def has_node_local(self, block_id: str, block_node_index: int) -> bool:
        """
        Check if a local node is linked to this global node.

        :param block_id: the block id in the net.
        :type block_id: str

        :param block_node_index: the local node index in the block
        :type block_node_index: int

        :return: True if the block local node is linked to this node, False otherwise
        :rtype: bool
        """
        return (block_id, block_node_index) in self._local_nodes


@register_type(NET_TYPE_ID)
class Net:
    """
    The **Net** stores the **Blocks** and linked them with **nodes**.

    It allows to create the global system.

        * Internal Equations of the blocks and their submodels are concatenated to the
          residual.
        * The fluxes shared at each node are summed by flux type and concatenated to
          the global system.
    """

    _blocks: dict[str, BlockDescription]
    """the collection of blocks in the net"""
    _nodes: dict[str, Node]
    """the collection of nodes in the net"""

    def __init__(self) -> None:
        self._nodes = {}
        self._blocks = {}

    @property
    def blocks(self) -> dict[str, BlockDescription]:
        """
        Get the :class:`~physioblocks.descriptions.BlockDescription` objects in the net.

        :return: the blocks descriptions in the net.
        :rtype: dict[str, BlockDescription]
        """
        return self._blocks.copy()

    @property
    def nodes(self) -> dict[str, Node]:
        """
        Get the :class:`~.Node` objects in the net.

        :return: the nodes in the net.
        :rtype: dict[str, Nodes]
        """
        return self._nodes.copy()

    @property
    def boundary_conditions(self) -> dict[str, list[BoundaryCondition]]:
        """
        Get :class:`~.BoundaryCondition` objects in the net with their matching
        node name.

        :return: the net boundaries conditions
        :rtype: dict[str, list[BoundaryCondition]]
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
        """
        Add a new node to the net.

        :param node_id: The node id.
        :type node_id: str

        :raise ValueError: Raise a ValueError if a node with the same id is already in
          the net.

        :return: the added node
        :rtype: Node
        """
        if node_id in self._nodes:
            raise ValueError(
                str.format(
                    "There is already a node with id {0} in the net",
                    node_id,
                )
            )

        node = Node(node_id)
        self._nodes[node_id] = node
        return node

    def remove_node(self, node_id: str) -> None:
        """
        Remove a node from the net.

        .. note::

            It also removes all the blocks linked to the node because their dofs no
            longer exists.

        :param node_id: The node id.
        :type node_id: str
        """
        # Remove all block at the node
        node = self._nodes[node_id]

        for loc_node in node.local_nodes:
            self.remove_block(loc_node[0])

        # Actualy remove the node
        self._nodes.pop(node_id)

    def add_block(
        self,
        block_local_id: str,
        block_description: BlockDescription,
        node_ids: dict[int, str],
    ) -> BlockDescription:
        """
        Add a block description in the net.

        The method returns a copy of the block updated with correct global and dofs ids
        in the net.

        :param block_description: the block to add
        :type block_description: BlockDescription

        :param node_ids: a mapping of local node indexes in the block to global nodes
          names in the net.
        :type node_ids: dict[int, str]

        :raise ValueError: Exception raised if the block is already in the net
          or if there is already a block with the given id.

        :return: the added block description
        :rtype: BlockDescription

        .. note::

            When adding a block to a net, every of its flux should be linked to a node.
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

        # link block local node to global node.
        dof_ids = {}
        for (
            node_index,
            flux_def,
        ) in block_description.described_type.fluxes_expressions.items():
            global_node_id = node_ids[node_index]
            global_node = self._nodes[global_node_id]

            # create new dof if necessary
            created_dof_types = [dof.dof_type for dof in global_node.dofs]
            dof_type = _flux_type_register.flux_dof_couples[block_description.flux_type]
            new_dof_id = ID_SEPARATOR.join([global_node_id, dof_type])
            # get matching local parameter in the block
            local_dof_id = flux_def.get_term(0).term_id
            if local_dof_id in block_description.described_type.local_ids:
                dof_ids[local_dof_id] = new_dof_id
                # else the dof is not used in the model
                # (it is only described to use in submodels)
            if dof_type not in created_dof_types:
                global_node.add_dof(new_dof_id, dof_type)

            # Add node local to node global
            global_node.add_node_local(block_description.name, node_index)

        # update global ids for the block with dof ids
        new_global_ids = block_description.global_ids
        new_global_ids.update(dof_ids)

        # create and save the block description
        block_description = BlockDescription(
            block_local_id,
            block_description.described_type,
            block_description.flux_type,
            new_global_ids,
            block_description.submodels,
        )

        self._blocks[block_local_id] = block_description

        return self._blocks[block_local_id]

    def remove_block(self, block_id: str) -> None:
        """
        Remove a block from the net.

        Also removes the dofs at the global nodes that no longer exists when this
        block is deleted (the dofs that are not linked to any block when the block
        is removed).

        :param block_id: the block id to remove
        :type block_id: str
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
                dof_flux_type = _flux_type_register.dof_flux_couples[dof.dof_type]
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
        """
        Get the id of the global node linked to the given local node.

        :param block_id: the id of the block in the net
        :type block_id: str

        :param index_block_node: the index of the local node in the block
        :type index_block_node: int

        :raise ValueError:
          Raise a ValueError if no globla node is linked to the given local node.

        :return: the global node name
        :rtype: str
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
        """
        Set a :class:`~.BoundaryCondition` object in the net.

        :param node_id: the index of the node where to set the boundary condition
        :type node_id: str

        :param condition_type: the flux or dof type of the condition.
        :type condition_type: str

        :param parameter_id: the condition matching parameter id
        :type parameter: str
        """
        node = self._nodes[node_id]
        matching_dof = [
            dof
            for dof in node.dofs
            if condition_type
            in [
                dof.dof_type,
                _flux_type_register.dof_flux_couples[dof.dof_type],
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
            and bc.condition_type in _flux_type_register.dof_flux_couples
        ):
            # rename potentiel with the new id in all blocks and models
            for block in self._blocks.values():
                self._rename_block_ids_rec(block, old_dof_id, bc.condition_id)

    def _rename_block_ids_rec(
        self, model: ModelComponentDescription, old: str, new: str
    ) -> None:
        model.rename_global_id(old, new)

        for submodel in model.submodels.values():
            self._rename_block_ids_rec(submodel, old, new)

    def remove_boundary(self, node_id: str, condition_type: str) -> None:
        """
        Remove a boundary condition from the net.

        :param node_id: the node name where the condition is
        :type node_id: str

        :param condition_type: the flux or dof type for the condition
        :type condition_type: str
        """
        node = self._nodes[node_id]
        node.remove_boundary_condition(condition_type)
