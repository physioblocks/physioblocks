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

"""Declares the **Blocks** and their **Local Nodes**."""

from __future__ import annotations

from collections.abc import Mapping
from copy import copy

from physioblocks.computing.models import (
    Block,
    Expression,
    ModelComponent,
    Term,
)
from physioblocks.registers.type_register import register_type

# Separator for model parameter names
ID_SEPARATOR = "."

# Model description type id
MODEL_DESCRIPTION_TYPE_ID = "model_description"


@register_type(MODEL_DESCRIPTION_TYPE_ID)
class ModelComponentDescription:
    """Description of a :class:`~.ModelComponent` in a :class:`~.Net`.

    **Model Components** have no fluxes and their description can not interact directly
    with the net.

    To use a model component in a net, it has to be added as a sub-model of a
    :class:`~.BlockDescription` object or of another
    :class:`~.ModelComponentDescription` object.

    The model component description is used as a submodel of a
    :class:`~.BlockDescription` or of another :class:`~.ModelComponentDescription`.

    Every model component local quantity can be given a global name in the
    net. The default global name of a quantity is ``<model name>.<local name>``.

    Parameters
    ----------
    unique_id : str
        the model name in the net
    model_type : type[ModelComponent]
        the described :class:`~.ModelComponent` type
    global_ids : dict[str, str]
        mapping of all the component local parameter name with
        their global names in the net
    submodels : dict[str, ModelComponentDescription]
        mapping of all the model submodels with their name.
    alternative_types : Mapping[str, type[ModelComponent]]
        mapping of all the alternative types of the model
        description with their tag id.

    Raises
    ------
    AttributeError
        if a key of ``global_ids`` is not a local id of the model type.

    See Also
    --------
    ~.ModelComponent
        the described objects.
    ~.BlockDescription
        Can reference model components
    ~.Net
        Can reference model components in the block descriptions

    Configuration
    -------------

    .. code-block:: json

        {
            "type": "model_description",
            "model_type": "<str>",        // Type id of the described model component
            "<local name>": "<str>",      // Global name of the local quantity
            // (optional, default: "<model name>.<local name>")
            "submodels": {                // Submodel descriptions with their names
                "<str>": "<model description type>"  // (optional)
            },
            "alternative_types": {        // Alternative model component type id
                "<str>": "<str>"          // with its tag (optional)
            }
        }

    """

    _unique_id: str

    _submodels: dict[str, ModelComponentDescription]
    _alternative_types: Mapping[str, type[ModelComponent]]
    _alternative_descriptions: Mapping[str, ModelComponentDescription]

    def __init__(
        self,
        unique_id: str,
        model_type: type[ModelComponent],
        global_ids: dict[str, str] | None = None,
        submodels: dict[str, ModelComponentDescription] | None = None,
        alternative_types: Mapping[str, type[ModelComponent]] | None = None,
    ):
        self._unique_id = unique_id
        self._described_type = model_type
        self._alternative_types = (
            alternative_types if alternative_types is not None else {}
        )

        # check user defined ids
        user_ids = {}
        if global_ids is not None:
            for key, item in global_ids.items():
                if key not in model_type.local_ids:
                    raise AttributeError(
                        str.format(
                            "{0} has no attribute named {1}.",
                            model_type.__name__,
                            key,
                        )
                    )
                user_ids[key] = item

        # initialise default ids
        self._global_ids = {
            local_id: ID_SEPARATOR.join([self.name, local_id])
            for local_id in self._described_type.local_ids
        }

        # update with user ids
        self._global_ids.update(user_ids)

        # Initialise submodels
        self._submodels = {}
        if submodels is not None:
            for model_id, model in submodels.items():
                # rename default ids with submodel new id
                self.add_submodel(model_id, model)

        self._alternative_descriptions = self._get_alternative_descriptions()

    def _get_global_expressions_definitions(
        self, local_definitions: list[Expression]
    ) -> list[Expression]:
        return [
            Expression(
                expression.size,
                expression.expr_func,
                [
                    Term(self.global_ids[local_id], size, index)
                    for local_id, size, index in expression.terms
                ],
                {
                    self.global_ids[local_id]: grad_func
                    for local_id, grad_func in expression.expr_gradients.items()
                },
            )
            for expression in local_definitions
        ]

    @property
    def name(self) -> str:
        """Get the model component name.

        Returns
        -------
        str
            the model component name

        """
        return self._unique_id

    @property
    def global_ids(self) -> dict[str, str]:
        """Get local name of the quantities matching their global name in the net.

        Returns
        -------
        dict[str, str]
            the global ids of the model

        """
        return self._global_ids.copy()

    @property
    def described_type(self) -> type[ModelComponent]:
        """Get the described type.

        Returns
        -------
        type[ModelComponent]
            the model component type

        """
        return self._described_type

    @property
    def alternative_types(self) -> Mapping[str, type[ModelComponent]]:
        """Get all the alternative types for the model.

        Returns
        -------
        Mapping[str, type[ModelComponent]]
            the alternatives model component types

        """
        return copy(self._alternative_types)

    @property
    def alternative_descriptions(self) -> Mapping[str, ModelComponentDescription]:
        """Get all the alternative descriptions for the model.

        Returns
        -------
        Mapping[str, ModelComponentDescription]
            the alternatives model component descriptions

        """
        return copy(self._alternative_descriptions)

    @property
    def submodels(self) -> dict[str, ModelComponentDescription]:
        """Get the submodels descriptions.

        Returns
        -------
        dict[str, ModelComponentDescription]
            the submodel descriptions

        """
        return self._submodels.copy()

    @property
    def internal_variables(self) -> list[Term]:
        """Get the model **Internal Variables** terms.

        Get the terms recursively for the model and its submodels.

        Returns
        -------
        list[Term]
            the internal variables terms

        """
        internal_variables = [
            Term(self.global_ids[term_id], term_size, term_index)
            for (
                term_id,
                term_size,
                term_index,
            ) in self._described_type.internal_variables
        ]

        for model in self.submodels.values():
            internal_variables.extend(model.internal_variables)

        return internal_variables

    @property
    def internal_expressions(self) -> list[Expression]:
        """Get the object expressions representing model's **Internal equations**.

        Returns
        -------
        list[Expression]
            all the model internal equations

        """
        return self._get_global_expressions_definitions(
            self._described_type.internal_expressions
        )

    @property
    def saved_quantities(self) -> list[Term]:
        """Get the model **Saved Quantities** terms.

        Get the terms recursively for the model and all its submodels.

        Returns
        -------
        list[Term]
            the saved quantities name and sizes

        """
        saved_quantities = [
            Term(self.global_ids[term_id], term_size, term_index)
            for term_id, term_size, term_index in self._described_type.saved_quantities
        ]

        for model in self.submodels.values():
            saved_quantities.extend(model.saved_quantities)

        return saved_quantities

    @property
    def saved_quantities_expressions(self) -> list[Expression]:
        """Get the model saved quantities expressions.

        Returns
        -------
        list[Expression]
            The model saved quantities expression definitions

        """
        return self._get_global_expressions_definitions(
            self._described_type.saved_quantities_expressions
        )

    def rename_global_id(self, old_id: str, new_id: str) -> None:
        """Rename the global id in the model and its submodels recursively.

        If no name is a match, then no name is changed.

        Parameters
        ----------
        old_id : str
            the global id to rename
        new_id : str
            the new id to set

        """
        for local_id, global_id in self._global_ids.items():
            if old_id == global_id:
                self._global_ids[local_id] = new_id

        for submodel in self._submodels.values():
            submodel.rename_global_id(old_id, new_id)

        for alt_description in self._alternative_descriptions.values():
            alt_description.rename_global_id(old_id, new_id)

    def add_submodel(
        self, local_model_id: str, model_description: ModelComponentDescription
    ) -> ModelComponentDescription:
        """Add a submodel to the model.

        Create and return a copy of the input model description
        updated with correct ids.

        Parameters
        ----------
        local_model_id : str
            The submodel name
        model_description : ModelComponentDescription
            The model to add

        Returns
        -------
        ModelComponentDescription
            the submodel description in the current model description

        """
        submodel_id = ID_SEPARATOR.join([self.name, local_model_id])

        renamed_ids = {
            local_id: global_id
            if global_id != ID_SEPARATOR.join([model_description.name, local_id])
            else ID_SEPARATOR.join([self.name, local_model_id, local_id])
            for local_id, global_id in model_description.global_ids.items()
        }

        self._submodels[local_model_id] = ModelComponentDescription(
            submodel_id,
            model_description.described_type,
            renamed_ids,
            model_description.submodels,
            model_description.alternative_types,
        )
        return self._submodels[local_model_id]

    def remove_submodel(self, model_id: str) -> ModelComponentDescription:
        """Remove the submodel.

        Parameters
        ----------
        model_id : str
            the id of the submodel to remove

        Returns
        -------
        ModelComponentDescription
            the removed submodel description

        """
        return self._submodels.pop(model_id)

    def _get_alternative_model_global_ids(
        self, alternative_type: type[ModelComponent]
    ) -> dict[str, str]:
        return {
            local_id: self.global_ids[local_id]
            for local_id in alternative_type.local_ids
            if local_id
            not in [
                saved_quantity_term.term_id
                for saved_quantity_term in alternative_type.saved_quantities
            ]
        }

    def _get_alternative_model_submodels(
        self, alternative_type_id: str
    ) -> dict[str, ModelComponentDescription]:
        return {
            submodel_id: submodel_desc.alternative_descriptions[alternative_type_id]
            for submodel_id, submodel_desc in self._submodels.items()
            if alternative_type_id in submodel_desc.alternative_descriptions
        }

    def _get_alternative_descriptions(self) -> dict[str, ModelComponentDescription]:
        return {
            alt_id: ModelComponentDescription(
                self.name,
                alt_type,
                self._get_alternative_model_global_ids(alt_type),
                self._get_alternative_model_submodels(alt_id),
            )
            for alt_id, alt_type in self._alternative_types.items()
        }


