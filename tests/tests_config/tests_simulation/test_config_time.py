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

import pytest

from physioblocks.configuration import Configuration
from physioblocks.configuration.constants import (
    TIME_DURATION_TIME_VAL_ID,
    TIME_MANAGER_ID,
    TIME_START_TIME_VAL_ID,
    TIME_STEP_MIN_VAL_ID,
    TIME_STEP_TIME_VAL_ID,
)
from physioblocks.configuration.functions import load, save
from physioblocks.simulation.time_manager import TimeManager
from tests.helpers.assertion_helpers import assert_time_manager_equals


@pytest.fixture
def ref_time_config() -> Configuration:
    config = Configuration(TIME_MANAGER_ID)
    config[TIME_START_TIME_VAL_ID] = 0.0
    config[TIME_DURATION_TIME_VAL_ID] = 1.0
    config[TIME_STEP_TIME_VAL_ID] = 0.1
    config[TIME_STEP_MIN_VAL_ID] = 0.01
    return config


@pytest.fixture
def ref_time_manager():
    manager = TimeManager(0.0, 1.0, 0.1, 0.01)
    return manager


def test_get_time_config(
    ref_time_config: ref_time_config, ref_time_manager: ref_time_manager
):
    configuration = save(ref_time_manager)
    assert ref_time_config == configuration


def test_load_time_config(
    ref_time_config: Configuration, ref_time_manager: TimeManager
):
    time_manager = TimeManager()
    load(ref_time_config, configuration_object=time_manager)

    assert_time_manager_equals(time_manager, ref_time_manager)
