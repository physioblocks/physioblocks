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
Declares the **Blocks** and their **Local Nodes**
"""

from __future__ import annotations

from physioblocks.computing.models import (
    Block,
    Expression,
    ExpressionDefinition,
    ModelComponent,
    TermDefinition,
)
from physioblocks.registers.type_register import register_type

# Separator for model parameter names
ID_SEPARATOR = "."

# Model description type id
MODEL_DESCRIPTION_TYPE_ID = "model_description"


@register_type(MODEL_DESCRIPTION_TYPE_ID)
class ModelComponentDescription:
    """
    Description of a :class:`~physioblocks.computing.models.ModelComponent` object
    in a :class:`~physioblocks.description.nets.Net` object.

    **Model Components** have no fluxes and their description can not interact directly
    with the net.

    To use a model component in a net, it has to be added has a sub-model of a
    :class:`~physioblocks.description.blocks.BlockDescription` object or
    of a another :class:`~physioblocks.description.blocks.ModelComponentDescription`
    object.

    :param unique_id: the model name in the net
    :type unique_id: str

    :param model_type: the described **ModelComponent type**
    :type model_type: type[ModelComponent]

    :param global_ids: mapping of all the component local parameter name with
      their global names in the net
    :type global_ids: dict[str, str]

    :param submodels: mapping of all the model submodels with their name.
    :type submodels: dict[str, ModelComponentDescription]
    """

    _unique_id: str

    _submodels: dict[str, ModelComponentDescription]

    def __init__(
        self,
        unique_id: str,
        model_type: type[ModelComponent],
        global_ids: dict[str, str] | None = None,
        submodels: dict[str, ModelComponentDescription] | None = None,
    ):
        self._unique_id = unique_id
        self._described_type = model_type

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

        # build expressions definitions once
        self._internal_defs = self._get_global_expressions_definitions(
            self._described_type.internal_expressions
        )
        self._saved_quantities_defs = self._get_global_expressions_definitions(
            self._described_type.saved_quantities_expressions
        )

        # Initialise submodels
        self._submodels = {}
        if submodels is not None:
            for model_id, model in submodels.items():
                # rename default ids with submodel new id
                self.add_submodel(model_id, model)

    def _get_global_expressions_definitions(
        self, local_definitions: list[ExpressionDefinition]
    ) -> list[ExpressionDefinition]:
        return [
            ExpressionDefinition(
                Expression(
                    expression_def.expression.size,
                    expression_def.expression.expr_func,
                    {
                        self.global_ids[grad_key]: grad_expr
                        for grad_key, grad_expr in expression_def.expression.expr_gradients.items()  # noqa: E501
                    },
                ),
                [
                    TermDefinition(self.global_ids[term.term_id], term.size, term.index)
                    for term in expression_def.terms
                ],
            )
            for expression_def in local_definitions
        ]

    @property
    def name(self) -> str:
        """Get the model component name.

        :return: the model component name
        :rtype: str
        """
        return self._unique_id

    @property
    def global_ids(self) -> dict[str, str]:
        """Get a mapping of all local name of the quantities matching
        their global name in the net.

        :return: the global ids of the model
        :rtype: dict[str, str]
        """
        return self._global_ids.copy()

    @property
    def described_type(self) -> type[ModelComponent]:
        """Get the described :class:`~physioblocks.computing.models.ModelComponent`
        type.

        :return: the model component type
        :rtype: type[ModelComponent]
        """
        return self._described_type

    @property
    def submodels(self) -> dict[str, ModelComponentDescription]:
        """Get the submodels descriptions.

        :return: the submodel descriptions
        :rtype: dict[str, ModelComponentDescription]
        """
        return self._submodels.copy()

    @property
    def internal_variables(self) -> list[tuple[str, int]]:
        """
        Get the model **Internal Variables** global names recursively for the
        model and its submodels.

        :return: the internal variables name and sizes
        :rtype: list[tuple[str, int]]
        """
        internal_variables = [
            (self._global_ids[term_def.term_id], term_def.size)
            for term_def in self._described_type.internal_variables
        ]

        for model in self.submodels.values():
            internal_variables.extend(model.internal_variables)

        return internal_variables

    @property
    def internal_expressions(self) -> list[ExpressionDefinition]:
        """
        Get the :class:`~physioblocks.computing.models.ExpressionDefinition` object
        representing model's **Internal equations**.

        :return: all the model internal equations
        :rtype: list[ExpressionDefinition]
        """
        return self._internal_defs

    @property
    def saved_quantities(self) -> list[tuple[str, int]]:
        """
        Get the model **Saved Quantities** global names and sizes recursivly
        for the model and its submodels.

        :return: the saved quantities name and sizes
        :rtype: list[tuple[str, int]]
        """

        saved_quantities = [
            (self._global_ids[term_def.term_id], term_def.size)
            for term_def in self._described_type.saved_quantities
        ]

        for model in self.submodels.values():
            saved_quantities.extend(model.saved_quantities)

        return saved_quantities

    @property
    def saved_quantities_expressions(self) -> list[ExpressionDefinition]:
        """
        Get all saved quantities expressions definitions for model

        :return: all the model saved quantities expression definitions
        :rtype: list[ExpressionDefinition]
        """
        return self._saved_quantities_defs

    def rename_global_id(self, old_id: str, new_id: str) -> None:
        """Rename the global name with the new name in the current model and
        all its submodels.

        If no name is a match, then no name are changed.

        :param old_id: the global name to rename
        :type old_id: str

        :param new_id: the new name to set
        :type new_id: str
        """
        for local_id, global_id in self._global_ids.items():
            if old_id == global_id:
                self._global_ids[local_id] = new_id

        for submodel in self.submodels.values():
            submodel.rename_global_id(old_id, new_id)

    def add_submodel(
        self, local_model_id: str, model_description: ModelComponentDescription
    ) -> ModelComponentDescription:
        """
        Add a submodel to the model.

        Create and return a copy of the input model description
        updated with correct ids.

        :param model_id: The submodel name
        :type model_id: str

        :param model_description: The model to add
        :type model_type: type[ModelComponent]

        :return: the submodel description in the current model description
        :rtype: ModelComponentDescritpion
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
        )
        return self._submodels[local_model_id]

    def remove_submodel(self, model_id: str) -> ModelComponentDescription:
        """
        Remove the submodel.

        :param model_id: the id of the submodel to remove
        :type model_id: str

        :return: the removed submodel description
        :rtype: ModelComponentDescritpion
        """
        return self._submodels.pop(model_id)


