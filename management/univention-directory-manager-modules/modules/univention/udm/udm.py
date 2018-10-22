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
user_mod = Udm.using_credentials('myuser', 's3cr3t').get('users/user')

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

	Udm.using_admin().obj_by_dn(dn)

It is recommended to hard code the used API version in your code. Supply it as
argument when creating a Udm object::

	Udm.using_admin().version(1)  # use API version 1
	Udm(lo).version(0).get('users/user')  # get users/user module for API version 0
	Udm(lo, 0).get('users/user')  # get users/user module for API version 0
	Udm.using_credentials('myuser', 'secret').version(2).obj_by_dn(dn)  # get object using API version 2
"""

from __future__ import absolute_import, unicode_literals
import sys
import os.path
import importlib
from operator import itemgetter
from fnmatch import fnmatch
from glob import glob

from .exceptions import ApiVersionNotSupported, NoObject, UnknownUdmModuleType
from .utils import UDebug as ud, ConnectionConfig, get_connection


__default_api_version__ = 1


class Udm(object):
	"""
	Dynamic factory for creating UdmModule objects.

	group_mod = Udm.using_admin().get('groups/group')
	folder_mod = Udm.using_machine().get('mail/folder')
	user_mod = Udm.using_credentials('myuser', 's3cr3t').get('users/user')

	A shortcut exists to get UDM objects directly::

		Udm.using_admin().obj_by_dn(dn)
	"""
	_module_class_cache = {}
	_module_object_cache = {}
	_imported = False
	_modules = []

	def __init__(self, connection_config, api_version=None):
		"""
		Use the provided connection.

		:param univention.admin.uldap.access lo: LDAP connection object
		:param int api_version: load only UDM modules that support the
			specified version, can be set later using :py:meth:`version()`.
		:return: None
		:rtype: None
		"""
		self.connection = get_connection(connection_config)
		self._api_version = None
		if api_version is not None:
			self.version(api_version)

	@classmethod
	def using_admin(cls):
		"""
		Use a cn=admin connection.

		:return: a Udm object
		:rtype: Udm
		:raises ConnectionError: Non-Master systems, server down, etc.
		"""
		return cls(ConnectionConfig(
			'univention.udm.connections.LDAP_connection',
			'get_admin_connection',	(),	{})
		)

	@classmethod
	def using_machine(cls):
		"""
		Use a machine connection.

		:return: a Udm object
		:rtype: Udm
		:raises ConnectionError: File permissions, server down, etc.
		"""
		return cls(ConnectionConfig(
			'univention.udm.connections.LDAP_connection',
			'get_machine_connection', (), {})
		)

	@classmethod
	def using_credentials(
			cls,
			identity,
			password,
			base=None,
			server=None,
			port=None,
	):
		"""
		Use the provided credentials to open an LDAP connection.

		`identity` must be either a username or a DN. If it is a username, a
		machine connection is used to retrieve the DN it belongs to.

		:param str identity: username or user dn to use for LDAP connection
		:param str password: password of user / DN to use for LDAP connection
		:param str base: optional search base
		:param str server: optional LDAP server address as FQDN
		:param int port: optional LDAP server port
		:return: a Udm object
		:rtype: Udm
		:raises ConnectionError: Invalid credentials, server down, etc.
		"""
		return cls(ConnectionConfig(
			'univention.udm.connections.LDAP_connection',
			'get_credentials_connection', (identity, password),	{'base': base, 'server': server, 'port': port})
		)

	def version(self, api_version):
		"""
		Set the version of the API that the UDM modules must support.

		Use in a chain of methods to get a UDM module::

			Udm.get_admin().version(1).get('groups/group')

		:param int api_version: load only UDM modules that support the
		specified version
		:return: self
		:rtype Udm
		"""
		assert isinstance(api_version, int), "Argument 'api_version' must be an int."
		self._api_version = api_version
		return self

	@classmethod
	def _import(cls):
		if cls._imported:
			return
		path = os.path.dirname(__file__)
		for pymodule in glob(os.path.join(path, 'modules', '*.py')):
			pymodule_name = os.path.basename(pymodule)[:-3]  # without .py
			importlib.import_module('univention.udm.modules.{}'.format(pymodule_name))
		cls._imported = True

	def get(self, name):
		"""
		Get an object of :py:class:`BaseUdmModule` (or of a subclass) for UDM
		module `name`.

		:param str name: UDM module name (e.g. `users/user`)
		:return: object of a subclass of :py:class:`BaseUdmModule`
		:rtype: BaseUdmModule
		:raises ApiVersionNotSupported: if the Python module for `name` could not be loaded
		"""
		self._import()
		possible = []
		for module in self._modules:
			if self.api_version not in module.meta.supported_api_versions:
				continue
			for suitable in module.meta.suitable_for:
				if fnmatch(name, suitable):
					possible.append((suitable.count('*'), module))
					break
		possible.sort(key=itemgetter(0))
		try:
			klass = possible[0][1]
		except IndexError:
			raise ApiVersionNotSupported(module_name=name, requested_version=self.api_version)
		else:
			return klass(self, name)

	def obj_by_dn(self, dn):
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
		if self.connection.__module__ != 'univention.admin.uldap':
			raise NotImplementedError('obj_by_dn() can only be used with an LDAP connection.')
		ldap_obj = self.connection.get(dn, attr=[str('univentionObjectType')])
		if not ldap_obj:
			raise NoObject(dn=dn)
		try:
			uot = ldap_obj['univentionObjectType'][0]
			if not uot:
				raise KeyError  # empty
		except (KeyError, IndexError):
			raise UnknownUdmModuleType, UnknownUdmModuleType(dn=dn), sys.exc_info()[2]
		udm_module = self.get(uot)
		return udm_module.get(dn)

	@property
	def api_version(self):
		if self._api_version is None:
			ud.warn('Using default API version ({}). It is recommended to set one explicitly.'.format(
				__default_api_version__))
			self._api_version = __default_api_version__
		return self._api_version
