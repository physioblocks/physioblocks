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

"""Declares functions to log exceptions and to catch unhandled exceptions."""

import functools
import logging
import traceback
import warnings
from collections.abc import Callable
from types import TracebackType
from typing import Any, TypeAlias

ExceptionHandlerFunction: TypeAlias = Callable[
    [type[BaseException], BaseException, TracebackType | None], None
]
"""Type alias for exception handler signature"""


def create_uncaught_exception_logger_handler(
    logger: logging.Logger,
) -> ExceptionHandlerFunction:
    """Create a handler that logs an uncaught exception.

    Parameters
    ----------
    logger : Logger
        the logger to use to log the exception

    Returns
    -------
    Callable
        the exception handler

    Examples
    --------

    .. code:: python

        # get a logger
        SIMULATION_LOG_FORMATER = logging.Formatter(logging.BASIC_FORMAT)
        _root_logger = logging.getLogger()
        _root_logger.setLevel(logging.DEBUG)

        # register a hook to log uncaught exceptions to the logger
        sys.excepthook = create_uncaught_exception_logger_handler(_root_logger)

    """

    def log_handler(
        exception_type: type[BaseException],
        exception_value: BaseException,
        tb: TracebackType | None = None,
    ) -> None:
        log_exception(logger, exception_type, exception_value, tb, logging.ERROR)

    return log_handler


def log_exception(
    logger: logging.Logger,
    exc_type: type[BaseException],
    exception: BaseException,
    tb: TracebackType | None,
    loglevel: int = logging.ERROR,
) -> None:
    """Log the provided exception.

    .. note:: Type and message of the exception are logged with the provided
      ``loglevel``, while the traceback information is logged as ``DEBUG``.

    Parameters
    ----------
    logger : Logger
        the logger used to log
    exc_type : type[BaseException]
        the exception type
    exception : BaseException
        the exception to log
    tb : TracebackType | None
        the traceback
    loglevel : int
        The loglevel. Default is ``logging.ERROR``.

    """
    logger.log(loglevel, str.format("{0}: {1}", exc_type.__name__, exception))

    if tb is not None:
        exception_tb = str.join(
            "", traceback.format_exception(exc_type, value=exception, tb=tb)
        )
        logger.debug(exception_tb)


def create_warning_logger_handler(
    logger: logging.Logger,
) -> Callable[..., None]:
    """Create a handler to log issued warnings.

    Parameters
    ----------
    logger : Logger
        the logger to use to log the warning

    Returns
    -------
    Callable[..., None]
        the warning handler

    Examples
    --------

    .. code:: python

        # get a logger
        _root_logger = logging.getLogger()
        _root_logger.setLevel(logging.DEBUG)

        # register a hook to log warnings to the logger
        warnings.showwarning = create_warning_logger_handler(_root_logger)

    """

    def warning_handler(
        message: Warning | str, category: type[Warning], *args: Any, **kwargs: Any
    ) -> None:
        logger.warning(f"{category.__name__}: {message}")

    return warning_handler


def experimental(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Notify the user the wrapped function might not work as expected.

    When the wrapped function is called, it issues a UserWarning.

    Parameters
    ----------
    func : Callable[..., Any]
        the function to wrap

    Returns
    -------
    Callable[..., Any]
        the wrapped function
    """

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        warnings.warn(
            f"{func.__qualname__} is experimental and may not work correctly.",
            category=UserWarning,
            stacklevel=2,
        )
        return func(*args, **kwargs)

    return wrapper