# Id for the model description type
BLOCK_DESCRIPTION_TYPE_ID = "block_description"


@register_type(BLOCK_DESCRIPTION_TYPE_ID)
class BlockDescription(ModelComponentDescription):
    """
    Extend the :class:`~.ModelComponentDescription` to describe
    :class:`~physioblocks.computing.models.Block` object in the net.

    Block descriptions connect their block's flux to
    :type:`~physioblocks.description.nets.Node` objects to share
    them across the net.

    .. note:: **Internal variables** can be empty, but described
      :type:`~physioblocks.computing.models.Block` type should at
      least define one **Flux** (otherwise, it can not interact with the others
      blocks in the net)

    :param block_id: the block name in the net
    :type block_id: str

    :param block_type: the described block type
    :type block_type: type[Block]

    :param flux_type: the type of flux exchanged by the block
    :type flux_type: str

    :param global_ids: mapping of all the block local parameter name with
      their global names in the net
    :type global_ids: dict[str, str]

    :param submodels: mapping of all the block submodels with their name.
    :type submodels: dict[str, ModelComponentDescription]

    Example
    ^^^^^^^

        >>> block_description = BlockDescription(
                "rc_block_1", # block name
                RCBlock, # block type
                "flow", # block flux type
                {
                    "resistance": "r1", # rename "rc_block_1.resistance" to "r1"
                    "capacitance": "c1", # rename "rc_block_1.capacitance" to "c1"
                }
                # no submodels defined
            )
    """

    _block_id: str
    _flux_type: str
    _described_type: type[Block]

    def __init__(
        self,
        block_id: str,
        block_type: type[Block],
        flux_type: str,
        global_ids: dict[str, str] | None = None,
        submodels: dict[str, ModelComponentDescription] | None = None,
    ):
        super().__init__(block_id, block_type, global_ids, submodels)
        self._flux_type = flux_type

    @property
    def described_type(self) -> type[Block]:
        """Get the described :class:`~physioblocks.computing.models.Block` type.

        :return: the block type
        :rtype: type[Block]
        """
        return self._described_type

    @property
    def fluxes(self) -> dict[int, Expression]:
        """
        Get a mapping of flux `~physioblocks.computing.models.Expression` associated
        with their **Local Node** index.

        :return: the flux expression at each local node
        :rtype: dict[int, Expression]
        """
        return {
            loc_node_index: Expression(
                flux_def.expression.size,
                flux_def.expression.expr_func,
                {
                    self.global_ids[grad_key]: grad_expr
                    for grad_key, grad_expr in flux_def.expression.expr_gradients.items()  # noqa: E501
                },
            )
            for loc_node_index, flux_def in self.described_type.fluxes_expressions.items()  # noqa: E501
        }

    @property
    def flux_type(self) -> str:
        """
        Get the type of the block's flux.

        :return: the flux type
        :rtype: str
        """
        return self._flux_type
