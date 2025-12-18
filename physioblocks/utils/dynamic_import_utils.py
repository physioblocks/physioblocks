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
Defines methods to dynamically import modules while in a script or python
application.
"""

import importlib
import logging
import pkgutil
import sys
from pathlib import Path

from physioblocks.utils.exceptions_utils import log_exception

_logger = logging.getLogger(__name__)


def import_libraries(libraries_folder_paths: list[Path]) -> None:
    """
    Dynamically import all the modules at the given paths.

    .. note:: The libraries folders must be in a site to be able to
      load theirs modules.

    :param libraries_folder_path: the paths
    :type libraries_folder_path: list[Path]

    Example
    ^^^^^^^

    .. code:: python

        # Add site for the library to load
        site.addsitedir(ABSOLUTE_PATH_TO_LIBRARY)

        lib_path = Path(ABSOLUTE_PATH_TO_LIBRARY)
        import_libraries([lib_path]) # dynamically import the library

    """
    packages_absolute_paths: list[tuple[Path, str]] = []

    for library_path in libraries_folder_paths:
        if library_path.exists() is True:
            absolute_path = library_path.absolute()
            full_package_name = _get_full_package_name(absolute_path)
            packages_absolute_paths.append((absolute_path, full_package_name))
        else:
            _logger.error(
                str.format(
                    "There is no library folder at path {0}. Path skipped.",
                    str(library_path),
                )
            )

    for package_path, full_package_name in packages_absolute_paths:
        _import_modules_recursivly_at_path(package_path, full_package_name)


def _get_full_package_name(package_path: Path) -> str:
    if _is_package(package_path) is False:
        raise ImportError(str.format("{0} is not a package", package_path.name))

    full_package_name = package_path.name
    parent = package_path.parent
    check_parent = True
    while check_parent is True:
        check_parent = False
        if _is_package(parent) is True:
            full_package_name = ".".join([parent.name, full_package_name])
            parent = parent.parent
            check_parent = True

    return full_package_name


def _is_package(dir_path: Path) -> bool:
    return (
        any(
            path.is_file() and path.name == "__init__.py" for path in dir_path.iterdir()
        )
        is True
    )


def _import_modules_recursivly_at_path(
    package_path: Path, full_package_name: str
) -> None:
    for module_info in pkgutil.walk_packages([str(package_path)]):
        full_module_name = module_info.name
        if full_package_name is not None:
            full_module_name = ".".join([full_package_name, module_info.name])
        if full_module_name in sys.modules:
            # already loaded module
            _logger.warning(
                str.format(
                    "Module {0} at {1} already loaded. Module skipped ",
                    full_module_name,
                    str(package_path),
                )
            )
        else:
            try:
                importlib.import_module(full_module_name)
            except ImportError as import_exception:
                # Error while loading the module, log and skip the module
                log_exception(
                    _logger,
                    ImportError,
                    import_exception,
                    import_exception.__traceback__,
                    logging.WARNING,
                )
                _logger.warning(
                    str.format(
                        "Import Error while loading {0} from {1}. Module skipped ",
                        full_module_name,
                        str(package_path),
                    )
                )

        if module_info.ispkg is True:
            # recursivle load packa submodules
            _import_modules_recursivly_at_path(
                package_path / module_info.name, full_module_name
            )
