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

"""Declare base functions to write functions used during the simulation."""

from abc import ABC, abstractmethod
from inspect import signature
from typing import Any

from physioblocks.simulation.state import STATE_NAME_ID
from physioblocks.simulation.time_manager import TIME_QUANTITY_ID


class AbstractFunction(ABC):
    """Base class for functions that update quantities during the simulation."""

    @abstractmethod
    def eval(self, *args: Any, **kwargs: Any) -> Any:
        """Child Functions have to overwrite this method to compute the
        function result."""


def is_time_function(tested_function: AbstractFunction) -> bool:
    """Test if the simulation function needs simulation time parameter.

    :param tested_function: the function
    :type tested_function: AbstractFunction

    :return: True if the function needs time, False otherwise
    :rtype: bool
    """

    sig = signature(tested_function.eval)
    return TIME_QUANTITY_ID in sig.parameters


def is_state_function(tested_function: AbstractFunction) -> bool:
    """Test if the simulation function needs the state.

    :param function: the simulation function
    :type function: AbstractFunction

    :return: True if the function needs the state, False otherwise
    :rtype: bool
    """

    sig = signature(tested_function.eval)
    return STATE_NAME_ID in sig.parameters
