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
Dynamic factory configuration backend.

UDM module factory configurations can be registered and retrieved using a
regular expression.

A UDM module factory configuration consists of:

* name regex pattern
* dotted Python module path
* name of Python class in above module

UDM module factory configurations are stored in
:py:`UdmModuleFactoryConfiguration` objects. The registry is persistent.

Multiple modules can be registered for the same UDM module name. When
retrieving by UDM module name and multiple configurations are found, the
decision which one to return is done in the following order:

1. exact name match, newest registration if multiple
2. regular expression name match, newest registration if multiple
3. the default configuration


>>> config_storage = UdmModuleFactoryConfigurationStorage(False)
>>> config1 = UdmModuleFactoryConfiguration('groups/.*', 'univention.udm.generic', 'GenericUdm1Module')
>>> config2 = UdmModuleFactoryConfiguration('^users/user$', 'univention.udm.users_user', 'UsersUserUdm1Module')
>>> config3 = UdmModuleFactoryConfiguration('^users/.*$', 'univention.udm.generic', 'GenericUdm1Module')
>>> config_storage.register_configuration(config1)
Debug: prepended '^' to pattern: u'^groups/.*'
Debug: appended '$' to pattern: u'^groups/.*$'
Debug: prepended '^' to pattern: u'^groups/.*'
Debug: appended '$' to pattern: u'^groups/.*$'
Debug: prepended '^' to pattern: u'^groups/.*'
Debug: appended '$' to pattern: u'^groups/.*$'
>>> config_storage.register_configuration(config2)
>>> config_storage.register_configuration(config3)
>>> config_storage.get_configuration('users/user')
UdmModuleFactoryConfiguration(udm_module_name_pattern=u'^users/user$', module_path=u'univention.udm.users_user', class_name=u'UsersUserUdm1Module')
>>> config_storage.get_configuration('users/ldap')
UdmModuleFactoryConfiguration(udm_module_name_pattern=u'^users/.*$', module_path=u'univention.udm.generic', class_name=u'GenericUdm1Module')
>>> config_storage.get_configuration('groups/group')
UdmModuleFactoryConfiguration(udm_module_name_pattern=u'^groups/.*$', module_path=u'univention.udm.generic', class_name=u'GenericUdm1Module')
>>> config_storage.get_configuration('computers/domaincontroller_master')
Debug: no specific factory for u'computers/domaincontroller_master' found, using {u'class_name': u'GenericUdm1Module', u'module_path': u'univention.udm.generic'}.
UdmModuleFactoryConfiguration(udm_module_name_pattern=u'computers/domaincontroller_master', module_path=u'univention.udm.generic', class_name=u'GenericUdm1Module')
>>> config_storage.unregister_configuration(config2)
Info: Unregistered configuration UdmModuleFactoryConfiguration(udm_module_name_pattern=u'^users/user$', module_path=u'univention.udm.users_user', class_name=u'UsersUserUdm1Module').
>>> config_storage.get_configuration('users/user')
UdmModuleFactoryConfiguration(udm_module_name_pattern=u'^users/.*$', module_path=u'univention.udm.generic', class_name=u'GenericUdm1Module')
"""

from __future__ import unicode_literals
import os
import re
import json
import time
import errno
from operator import attrgetter
from collections import namedtuple
from univention.udm.utils import UDebug as ud

try:
	from typing import Any, Dict, List, Optional, Pattern, Text, Tuple, Union
except ImportError:
	pass


UdmModuleFactoryConfiguration = namedtuple(
	'UdmModuleFactoryConfiguration',
	('udm_module_name_pattern', 'module_path', 'class_name')
)  # e.g. UdmModuleFactoryConfiguration('users/.*', 'univention.admin.udm', 'GenericUdm1Module')


_UdmModuleFactoryConfigurationWithDate = namedtuple(
	'UdmModuleFactoryConfigurationWithDate',
	('udm_module_name_pattern', 'module_path', 'class_name', 'addition_date')
)


class UdmModuleFactoryConfigurationStorage(object):
	"""Handle loading and storing of the dynamic factory metadata."""
	_default_factory = {'module_path': 'univention.udm.generic', 'class_name': 'GenericUdm1Module'}
	_persistence_path = '/var/lib/univention-directory-manager-modules/udm_module_factory.json'

	def __init__(self, persistent=True):  # type: (Optional[bool]) -> None
		"""
		:param bool persistent: whether configuration changes should be stored (and immediately be used by other processes) or should be transient, and used in this process only
		"""
		self.persistent = persistent
		self._config = {}  # type: Dict[Pattern, List[_UdmModuleFactoryConfigurationWithDate]]
		self._transient_operations = []  # type: List[Tuple[Text, Pattern, _UdmModuleFactoryConfigurationWithDate]]
		self._persistence_date = 0.0  # type: float

		try:
			self._load_configuration()
		except IOError:
			ud.warn('No configuration could be loaded from disk. Continuing with empty one.')
			self._config = {}

	def get_configuration(self, module_name):  # type: (str) -> UdmModuleFactoryConfiguration
		"""
		Get configuration for a module.

		:param str module_name: the UDM modules name for which to get the factory configuration
		:return: the factory configuration
		:rtype: UdmModuleFactoryConfiguration
		"""
		candidates_exact = []
		candidates_regex = []

		self.refresh_config()

		for udm_module_name_pattern, configurations in self._config.iteritems():
			if udm_module_name_pattern.pattern == '^{}$'.format(module_name):
				candidates_exact.extend(configurations)
			elif udm_module_name_pattern.match(module_name):
				candidates_regex.extend(configurations)

		if candidates_exact:
			candidates_exact.sort(key=attrgetter('addition_date'), reverse=True)
			return self._config_with_date_2_config_without_date(candidates_exact[0])

		if candidates_regex:
			candidates_regex.sort(key=attrgetter('addition_date'), reverse=True)
			return self._config_with_date_2_config_without_date(candidates_regex[0])

		ud.debug('No specific factory for {!r} found, using {!r}.'.format(module_name, self._default_factory))
		return UdmModuleFactoryConfiguration(
			udm_module_name_pattern=module_name, **self._default_factory
		)

	def register_configuration(self, factory_configuration):  # type: (UdmModuleFactoryConfiguration) -> None
		"""
		Store configuration for a module.

		:param UdmModuleFactoryConfiguration factory_configuration: the configuration to save
		:return: None
		:raises IOError: if the configuration could not be written to disk
		"""
		self.refresh_config()

		compiled_pattern = re.compile(self._add_regex_bounds(factory_configuration.udm_module_name_pattern))

		# check if configuration already exists
		old_config = self._find_configuration(factory_configuration)
		if old_config:
			# cannot update tuple -> remove, add
			self._config[compiled_pattern].remove(old_config)

		config_with_date = self._config_without_date_2_config_with_date(factory_configuration)
		self._config.setdefault(compiled_pattern, []).append(config_with_date)
		if self.persistent:
			self._save_configuration()
		else:
			if old_config:
				self._transient_operations.append(('del', compiled_pattern, old_config))
			self._transient_operations.append(('add', compiled_pattern, config_with_date))

	def unregister_configuration(self, factory_configuration):  # type: (UdmModuleFactoryConfiguration) -> None
		"""
		Remove configuration for a module from storage.

		:param UdmModuleFactoryConfiguration factory_configuration: the configuration to remove
		:return: None
		:raises IOError: if the changed configuration could not be written to disk
		"""
		self.refresh_config()
		config_with_date = self._find_configuration(factory_configuration)

		if config_with_date:
			compiled_pattern = re.compile(factory_configuration.udm_module_name_pattern)
			self._config[compiled_pattern].remove(config_with_date)
			if not self._config[compiled_pattern]:
				del self._config[compiled_pattern]
			ud.info('Unregistered configuration {!r}.'.format(
				self._config_with_date_2_config_without_date(config_with_date)))
			if self.persistent:
				self._save_configuration()
			else:
				self._transient_operations.append(('del', compiled_pattern, config_with_date))
		else:
			ud.warn('Could not find configuration to unregister: {!r}.'.format(factory_configuration))

	def refresh_config(self):
		"""
		If the configuration storage was updated, load it.

		Will reapply register and unregister operations if in non-persistent
		mode.

		:return: None
		"""
		try:
			mtime = os.stat(self._persistence_path).st_mtime
		except OSError as exc:
			if exc.errno == errno.ENOENT:
				# No such file or directory. When starting without storage.
				return
			else:
				raise

		if mtime > self._persistence_date:
			self._load_configuration()
			# reapply register and unregister operations if in non-persistent mode
			while self._transient_operations:
				operation, pattern, config = self._transient_operations.pop(0)
				if operation == 'add':
					self._config.setdefault(pattern, []).append(config)
				elif operation == 'del':
					try:
						self._config[pattern].remove(config)
					except (KeyError, ValueError):
						pass
				else:
					raise RuntimeError('Unknown operation in self._transient_operations: {!r}'.format(self._transient_operations))

	def _find_configuration(self, factory_configuration):
		# type: (UdmModuleFactoryConfiguration) -> Union[_UdmModuleFactoryConfigurationWithDate, None]
		compiled_pattern = re.compile(self._add_regex_bounds(factory_configuration.udm_module_name_pattern))
		try:
			configs = self._config[compiled_pattern]
		except KeyError:
			return None
		for config in configs:
			if (
				config.module_path == factory_configuration.module_path and
				config.class_name == factory_configuration.class_name
			):
				return config
		return None

	def _load_configuration(self):  # type: () -> Dict[Pattern, List[_UdmModuleFactoryConfigurationWithDate]]
		"""
		Load configuration from disk.

		:return: mapping module_name -> configuration
		:rtype: Dict[str, List[_UdmModuleFactoryConfigurationWithDate]]
		"""
		# TODO: file locking
		try:
			with open(self._persistence_path) as fp:
				config = json.load(fp)  # type: Dict[str, List[Dict[str, Any]]]
		except IOError as exc:
			ud.error('Could not open UDM module factory configuration: {}'.format(exc))
			raise
		self._config = {}
		for regex, configs in config.iteritems():
			self._config[re.compile(regex)] = [_UdmModuleFactoryConfigurationWithDate(**c) for c in configs]
		return self._config

	def _save_configuration(self):  # type: () -> None
		"""
		Saves non-default configurations to disk.

		:return: None
		:raises IOError: if the configuration could not be written to disk
		"""
		# TODO: file locking
		config_as_dict = {}
		try:
			for regex, configs in self._config.iteritems():
				config_as_dict[regex.pattern] = [dict(**config.__dict__) for config in configs]
			with open(self._persistence_path, 'wb') as fp:
				json.dump(config_as_dict, fp)
			ud.info('Saved UDM module factory configuration.')
		except IOError as exc:
			ud.error('Could not write UDM module factory configuration: {}'.format(exc))
			raise

	@staticmethod
	def _add_regex_bounds(regex):  # type: (str) -> Text
		"""
		Make pattern safe for exact match by prepending `^` and appending `$`.

		:param str regex: regular expression string
		:return: regular expression string
		:rtype: str
		"""
		if not regex.startswith('^'):
			regex = r'^{}'.format(regex)
			ud.debug("Prepended '^' to pattern: {!r}".format(regex))
		if not regex.endswith('$'):
			regex = r'{}$'.format(regex)
			ud.debug("Appended '$' to pattern: {!r}".format(regex))
		return unicode(regex)

	@staticmethod
	def _config_with_date_2_config_without_date(config_with_date):
			# type: (_UdmModuleFactoryConfigurationWithDate) -> UdmModuleFactoryConfiguration
			kwargs = config_with_date.__dict__
			del kwargs['addition_date']
			return UdmModuleFactoryConfiguration(**kwargs)

	@classmethod
	def _config_without_date_2_config_with_date(cls, config_without_date):
		# type: (UdmModuleFactoryConfiguration) -> _UdmModuleFactoryConfigurationWithDate
		kwargs = config_without_date.__dict__
		kwargs['udm_module_name_pattern'] = cls._add_regex_bounds(config_without_date.udm_module_name_pattern)
		kwargs['addition_date'] = time.time()
		return _UdmModuleFactoryConfigurationWithDate(**kwargs)


if __name__ == '__main__':
	import doctest
	doctest.testmod()
