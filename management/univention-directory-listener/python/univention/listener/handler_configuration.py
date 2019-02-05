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
import string
import inspect
import listener
from univention.listener.handler_logging import get_logger
from univention.listener.exceptions import ListenerModuleConfigurationError


listener.configRegistry.load()


class ListenerModuleConfiguration(object):
	"""
	Interface class for accessing the configuration and code of a listener
	module.

	Subclass this and set the class attributes or pass them through __init__.
	If more logic is needed, overwrite the corresponding
	get_<attribute> method. Setting "name", "description", "ldap_filter" and
	"listener_module_class" is mandatory.

	To extend the configuration, add key names in get_configuration_keys()
	and create a get_<attribute> method.

	The listener server will use an object of your subclass to access your
	listener module through:
	1. get_configuration()
	2. get_listener_module_instance()
	"""

	name = ''                     # (*) name of the listener module
	description = ''              # (*) description of the listener module
	ldap_filter = ''              # (*) LDAP filter, if matched will trigger the listener module
	listener_module_class = None  # (**) class that implements the module
	attributes = []               # only trigger module, if any of the listed attributes has changed
	# (*) required
	# (**) will be set automatically by the handlers metaclass

	_mandatory_attributes = ('name', 'description', 'ldap_filter', 'listener_module_class')

	def __init__(self, *args, **kwargs):
		_keys = self.get_configuration_keys()
		for k, v in kwargs.items():
			if k in _keys:
				setattr(self, k, kwargs.pop(k))
		self.logger = get_logger(self.get_name())
		self._run_checks()

	def __repr__(self):
		return '{}({})'.format(
			self.__class__.__name__,
			', '.join('{}={!r}'.format(k, v) for k, v in self.get_configuration().items())
		)

	def _run_checks(self):
		allowed_name_chars = string.ascii_letters + string.digits + ',.-_'

		for attr in self._mandatory_attributes:
			if not getattr(self, 'get_{}'.format(attr), lambda: '')() and not getattr(self, attr, ''):
				raise ListenerModuleConfigurationError('Missing or empty {!r} attribute in configuration.'.format(attr))
		if set(self.get_name()) - set(allowed_name_chars):
			raise ListenerModuleConfigurationError(
				'The "name" of a listener module may only contain the following characters: {!r}'.format(allowed_name_chars)
			)
		if not inspect.isclass(self.get_listener_module_class()):
			raise ListenerModuleConfigurationError('Attribute "listener_module_class" must be a class.')

	def get_configuration(self):
		"""
		Get the configuration of a listener module.

		:return: configuration of listener module
		:rtype: dict
		"""
		res = dict()
		for key in self.get_configuration_keys():
			getter = getattr(self, 'get_{}'.format(key), None)
			if getter and callable(getter):
				value = getter()
			else:
				if hasattr(self, key):
					self.logger.warn("No 'get_%s' method found, using value of attribute %r directly.", key, key)
					value = getattr(self, key)
				else:
					raise ListenerModuleConfigurationError(
						'Neither "get_{0}" method nor class attribute found for configuration key {0!r}.'.format(key))
			res[key] = value
		return res

	@classmethod
	def get_configuration_keys(cls):
		"""
		List of known configuration keys. Subclasses can expand this to support
		additional attributes.

		:return: list of known configuration keys
		:rtype: list(str)
		"""
		return [
			'attributes',
			'description',
			'ldap_filter',
			'listener_module_class',
			'name',
		]

	def get_name(self):
		"""
		:return: name of module
		:rtype: str
		"""
		return self.name

	def get_description(self):
		"""
		:return: description string of module
		:rtype: str
		"""
		return self.description

	def get_ldap_filter(self):
		"""
		:return: LDAP filter of module
		:rtype: str
		"""
		return self.ldap_filter

	def get_attributes(self):
		"""
		:return: attributes of matching LDAP objects the module will be
		notified about if changed
		:rtype: list(str)
		"""
		assert isinstance(self.attributes, list)
		return self.attributes

	def get_listener_module_instance(self, *args, **kwargs):
		"""
		Get an instance of the listener module.

		:param tuple args: passed to __init__ of ListenerModuleHandler
		:param dict kwargs: : passed to __init__ of ListenerModuleHandler
		:return: instance of ListenerModuleHandler
		:rtype: ListenerModuleHandler
		"""
		return self.get_listener_module_class()(self, *args, **kwargs)

	def get_listener_module_class(self):
		"""
		Get the class to instantiate for a listener module.

		:return: subclass of univention.listener.ListenerModuleHandler
		:rtype: ListenerModuleHandler
		"""
		return self.listener_module_class

	def get_active(self):
		"""
		If this listener module should run. Determined by the value of
		listener/module/<name>/deactivate.

		:return: whether the listener module should be activated
		:rtype: bool
		"""
		return not listener.configRegistry.is_true('listener/module/{}/deactivate'.format(self.get_name()), False)
