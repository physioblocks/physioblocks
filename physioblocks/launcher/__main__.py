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

"""Launch a simulation from a configuration file and organize the results.

When deleting a series from the launcher folder, or a specific simulation from
a series, the launchers logs are updated the next time any simulation is launched.
"""

import argparse
import logging
import os
import site
import sys
import warnings
from pathlib import Path
from typing import Any

import pandas as pd
from rich.logging import RichHandler

import physioblocks.utils.exceptions_utils as exception_utils
from physioblocks.configuration import Configuration, load, unwrap_aliases
from physioblocks.configuration.constants import PLOTS_CONFIGURATION_ID
from physioblocks.io.configuration import read_json, write_json
from physioblocks.launcher.configuration import (
    check_launcher_directory,
    create_simulation_folder_path,
    get_launcher_configuration,
    import_configured_aliases,
    import_configured_libraries,
)
from physioblocks.launcher.constants import (
    LAUNCHER_SERIES_DIR_NAME,
)
from physioblocks.launcher.files import (
    write_simulation_log_entry,
    write_simulation_results,
)
from physioblocks.launcher.series import get_simulation_info
from physioblocks.simulation import AbstractSimulation
from physioblocks.simulation.process import AbstractPlotProcess, run_processes

FILE_LOG_FORMATTER = logging.Formatter(logging.BASIC_FORMAT)
RICH_LOG_FORMATTER = logging.Formatter("%(message)s", "[%X]")

_root_logger = logging.getLogger()
_root_logger.setLevel(logging.DEBUG)

# register a hook to log uncaught exceptions
sys.excepthook = exception_utils.create_uncaught_exception_logger_handler(_root_logger)

warnings.filterwarnings(
    "always", category=DeprecationWarning, module=r"physioblocks\..*"
)

# register a hook to log warnings
warnings.showwarning = exception_utils.create_warning_logger_handler(_root_logger)


def _load_configuration(config_file_path: Path) -> Any:
    simulation_config = read_json(str(config_file_path))
    return unwrap_aliases(simulation_config)


def _run_simulation(config: Configuration) -> dict[str, pd.DataFrame]:
    simulation: AbstractSimulation = load(config)

    # Log simulation information
    _root_logger.debug(f"Net:{os.linesep}{simulation.simulation_model.factory.net}")
    _root_logger.debug(f"State:{os.linesep}{simulation.simulation_model.state}")
    _root_logger.debug(
        f"System:{os.linesep}{simulation.simulation_model.equation_system}"
    )

    results = simulation.run()
    _root_logger.info("Simulation complete.")

    return results


def _add_log_handler(
    handler: logging.Handler, level: str | int, formatter: logging.Formatter
) -> None:
    handler.setFormatter(formatter)
    handler.setLevel(level)
    _root_logger.addHandler(handler)


def _main(
    root_sim_directory: Path,
    config_file_path: Path,
    series: str,
    message: str,
    extension: str,
) -> int:
    if check_launcher_directory(root_sim_directory) is False:
        raise ValueError(
            f"{root_sim_directory.absolute()} is not a suitable directory for the "
            "launcher. Use the configure script to setup a new launcher directory.",
        )

    # Add site base libraries
    site.addsitedir(str(root_sim_directory.absolute()))

    # Prepare the series directory if necessary
    serie_path = root_sim_directory / LAUNCHER_SERIES_DIR_NAME / series
    if serie_path.exists() is False:
        serie_path.mkdir(parents=True)

    # Write the simulation log
    sim_info = get_simulation_info(serie_path, message)
    write_simulation_log_entry(root_sim_directory, sim_info)
    sim_folder = create_simulation_folder_path(serie_path, sim_info)

    # configure the simulation log file (always in DEBUG)
    log_file_path = sim_folder / str.join(".", [sim_info.reference, "log"])
    file_handler = logging.FileHandler(log_file_path)
    _add_log_handler(file_handler, logging.DEBUG, FILE_LOG_FORMATTER)

    # log the current simulation infos
    _root_logger.info(str(sim_info))

    launcher_configuration = get_launcher_configuration(root_sim_directory)
    import_configured_libraries(launcher_configuration)
    import_configured_aliases(launcher_configuration)

    exec_dir = Path.cwd()
    # Config paths are relative to the config file.
    os.chdir(config_file_path.parent)

    try:
        # Load configuration and unwrap aliases
        sim_config: Configuration = _load_configuration(config_file_path)

        # copy the unwrapped simulation configuration file to the simulation folder
        write_json(str(sim_folder / config_file_path.name), sim_config)

        # run the simulation
        data = _run_simulation(sim_config)

        # write the result
        write_simulation_results(sim_folder, data, extension)

        # trace the configured plots.
        if PLOTS_CONFIGURATION_ID in sim_config:
            plots: dict[str, AbstractPlotProcess] = load(
                sim_config[PLOTS_CONFIGURATION_ID]
            )

            # Initialize plot processes
            for plot_id, plot_process in plots.items():
                plot_process.folder_path = sim_folder
                plot_process.plot_name = plot_id

            run_processes(plots, data)
    finally:
        os.chdir(exec_dir)

    return 0


if __name__ == "__main__":
    # arguments handling

    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.HelpFormatter
    )
    parser.add_argument(
        "simulation_configuration",
        help="The simulation configuration file path.",
    )
    parser.add_argument(
        "-d",
        "--launcher_directory",
        default="./",
        required=False,
        help="A valid folder for the launcher to run (initialized with the configure "
        "script)",
    )
    parser.add_argument(
        "-s",
        "--series",
        dest="series",
        default="Z",
        required=False,
        help="The series name to save the simulation result.",
    )
    parser.add_argument(
        "-m",
        "--message",
        dest="message",
        default="",
        required=False,
        help="An optional comment on the simulation",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        dest="verbose",
        action="store_true",
        default=False,
        required=False,
        help="Display INFO level logs in the console",
    )

    parser.add_argument(
        "--DEBUG",
        dest="debug",
        action="store_true",
        default=False,
        required=False,
        help="Display DEBUG logs in console when used with -v",
    )

    parser.add_argument(
        "-ext",
        "--file_extension",
        dest="extension",
        default="csv",
        required=False,
        help="The file extension to write the simulation results.",
        choices=["csv", "parquet"],
    )
    args = parser.parse_args()

    # setup logger for console
    console_level = logging.WARNING

    if args.verbose is True:
        console_level = logging.INFO
        if args.debug is True:
            console_level = logging.DEBUG

    _add_log_handler(RichHandler(), console_level, RICH_LOG_FORMATTER)

    # create paths from arguments
    root_folder_path = Path(args.launcher_directory).absolute()
    config_file_path = Path(args.simulation_configuration).absolute()

    sys.exit(
        _main(
            root_sim_directory=root_folder_path,
            config_file_path=config_file_path,
            series=args.series,
            message=args.message,
            extension=args.extension,
        )
    )
