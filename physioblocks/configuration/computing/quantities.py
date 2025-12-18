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

import numpy as np

from physioblocks.computing.quantities import Quantity
from physioblocks.registers.load_function_register import loads
from physioblocks.registers.save_function_register import saves


@loads(Quantity)
def load_quantity(
    configuration: Any,
    configuration_object: Quantity[Any] | None = None,
    *args: Any,
    **kwargs: Any,
) -> Any:
    if configuration_object is not None:
        configuration_object.initialize(configuration)
    else:
        configuration_object = Quantity(configuration)
    return configuration_object


@saves(Quantity)
def save_quantity(
    quantity: Quantity[Any],
    *args: Any,
    **kwargs: Any,
) -> Any:
    return float(quantity) if quantity.size == 1 else np.asarray(quantity).tolist()
