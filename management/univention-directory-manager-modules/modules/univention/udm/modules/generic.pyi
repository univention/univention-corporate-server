# -*- coding: utf-8 -*-
#
# Copyright 2018-2019 Univention GmbH
#
# https://www.univention.de/
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
# <https://www.gnu.org/licenses/>.

"""
A generic UDM module and object implementation.
Will work for all kinds of UDM modules.
"""

from __future__ import absolute_import, unicode_literals
import univention.config_registry
from ..encoders import BaseEncoder, DnPropertyEncoder
from ..base import BaseObjectProperties, BaseObjectTV, BaseModuleTV, BaseModuleMetadataTV, ModuleMeta
from typing import Any, Dict, Iterable, Iterator, List, Optional, Text, Tuple, Type, TypeVar, Union


GenericObjectPropertiesTV = TypeVar(
	'GenericObjectPropertiesTV', bound='univention.udm.modules.generic.GenericObjectProperties'
)
GenericObjectTV = TypeVar('GenericObjectTV', bound='univention.udm.modules.generic.GenericObject')
GenericModuleMetadataTV = TypeVar(
	'GenericModuleMetadataTV', bound='univention.udm.modules.generic.GenericModuleMetadata'
)
GenericModuleTV = TypeVar('GenericModuleTV', bound='univention.udm.modules.generic.GenericModule')

OriUdmHandlerTV = TypeVar('OriUdmHandlerTV', bound='univention.admin.handlers.simpleLdap')


ucr = None  # type: univention.config_registry.ConfigRegistry
DEFAULT_CONTAINERS_DN = ''


class GenericObjectProperties(BaseObjectProperties):
	_encoders = {}  # type: Dict[Text, Type[BaseEncoder]]

	def __init__(self, udm_obj):  # type: (BaseObjectTV) -> None
		...
	def __setattr__(self, key, value):  # type: (Text, Any) -> None
		...

class GenericObject(BaseObjectTV):
	def __init__(self):  # type: () -> None
		self._udm_module = None  # type: GenericModuleTV
		self.props = None  # type: GenericObjectPropertiesTV
		self.policies = []  # type: List[Union[GenericObjectTV, DnPropertyEncoder.DnStr, Text]]
		self.superordinate = None  # type: Union[GenericObjectTV, DnPropertyEncoder.DnStr, Text]
		self._lo = None  # type: OriUdmHandlerTV
		self._orig_udm_object = None  # type: OriUdmHandlerTV
		self._old_position = ''
		self._fresh = True
		self._deleted = False

	def reload(self):  # type: () -> GenericObject
		...

	def save(self):  # type: () -> GenericObject
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


class GenericModuleMetadata(BaseModuleMetadataTV):
	def __init__(self, meta):  # type: (GenericModuleTV.Meta) -> None
		self.default_positions_property = None  # type: Text


class GenericModuleMeta(ModuleMeta):
	udm_meta_class = GenericModuleMetadata


class GenericModule(BaseModuleTV):
	_udm_object_class = GenericObject  # type: Type[GenericObjectTV]
	_udm_module_meta_class = GenericModuleMetadata  # type: Type[GenericModuleMetadata]
	_udm_module_cache = {}  # type: Dict[Tuple[Text, Text, Text, Text], OriUdmHandlerTV]
	_default_containers = {}  # type: Dict[Text, Dict[Text, Any]]

	class Meta:
		supported_api_versions = ()  # type: Iterable[int]
		suitable_for = []  # type: Iterable[Text]

	def __init__(self, name, connection, api_version):  # type: (Text, Any, int) -> None
		self._orig_udm_module = None  # type: OriUdmHandlerTV

	def new(self, superordinate=None):  # type: (Optional[Union[Text, GenericObjectTV]]) -> GenericObjectTV
		...

	def get(self, dn):  # type: (Text) -> GenericObject
		...

	def search(self, filter_s='', base='', scope='sub'):  # type: (Text, Text, Text) -> Iterator[GenericObjectTV]
		...
	def _dn_exists(self, dn):  # type: (Text) -> bool
		...

	def _get_default_position_property(self):  # type: () -> Text
		...

	def _get_default_containers(self):  # type: () -> Dict[Text, List[Text]]
		...

	def _get_default_object_positions(self):  # type: () -> List[Text]
		...
	def _get_orig_udm_module(self):  # type: () -> OriUdmHandlerTV
		...

	def _get_orig_udm_object(self, dn, superordinate=None):
		# type: (Text, Optional[Union[Text, GenericObjectTV]]) -> OriUdmHandlerTV
		...

	def _load_obj(self, dn, superordinate=None, orig_udm_object=None):
		# type: (Text, Optional[Union[Text, GenericObjectTV]], Optional[OriUdmHandlerTV]) -> GenericObject
		...

	def _verify_univention_object_type(self, orig_udm_obj):  # type: (OriUdmHandlerTV) -> None
		...
