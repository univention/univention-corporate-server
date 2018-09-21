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

user_mod = Udm(lo).get('users/user')
or
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

for obj in Udm.using_machine().get('users/user').search('uid=a*'):  # search() returns a generator
	print(obj.props.firstname, obj.props.lastname)

A shortcut exists to get a UDM object directly::

	Udm.using_admin().get_obj(dn)

It is recommended to hard code the used API version in your code. Supply it as
argument when creating a Udm object::

	Udm.using_admin(1)  # use API version 1
	Udm(lo, 0).get('users/user')  # get users/user module for API version 0
	Udm.using_credentials('s3cr3t', 'uid=myuser,..', 2).get_obj(dn)  # get object using API version 2
"""

from __future__ import absolute_import, unicode_literals
from .base import BaseUdmModule
from .exceptions import ApiVersionNotSupported, NoObject, UnknownUdmModuleType
from .factory_config import UdmModuleFactoryConfiguration, UdmModuleFactoryConfigurationStorage
from .utils import load_class, LDAP_connection, UDebug as ud

try:
	from typing import Dict, Optional, Tuple, Type
	from .base import BaseUdmObject
except ImportError:
	pass


__default_api_version__ = 1


class Udm(object):
	"""
	Dynamic factory for creating UdmModule objects.

	group_mod = Udm.using_admin().get('groups/group')
	folder_mod = Udm.using_machine().get('mail/folder')
	user_mod = Udm.using_credentials('myuser', 's3cr3t').get('users/user')

	A shortcut exists to get UDM objects directly::

		Udm.using_admin().get_obj(dn)
	"""
	_module_class_cache = {}  # type: Dict[Tuple[str, str], Type[BaseUdmModule]]
	_module_object_cache = {}  # type: Dict[Tuple[str, str, str, str, str], BaseUdmModule]
	_connection_handler = LDAP_connection

	def __init__(self, lo, api_version=__default_api_version__):
		# type: (univention.admin.uldap.access, Optional[int]) -> None
		"""
		Use the provided connection.

		:param univention.admin.uldap.access lo: LDAP connection object
		:param int api_version: load only UDM modules that support the
			specified version
		:return: None
		:rtype: None
		"""
		self.lo = lo
		self._api_version = api_version
		self._configuration_storage = UdmModuleFactoryConfigurationStorage()

	@classmethod
	def using_admin(cls, api_version=__default_api_version__):  # type: (Optional[int]) -> Udm
		"""
		Use a cn=admin connection.

		:param int api_version: load only UDM modules that support the
			specified version
		:return: a Udm object
		:rtype: Udm
		"""
		return cls(cls._connection_handler.get_admin_connection(), api_version)

	@classmethod
	def using_machine(cls, api_version=__default_api_version__):  # type: (Optional[int]) -> Udm
		"""
		Use a machine connection.

		:param int api_version: load only UDM modules that support the
			specified version
		:return: a Udm object
		:rtype: Udm
		"""
		return cls(cls._connection_handler.get_machine_connection(), api_version)

	@classmethod
	def using_credentials(
			cls,
			password,  # type: str
			username=None,  # type: Optional[str]
			dn=None,  # type: Optional[str]
			base=None,  # type: Optional[str]
			server=None,  # type: Optional[str]
			port=None,  # type: Optional[int]
			api_version=__default_api_version__,  # type: Optional[int]
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
		:param int api_version: load only UDM modules that support the
			specified version
		:return: a Udm object
		:rtype: Udm
		"""
		return cls(cls._connection_handler.get_credentials_connection(password, username, dn, base, server, port, api_version))

	def get(self, name):  # type: (str) -> BaseUdmModule
		"""
		Get an object of :py:class:`BaseUdmModule` (or of a subclass) for UDM
		module `name`.

		:param str name: UDM module name (e.g. `users/user`)
		:return: object of a subclass of :py:class:`BaseUdmModule`
		:rtype: BaseUdmModule
		:raises ImportError: if the Python module for `name` could not be loaded
		"""
		factory_config = self._configuration_storage.get_configuration(name, self._api_version)
		return self.get_by_factory_config(name, factory_config)

	def get_obj(self, dn):  # type: (str) -> BaseUdmObject
		"""
		Try to load an UDM object from LDAP. Guess the required UDM module
		from the ``univentionObjectType`` LDAP attribute of the LDAP object.

		:param str dn: DN of the object to load
		:return: object of a subclass of :py:class:`BaseUdmObject`
		:rtype: BaseUdmObject
		:raises NoObject: if no object is found at `dn`
		:raises ImportError: if the Python module for ``univentionObjectType``
			at ``dn`` could not be loaded
		:raises UnknownUdmModuleType: if the LDAP object at ``dn`` had no or
			empty attribute ``univentionObjectType``
		"""
		ldap_obj = self.lo.get(dn, attr=[str('univentionObjectType')])
		if not ldap_obj:
			raise NoObject(dn=dn)
		try:
			uot = ldap_obj['univentionObjectType'][0]
			if not uot:
				raise KeyError  # empty
		except (KeyError, IndexError):
			raise UnknownUdmModuleType(dn=dn)
		udm_module = self.get(uot)
		return udm_module.get(dn)

	def get_by_factory_config(self, name, factory_config):  # type: (str, UdmModuleFactoryConfiguration) -> BaseUdmModule
		"""
		Get an object of :py:class:`BaseUdmModule` (or of a subclass) for UDM
		factory configuration `factory_configuration`.

		:param str name: UDM module name (e.g. `users/user`)
		:param UdmModuleFactoryConfiguration factory_config: UDM module factory configuration
		:return: object of a subclass of :py:class:`BaseUdmModule`
		:rtype: BaseUdmModule
		:raises ImportError: if the Python module for `name` could not be loaded
		"""
		assert isinstance(factory_config, UdmModuleFactoryConfiguration)
		# key is (connection + class)
		key = (
			self.lo.base, self.lo.binddn, self.lo.host,
			name, factory_config.module_path, factory_config.class_name
		)
		if key not in self._module_object_cache:
			ud.debug('Trying to load UDM module {!r} for configuration {!r}...'.format(name, factory_config))
			module_cls = self._load_module(factory_config)
			if self._api_version not in module_cls.supported_api_versions:
				raise ApiVersionNotSupported(
					module_name=name,
					module_cls=module_cls,
					requested_version=self._api_version,
					supported_versions=module_cls.supported_api_versions,
				)
			self._module_object_cache[key] = module_cls(name, self.lo, self._api_version)
		return self._module_object_cache[key]

	def _load_module(self, factory_config):  # type: (UdmModuleFactoryConfiguration) -> Type[BaseUdmModule]
		key = (factory_config.module_path, factory_config.class_name)
		if key not in self._module_class_cache:
			candidate_cls = load_class(factory_config.module_path, factory_config.class_name)
			if not issubclass(candidate_cls, BaseUdmModule):
				raise ValueError('{!r} is not a subclass of BaseUdmModule.'.format(candidate_cls))
			ud.debug('Loaded {!r}.'.format(candidate_cls))
			self._module_class_cache[key] = candidate_cls
		return self._module_class_cache[key]
