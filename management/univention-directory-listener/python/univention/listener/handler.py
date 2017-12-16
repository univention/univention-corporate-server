# -*- coding: utf-8 -*-
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
import os
import inspect
from contextlib import contextmanager
import listener
import univention.admin.objects
from univention.admin.uldap import access, position
from univention.listener.handler_logging import get_logger
from univention.listener.exceptions import ListenerModuleConfigurationError, ListenerModuleRuntimeError
from univention.listener.handler_configuration import ListenerModuleConfiguration
from univention.listener.api_adapter import ListenerModuleAdapter

try:
	from typing import Any, Dict, Iterable, Iterator, List, Optional, Tuple, Type
	import logging
	import types.TracebackType
	import univention.admin.handlers.simpleLdap
	import univention.config_registry.ConfigRegistry
except ImportError:
	pass

listener.configRegistry.load()


class HandlerMetaClass(type):
	"""
	Read handler configuration and invoke adapter.
	"""
	def __new__(cls, clsname, bases, attrs):
		# type: (HandlerMetaClass, str, Tuple[Type], dict) -> Type[ListenerModuleHandler]
		kls = super(HandlerMetaClass, cls).__new__(cls, clsname, bases, attrs)  # type: Type[ListenerModuleHandler]
		if getattr(kls, '_is_listener_module', lambda: False)():
			kls.config = kls._get_configuration()  # type: ListenerModuleConfiguration
			lm_module = inspect.getmodule(kls)  # type: types.ModuleType
			adapter_cls = kls._adapter_class  # type: Type[ListenerModuleAdapter]
			for k, v in adapter_cls(kls.config).get_globals().items():
				setattr(lm_module, k, v)
		return kls


