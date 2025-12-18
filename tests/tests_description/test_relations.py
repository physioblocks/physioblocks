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

from unittest.mock import patch

import pytest

from physioblocks.description.flux import (
    Dof,
    FluxDofTypesRegister,
    get_flux_dof_register,
)

FLUX_TYPE_ID = "flux"
DOF_TYPE_ID = "potential"

FLUX_TYPE_A = "flux_a"
DOF_TYPE_A = "potential_a"

FLUX_TYPE_B = "flux_b"
DOF_TYPE_B = "potential_b"


@pytest.fixture
def register() -> FluxDofTypesRegister:
    return get_flux_dof_register()


class TestFluxDofCouple:
    def test_register(self, register: FluxDofTypesRegister):
        register.register_flux_dof_couple(FLUX_TYPE_ID, DOF_TYPE_ID)
        assert DOF_TYPE_ID in register.dof_flux_couples
        assert FLUX_TYPE_ID in register.flux_dof_couples

        with pytest.raises(ValueError):
            register.register_flux_dof_couple(FLUX_TYPE_ID, "unregistered")

        with pytest.raises(ValueError):
            register.register_flux_dof_couple("unregistered", FLUX_TYPE_ID)

        with pytest.raises(ValueError):
            register.register_flux_dof_couple(DOF_TYPE_ID, "unregistered")

        with pytest.raises(ValueError):
            register.register_flux_dof_couple("unregistered", DOF_TYPE_ID)

        assert "unregistered" not in register.dof_flux_couples
        assert "unregistered" not in register.flux_dof_couples

        assert FLUX_TYPE_ID not in register.dof_flux_couples
        assert DOF_TYPE_ID not in register.flux_dof_couples

        register.unregister_flux_dof_couple(FLUX_TYPE_ID)

    def test_get_matching_type(self, register: FluxDofTypesRegister):
        with patch.multiple(
            register,
            _fluxes_types={FLUX_TYPE_ID: DOF_TYPE_ID},
            _dof_types={DOF_TYPE_ID: FLUX_TYPE_ID},
        ):
            assert register.flux_dof_couples[FLUX_TYPE_ID] == DOF_TYPE_ID
            assert register.dof_flux_couples[DOF_TYPE_ID] == FLUX_TYPE_ID

    def test_unregister(self, register: FluxDofTypesRegister):
        register.register_flux_dof_couple(FLUX_TYPE_ID, DOF_TYPE_ID)
        register.unregister_flux_dof_couple(FLUX_TYPE_ID)
        with pytest.raises(KeyError):
            register.flux_dof_couples[FLUX_TYPE_ID]

        register.register_flux_dof_couple(FLUX_TYPE_ID, DOF_TYPE_ID)
        register.unregister_flux_dof_couple(DOF_TYPE_ID)
        with pytest.raises(KeyError):
            register.dof_flux_couples[DOF_TYPE_ID]

        with pytest.raises(ValueError):
            register.unregister_flux_dof_couple(FLUX_TYPE_ID)

        with pytest.raises(ValueError):
            register.unregister_flux_dof_couple(DOF_TYPE_ID)


class TestDof:
    def test_constructor(self):
        dof = Dof("dof_a", DOF_TYPE_ID)
        assert dof.dof_id == "dof_a"
        assert dof.dof_type == DOF_TYPE_ID

    def test_eq(self):
        dof_1 = Dof("dof_a", DOF_TYPE_A)
        dof_2 = Dof("dof_a", DOF_TYPE_A)
        dof_3 = Dof("dof_a", DOF_TYPE_B)
        dof_4 = Dof("dof_b", DOF_TYPE_A)
        dof_5 = Dof("dof_b", DOF_TYPE_B)

        dof_id_1 = "dof_a"
        dof_id_2 = "dof_b"

        assert dof_1 == dof_2
        assert dof_1 == dof_3
        assert dof_1 != dof_4
        assert dof_1 != dof_5
        assert dof_1 == dof_id_1
        assert dof_1 != dof_id_2
        assert dof_1 != 1
