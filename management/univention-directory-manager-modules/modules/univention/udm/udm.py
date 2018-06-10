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
Univention Directory Manager Modules (UDM) API

This is a simplified API for accessing UDM objects.
It consists of UDM modules and UDM object.
UDM modules are factories for UDM objects.
UDM objects manipulate LDAP objects.

Usage:

from univention.udm import Udm

user_mod = Udm.using_admin().get('users/user')
or
user_mod = Udm.using_machine().get('users/user')
or
user_mod = Udm.using_credentials('s3cr3t', 'uid=myuser,cn=users,...').get('users/user')

obj = user_mod.get(dn)
obj.props.firstname = 'foo'  # modify property
obj.position = 'cn=users,cn=example,dc=com'  # move LDAP object
obj.save()  # apply changes

obj = user_mod.get(dn)
obj.delete()

obj = user_mod.new()
obj.props.username = 'bar'
obj.save().refresh()  # reload obj.props from LDAP after save()

for obj in user_mod.search('uid=a*'):  # search() returns a generator
	print(obj.props.firstname, obj.props.lastname)
"""

from __future__ import absolute_import
import importlib
from .base import BaseUdmModule
from .factory_config import UdmModuleFactoryConfigurationStorage
from .utils import LDAP_connection

try:
	from typing import Dict, Optional, Tuple
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
		"""
		Use a cn=admin connection.

		:return: a Udm object
		:rtype: Udm
		"""
		return cls(cls._connection_handler.get_admin_connection())

	@classmethod
	def using_machine(cls):  # type: () -> Udm
		"""
		Use a machine connection.

		:return: a Udm object
		:rtype: Udm
		"""
		return cls(cls._connection_handler.get_machine_connection())

	@classmethod
	def using_credentials(
			cls,
			password,  # type: str
			username=None,  # type: Optional[str]
			dn=None,  # type: Optional[str]
			base=None,  # type: Optional[str]
			server=None,  # type: Optional[str]
			port=None  # type: Optional[int]
	):
		# type: (...) -> Udm
		"""
		Use the provided credentials to open an LDAP connection.

		Either `username` or `dn` are required. If `username`, a machine
		connection is used to retrieve the DN it belongs to.

		:param str password: password of user / DN to use for LDAP connection
		:param str username: username to use for LDAP connection
		:param str dn: DN to use for LDAP connection
		:param str base: optional search base
		:param str server: optional LDAP server address as FQDN
		:param int port: optional LDAP server port
		:return: a Udm object
		:rtype: Udm
		"""
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
