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

"""Declare functions and their inverses."""

from dataclasses import dataclass
from typing import Any

import numpy as np

from physioblocks.registers.type_register import register_type
from physioblocks.simulation.functions import AbstractTransformation


@register_type("atan_transform")
@dataclass
class ArcTanTransform(AbstractTransformation):
    r"""Constrain the value with upper and lower boundaries.

    .. math::

        y = a + (b - a) (\frac{1}{2} + \frac{1}{\pi} \arctan{(x / \alpha)})

    The inverse transform:

    .. math::

        x = \alpha \tan{(\pi (\frac {y - a}{b - a} - \frac{1}{2}))}

    Attributes
    ----------
    upper_bound : float
        :math:`b` the maximum value
    lower_bound : float
        :math:`a` the minimum value
    scaling_factor : float
        :math:`\alpha` the scaling factor.
        Its magnitude should be around magnitude of x.

    Configuration
    -------------

    .. code-block:: json

        {
            "type": "atan_transform",
            "upper_bound": "<float>",    // b the maximum value
            "lower_bound": "<float>",    // a the minimum value (optional, default: 0.0)
            "scaling_factor": "<float>"  // alpha the scaling factor
                                         // (optional, default: 1.0)
        }

    """

    __INV_PI = 1.0 / np.pi

    upper_bound: float

    lower_bound: float = 0.0

    scaling_factor: float = 1.0

    def eval(self, x: Any) -> Any:
        """Transform the input.

        Parameters
        ----------
        x : float
            the input to transform

        Returns
        -------
        Any
            the scaled input

        """
        return (self.upper_bound - self.lower_bound) * (
            np.atan(x / self.scaling_factor) * self.__INV_PI + 0.5
        ) + self.lower_bound

    def eval_inverse(self, y: Any) -> Any:
        """Un-transform the input.

        Parameters
        ----------
        y : float
            the input to un-transform

        Returns
        -------
        Any
            the unscaled input

        """
        return self.scaling_factor * np.tan(
            np.pi
            * ((y - self.lower_bound) / (self.upper_bound - self.lower_bound) - 0.5)
        )


@register_type("tanh_transform")
@dataclass
class HyperbolicTanTransform(AbstractTransformation):
    r"""Constrain the value with upper and lower boundaries.

    .. math::

        y = a + \frac{b - a}{2} \left(1 + \tanh{\left(\frac{x}{2 \alpha}\right)}\right)

    For the inverse transformation, we use the :math:`\ln` formulation:

    .. math::

        x = \alpha \ln{\left(\frac{y - a}{b - y}\right)}

    Attributes
    ----------
    upper_bound : float
        :math:`b` the maximum value
    lower_bound : float
        :math:`a` the minimum value
    scaling_factor : float
        :math:`\alpha` the scaling factor.
        Its magnitude should be around magnitude of x.

    Configuration
    -------------

    .. code-block:: json

        {
            "type": "tanh_transform",
            "upper_bound": "<float>",    // b the maximum value
            "lower_bound": "<float>",    // a the minimum value (optional, default: 0.0)
            "scaling_factor": "<float>"  // alpha the scaling factor
                                         // (optional, default: 1.0)
        }

    """

    upper_bound: float

    lower_bound: float = 0.0

    scaling_factor: float = 1.0

    def eval(self, x: Any) -> Any:
        """Transform the input.

        Parameters
        ----------
        x : float
            the input to transform

        Returns
        -------
        Any
            the scaled input

        """
        return (self.upper_bound - self.lower_bound) * 0.5 * (
            1.0 + np.tanh(0.5 * x / self.scaling_factor)
        ) + self.lower_bound

    def eval_inverse(self, y: Any) -> Any:
        """Un-transform the input.

        Parameters
        ----------
        y : float
            the input to un-transform

        Returns
        -------
        Any
            the unscaled input

        """
        return self.scaling_factor * np.log(
            (y - self.lower_bound) / (self.upper_bound - y)
        )


@dataclass
@register_type("power_transform")
class PowerTransform(AbstractTransformation):
    r"""
    Constrain the value to be strictly superior to a boundary.

    .. math::

        y = a + 2^{x / \alpha}

    The inverse transform:

    .. math::

        x = \alpha \log_2{(y - a)}

    Parameters
    ----------
    boundary: float
        :math:`a` the lower boundary. Default is 0.0.

    scaling_factor: float
        :math:`\alpha` the scaling factor for the transform. Default is 1.0.

    Configuration
    -------------

    .. code-block:: json

        {
            "type": "power_transform",
            "boundary": "<float>",       // a the lower bound (optional, default: 0.0)
            "scaling_factor": "<float>"  // alpha the scaling factor
                                         // (optional, default: 1.0)
        }

    """

    boundary: float = 0.0
    scaling_factor: float = 1.0

    def eval(self, x: Any) -> Any:
        """Transform the input.

        Parameters
        ----------
        x : float
            the input to transform

        Returns
        -------
        Any
            the scaled input

        """
        return (2 ** (x / self.scaling_factor)) + self.boundary

    def eval_inverse(self, y: Any) -> Any:
        """Un-transform the input.

        Parameters
        ----------
        y : float
            the input to un-transform

        Returns
        -------
        Any
            the unscaled input

        """
        return self.scaling_factor * np.log2(y - self.boundary)
