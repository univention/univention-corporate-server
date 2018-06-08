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
# TODO: update module doc -> same as in __init__.py

import univention.admin.uldap
lo, po = univention.admin.uldap.getAdminConnection()

from univention.admin.simple_udm import UdmModuleFactory
user_mod = UdmModuleFactory._get_simple_udm_module('users/user', lo)
all_users = user_mod.search()
myuser = user_mod.get('uid=myuser,cn=users,dc=example,dc=com')
"""

from __future__ import absolute_import
import importlib
from .base import BaseUdmModule
from .factory_config import UdmModuleFactoryConfigurationStorage
from .utils import LDAP_connection

try:
	from typing import Dict, Optional, Tuple
	from six import string_types
except ImportError:
	pass

#
# TODO: ucs-test
# TODO: log to univention.debug.ADMIN
#


class Udm(object):
	"""
	Dynamic factory for creating UdmModule objects.

	group_mod = Udm.using_admin().get('groups/group')
	folder_mod = Udm.using_machine().get('mail/folder')
	user_mod = Udm.using_credentials('myuser', 's3cr3t').get('users/user')
	"""
	_module_cache = {}  # type: Dict[Tuple[str, str, str, str], BaseUdmModule]
	_connection_handler = LDAP_connection

	def __init__(self, lo):  # type: (univention.admin.uldap.access) -> None
		self.lo = lo
		self._configuration_storage = UdmModuleFactoryConfigurationStorage()

	@classmethod
	def using_admin(cls):  # type: () -> Udm
		return cls(cls._connection_handler.get_admin_connection())

	@classmethod
	def using_machine(cls):  # type: () -> Udm
		return cls(cls._connection_handler.get_machine_connection())

	@classmethod
	def using_credentials(cls, username, password, dn=None, base=None, server=None, port=None):
		# type: (string_types, string_types, Optional[string_types], Optional[string_types], Optional[string_types], Optional[int]) -> Udm
		return cls(cls._connection_handler.get_credentials_connection(username, password, dn, base, server, port))

	def get(self, name):  # type: (str) -> BaseUdmModule
		"""
		Load a (subclass of) :py:class:`BaseUdmModule`.

		:param str name: UDM module name (e.g. 'users/user')
		:return: subclass of :py:class:`BaseUdmModule`
		:rtype: BaseUdmModule
		:raises ImportError: if the Python module for `name` could not be self.loaded
		"""
		key = (self.lo.base, self.lo.binddn, self.lo.host, name)
		if key not in self._module_cache:
			factory_config = self._configuration_storage.get_configuration(name)
			# TODO: log
			print('Debug: trying to self.load module {!r}...'.format(factory_config.module_path))
			module = importlib.import_module(factory_config.module_path)
			print('Debug: trying to self.load class {!r} from module {!r}...'.format(
				factory_config.class_name, module.__name__))
			simple_udm_module_cls = getattr(module, factory_config.class_name)
			assert issubclass(simple_udm_module_cls, BaseUdmModule), '{!r} is not a subclass of BaseUdmModule.'.format(
				simple_udm_module_cls)
			print('Debug: loaded {!r}.'.format(simple_udm_module_cls))
			self._module_cache[key] = simple_udm_module_cls(name, self.lo)
		return self._module_cache[key]
