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

from typing import Any

from physioblocks.configuration.base import Configuration, ConfigurationError
from physioblocks.configuration.constants import (
    BLOCKS_ITEM_ID,
    BOUNDARIES_ID,
    FLUX_DOF_DEFINITION_ID,
    NET_ID,
    NODES_ITEM_ID,
)
from physioblocks.configuration.functions import load, save
from physioblocks.description.blocks import BlockDescription
from physioblocks.description.flux import get_flux_dof_register
from physioblocks.description.nets import BoundaryCondition, Net
from physioblocks.registers.load_function_register import loads
from physioblocks.registers.save_function_register import saves


@saves(Net)
def save_net_config(net: Net, *args: Any, **kwargs: Any) -> Configuration:
    """
    Create a Configuration for a net

    :param net: the net
    :type net: Net

    :return: the configuration
    :rtype: Configuration
    """
    # save blocks
    blocks_config = save(net.blocks, *args, **kwargs)
    if isinstance(blocks_config, dict) is False:
        raise ConfigurationError(
            str.format(
                "Expected a dict for {0} configuration, got {1}.",
                BLOCKS_ITEM_ID,
                type(net.blocks).__name__,
            )
        )

    # add node informations
    for block_id, block in net.blocks.items():
        block_connections = {
            str(node_index): net.local_to_global_node_id(block_id, node_index)
            for node_index in block.described_type.nodes
        }

        blocks_config[block_id][NODES_ITEM_ID] = block_connections

    node_ids = list(net.nodes.keys())
    flux_dof_register = get_flux_dof_register()

    net_config = Configuration(NET_ID)
    net_config[FLUX_DOF_DEFINITION_ID] = save(flux_dof_register.flux_dof_couples)
    net_config[NODES_ITEM_ID] = node_ids
    net_config[BLOCKS_ITEM_ID] = blocks_config
    net_config[BOUNDARIES_ID] = save(net.boundary_conditions, *args, **kwargs)

    return net_config


@loads(Net)
def load_net_config(
    configuration: Configuration,
    configuration_type: type[Net],
    configurable_object: Net | None = None,
    *args: Any,
    **kwargs: Any,
) -> Net:
    """
    Load a net from a configuration.

    :param configuration: the configuration
    :type configuration: Configuration

    :param boundaries: the boundaries of the net at each node
    :type boundaries: dict[str, list[BoundaryCondition]]

    :return: the net
    :rtype: Net
    """

    configurable_net = (
        configuration_type() if configurable_object is None else configurable_object
    )
    nodes_ids = configuration[NODES_ITEM_ID]

    # Fill the flux type singleton from the configured value
    if FLUX_DOF_DEFINITION_ID in configuration:
        load(
            configuration[FLUX_DOF_DEFINITION_ID],
            configuration_object=get_flux_dof_register(),
        )

    for node_id in nodes_ids:
        configurable_net.add_node(node_id)

    blocks_config: dict[str, Configuration] = configuration[BLOCKS_ITEM_ID].copy()
    connections_config: dict[str, dict[str, str]] = {
        block_key: block_config.configuration_items.pop(NODES_ITEM_ID)
        for block_key, block_config in blocks_config.items()
    }

    connections: dict[str, dict[int, str]] = {
        block_id: {
            int(node_index): global_node
            for node_index, global_node in connection_config.items()
        }
        for block_id, connection_config in connections_config.items()
    }
    blocks: dict[str, BlockDescription] = load(blocks_config)

    for block_id, block in blocks.items():
        # remove the node key (on a block configuration copy) before loading the block
        configurable_net.add_block(block_id, block, connections[block_id])

    boundaries: dict[str, list[BoundaryCondition]] | None = (
        load(configuration[BOUNDARIES_ID]) if BOUNDARIES_ID in configuration else None
    )

    # Add boundaries conditions
    if boundaries is not None:
        for node_id, conditions in boundaries.items():
            for bc in conditions:
                configurable_net.set_boundary(
                    node_id, bc.condition_type, bc.condition_id
                )

    return configurable_net