# Id for the model description type
BLOCK_DESCRIPTION_TYPE_ID = "block_description"


@register_type(BLOCK_DESCRIPTION_TYPE_ID)
class BlockDescription(ModelComponentDescription):
    """Extend :class:`ModelComponentDescription` to describe :class:`~.Block` objects.

    Block descriptions connect their block's flux to :class:`~.Node` objects to share
    them across the net.

    .. note:: **Internal variables** can be empty, but described
      :class:`~.Block` type should define
      fluxes to interact with the others blocks in the net.

    Every block local quantity can be given a global name in the
    configuration. Default global name is ``<block name>.<local name>``.

    Parameters
    ----------
    block_id : str
        the block name in the net
    block_type : type[Block]
        the described block type
    flux_type : str
        the type of flux exchanged by the block
    global_ids : dict[str, str]
        mapping of all the block local parameter name with
        their global names in the net
    submodels : dict[str, ModelComponentDescription]
        mapping of all the block submodels with their name.
    alternative_types : Mapping[str, type[Block]]
        mapping of all the alternative block types of the block
        description with their tag id.

    Examples
    --------
    >>> block_description = BlockDescription(
    ...     "rc_block_1",  # block name
    ...     RCBlock,  # block type
    ...     "flow",  # block flux type
    ...     {
    ...         "resistance": "r1",  # rename "rc_block_1.resistance" to "r1"
    ...         "capacitance": "c1",  # rename "rc_block_1.capacitance" to "c1"
    ...     },
    ...     # no submodels defined
    ... )

    See Also
    --------
    ~.Block
        the described object
    ~.ModelComponentDescription
        base class
    ~.Net
        reference block description to describe the fluxes

    Configuration
    -------------

    The ``node`` field of the block configuration matches node indexes in the actual
    :class:`~.Block` type to a node defined in the net.

    .. code-block:: json

        {
            "type": "block_description",
            "model_type": "<str>",        // Type id of the described block
            "flux_type": "<str>",         // Type of flux exchanged by the block
            "nodes": {                    // Net node name for each block local node
                "<int>": "<str>"
            },
            "<local name>": "<str>",      // Global name of the local quantity
            // (optional, default: "<block name>.<local name>")
            "submodels": {                // Submodel descriptions with their names
                "<str>": "<model description type>"  // (optional)
            },
            "alternative_types": {        // Alternative block type id
                "<str>": "<str>"          // with its tag (optional)
            }
        }

    """

    _block_id: str
    _flux_type: str
    _described_type: type[Block]
    _alternative_types: Mapping[str, type[Block]]
    alternative_types: Mapping[str, type[Block]]
    _alternative_descriptions: dict[str, BlockDescription]
    alternative_descriptions: dict[str, BlockDescription]

    def __init__(
        self,
        block_id: str,
        block_type: type[Block],
        flux_type: str,
        global_ids: dict[str, str] | None = None,
        submodels: dict[str, ModelComponentDescription] | None = None,
        alternative_types: Mapping[str, type[Block]] | None = None,
    ):
        super().__init__(block_id, block_type, global_ids, submodels)
        self._flux_type = flux_type
        self._alternative_types = (
            alternative_types if alternative_types is not None else {}
        )
        self._alternative_descriptions = self._get_alternative_block_descriptions()

    @property
    def described_type(self) -> type[Block]:
        """Get the described block type.

        Returns
        -------
        type[Block]
            the block type

        """
        return self._described_type

    @property
    def fluxes(self) -> dict[int, Expression]:
        """Get the fluxes expressions associated with their **Local Node** index.

        Returns
        -------
        dict[int, Expression]
            the flux expression at each local node

        """
        return {
            loc_node_index: Expression(
                flux_expression.size,
                flux_expression.expr_func,
                [
                    Term(self.global_ids[term_id], term_size, term_index)
                    for term_id, term_size, term_index in flux_expression.terms
                    if term_id in self.global_ids
                ],
                {
                    self.global_ids[grad_key]: grad_expr
                    for grad_key, grad_expr in flux_expression.expr_gradients.items()
                },
            )
            for loc_node_index, flux_expression in self.described_type.fluxes_expressions.items()  # noqa: E501
        }

    @property
    def flux_type(self) -> str:
        """Get the type of the block's flux.

        Returns
        -------
        str
            the flux type

        """
        return self._flux_type

    def _get_alternative_block_descriptions(self) -> dict[str, BlockDescription]:
        return {
            alt_id: BlockDescription(
                self.name,
                alt_type,
                self._flux_type,
                self._get_alternative_model_global_ids(alt_type),
                self._get_alternative_model_submodels(alt_id),
            )
            for alt_id, alt_type in self._alternative_types.items()
        }
