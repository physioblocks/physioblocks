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
"""Define configuration save / load function for io module objects."""

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, ClassVar

import pandas as pd
from pandas import DataFrame

from physioblocks.configuration.base import Configuration
from physioblocks.configuration.functions import load
from physioblocks.registers.load_function_register import loads
from physioblocks.registers.type_register import register_type


@dataclass
@register_type("read_data")
class DataReader:
    """Configurable object to read a file and return a DataFrame.

    The read method calls the pandas method matching the extension of the file.
    You can configure any positional or keyword arguments the pandas method accepts.

    The method currently supports

    * csv: https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html
    * parquet: https://pandas.pydata.org/docs/reference/api/pandas.read_parquet.html


    Loading a ``read_data`` configuration returns the read DataFrame.

    Parameters
    ----------
    filepath : str
        the location of the file to load.

    Configuration
    -------------

    .. code-block:: json

        {
            "type": "read_data",
            "filepath": "<str>",  // Location of the file to load (.csv or .parquet)
            "<str>": "<any>"      // Arguments for the pandas read method
                                  // (optional)
        }

    """

    _supported_formats: ClassVar[Iterable[str]] = [".csv", ".parquet"]
    filepath: str

    def read(self, *args: Any, **kwargs: Any) -> DataFrame:
        """
        Read the dataframe at configured filepath.

        Returns
        -------
        DataFrame
            the dataframe described in the file.

        Raises
        ------
        NotImplementedError
            if the file format is not supported.
        """
        path = Path(self.filepath).absolute()
        match path.suffix:
            case ".csv":
                return pd.read_csv(path, *args, **kwargs)
            case ".parquet":
                return pd.read_parquet(path, *args, **kwargs)
            case _:
                raise NotImplementedError(
                    f"{path}: Data Reader not implemented for {path.suffix} files. \
                    Supported format are: {DataReader._supported_formats}"
                )


@loads(DataReader)
def load_datareader(
    configuration: Configuration, *args: Any, **kwargs: Any
) -> DataFrame:
    """Define a function to load a dataframe from a :class:`DataReader` configuration.

    Parameters
    ----------
    configuration : Configuration
        The configuration to load

    Returns
    -------
    DataFrame
        a dataframe

    """
    arguments = load(configuration.configuration_items, configuration_type=dict)
    config_object = DataReader(arguments.pop("filepath"))
    return config_object.read(**arguments)
