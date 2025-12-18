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
Defines a Time object, and a manager to hold the simulation time.
"""

from typing import Any

import numpy as np

from physioblocks.computing.quantities import Quantity
from physioblocks.registers.type_register import register_type

# Constant for the time quantity id in the simulation
TIME_QUANTITY_ID = "time"

_DEFAULT_STEP = 0.001
_DEFAULT_MIN_STEP = _DEFAULT_STEP / 16.0


class Time(Quantity[np.float64]):
    """
    Extend :class:`~physioblocks.computing.quantities.Quantity` class to define
    simulation time.

    Whenever the time is updated, it recomputes the difference between the new
    and the current value and its inverse (accessibles trough the ``dt`` and ``inv_dt``
    properties)
    """

    _dt: float
    """Difference between ``new`` and ``current`` values"""

    _inv_dt: float
    """Inverse of ``dt``"""

    def __init__(self, value: float):
        """
        Initialize ``dt`` and ``inv_dt`` to 0.

        :param value: the initial time value
        :type value: float
        """
        super().__init__(value)
        self._dt = 0.0
        self._inv_dt = 0.0

    @property
    def dt(self) -> float:
        """
        Get the difference between the ``new`` and the ``current`` value of the time.

        :return: the delta time value
        :rtype: float
        """
        return self._dt

    @property
    def inv_dt(self) -> float:
        """
        Get the inverse of ``dt``.

        :return: the delta time inverse
        :rtype: float
        """
        return self._inv_dt

    def update(self, new: Any) -> None:
        """
        Update the ``new`` value of the time and recomputes ``dt`` and ``inv_dt``.

        .. note::

            If ``dt`` is 0.0, ``inv_dt`` is set to 0.0.

        :param new: the new value to set
        :type new: float
        """
        super().update(new)

        self._dt = self._new - self._current
        if self._dt != 0.0:
            self._inv_dt = 1.0 / self._dt
        else:
            self._inv_dt = 0.0

    def initialize(self, value: Any) -> None:
        """
        Initialize the ``new`` and ``current`` value.

        .. note::

            It set both ``dt`` and ``inv_dt`` to 0.

        :param value: the value to set
        :type new: Any
        """
        super().initialize(value)
        self._dt = 0.0
        self._inv_dt = 0.0


# Constant for time manager type
TIME_MANAGER_ID = "time"


@register_type(TIME_MANAGER_ID)
class TimeManager:
    """
    Updates the time value during the simulation.

    :param start: start value for the simulation time.
    :type start: float

    :param end: end value for the simulation time.
      The time ``new`` and ``current`` value can not exceed it.
    :type end: float

    :param time_step: time increment when update time is called.
    :type time_step: float

    :param min_step: minimum allowed value of the time increment.
    :type time_step: float

    :raise ValueError: ValueError is raised when :
        * the start parameter is superior to the end parameter.
        * the time_step parameter is negative.

    """

    _time: Time
    """Store the current time value"""

    start: float
    """The starting time of the time manager."""

    def __init__(
        self,
        start: float = 0.0,
        duration: float = _DEFAULT_STEP,
        step_size: float = _DEFAULT_STEP,
        min_step: float = _DEFAULT_MIN_STEP,
    ):
        if min_step <= 0.0:
            raise ValueError(
                str.format(
                    "Time Manager minimum time step value can not be 0 or negative",
                )
            )
        self._min_step = min_step
        self._time = Time(start)
        self.start = start
        self.duration = duration
        self.step_size = step_size
        self.current_step_size = step_size

    @property
    def min_step(self) -> float:
        """
        Get the minimum time step size allowed.

        :return: the minimum time step size.
        :rtype: float
        """
        return self._min_step

    @min_step.setter
    def min_step(self, value: float) -> None:
        """
        Set the start time.

        :param value: the start time to set
        :type value: float

        :raise ValueError: Raises a ValueError if the given value is greater than the
          end time.
        """

        if value <= 0.0:
            raise ValueError(
                str.format(
                    "Time Manager minimum time step value can not be 0 or negative",
                )
            )
        elif value > self.step_size:
            raise ValueError(
                str.format(
                    "Time Manager minimum step value can not be superior to time_step",
                )
            )
        self._min_step = value

    @property
    def end(self) -> float:
        """
        Get the current end time.

        :return: the end time
        :rtype: float
        """
        return self.start + self._duration

    @property
    def duration(self) -> float:
        """
        Get the duration.

        :return: the duration
        :rtype: float
        """
        return self._duration

    @duration.setter
    def duration(self, value: float) -> None:
        """
        Set the duration

        :return: the duration
        :rtype: float
        """
        if value <= 0.0:
            raise ValueError(
                str.format(
                    "Time Manager duration value can not be 0 or negative",
                )
            )
        self._duration = value

    @property
    def step_size(self) -> float:
        """
        Get the standard step size

        :return: the standard step size
        :rtype: float
        """
        return self._max_step

    @step_size.setter
    def step_size(self, value: float) -> None:
        """
        Get the standard step size

        :return: the standard step size
        :rtype: float
        """
        if value <= 0.0:
            raise ValueError(
                str.format(
                    "Time Manager time step value can not be 0 or negative",
                )
            )
        self._max_step = value
        self.current_step_size = value

    @property
    def current_step_size(self) -> float:
        """
        Get the current time step size.

        :return: the time step
        :rtype: float
        """
        return self._time_step

    @current_step_size.setter
    def current_step_size(self, value: float) -> None:
        """
        Set the current time step size.

        :param value: the time step to set
        :type value: float

        :raise ValueError: Raises a ValueError if the given value is
          less than min_step or greater than max_step.
        """

        if value < self.min_step:
            raise ValueError(
                "Time Manager time step value can not be inferior to minimum step",
            )
        elif value > self._max_step:
            raise ValueError(
                "Time Manager time step value can not be superior to default step",
            )

        self._time_step = value

    @property
    def time(self) -> Time:
        """
        Get the current :class:`~.Time` quantity

        :return: the time quantity
        :rtype: Time
        """
        return self._time

    @property
    def ended(self) -> bool:
        """
        Get if the time has reached the end time.

        :return: True if the new time value has reached the end time, False otherwise.
        :rtype: bool
        """
        return bool(self._time.new >= self.end)

    def update_time(self) -> None:
        """
        Set the ``current`` time value to the ``new`` time value and update the ``new``
        time value with the defined time step increment.

        If the ``end`` value is reached, the ``new`` time value is set
        to the ``end`` value.
        """
        updated_time = self._time.current + self._time_step
        if updated_time < self.end:
            self._time.initialize(self._time.new)
            self._time.update(self._time.current + self._time_step)
        else:
            # time manager reached end time
            self._time.initialize(self._time.new)
            self._time.update(self.end)

    def initialize(self) -> None:
        """
        Initialize the time with the ``start`` value.
        """
        self._time.initialize(self.start)
