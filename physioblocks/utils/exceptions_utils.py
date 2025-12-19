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

"""Declares a functions to log exceptions and to caught unhandled exceptions"""

import logging
import traceback
from collections.abc import Callable
from logging import Logger
from types import TracebackType
from typing import TypeAlias

ExceptionHandlerFunction: TypeAlias = Callable[
    [type[BaseException], BaseException, TracebackType | None], None
]
"""Type alias for exception handler signature"""


def create_uncaught_exception_logger_handler(
    logger: Logger,
) -> ExceptionHandlerFunction:
    """create_uncaught_exception_logger_handler(logger: Logger) -> ExceptionHandlerFunction

    Create an handler that log an uncaught exception.

    :param logger: the logger to use to log the exception
    :type logger: Logger

    :return: the exception handler
    :rtype: Callable

    Example
    ^^^^^^^

    .. code:: python

        # get a logger
        SIMULATION_LOG_FORMATER = logging.Formatter(logging.BASIC_FORMAT)
        _root_logger = logging.getLogger()
        _root_logger.setLevel(logging.DEBUG)

        # register a hook to log uncaught exceptions to the logger
        sys.excepthook = create_uncaught_exception_logger_handler(_root_logger)

    """  # noqa: E501

    def log_handler(
        exception_type: type[BaseException],
        exception_value: BaseException,
        tb: TracebackType | None = None,
    ) -> None:
        log_exception(logger, exception_type, exception_value, tb, logger.level)

    return log_handler


def log_exception(
    logger: Logger,
    exc_type: type[BaseException],
    exception: BaseException,
    tb: TracebackType | None,
    loglevel: int = logging.ERROR,
) -> None:
    """
    Log the provided exception.

    .. note:: Type and message of the exception are logged with the provided
      ``loglevel``, while the traceback informations are logged as ``DEBUG``.

    :param logger: the logger used to log
    :type logger: Logger

    :param exc_type: the exception type
    :type exception: type[BaseException]

    :param exception: the exception to log
    :type exception: Exception

    :param tb: the traceback
    :type exception: TracebackType

    :param loglevel: The loglevel, default is error
    :type loglevel: int
    """

    logger.log(loglevel, str.format("{0}: {1}", exc_type.__name__, exception))

    if tb is not None:
        exception_tb = str.join(
            "", traceback.format_exception(exc_type, value=exception, tb=tb)
        )
        logger.debug(exception_tb)
