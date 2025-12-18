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

"""Defines some math functions to help compute quantities"""

from typing import Any

import numpy as np


def exp_diff(a: float, b: float, diff: float) -> Any:
    """
    Computes exponential differences with more numerical accuracy when a and b are close
    using the relationship:

    .. math::

        e^a - e^b = 2\\ e^{\\frac{a + b}{2}}\\ \\text{sinh}(\\frac{a + b}{2})

    :param a: value of a
    :type a: np.float64

    :param b: value of b
    :type b: np.float64

    :param diff: value of a - b
    :type diff: np.float64

    :return: exponential difference value
    :rtype: np.float64
    """
    return np.exp(0.5 * (a + b)) * 2.0 * np.sinh(0.5 * diff)


def power_diff(a: float, b: float, diff: float, n: int) -> Any:
    """
    Computes the a and b power n difference with more numerical accuracy when a and
    b are close by using the following relationship:

    .. math::

        a^n - b^n = (a-b) * \\sum_{i = 0}^{n -1}{a^i b^{n-1-i}}

    When n is negative, the following transformation is used:

    .. math::

        \\frac{1}{a^n} - \\frac{1}{b^n} = -\\frac{a^n-b^n}{{ab}^n}

    :param a: value of a
    :type a: np.float64

    :param b: value of b
    :type b: np.float64

    :param diff: value of a - b
    :type diff: np.float64

    :return: the a and b power n difference value
    :rtype: np.float64
    """

    if n < 0:
        return -power_diff(a, b, diff, -n) / np.pow(a * b, -n)
    elif n > 0:
        return diff * _power_dec(a, b, n - 1, 0)
    else:
        return 0.0


def _power_dec(a: float, b: float, n1: int, n2: int) -> Any:
    """
    Helper recursive function used by :func:`power_diff` to compute the term:

    .. math::

        \\sum_{i = 0}^{n -1}{a^i b^{n-1-i}}
    """

    if n1 != 0 or n2 != 0:
        if n1 != 0:
            return np.pow(a, n1) * np.pow(b, n2) + _power_dec(a, b, n1 - 1, n2 + 1)
        else:
            return np.pow(b, n2)

    return 1.0
