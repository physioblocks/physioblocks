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

"""
Declares **Flux** and **DOF** related objects.
"""

from collections.abc import Mapping
from dataclasses import dataclass

FLUX_TYPE_REGISTER_ID = "flux_type_register"


class FluxDofTypesRegister:
    """Stores relations between **Flux types** and **DOFs types**"""

    def __init__(self) -> None:
        # Stores relations between flux types and dof types
        self._fluxes_types: dict[str, str] = {}

        # Stores relations between dof types and flux types
        self._dof_types: dict[str, str] = {}

    @property
    def flux_dof_couples(self) -> dict[str, str]:
        """Get all **Flux-DOF** types couples.

        :return: the **Flux-DOF** couples
        :rtype: dict[str, str]
        """
        return self._fluxes_types.copy()

    @property
    def dof_flux_couples(self) -> dict[str, str]:
        """Get all **DOF-Flux** types couples.

        :return: the **DOF-Flux** couples
        :rtype: dict[str, str]
        """
        return self._dof_types.copy()

    def __type_registered(self, type_id: str) -> bool:
        return type_id in self._fluxes_types or type_id in self._dof_types

    def get(self, value: str) -> str | None:
        return self.flux_dof_couples.get(value, None)

    def update(self, mapping: Mapping[str, str]) -> None:
        for key, value in mapping.items():
            if value not in self.dof_flux_couples or key not in self.flux_dof_couples:
                self.register_flux_dof_couple(key, value)

    def register_flux_dof_couple(self, flux_type: str, dof_type: str) -> None:
        """
        Register a matching **Flux-DOF** type couple.

        :param flux_type: The flux type to register
        :type flux_type: str

        :param dof_type: The matching DOF type
        :type dof_type: str

        :raise ValueError: Raise a ValueError when either the **Flux** or the **DOF**
          type is already registered.
        """
        if self.__type_registered(flux_type) is True:
            raise ValueError(str.format("{0} is already registered", flux_type))
        if self.__type_registered(dof_type) is True:
            raise ValueError(str.format("{0} is already registered", dof_type))

        self._fluxes_types[flux_type] = dof_type
        self._dof_types[dof_type] = flux_type

    def unregister_flux_dof_couple(self, type_id: str) -> None:
        """
        Unregister the flux or DOF type and its matching type.

        :param type_id: The flux or DOF type to unregister
        :type type_id: str

        :raise ValueError: Raises a ValueError when no flux or DOF type with
          the given name is registered
        """
        if type_id in self._fluxes_types:
            flux_type = type_id
            dof_type = self._fluxes_types[flux_type]

        elif type_id in self._dof_types:
            dof_type = type_id
            flux_type = self._dof_types[dof_type]
        else:
            raise ValueError(
                str.format(
                    "No flux or dof type registered with {0}.",
                    str(type_id),
                )
            )

        self._fluxes_types.pop(flux_type)
        self._dof_types.pop(dof_type)


__flux_dof_register = FluxDofTypesRegister()


def get_flux_dof_register() -> FluxDofTypesRegister:
    """
    Get the unique register storing the relation between flux types
    and DOF types.

    :return: The register mapping flux types with DOF types
    :rtype: FluxDofTypesRegister
    """
    return __flux_dof_register


@dataclass
class Dof:
    """
    Degrees of freedom description.
    """

    dof_id: str
    """The id of the dof"""

    dof_type: str
    """The type of dof (ex: pressure, chemical, etc)"""

    def __eq__(self, value: object) -> bool:
        if isinstance(value, Dof):
            return value.dof_id == self.dof_id
        if isinstance(value, str):
            return value == self.dof_id
        return False
