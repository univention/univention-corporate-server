# -*- coding: utf-8 -*-
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2018-2023 Univention GmbH
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
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <https://www.gnu.org/licenses/>.

from __future__ import absolute_import, unicode_literals

from typing import Any, Dict, Iterable, Iterator, List, Optional, Tuple, Type, TypeVar, Union  # noqa: F401

import univention.config_registry

from ..base import BaseModuleMetadataTV, BaseModuleTV, BaseObjectProperties, BaseObjectTV, ModuleMeta
from ..encoders import BaseEncoder, DnPropertyEncoder  # noqa: F401


GenericObjectPropertiesTV = TypeVar(  # noqa: PYI001
    'GenericObjectPropertiesTV', bound=univention.udm.modules.generic.GenericObjectProperties,
)
GenericObjectTV = TypeVar('GenericObjectTV', bound=univention.udm.modules.generic.GenericObject)  # noqa: PYI001
GenericModuleMetadataTV = TypeVar(  # noqa: PYI001
    'GenericModuleMetadataTV', bound=univention.udm.modules.generic.GenericModuleMetadata,
)
GenericModuleTV = TypeVar('GenericModuleTV', bound=univention.udm.modules.generic.GenericModule)  # noqa: PYI001

OriUdmHandlerTV = TypeVar('OriUdmHandlerTV', bound=univention.admin.handlers.simpleLdap)  # noqa: PYI001


ucr = None  # type: univention.config_registry.ConfigRegistry  # noqa: PYI026
DEFAULT_CONTAINERS_DN = ''


class GenericObjectProperties(BaseObjectProperties):
    _encoders = {}  # type: Dict[str, Type[BaseEncoder]]

    def __init__(self, udm_obj):  # type: (BaseObjectTV) -> None
        ...

    def __setattr__(self, key, value):  # type: (str, Any) -> None
        ...


class GenericObject(BaseObjectTV):
    def __init__(self):  # type: () -> None
        self._udm_module = None  # type: GenericModuleTV
        self.props = None  # type: GenericObjectPropertiesTV
        self.policies = []  # type: List[Union[GenericObjectTV, DnPropertyEncoder.DnStr, str]]
        self.superordinate = None  # type: Union[GenericObjectTV, DnPropertyEncoder.DnStr, str]
        self._lo = None  # type: OriUdmHandlerTV
        self._orig_udm_object = None  # type: OriUdmHandlerTV
        self._old_position = ''
        self._fresh = True
        self._deleted = False

    def reload(self):  # type: () -> GenericObject
        ...

    def save(self):  # type: () -> GenericObject
        ...

    def delete(self, remove_childs=False):  # type: (Optional[bool]) -> None
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
        ...


class GenericModuleMeta(ModuleMeta):
    udm_meta_class = GenericModuleMetadata


class GenericModule(BaseModuleTV):
    _udm_object_class = GenericObject  # type: Type[GenericObjectTV]
    _udm_module_meta_class = GenericModuleMetadata  # type: Type[GenericModuleMetadata]
    _udm_module_cache = {}  # type: Dict[Tuple[str, str, str, str], OriUdmHandlerTV]
    _default_containers = {}  # type: Dict[str, Dict[str, Any]]
    _orig_udm_module = None  # type: OriUdmHandlerTV  # noqa: PYI026

    class Meta:
        supported_api_versions = ()  # type: Iterable[int]
        suitable_for = []  # type: Iterable[str]

    def __init__(self, name, connection, api_version):  # type: (str, Any, int) -> None
        ...

    def new(self, superordinate=None):  # type: (Optional[Union[str, GenericObjectTV]]) -> GenericObjectTV
        ...

    def get(self, dn):  # type: (str) -> GenericObject
        ...

    def search(self, filter_s='', base='', scope='sub', sizelimit=0):  # type: (str, str, str, int) -> Iterator[GenericObjectTV]
        ...

    def _dn_exists(self, dn):  # type: (str) -> bool
        ...

    def _get_default_position_property(self):  # type: () -> str
        ...

    def _get_default_containers(self):  # type: () -> Dict[str, List[str]]
        ...

    def _get_default_object_positions(self):  # type: () -> List[str]
        ...

    def _get_orig_udm_module(self):  # type: () -> OriUdmHandlerTV
        ...

    def _get_orig_udm_object(self, dn, superordinate=None):
        # type: (str, Optional[Union[str, GenericObjectTV]]) -> OriUdmHandlerTV
        ...

    def _load_obj(self, dn, superordinate=None, orig_udm_object=None):
        # type: (str, Optional[Union[str, GenericObjectTV]], Optional[OriUdmHandlerTV]) -> GenericObject
        ...

    def _verify_univention_object_type(self, orig_udm_obj):  # type: (OriUdmHandlerTV) -> None
        ...
