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
Defines methods to save and load
:class:`~physioblocks.configuration.base.Configuration` objects to a json file

.. note::

    It is possible to save and load ``.jsonc`` files and use ``//`` characters to
    comment the file.

    The comments are discarded when the file is loaded: there are only here to increase
    the json readability.

"""

import json
import os
from pathlib import Path
from typing import Any

from physioblocks.configuration.base import Configuration

# Key giving the type of the configured object
_ITEM_TYPE_LABEL = "type"

# Character delimiting a comment
_COMMENT_CHAR = "//"


class _JSONConfigEncoder(json.JSONEncoder):
    """
    Derive from the base JSONEncoder class to redefine the
    encoding of Configuration and Configuration objects
    """

    def default(self, obj: Any) -> Any:
        """
        Overwrite the default encoder method.

        :param obj: the object to encode
        :type obj: Any

        :return: the encoded object
        :rtype: dict[str, obj]
        """

        if isinstance(obj, Configuration):
            item_dict: dict[str, Any]
            item_dict = {}
            item_dict[_ITEM_TYPE_LABEL] = obj.label
            item_dict.update(obj.configuration_items)

            return item_dict

        return super().default(obj)


def write_json(file_path: str, config: Configuration) -> None:
    """
    Write the :class:`~physioblocks.configuration.base.Configuration` object
    to a json file

    :param file_path: the path of the file to read
    :type file_path: str

    :param config: the configuration to write
    :type config: Configuration
    """
    config_json = json.dumps(config, cls=_JSONConfigEncoder, indent=4)
    Path(file_path).write_text(config_json)


def read_json(file_path: str) -> Any:
    """
    Read a :class:`~physioblocks.configuration.base.Configuration` from a json file

    :param file_path: the path of the file to read
    :type file_path: str

    :return: the loaded configuration
    :rtype: Configuration
    """
    json_txt = Path(file_path).read_text()

    uncommented_lines = [
        line.split(_COMMENT_CHAR, 1)[0] for line in json_txt.splitlines()
    ]
    uncommented_json_txt = os.linesep.join(uncommented_lines)
    return json.loads(uncommented_json_txt, object_hook=_as_config)


def _as_config(dict_obj: dict[Any, Any]) -> Any:
    if _ITEM_TYPE_LABEL in dict_obj:
        config_item = Configuration(
            dict_obj[_ITEM_TYPE_LABEL],
            {key: value for key, value in dict_obj.items() if key != _ITEM_TYPE_LABEL},
        )
        return config_item

    return dict_obj
