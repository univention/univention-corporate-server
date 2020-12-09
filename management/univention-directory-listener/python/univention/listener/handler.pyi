# -*- coding: utf-8 -*-
#
# Univention Directory Listener
#  PEP 484 type hints stub file
#
# Copyright 2017-2021 Univention GmbH
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

from typing import Any, Dict, Iterable, Iterator, List, Optional, Tuple, Union, Type
import types
import inspect
import logging
from contextlib import contextmanager
from univention.admin.uldap import access, position
from univention.config_registry import ConfigRegistry
from univention.listener.handler_logging import get_logger
from univention.listener.handler_configuration import ListenerModuleConfiguration
from univention.listener.api_adapter import ListenerModuleAdapter


class HandlerMetaClass(type):
	"""
	Read handler configuration and invoke adapter.
	"""
	def __new__(cls, clsname: str, bases: List[Type[Any]], attrs: Dict[str, str]) -> Union[Type[Any], Type[ListenerModuleHandler]]:
		kls = super(HandlerMetaClass, cls).__new__(cls, clsname, bases, attrs)  # type: Union[Type[Any], Type[ListenerModuleHandler]]
		if getattr(kls, '_is_listener_module', lambda: False)():
			kls.config = kls._get_configuration()
			lm_module = inspect.getmodule(kls)  # type: types.ModuleType
			adapter_cls = kls._adapter_class  # type: Type[ListenerModuleAdapter]
		return kls


class ListenerModuleHandler(object):
	__metaclass__ = HandlerMetaClass

	_metadata_attributes = (
		'createTimestamp', 'creatorsName', 'entryCSN', 'entryDN', 'entryUUID',
		'hasSubordinates', 'modifiersName', 'modifyTimestamp',
		'structuralObjectClass', 'subschemaSubentry'
	)
	_configuration_class = ListenerModuleConfiguration  # type: Type[ListenerModuleConfiguration]
	_adapter_class = ListenerModuleAdapter  # type: Type[ListenerModuleAdapter]
	config: ListenerModuleConfiguration = ...
	ucr: ConfigRegistry = ...

	class Configuration(ListenerModuleConfiguration):
		...
	def __init__(self, *args: str, **kwargs: str) -> None:
		self._lo = None  # type: access
		self.logger =  get_logger(self.config.get_name())  # type: logging.Logger
		self._ldap_credentials = dict()  # type: Dict[str, str]
	@classmethod
	def _get_configuration(cls) -> ListenerModuleConfiguration:
		...
	def create(self, dn: str, new: Dict[str, List[str]]) -> None:
		...
	def modify(self, dn: str, old: Dict[str, List[str]], new: Dict[str, List[str]], old_dn: str) -> None:
		...
	def remove(self, dn: str, old: Dict[str, List[str]]) -> None:
		...
	def initialize(self) -> None:
		...
	def clean(self) -> None:
		...
	def pre_run(self) -> None:
		...
	def post_run(self) -> None:
		...
	@staticmethod
	@contextmanager
	def as_root() -> Iterator[None]:
		...
	@classmethod
	def diff(cls, old: Dict[str, List], new: Dict[str, List], keys: Optional[Iterable[str]] = None, ignore_metadata:bool = True) -> dict:
		...
	def error_handler(self, dn: str, old: Dict[str, List], new: Dict[str, List], command: str, exc_type: Type[BaseException], exc_value: BaseException, exc_traceback: types.TracebackType) -> None:
		...
	@property
	def lo(self) -> access:
		...
	@property
	def po(self) -> position:
		...
	def _get_ldap_credentials(self) -> Dict[str, str]:
		...
	def _set_ldap_credentials(self, base: str, binddn: str, bindpw: str, host: str) -> None:
		...
	def _is_listener_module(cls) -> bool:
		...
