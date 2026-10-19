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

"""Define a time object, and a manager to hold the simulation time."""

from typing import Any

import numpy as np

from physioblocks.computing.quantities import Quantity

# Constant for the time quantity id in the simulation
TIME_QUANTITY_ID = "time"

_DEFAULT_STEP = 0.001
_DEFAULT_MIN_STEP = _DEFAULT_STEP / 16.0


class Time(Quantity[np.float64]):
    """Simulation time class.

    Whenever the time is updated, it recomputes the difference between the new
    and the current value and its inverse (accessible through the ``dt`` and ``inv_dt``
    properties)

    Parameters
    ----------
    value : float
        the initial time value

    """

    _dt: float

    _inv_dt: float

    def __init__(self, value: float):
        super().__init__(value)
        self._dt = 0.0
        self._inv_dt = np.inf

    @property
    def dt(self) -> float:
        """Get the difference between the ``new`` and the ``current`` value of the time.

        Returns
        -------
        float
            the delta time value

        """
        return self._dt

    @property
    def inv_dt(self) -> float:
        """Get the inverse of ``dt``.

        This is ``np.inf`` when ``dt = 0``.

        Returns
        -------
        float
            the delta time inverse

        """
        return self._inv_dt

    def update(self, new: Any) -> None:
        """Update the ``new`` value of the time and recomputes ``dt`` and ``inv_dt``.

        .. note::

            If ``dt`` is 0.0, ``inv_dt`` is ``np.inf``.

        Parameters
        ----------
        new : float
            the new value to set

        """
        super().update(new)

        self._dt = self._new - self._current
        self._inv_dt = 1.0 / self._dt

    def initialize(self, value: Any) -> None:
        """Initialize the ``new`` and ``current`` value.

        .. note::

            It set both ``dt`` to ``0.0`` and ``inv_dt`` to ``np.inf``.

        Parameters
        ----------
        value : Any
            the value to set

        """
        super().initialize(value)
        self._dt = 0.0
        self._inv_dt = np.inf


class TimeManager:
    """Store the time value during the simulation.

    Parameters
    ----------
    start : float
        start value for the simulation time. Default is 0.0.
    duration : float
        simulation duration. Default is 1e-3.
    step_size : float
        time increment. Default is 1e-3.

    Raises
    ------
    ValueError
        When the ``duration`` or the ``step_size`` parameter is 0 or negative.

    """

    _time: Time

    def __init__(
        self,
        start: float = 0.0,
        duration: float = _DEFAULT_STEP,
        step_size: float = _DEFAULT_STEP,
    ):
        self._time = Time(start)
        self.start = start
        self.duration = duration
        self.step_size = step_size

    @property
    def end(self) -> float:
        """Get the current end time.

        Returns
        -------
        float
            the end time

        """
        return self.start + self._duration

    @property
    def duration(self) -> float:
        """Get the duration.

        Returns
        -------
        float
            the duration

        """
        return self._duration

    @duration.setter
    def duration(self, value: float) -> None:
        """Set the duration.

        Parameters
        ----------
        value : float
            the duration

        Raises
        ------
        ValueError
            if the duration is 0 or negative.

        """
        if value <= 0.0:
            raise ValueError(f"Duration value can not be 0 or negative. Got {value}")
        self._duration = value

    @property
    def step_size(self) -> float:
        """Get the standard step size.

        Returns
        -------
        float
            the standard step size

        """
        return self._step_size

    @step_size.setter
    def step_size(self, value: float) -> None:
        """Set the standard step size.

        Parameters
        ----------
        value : float
            the standard step size

        Raises
        ------
        ValueError
            if the step size is 0 or negative.

        """
        if value <= 0.0:
            raise ValueError(f"Time step value can not be 0 or negative. Got {value}")
        self._step_size = value

    @property
    def time(self) -> Time:
        """Get the current :class:`~.Time` quantity.

        Returns
        -------
        Time
            the time quantity

        """
        return self._time

    @property
    def ended(self) -> bool:
        """Get if the time has reached the end time.

        Returns
        -------
        bool
            True if the new time value has reached the end time, False otherwise.

        """
        return bool(self._time.new >= self.end)

    def initialize(self) -> None:
        """Initialize the time with the ``start`` value."""
        self._time.initialize(self.start)
        self._time.update(self.start + self.step_size)

    def update(self) -> None:
        """Update the time with the ``step_size`` value."""
        self._time.initialize(self.time.current + self.step_size)
        self._time.update(self.time.current + self.step_size)
