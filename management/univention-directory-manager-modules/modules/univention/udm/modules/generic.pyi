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
A generic UDM module and object implementation.
Will work for all kinds of UDM modules.
"""

from __future__ import absolute_import, unicode_literals
import univention.admin.objects
import univention.admin.modules
import univention.admin.uexceptions
import univention.admin.uldap
import univention.config_registry
from ..encoders import BaseEncoder
from ..base import BaseUdmModule, BaseUdmModuleMetadata, BaseUdmObject, BaseUdmObjectProperties, UdmLdapMapping
from ..utils import UDebug as ud

from typing import Any, Dict, Iterator, List, Optional, Text, Tuple, Type, Union


class GenericUdmObjectProperties(BaseUdmObjectProperties):
	_encoders = {}  # type: Dict[Text, Type[BaseEncoder]]

	def __init__(self, udm_obj):  # type: (BaseUdmObject) -> None
		...
	def __setattr__(self, key, value):  # type: (str, Any) -> None
		...

class GenericUdmObject(BaseUdmObject):
	def __init__(self):  # type: () -> None
		self._udm_module = None  # type: GenericUdmModule
		self._lo = None  # type: univention.admin.uldap.access
		self._orig_udm_object = None  # type: univention.admin.handlers.simpleLdap

	def reload(self):  # type: () -> GenericUdmObject
		...

	def save(self):  # type: () -> GenericUdmObject
		...

	def delete(self):  # type: () -> None
		...

	def _copy_from_udm_obj(self):  # type: () -> None
		...

	def _copy_to_udm_obj(self):  # type: () -> None
		...

	def _init_new_object_props(self):  # type: () -> None
		...

	def _init_encoder(self, encoder_class, **kwargs):
		# type: (Type[BaseEncoder], **Any) -> Union[Type[BaseEncoder], BaseEncoder]
		...


class GenericUdmModuleMetadata(BaseUdmModuleMetadata):
	@property
	def identifying_property(self):  # type: () -> Text
		...

	def lookup_filter(self, filter_s=None):  # type: (Optional[str]) -> str
		...

	@property
	def mapping(self):  # type: () -> UdmLdapMapping
		...


class GenericUdmModule(BaseUdmModule):
	_udm_module_cache = {}  # type: Dict[Tuple[str, str, str, str], univention.admin.handlers.simpleLdap]

	def __init__(self, name, lo, api_version):  # type: (str, univention.admin.uldap.access, int) -> None
		ucr = None  # type: univention.config_registry.ConfigRegistry
		self.lo = self.connection  # type: univention.admin.uldap.access

	def new(self):  # type: () -> GenericUdmObject
		...

	def get(self, dn):  # type: (str) -> GenericUdmObject
		...

	def search(self, filter_s='', base='', scope='sub'):  # type: (str, str, str) -> Iterator[GenericUdmObject]
		...
	def _dn_exists(self, dn):  # type: (str) -> bool
		...

	def _get_default_position_property(self):  # type: () -> str
		...

	def _get_default_containers(self):  # type: () -> Dict[str, List[str]]
		...

	def _get_default_object_positions(self):  # type: () -> List[str]
		...
	def _get_orig_udm_module(self):  # type: () -> univention.admin.handlers.simpleLdap
		...

	def _get_orig_udm_object(self, dn):  # type: (str) -> univention.admin.handlers.simpleLdap
		...

	def _load_obj(self, dn):  # type: (str) -> GenericUdmObject
		...

	def _verify_univention_object_type(self, orig_udm_obj):  # type: (univention.admin.handlers.simpleLdap) -> None
		...
