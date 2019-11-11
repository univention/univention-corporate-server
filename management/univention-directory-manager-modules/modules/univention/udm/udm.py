# -*- coding: utf-8 -*-
#
# Copyright 2018-2019 Univention GmbH
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

"""
Univention Directory Manager Modules (UDM) API

This is a simplified API for accessing UDM objects.
It consists of UDM modules and UDM object.
UDM modules are factories for UDM objects.
UDM objects manipulate LDAP objects.

Usage::

	from univention.udm import UDM

	user_mod = UDM.admin().get('users/user')

or::

	user_mod = UDM.machine().get('users/user')

or::

	user_mod = UDM.credentials('myuser', 's3cr3t').get('users/user')

	obj = user_mod.get(dn)
	obj.props.firstname = 'foo'  # modify property
	obj.position = 'cn=users,cn=example,dc=com'  # move LDAP object
	obj.save()  # apply changes

	obj = user_mod.get(dn)
	obj.delete()

	obj = user_mod.new()
	obj.props.username = 'bar'
	obj.save().refresh()  # reload obj.props from LDAP after save()

	for obj in UDM.machine().get('users/user').search('uid=a*'):  # search() returns a generator
		print(obj.props.firstname, obj.props.lastname)

A shortcut exists to get a UDM object directly::

	UDM.admin().obj_by_dn(dn)

The API is versioned. A fixed version must be hard coded in your code. Supply
it as argument to the UDM module factory or via :py:meth:`version()`::

	UDM.admin().version(1)  # use API version 1
	UDM.credentials('myuser', 'secret').version(2).obj_by_dn(dn)  # get object using API version 2
"""

from __future__ import absolute_import, unicode_literals
from operator import itemgetter
from fnmatch import fnmatch

from .exceptions import ApiVersionMustNotChange, ApiVersionNotSupported, NoApiVersionSet, NoObject
from .plugins import Plugins


_MODULES_PATH = 'univention.udm.modules'


class UDM(object):
	"""
	Dynamic factory for creating :py:class:`BaseModule` objects::

		group_mod = UDM.admin().get('groups/group')
		folder_mod = UDM.machine().get('mail/folder')
		user_mod = UDM.credentials('myuser', 's3cr3t').get('users/user')

	A shortcut exists to get UDM objects directly::

		UDM.admin().obj_by_dn(dn)
	"""
	_module_object_cache = {}

	def __init__(self, connection, api_version=None):
		"""
		Use the provided connection.

		:param connection: Any connection object (e.g., univention.admin.uldap.access)
		:param int api_version: load only UDM modules that support the
			specified version, can be set later using :py:meth:`version()`.
		:return: None
		:rtype: None
		"""
		self.connection = connection
		self._api_version = None
		if api_version is not None:
			self.version(api_version)

	@classmethod
	def admin(cls):
		"""
		Use a cn=admin connection.

		:return: a :py:class:`univention.udm.udm.UDM` instance
		:rtype: univention.udm.udm.UDM
		:raises univention.udm.exceptions.ConnectionError: Non-master systems, server down, etc.
		"""
		from .connections import LDAP_connection
		connection = LDAP_connection.get_admin_connection()
		return cls(connection)

	@classmethod
	def machine(cls):
		"""
		Use a machine connection.

		:return: a :py:class:`univention.udm.udm.UDM` instance
		:rtype: univention.udm.udm.UDM
		:raises univention.udm.exceptions.ConnectionError: File permissions, server down, etc.
		"""
		from .connections import LDAP_connection
		connection = LDAP_connection.get_machine_connection()
		return cls(connection)

	@classmethod
	def credentials(
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
		:return: a :py:class:`univention.udm.udm.UDM` instance
		:rtype: univention.udm.udm.UDM
		:raises univention.udm.exceptions.ConnectionError: Invalid credentials, server down, etc.
		"""
		from .connections import LDAP_connection
		connection = LDAP_connection.get_credentials_connection(identity, password, base, server, port)
		return cls(connection)

	def version(self, api_version):
		"""
		Set the version of the API that the UDM modules must support.

		Use in a chain of methods to get a UDM module::

			UDM.get_admin().version(1).get('groups/group')

		:param int api_version: load only UDM modules that support the
			specified version
		:return: self (the :py:class:`univention.udm.udm.UDM` instance)
		:rtype: univention.udm.udm.UDM
		:raises univention.udm.exceptions.ApiVersionMustNotChange: if called twice
		"""
		if not isinstance(api_version, int):
			raise ApiVersionNotSupported("Argument 'api_version' must be an int.", requested_version=api_version)
		if self._api_version is None:
			self._api_version = api_version
		else:
			raise ApiVersionMustNotChange()
		return self

	def get(self, name):
		"""
		Get an object of :py:class:`BaseModule` (or of a subclass) for UDM
		module `name`.

		:param str name: UDM module name (e.g. `users/user`)
		:return: object of a subclass of :py:class:`BaseModule`
		:rtype: BaseModule
		:raises univention.udm.exceptions.ApiVersionNotSupported: if the Python module for `name` could not be loaded
		:raises univention.udm.exceptions.NoApiVersionSet: if the API version has not been set
		"""
		key = (name, self._api_version, id(self.connection))
		if key not in self._module_object_cache:
			suitable_modules = []
			plugins = Plugins(_MODULES_PATH)
			for module in plugins:
				if self.api_version not in module.meta.supported_api_versions:
					continue
				for suitable in module.meta.suitable_for:
					if fnmatch(name, suitable):
						suitable_modules.append((suitable.count('*'), module))
						break
			suitable_modules.sort(key=itemgetter(0))
			try:
				klass = suitable_modules[0][1]
			except IndexError:
				raise ApiVersionNotSupported(module_name=name, requested_version=self.api_version)
			else:
				self._module_object_cache[key] = klass(name, self.connection, self.api_version)
		return self._module_object_cache[key]

	def obj_by_dn(self, dn):
		"""
		Try to load an UDM object from LDAP. Guess the required UDM module
		from the ``univentionObjectType`` LDAP attribute of the LDAP object.

		:param str dn: DN of the object to load
		:return: object of a subclass of :py:class:`BaseObject`
		:rtype: BaseObject
		:raises univention.udm.exceptions.NoApiVersionSet: if the API version has not been set
		:raises univention.udm.exceptions.NoObject: if no object is found at `dn`
		:raises univention.udm.exceptions.ImportError: if the Python module for ``univentionObjectType``
			at ``dn`` could not be loaded
		:raises univention.udm.exceptions.UnknownModuleType: if the LDAP object at ``dn`` had no or
			empty attribute ``univentionObjectType``
		"""
		if self.connection.__module__ != 'univention.admin.uldap':
			raise NotImplementedError('obj_by_dn() can only be used with an LDAP connection.')
		ldap_obj = self.connection.get(dn, attr=[str('univentionObjectType')])
		if not ldap_obj:
			raise NoObject(dn=dn)
		uot = ldap_obj['univentionObjectType'][0]
		udm_module = self.get(uot)
		return udm_module.get(dn)

	@property
	def api_version(self):
		if self._api_version is None:
			raise NoApiVersionSet()
		return self._api_version
