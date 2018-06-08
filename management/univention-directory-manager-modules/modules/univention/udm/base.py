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
Base classes for simple UDM modules and objects.
"""

import pprint
from collections import namedtuple

try:
	from typing import Iterator, List
	import univention.admin.uldap
except ImportError:
	pass


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

	Please be aware that UDM hooks and listener modules often add, modify or
	remove properties when saving to LDAP. When continuing to use a
	:py:class:`BaseUdmObject` after :py:meth:`save()`, it is *strongly*
	recommended to :py:meth:`reload()` it: `obj.save().reload()`
	"""
	def __init__(self):  # type: () -> None
		"""
		Don't instantiate a :py:class:`UdmObject` directly. Use a
		:py:class:`BaseUdmModule`.
		"""
		self.dn = ''
		self.props = None  # type: BaseUdmObjectProperties
		self.options = []  # type: List[str]
		self.policies = []  # type: List[str]
		self.position = ''
		self._simple_udm_module = None  # type: BaseUdmModule

	def __repr__(self):  # type: () -> str
		return '{}({!r}, {!r})'.format(
			self.__class__.__name__,
			self._simple_udm_module.name if self._simple_udm_module else '<not initialized>',
			self.dn
		)

	def reload(self):  # type: () -> BaseUdmObject
		"""
		Refresh object from LDAP.

		:return: self
		:rtype: UdmObject
		"""
		raise NotImplementedError()

	def save(self):  # type: () -> BaseUdmObject
		"""
		Save object to LDAP.

		:return: self
		:rtype: UdmObject
		:raises MoveError: when a move operation fails
		"""
		raise NotImplementedError()

	def delete(self):  # type: () -> None
		"""
		Remove the object from the LDAP database.

		:return: None
		"""
		raise NotImplementedError()


class BaseUdmObjectProperties(object):
	"""Container for UDM properties."""
	def __init__(self, simple_udm_obj):  # type: (BaseUdmObject) -> None
		self._simple_udm_obj = simple_udm_obj

	def __repr__(self):  # type: () -> str
		return pprint.pformat(dict((k, v) for k, v in self.__dict__.iteritems() if not str(k).startswith('_')), indent=2)




UdmLdapMapping = namedtuple('UdmLdapMapping', ('ldap2udm', 'udm2ldap'))


class BaseUdmModule(object):
	"""
	Base class for UdmModule classes. UdmModules are basically UdmObject
	factories.

	Usage:
	0. Get module using
		user_mod = Udm.using_*().get('users/user')
	1 Create fresh, not yet saved BaseUdmModule:
		new_user = user_mod.new()
	2 Load an existing object:
		group = group_mod.get('cn=test,cn=groups,dc=example,dc=com')
	3 Search and load existing objects:
		dc_slaves = dc_slave_mod.search(lo, filter_s='cn=s10*')
		campus_groups = group_mod.search(lo, base='ou=campus,dc=example,dc=com')
	"""
	udm_object_class = BaseUdmObject

	def __init__(self, name, lo):  # type: (str, univention.admin.uldap.access) -> None
		self.name = name
		self.lo = lo

	def __repr__(self):  # type: () -> str
		return '{}({!r})'.format(self.__class__.__name__, self.name)

	def new(self):  # type: () -> BaseUdmObject
		"""
		Create a new, unsaved BaseUdmObject object.

		:return: a new, unsaved BaseUdmObject object
		:rtype: BaseUdmObject
		"""
		raise NotImplementedError()

	def get(self, dn):  # type: (str) -> BaseUdmObject
		"""
		Load UDM object from LDAP.

		:param str dn:
		:return: an existing BaseUdmObject object
		:rtype: BaseUdmObject
		:raises NoObject: if no object is found at `dn`
		:raises WrongObjectType: if the object found at `dn` is not of type :py:attr:`self.name`
		"""
		raise NotImplementedError()

	def search(self, filter_s='', base='', scope='sub'):  # type: (str, str, str) -> Iterator[BaseUdmObject]
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

	@property
	def identifying_property(self):  # type: () -> str
		"""
		UDM Property of which the mapped LDAP attribute is used as first
		component in a DN, e.g. `username` (LDAP attribute `uid`) or `name`
		(LDAP attribute `cn`).
		"""
		raise NotImplementedError()

	@property
	def mapping(self):  # type: () -> UdmLdapMapping
		"""
		UDM properties to LDAP attributes mapping and vice versa.

		:return: a namedtuple containing two mappings: a) from UDM property to LDAP attribute and b) from LDAP attribute to UDM property
		:rtype: UdmLdapMapping
		"""
		raise NotImplementedError()
