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

from pathlib import Path

import pandas as pd
import pytest

from physioblocks.configuration.base import Configuration
from physioblocks.configuration.io import DataReader, load_datareader


@pytest.fixture
def reference_data():
    data = {"col1": [1, 2, 3], "col2": ["a", "b", "c"]}
    return pd.DataFrame(data)


@pytest.fixture
def reference_configuration(tmp_path: Path):
    return Configuration(
        "read_data", {"filepath": str(tmp_path.absolute() / "reference.csv")}
    )


def test_data_reader_csv(tmp_path, reference_data: pd.DataFrame):
    datapath = tmp_path / "reference.csv"
    reference_data.to_csv(datapath, index=False)

    reader = DataReader(datapath)
    data = reader.read()

    assert reference_data.equals(data)


def test_data_reader_csv_with_arguments(tmp_path, reference_data: pd.DataFrame):
    datapath = tmp_path / "reference.csv"
    reference_data.to_csv(datapath, index=False, sep=";")

    reader = DataReader(datapath)
    data = reader.read(sep=";")

    assert reference_data.equals(data)


def test_data_reader_parquet(tmp_path, reference_data: pd.DataFrame):
    datapath = tmp_path / "reference.parquet"
    reference_data.to_parquet(datapath, index=False)

    reader = DataReader(datapath)
    data = reader.read()

    assert reference_data.equals(data)


def test_data_reader_parquet_with_arguments(tmp_path, reference_data: pd.DataFrame):
    datapath = tmp_path / "reference.parquet"
    reference_data.to_parquet(datapath, index=False)

    reader = DataReader(datapath)
    data = reader.read(columns=["col2"])

    assert pd.DataFrame(reference_data["col2"]).equals(data)


def test_data_reader_unsupported_format(tmp_path):
    datapath = tmp_path / "reference.txt"
    reader = DataReader(datapath)

    with pytest.raises(NotImplementedError, match=(r"not implemented for .txt files")):
        reader.read()


def test_load_data_reader(tmp_path, reference_data: pd.DataFrame):
    config = Configuration("read_data")
    config.configuration_items["filepath"] = str(tmp_path / "reference.csv")
    reference_data.to_csv(config.configuration_items["filepath"], index=False)

    data = load_datareader(config)

    assert reference_data.equals(data)


def test_load_data_with_additional_params(tmp_path, reference_data: pd.DataFrame):
    config = Configuration("read_data")
    config.configuration_items["filepath"] = str(tmp_path / "reference.csv")
    config.configuration_items["sep"] = ";"
    reference_data.to_csv(config.configuration_items["filepath"], index=False, sep=";")

    data = load_datareader(config)

    assert reference_data.equals(data)
