# -*- coding: utf-8 -*-
#
# Univention Directory Listener
#  PEP 484 type hints stub file
#
# Copyright 2017 Univention GmbH
#
# http://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention.
#
# This program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <http://www.gnu.org/licenses/>.

from __future__ import absolute_import
from univention.listener.handler_configuration import ListenerModuleConfiguration
from typing import Callable, Dict, List, Tuple, Union


class DecodeDictError(Exception):
	pass

def encode_dict(dic: Dict[str, List[str]]) -> Dict[str, List[str]]:
	...
def decode_dict(dic: Dict[str, List[str]]) -> Dict[str, List[str]]:
	...
def decode_dicts(*dicts: str) -> Callable:
	...
def entry_uuid_var_name(entry_uuid: str) -> str:
	...
def get_configuration_object(path: str) -> Union[ListenerModuleConfiguration, None]:
	...
def get_all_configuration_objects() -> List[ListenerModuleConfiguration]:
	...
def get_listener_module_file_stats() -> Dict[str, str]:
	...
def load_listener_module_cache() -> Dict[str, Dict[str, str]]:
	...
def store_listener_module_cache(obj: Dict[str, Dict[str, str]]) -> None:
	...
def update_listener_module_cache() -> Tuple[bool, Dict[str, Dict[str, str]]]:
	...
