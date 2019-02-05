# -*- coding: utf-8 -*-
#
# Copyright 2017-2019 Univention GmbH
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
from univention.admin.uldap import access, position
from univention.listener.handler_logging import get_logger
from univention.listener.exceptions import ListenerModuleConfigurationError, ListenerModuleRuntimeError
from univention.listener.handler_configuration import ListenerModuleConfiguration
from univention.listener.api_adapter import ListenerModuleAdapter


listener.configRegistry.load()


class HandlerMetaClass(type):
	"""
	Read handler configuration and invoke adapter.
	"""
	def __new__(cls, clsname, bases, attrs):
		kls = super(HandlerMetaClass, cls).__new__(cls, clsname, bases, attrs)
		if getattr(kls, '_is_listener_module', lambda: False)():
			kls.config = kls._get_configuration()
			lm_module = inspect.getmodule(kls)
			adapter_cls = kls._adapter_class
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
	_configuration_class = ListenerModuleConfiguration
	_adapter_class = ListenerModuleAdapter
	config = None
	ucr = listener.configRegistry

	class Configuration(ListenerModuleConfiguration):
		"""
		Overwrite this with your own class of the same name. It can be an
		any Python class with just the require attributes (name, description,
		ldap_filter) or a subclass of ListenerModuleConfiguration.
		"""
		pass

	def __init__(self, *args, **kwargs):
		"""
		When subclassing, in __init__() first call must be:
		super(.., self).__init__(*args, **kwargs)

		self.config will be set by the metaclass.
		"""
		if not self.config:
			raise ListenerModuleConfigurationError('{}.config was not set by meta class.'.format(self.__class__.__name__))
		self.logger = get_logger(self.config.get_name())
		self.ucr.load()
		self._lo = None
		self._po = None
		self._ldap_credentials = None
		self.logger.debug('Starting with configuration: %r', self.config)
		if not self.config.get_active():
			self.logger.warn(
				'Listener module %r deactivated by UCRV "listener/module/%s/deactivate".',
				self.config.get_name()
			)

	def __repr__(self):
		return '{}({})'.format(self.__class__.__name__, self.config.name)

	def create(self, dn, new):
		"""
		Called when a new object was created.

		:param str dn: current objects DN
		:param dict new: new LDAP objects attributes
		:return: None
		:rtype: None
		"""
		pass

	def modify(self, dn, old, new, old_dn):
		"""
		Called when an existing object was modified or moved.

		A move can be be detected by looking at old_dn. Attributes can be
		modified during a move.

		:param str dn: current objects DN
		:param dict old: previous LDAP objects attributes
		:param dict new: new LDAP objects attributes
		:param old_dn: previous DN if object was moved/renamed, None otherwise
		:type old_dn: str or None
		:return: None
		:rtype: None
		"""
		pass

	def remove(self, dn, old):
		"""
		Called when an object was deleted.

		:param str dn: current objects DN
		:param dict old: previous LDAP objects attributes
		:return: None
		:rtype: None
		"""
		pass

	def initialize(self):
		"""
		Called once when the Univention Directory Listener loads the module
		for the first time or when a resync it triggered.

		:return: None
		:rtype: None
		"""
		pass

	def clean(self):
		"""
		Called once when the Univention Directory Listener loads the module
		for the first time or when a resync it triggered.

		:return: None
		:rtype: None
		"""
		pass

	def pre_run(self):
		"""
		Called before create/modify/remove if either the Univention Directory
		Listener has been restarted or when post_run() has run before.

		Use for example to open an LDAP connection.

		:return: None
		:rtype: None
		"""
		pass

	def post_run(self):
		"""
		Called only, when no change happens for 15 seconds - for *any* listener
		module.

		Use for example to close an LDAP connection.

		:return: None
		:rtype: None
		"""
		pass

	@staticmethod
	@contextmanager
	def as_root():
		"""
		Contextmanager to temporarily change the effective UID of the current
		process to 0.

		with self.as_root():
			do something

		Use :py:func:`listener.setuid()` for any other user than `root`. But be
		aware that :py:func:`listener.unsetuid()` will not be possible
		afterwards, as that requires root privileges.

		:return: None
		:rtype: None
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
		"""
		Find differences in old and new. Returns dict with keys pointing to old
		and new values.

		:param dict old: previous LDAP objects attributes
		:param dict new: new LDAP objects attributes
		:param list keys: consider only those keys in comparison
		:param bool ignore_metadata: ignore changed metadata attributes (if `keys` is not set)
		:return: key -> (old[key], new[key]) mapping
		:rtype: dict
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
		"""
		Will be called for unhandled exceptions in create/modify/remove.

		:param str dn: current objects DN
		:param dict old: previous LDAP objects attributes
		:param dict new: new LDAP objects attributes
		:param str command: LDAP modification type
		:param Exception exc_type: exception class
		:param Exception exc_value: exception object
		:param traceback exc_traceback: traceback object
		:return: None
		:rtype: None
		"""
		self.logger.exception('dn=%r command=%r\n    old=%r\n    new=%r', dn, command, old, new)
		raise exc_type, exc_value, exc_traceback

	@property
	def lo(self):
		"""
		LDAP connection object.

		:return: uldap.access object
		:rtype: univention.admin.uldap.access
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
	def po(self):
		"""
		Get a LDAP position object for the base DN (ldap/base).

		:return: uldap.position object
		:rtype: univention.admin.uldap.position
		"""
		if not self._po:
			self._po = position(self.lo.base)
		return self._po

	def _get_ldap_credentials(self):
		"""
		Get the LDAP credentials received through setdata().

		:return: the LDAP credentials
		:rtype: dict(str, str)
		"""
		return self._ldap_credentials

	def _set_ldap_credentials(self, base, binddn, bindpw, host):
		"""
		Store LDAP connection credentials for use by self.lo. It is not
		necessary to manually run this method. The listener will automatically
		run it at startup.

		:param str base: base DN
		:param str binddn: bind DB
		:param str bindpw: bind password
		:param str host: LDAP server
		:return: None
		:rtype: None
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
			self._lo = self._po = None

	@classmethod
	def _get_configuration(cls):
		"""
		Load configuration, optionally converting a plain Python class to a
		ListenerModuleConfiguration object. Set cls._configuration_class to
		a subclass of ListenerModuleConfiguration to change the returned
		object type.

		:return: configuration object
		:rtype: ListenerModuleConfiguration
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
	def _is_listener_module(cls):
		"""
		Is this a listener module?

		:return: True id the file is in /usr/lib/univention-directory-listener.
		:rtype: bool
		"""
		try:
			path = inspect.getfile(cls)
		except TypeError:
			# loaded from interactive console: <module '__main__' (built-in)> is a built-in class
			return False
		return path.startswith('/usr/lib/univention-directory-listener')
