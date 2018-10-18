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

"""
Base classes for (simplified) UDM modules and objects.
"""

from __future__ import absolute_import, unicode_literals
from collections import namedtuple
from typing import Any, Dict, Iterator, Optional, Text
from .utils import ConnectionConfig


UdmLdapMapping = namedtuple('UdmLdapMapping', ('ldap2udm', 'udm2ldap'))


class BaseUdmObjectProperties(object):
	def __init__(self, udm_obj):  # type: (BaseUdmObject) -> None
		...

	def __repr__(self):  # type: () -> str
		...

	def __deepcopy__(self, memo):  # type: (Dict[int, Dict[str, Any]]) -> Dict[str, Any]
		...


class BaseUdmObject(object):
	def __init__(self):  # type: () -> None
		...

	def __repr__(self):  # type: () -> Text
		...

	def reload(self):  # type: () -> BaseUdmObject
		...

	def save(self):  # type: () -> BaseUdmObject
		...

	def delete(self):  # type: () -> None
		...


class BaseUdmModuleMetadata(object):
	def __init__(self, udm_module, api_version):  # type: (BaseUdmModule, int) -> None
		...

	@property
	def identifying_property(self):  # type: () -> str
		...

	def lookup_filter(self, filter_s=None):  # type: (Optional[str]) -> str
		...

	@property
	def mapping(self):  # type: () -> UdmLdapMapping
		...


class BaseUdmModule(object):
	def __init__(self, name, connection_config, api_version):  # type: (Text, ConnectionConfig, int) -> None
		...

	def __repr__(self):  # type: () -> Text
		...

	def new(self):  # type: () -> BaseUdmObject
		...

	def get(self, dn):  # type: (Text) -> BaseUdmObject
		...

	def get_by_id(self, id):  # type: (Text) -> BaseUdmObject
		...

	def search(self, filter_s='', base='', scope='sub'):
		# type: (str, Optional[str], Optional[str]) -> Iterator[BaseUdmObject]
		...
