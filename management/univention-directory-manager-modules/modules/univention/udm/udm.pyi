# -*- coding: utf-8 -*-
#
# Copyright 2018 Univention GmbH
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

from __future__ import absolute_import, unicode_literals
from .base import BaseUdmModule, BaseUdmObject
from .factory_config import UdmModuleFactoryConfiguration
from .utils import UDebug as ud, ConnectionConfig
from typing import Dict, Optional, Text, Tuple, Type


__default_api_version__ = 1


class Udm(object):
	_module_class_cache = {}  # type: Dict[Tuple[int, Text, Text], Type[BaseUdmModule]]
	_module_object_cache = {}  # type: Dict[Tuple[int, Text, Text, Text, Text, Text], BaseUdmModule]

	def __init__(self, connection_config, api_version=None):  # type: (ConnectionConfig, Optional[int]) -> None
		...

	@classmethod
	def using_admin(cls):  # type: () -> Udm
		...

	@classmethod
	def using_machine(cls):  # type: () -> Udm
		...

	@classmethod
	def using_credentials(
			cls,
			identity,  # type: Text
			password,  # type: Text
			base=None,  # type: Optional[Text]
			server=None,  # type: Optional[Text]
			port=None,  # type: Optional[int]
	):
		# type: (...) -> Udm
		...

	def version(self, api_version):  # type: (int) -> Udm
		...

	def get(self, name):  # type: (Text) -> BaseUdmModule
		...

	def identify_object_by_dn(self, dn):  # type: (Text) -> BaseUdmObject
		...

	def _get_by_factory_config(self, name, factory_config):
		# type: (Text, UdmModuleFactoryConfiguration) -> BaseUdmModule
		...

	@property
	def _api_version(self):  # type: () -> int
		...

	def _load_module(self, factory_config):  # type: (UdmModuleFactoryConfiguration) -> Type[BaseUdmModule]
		...
