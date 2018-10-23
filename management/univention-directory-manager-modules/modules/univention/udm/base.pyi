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
from typing import Any, Dict, Iterable, Iterator, List, Optional, Text, TypeVar
from .udm import Udm


UdmLdapMapping = namedtuple('UdmLdapMapping', ('ldap2udm', 'udm2ldap'))


BaseUdmObjectTV = TypeVar('BaseUdmObjectTV', bound='BaseUdmObject')
BaseUdmModuleTV = TypeVar('BaseUdmModuleTV', bound='BaseUdmModule')
BaseUdmModuleMetadataTV = TypeVar('BaseUdmModuleMetadataTV', bound='BaseUdmModuleMetadata')
BaseUdmObjectPropertiesTV = TypeVar('BaseUdmObjectPropertiesTV', bound='BaseUdmObjectProperties')


class BaseUdmObjectProperties(object):
	def __init__(self, udm_obj):  # type: (BaseUdmObjectTV) -> None
		self._udm_obj = udm_obj

	def __repr__(self):  # type: () -> Text
		...

	def __deepcopy__(self, memo):  # type: (Dict[int, Dict[Text, Any]]) -> Dict[Text, Any]
		...


class BaseUdmObject(object):
	def __init__(self):  # type: () -> None
		self.dn = ''
		self.props = None  # type: BaseUdmObjectPropertiesTV
		self.options = []  # type: List[Text]
		self.policies = []  # type: List[Text]
		self.position = ''  # type: Text
		self._udm_module = None  # type: BaseUdmModuleTV

	def __repr__(self):  # type: () -> Text
		...

	def reload(self):  # type: () -> BaseUdmObjectTV
		...

	def save(self):  # type: () -> BaseUdmObjectTV
		...

	def delete(self):  # type: () -> None
		...


class BaseUdmModuleMetadata(object):
	auto_open = True
	auto_reload = True

	def __init__(self, udm_module, api_version):  # type: (BaseUdmModuleTV, int) -> None
		self._udm_module = udm_module
		self.api_version = api_version

	@property
	def identifying_property(self):  # type: () -> Text
		...

	def lookup_filter(self, filter_s=None):  # type: (Optional[Text]) -> Text
		...

	@property
	def mapping(self):  # type: () -> UdmLdapMapping
		...


class BaseUdmModule(object):
	supported_api_versions = ()  # type: Iterable[int]
	_udm_object_class = BaseUdmObject
	_udm_module_meta_class = BaseUdmModuleMetadata

	def __init__(self, udm, name):  # type: (Udm, Text) -> None
		self._udm = udm  # type: Udm
		self.name = name  # type: Text
		self.meta = None  # type: BaseUdmModuleMetadataTV

	def __repr__(self):  # type: () -> Text
		...

	@property
	def connection(self):  # type: () -> Any
		...

	def new(self):  # type: () -> BaseUdmObjectTV
		...

	def get(self, dn):  # type: (Text) -> BaseUdmObjectTV
		...

	def get_by_id(self, id):  # type: (Text) -> BaseUdmObjectTV
		...

	def search(self, filter_s='', base='', scope='sub'):
		# type: (Text, Optional[Text], Optional[Text]) -> Iterator[BaseUdmObjectTV]
		...
