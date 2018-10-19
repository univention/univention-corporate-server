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
Base classes for (simplified) UDM modules and objects.
"""

from __future__ import absolute_import, unicode_literals
import copy
import pprint
from collections import namedtuple
from ldap.filter import filter_format
from .exceptions import NoObject, MultipleObjects
from .utils import get_connection


UdmLdapMapping = namedtuple('UdmLdapMapping', ('ldap2udm', 'udm2ldap'))


class BaseUdmObjectProperties(object):
	"""Container for UDM properties."""
	def __init__(self, udm_obj):
		self._udm_obj = udm_obj

	def __repr__(self):
		return pprint.pformat(dict((k, v) for k, v in self.__dict__.iteritems() if not str(k).startswith('_')), indent=2)

	def __deepcopy__(self, memo):
		id_self = id(self)
		if not memo.get(id_self):
			memo[id_self] = {}
			for k, v in self.__dict__.items():
				if k == '_udm_obj':
					continue
				memo[id_self][k] = copy.deepcopy(v)
		return memo[id_self]


class BaseUdmObject(object):
	"""
	Base class for UdmObject classes.

	Usage:
	* Creation of instances :py:class:`BaseUdmObject` is always done through a
	:py:class:`BaseUdmModul` instances py:meth:`new()`, py:meth:`get()` or
	py:meth:`search()` methods.
	* Modify an object:
		user.props.firstname = 'Peter'
		user.props.lastname = 'Pan'
		user.save()
	* Move an object:
		user.position = 'cn=users,ou=Company,dc=example,dc=com'
		user.save()
	* Delete an object:
		obj.delete()

	After saving a :py:class:`BaseUdmObject`, it is :py:meth:`reload()`ed
	automtically because UDM hooks and listener modules often add, modify or
	remove properties when saving to LDAP. As this involves LDAP, it can be
	disabled if the object is not used afterwards and performance is an issue:
		user_mod.meta.auto_reload = False
	"""
	udm_prop_class = BaseUdmObjectProperties

	def __init__(self):
		"""
		Don't instantiate a :py:class:`UdmObject` directly. Use a
		:py:class:`BaseUdmModule`.
		"""
		self.dn = ''
		self.props = None
		self.options = []
		self.policies = []
		self.position = ''
		self._udm_module = None

	def __repr__(self):
		return '{}({!r}, {!r})'.format(
			self.__class__.__name__,
			self._udm_module.name if self._udm_module else '<not initialized>',
			self.dn
		)

	def reload(self):
		"""
		Refresh object from LDAP.

		:return: self
		:rtype: UdmObject
		"""
		raise NotImplementedError()

	def save(self):
		"""
		Save object to LDAP.

		:return: self
		:rtype: UdmObject
		:raises MoveError: when a move operation fails
		"""
		raise NotImplementedError()

	def delete(self):
		"""
		Remove the object from the LDAP database.

		:return: None
		"""
		raise NotImplementedError()


class BaseUdmModuleMetadata(object):
	"""Base class for UDM module meta data."""

	auto_open = True  # whether UDM objects should be `open()`ed
	auto_reload = True  # whether UDM objects should be `reload()`ed after saving

	def __init__(self, udm_module, api_version):
		self._udm_module = udm_module
		self.api_version = api_version

	@property
	def identifying_property(self):
		"""
		UDM Property of which the mapped LDAP attribute is used as first
		component in a DN, e.g. `username` (LDAP attribute `uid`) or `name`
		(LDAP attribute `cn`).
		"""
		raise NotImplementedError()

	def lookup_filter(self, filter_s=None):
		"""
		Filter the UDM module uses to find its corresponding LDAP objects.

		This can be used in two ways:

		* get the filter to find all objects:
			`myfilter_s = obj.meta.lookup_filter()`
		* get the filter to find a subset of the corresponding LDAP objects (`filter_s` will be combined with `&` to the filter for all objects):
			`myfilter = obj.meta.lookup_filter('(|(givenName=A*)(givenName=B*))')`

		:param str filter_s: optional LDAP filter expression
		:return: an LDAP filter string
		:rtype: str
		"""
		raise NotImplementedError()

	@property
	def mapping(self):
		"""
		UDM properties to LDAP attributes mapping and vice versa.

		:return: a namedtuple containing two mappings: a) from UDM property to LDAP attribute and b) from LDAP attribute to UDM property
		:rtype: UdmLdapMapping
		"""
		raise NotImplementedError()


class BaseUdmModule(object):
	"""
	Base class for UdmModule classes. UdmModules are basically UdmObject
	factories.

	Usage:
	0. Get module using
		user_mod = Udm.using_*().get('users/user')
	1 Create fresh, not yet saved BaseUdmObject:
		new_user = user_mod.new()
	2 Load an existing object:
		group = group_mod.get('cn=test,cn=groups,dc=example,dc=com')
		group = group_mod.get_by_id('Domain Users')
	3 Search and load existing objects:
		dc_slaves = dc_slave_mod.search(filter_s='cn=s10*')
		campus_groups = group_mod.search(base='ou=campus,dc=example,dc=com')
	4. Load existing object(s) without `open()`ing them;
		user_mod.meta.auto_open = False
		user = user_mod.get(dn)
		user.props.groups == []
	"""
	supported_api_versions = ()  # type: Iterable[int]
	_udm_object_class = BaseUdmObject
	_udm_module_meta_class = BaseUdmModuleMetadata

	def __init__(self, name, connection_config, api_version):
		self.name = name
		self._connection_config = connection_config
		self.connection = get_connection(connection_config)
		self.meta = self._udm_module_meta_class(self, api_version)

	def __repr__(self):
		return '{}({!r})'.format(self.__class__.__name__, self.name)

	def new(self):
		"""
		Create a new, unsaved BaseUdmObject object.

		:return: a new, unsaved BaseUdmObject object
		:rtype: BaseUdmObject
		"""
		raise NotImplementedError()

	def get(self, dn):
		"""
		Load UDM object from LDAP.

		:param str dn: DN of the object to load
		:return: an existing BaseUdmObject object
		:rtype: BaseUdmObject
		:raises NoObject: if no object is found at `dn`
		:raises WrongObjectType: if the object found at `dn` is not of type :py:attr:`self.name`
		"""
		raise NotImplementedError()

	def get_by_id(self, id):
		"""
		Load UDM object from LDAP by searching for its ID.

		This is a convenience function around :py:meth:`search()`.

		:param str id: ID of the object to load (e.g. username (uid) for users/user,
			name (cn) for groups/group etc.)
		:return: an existing BaseUdmObject object
		:rtype: BaseUdmObject
		:raises NoObject: if no object is found with ID `id`
		:raises MultipleObjects: if more than one object is found with ID `id`
		"""
		filter_s = filter_format('{}=%s'.format(self.meta.identifying_property), (id,))
		res = list(self.search(filter_s))
		if not res:
			raise NoObject('No object found for {!r}.'.format(filter_s), module_name=self.name)
		elif len(res) > 1:
			raise MultipleObjects(
				'Searching in module {!r} with identifying_property {!r} (filter: {!r}) returned {} objects.'.format(
					self.name, self.meta.identifying_property, filter_s, len(res)), module_name=self.name)
		return res[0]

	def search(self, filter_s='', base='', scope='sub'):
		"""
		Get all UDM objects from LDAP that match the given filter.

		:param str filter_s: LDAP filter (only object selector like uid=foo
			required, objectClasses will be set by the UDM module)
		:param str base:
		:param str scope:
		:return: iterator of BaseUdmObject objects
		:rtype: Iterator(BaseUdmObject)
		"""
		raise NotImplementedError()
