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
Dynamic factory code.
"""

import json
import os.path
from collections import namedtuple

try:
	from typing import Dict
except ImportError:
	pass


_UDM_MODULE_FACTORY_CONFIGURATION_PATH = os.path.join(os.path.dirname(__file__), 'udm_module_factory.json')


UdmModuleFactoryConfiguration = namedtuple(
	'UdmModuleFactoryConfiguration',
	('udm_module_name', 'module_path', 'class_name')
)  # e.g. UdmModuleFactoryConfiguration('users/user', 'univention.admin.simple_udm', 'GenericUdmModule')


class UdmModuleFactoryConfigurationStorage(object):
	"""Handle loading and storing of the dynamic factory metadata."""
	_config = None  # type: Dict[str, UdmModuleFactoryConfiguration]
	_default_factory = {'module_path': 'univention.udm.generic', 'class_name': 'GenericUdmModule'}

	@classmethod
	def get_configuration(cls, module_name):  # type: (str) -> UdmModuleFactoryConfiguration
		"""
		Get configuration for a module.

		:param str module_name: the UDM modules name for which to get the factory configuration
		:return: the factory configuration
		:rtype: UdmModuleFactoryConfiguration
		"""
		if cls._config is None:
			cls._load_configuration()
		if module_name not in cls._config:
			cls._config[module_name] = UdmModuleFactoryConfiguration(
				udm_module_name=module_name, **cls._default_factory
			)
			# TODO: log
			print(
				'Debug: no specific factory for {!r} found, using {!r}.'.format(
					module_name, cls._config[module_name])
			)
		return cls._config[module_name]

	@classmethod
	def set_configuration(cls, factory_configuration):  # type: (UdmModuleFactoryConfiguration) -> None
		"""
		Store configuration for a module.

		:param UdmModuleFactoryConfiguration factory_configuration: the class configuration to save
		:return: None
		:raises IOError: if the configuration could not be written to disk
		"""
		# TODO: add permanent-or-transient option
		if cls._config is None:
			cls._load_configuration()
		cls._config[factory_configuration.udm_module_name] = factory_configuration
		cls._save_configuration()

	@classmethod
	def _load_configuration(cls):  # type: () -> Dict[str, UdmModuleFactoryConfiguration]
		"""
		Load configuration from disk.

		:return: mapping module_name -> configuration
		:rtype: Dict(str, UdmModuleFactoryConfiguration)
		"""
		try:
			with open(_UDM_MODULE_FACTORY_CONFIGURATION_PATH) as fp:
				config = json.load(fp)
		except IOError as exc:
			# TODO: log
			print('Warn: Could not open UDM module factory configuration: {}'.format(exc))
			# TODO: should we raise an exception?
			config = {}
		cls._config = {}
		for k, v in config.iteritems():
			cls._config[k] = UdmModuleFactoryConfiguration(**v)
		return cls._config

	@classmethod
	def _save_configuration(cls):  # type: () -> None
		"""
		Saves non-default configurations to disk.

		:return: None
		:raises IOError: if the configuration could not be written to disk
		"""
		config = {}
		try:
			for k, v in cls._config.iteritems():
				if v.module_path == cls._default_factory['module_path'] and v.class_name == cls._default_factory['class_name']:
					# don't save default configurations
					continue
				config[k] = dict(**v.__dict__)
			with open(_UDM_MODULE_FACTORY_CONFIGURATION_PATH, 'wb') as fp:
				json.dump(config, fp)
		except IOError as exc:
			# TODO: log
			print('Error: Could not write UDM module factory configuration: {}'.format(exc))
			raise