class ListenerModuleHandler(object):
	"""
	Listener module base class.

	Subclass this to implement the logic of your listener module and have
	ListenerModuleConfiguration.get_listener_module_class return the name of
	your subclass.

	This class is not intended to be used directly. It should only be
	instantiated by ListenerModuleConfiguration.get_listener_module_instance().
	"""
	__metaclass__ = HandlerMetaClass

	_metadata_attributes = (
		'createTimestamp', 'creatorsName', 'entryCSN', 'entryDN', 'entryUUID',
		'hasSubordinates', 'modifiersName', 'modifyTimestamp',
		'structuralObjectClass', 'subschemaSubentry'
	)
	_support_async = False
	_udm_module_cache = dict()  # type: Dict
	_configuration_class = ListenerModuleConfiguration  # type: Type[ListenerModuleConfiguration]
	_adapter_class = ListenerModuleAdapter  # type: Type[ListenerModuleAdapter]
	config = None  # type: ListenerModuleConfiguration
	ucr = listener.configRegistry    # type: univention.config_registry.ConfigRegistry

	class Configuration(ListenerModuleConfiguration):
		"""
		Overwrite this with your own class of the same name. It can be an
		any Python class with just the require attributes (name, description,
		ldap_filter) or a subclass of ListenerModuleConfiguration.
		"""
		pass

	def __init__(self, *args, **kwargs):  # type: (*Tuple, **Dict) -> None
		"""
		When subclassing, in __init__() first call must be:
		super(.., self).__init__(*args, **kwargs)

		self.config will be set by the metaclass.
		"""
		if not self.config:
			raise ListenerModuleConfigurationError('{}.config was not set by meta class.'.format(self.__class__.__name__))
		self.logger = get_logger(self.config.get_name())  # type: logging.Logger
		self.ucr.load()
		self._lo = None  # type: access
		self._ldap_credentials = None  # type: Dict[str, str]
		self.logger.debug('Starting with configuration: %r', self.config)

	def __repr__(self):
		return '{}({})'.format(self.__class__.__name__, self.config.name)

	def create(self, dn, new):  # type: (str, Dict[str, List[str]]) -> None
		"""
		Called when a new object was created.

		:param dn: str
		:param new: dict
		:return: None
		"""
		pass

	def modify(self, dn, old, new, old_dn):  # type: (str, Dict[str, List[str]], Dict[str, List[str]], str) -> None
		"""
		Called when an existing object was modified or moved.

		A move can be be detected by looking at old_dn. Attributes can be
		modified during a move.

		:param dn: str
		:param old: dict
		:param new: dict
		:param old_dn: str if object was moved/renamed, None otherwise
		:return: None
		"""
		pass

	def remove(self, dn, old):  # type: (str, Dict[str, List[str]]) -> None
		"""
		Called when an object was deleted.

		:param dn: str
		:param old: dict
		:return: None
		"""
		pass

	def initialize(self):  # type: () -> None
		"""
		Called once when the Univention Directory Listener loads the module
		for the first time or when a resync it triggered.

		:return: None
		"""
		pass

	def clean(self):  # type: () -> None
		"""
		Called once when the Univention Directory Listener loads the module
		for the first time or when a resync it triggered.

		:return: None
		"""
		pass

	def pre_run(self):  # type: () -> None
		"""
		Called before create/modify/remove if either the Univention Directory
		Listener has been restarted or when post_run() has run before.

		Use for example to open an LDAP connection.

		:return: None
		"""
		pass

	def post_run(self):  # type: () -> None
		"""
		Called only, when no change happens for 15 seconds - for *any* listener
		module.

		Use for example to close an LDAP connection.

		:return: None
		"""
		pass

	@staticmethod
	@contextmanager
	def as_root():  # type: () -> Iterator[None]
		"""
		Temporarily change the UID of the current process to 0.

		with self.as_root():
			do something

		Use listener.setuid(<int|str>) for any other user that root. But be
		aware that listener.unsetuid() will not be possible afterwards, as
		that requires root privileges.

		:return: None
		"""
		old_uid = os.geteuid()
		try:
			if old_uid != 0:
				listener.setuid(0)
			yield
		finally:
			if old_uid != 0:
				listener.unsetuid()

	@classmethod
	def diff(cls, old, new, keys=None, ignore_metadata=True):
		# type: (Dict[str, List], Dict[str, List], Optional[Iterable[str]], Optional[bool]) -> dict
		"""
		Find differences in old and new. Returns dict with keys pointing to old
		and new values.

		:param old: dict
		:param new: dict
		:param keys: list: consider only those keys in comparison
		:param ignore_metadata: bool: ignore changed metadata attributes (if `keys` is not set)
		:return: dict: key -> (old[key], new[key])
		"""
		res = dict()
		if keys:
			keys = set(keys)
		else:
			keys = set(old.keys()).union(set(new.keys()))
			if ignore_metadata:
				keys.difference_update(cls._metadata_attributes)
		for key in keys:
			if set(old.get(key, [])) != set(new.get(key, [])):
				res[key] = old.get(key), new.get(key)
		return res

	def error_handler(self, dn, old, new, command, exc_type, exc_value, exc_traceback):
		# type: (str, Dict[str, List], Dict[str, List], str, Type[BaseException], BaseException, types.TracebackType) -> None
		"""
		Will be called for unhandled exceptions in create/modify/remove.

		The error_handler() in an asynchronous listener module must *not* raise
		an exception itself, or the worker will exit and further replication
		will cease!

		:param dn: str
		:param old: dict
		:param new: dict
		:param command: str
		:param exc_type: exception class
		:param exc_value: exception object
		:param exc_traceback: traceback object
		:return: None
		"""
		self.logger.exception('dn=%r command=%r\n    old=%r\n    new=%r', dn, command, old, new)
		if not self._support_async:
			raise exc_type, exc_value, exc_traceback

	@classmethod
	def get_udm_objects(cls, module_name, filter_s, base_dn, lo, po, **kwargs):
		# type: (str, str, str, access, position, **Dict) -> List[univention.admin.handlers.simpleLdap]
		"""
		Search LDAP for UDM objects.

		:param module_name: str: UDM module ("users/user", "groups/group" etc)
		:param filter_s: str: LDAP filter
		:param base_dn: str: LDAP DN to start search from
		:param lo: univention.admin.uldap.access object
		:param po: univention.admin.uldap.position object
		:param kwargs: dict: arguments to pass to udm_module.lookup()
		:return: list of (not yet opened) univention.admin.handlers.simpleLdap objects
		"""
		key = (lo.base, lo.binddn, lo.bindpw, po.getDn())
		if key not in cls._udm_module_cache:
			univention.admin.modules.update()
			udm_module = univention.admin.modules.get(module_name)
			univention.admin.modules.init(lo, po, udm_module)
			cls._udm_module_cache[key] = udm_module
		udm_module = cls._udm_module_cache[key]
		return udm_module.lookup(None, lo, filter_s=filter_s, base=base_dn, **kwargs)

	@property
	def lo(self):  # type: () -> access
		"""
		LDAP connection object.

		:return: univention.admin.uldap.access object
		"""
		if not self._lo:
			ldap_credentials = self._get_ldap_credentials()
			if not ldap_credentials:
				raise ListenerModuleRuntimeError(
					'LDAP connection of listener module {!r} has not yet been initialized.'.format(self.config.get_name())
				)
			self._lo = access(**ldap_credentials)
		return self._lo

	@property
	def po(self):  # type: () -> position
		"""
		Get a LDAP position object for the base DN (ldap/base).

		:return: univention.admin.uldap.position object
		"""
		return position(self.lo.base)

	def _get_ldap_credentials(self):  # type: () -> Dict[str, str]
		return self._ldap_credentials

	def _set_ldap_credentials(self, base, binddn, bindpw, host):  # type: (str, str, str, str) -> None
		"""
		Store LDAP connection credentials for use by self.lo.

		:param base: str
		:param binddn: str
		:param bindpw: str
		:param host: str
		:return: None
		"""
		old_credentials = self._ldap_credentials
		self._ldap_credentials = dict(
			host=host,
			base=base,
			binddn=binddn,
			bindpw=bindpw
		)
		if old_credentials != self._ldap_credentials:
			# force creation of new LDAP connection
			self._lo = None

	@classmethod
	def _get_configuration(cls):  # type: () -> ListenerModuleConfiguration
		"""
		Load configuration, optionally converting a plain Python class to a
		ListenerModuleConfiguration object. Set cls._configuration_class to
		a subclass of ListenerModuleConfiguration to change the returned
		object type.

		:return: ListenerModuleConfiguration object
		"""
		try:
			conf_class = cls.Configuration
		except AttributeError:
			raise ListenerModuleConfigurationError('Class {!r} missing inner "Configuration" class.'.format(cls.__name__))
		if not inspect.isclass(conf_class):
			raise ListenerModuleConfigurationError('{!s}.Configuration must be a class.'.format(cls.__name__))
		if conf_class is ListenerModuleHandler.Configuration:
			raise ListenerModuleConfigurationError('Missing {!s}.Configuration class.'.format(cls.__name__))
		if issubclass(cls.Configuration, cls._configuration_class):
			cls.Configuration.listener_module_class = cls
			return cls.Configuration()
		else:
			conf_obj = cls.Configuration()
			attrs = cls._configuration_class.get_configuration_keys()
			kwargs = dict(listener_module_class=cls)
			for attr in attrs:
				try:
					get_method = getattr(conf_obj, 'get_{}'.format(attr))
					if not callable(get_method):
						raise ListenerModuleConfigurationError(
							'Attribute {!r} of configuration class {!r} is not callable.'.format(
								get_method, conf_obj.__class__)
						)
					kwargs[attr] = get_method()
					continue
				except AttributeError:
					pass
				try:
					kwargs[attr] = getattr(conf_obj, attr)
				except AttributeError:
					pass
				# Checking for required attributes is done in ListenerModuleConfiguration().
			return cls._configuration_class(**kwargs)

	@classmethod
	def _is_listener_module(cls):  # type () -> bool
		try:
			path = inspect.getfile(cls)
		except TypeError:
			# loaded from interactive console: <module '__main__' (built-in)> is a built-in class
			return False
		return path.startswith('/usr/lib/univention-directory-listener')
