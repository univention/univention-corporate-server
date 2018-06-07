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
A generic UDM module and object implementation.
Will work for all kinds of UDM modules.
"""

from __future__ import absolute_import
from ldap.dn import dn2str, str2dn
import univention.admin.objects
import univention.admin.modules
import univention.admin.uexceptions
import univention.admin.uldap
from .base import BaseUdmModule, BaseUdmObject, BaseUdmObjectProperties, UdmLdapMapping
from .exceptions import DeletedError, FirstUseError, ModifyError, MoveError, NoObject, UnknownProperty, WrongObjectType

try:
	from typing import Any, Dict, Iterator, Tuple
except ImportError:
	pass


class GenericUdmObjectProperties(BaseUdmObjectProperties):
	def __init__(self, simple_udm_obj):  # type: (GenericUdmObject) -> None
		assert isinstance(simple_udm_obj, GenericUdmObject)
		self._simple_udm_obj = simple_udm_obj

	def __setattr__(self, key, value):  # type: (str, Any) -> None
		if not str(key).startswith('_') and key not in self._simple_udm_obj._udm_object:
			raise UnknownProperty(
				'Unknown property {!r} for UDM module {!r}.'.format(key, self._simple_udm_obj._simple_udm_module.name),
				dn=self._simple_udm_obj.dn,
				module_name=self._simple_udm_obj._simple_udm_module.name
			)
		super(GenericUdmObjectProperties, self).__setattr__(key, value)


class GenericUdmObject(BaseUdmObject):
	"""
	Simple API to use UDM objects.

	Usage:
	* Creation of instances :py:class:`UdmObject` is always done through a
	:py:class:`UdmModul` instances py:meth:`new()`, py:meth:`get()` or
	py:meth:`search()` methods.
	* There is a convenience function to create or load :py:class:`UdmObject`s:
	:py:func:`get_udm_object(<module_name>, <lo>, [dn])`.
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
	:py:class:`UdmObject` after :py:meth:`save()`, it is *strongly* recommended
	to :py:meth:`reload()` it: `obj = obj.save().reload()`
	"""
	udm_prop_class = GenericUdmObjectProperties

	def __init__(self):  # type: () -> None
		"""
		Don't instantiate a :py:class:`UdmObject` directly. Use a
		:py:class:`UdmModule` or :py:func:`get_udm_object()`.
		"""
		super(GenericUdmObject, self).__init__()
		self._simple_udm_module = None  # type: GenericUdmModule
		self._lo = None  # type: univention.admin.uldap.access
		self._udm_object = None  # type: univention.admin.handlers.simpleLdap
		self._old_position = ''
		self._fresh = True
		self._deleted = False

	def reload(self):  # type: () -> GenericUdmObject
		"""
		Refresh object from LDAP.

		:return: self
		:rtype: UdmObject
		"""
		if self._deleted:
			raise DeletedError('{} has been deleted.'.format(self), dn=self.dn, module_name=self._simple_udm_module.name)
		if not self.dn or not self._udm_object:
			raise FirstUseError(module_name=self._simple_udm_module.name)
		self._udm_object = self._simple_udm_module._get_udm_object(self.dn)
		self._copy_from_udm_obj()
		return self

	def save(self):  # type: () -> GenericUdmObject
		"""
		Save object to LDAP.

		:return: self
		:rtype: UdmObject
		:raises MoveError: when a move operation fails
		"""
		if self._deleted:
			raise DeletedError('{} has been deleted.'.format(self), dn=self.dn, module_name=self._simple_udm_module.name)
		if not self._fresh:
			# TODO: log warning
			print('*** WARNING: saving stale UDM object instance.')
		self._copy_to_udm_obj()
		if self.dn:
			if self._old_position and self._old_position != self.position:
				new_dn_li = [str2dn(self._udm_object.dn)[0]]
				new_dn_li.extend(str2dn(self.position))
				new_dn = dn2str(new_dn_li)
				try:
					self.dn = self._udm_object.move(new_dn)
				except univention.admin.uexceptions.invalidOperation as exc:
					raise MoveError(
						'Error moving {!r} object from {!r} to {!r}: {}'.format(
							self._simple_udm_module.name, self.dn, self.position, exc
						), dn=self.dn, module_name=self._simple_udm_module.name
					)
				assert self.dn == self._udm_object.dn
				self.position = self._lo.parentDn(self.dn)
				self._old_position = self.position
				self._udm_object.position.setDn(self.position)
			try:
				self.dn = self._udm_object.modify()
			except (
					univention.admin.uexceptions.noProperty,
					univention.admin.uexceptions.valueError,
					univention.admin.uexceptions.valueInvalidSyntax
			) as exc:
				raise ModifyError(
					'Error saving {!r} object at {!r}: {}'.format(
						self._simple_udm_module.name, self.dn, exc
					), dn=self.dn, module_name=self._simple_udm_module.name
				)
		else:
			self.dn = self._udm_object.create()
		assert self.dn == self._udm_object.dn
		assert self.position == self._lo.parentDn(self.dn)
		self._fresh = False
		return self

	def delete(self):  # type: () -> None
		"""
		Remove the object from the LDAP database.

		:return: None
		"""
		if self._deleted:
			# TODO: log warning
			print('*** WARNING: {} has already been deleted.'.format(self))
			return
		if not self.dn or not self._udm_object:
			raise FirstUseError()
		self._udm_object.remove()
		if univention.admin.objects.wantsCleanup(self._udm_object):
			univention.admin.objects.performCleanup(self._udm_object)
		self._udm_object = None
		self._deleted = True

	def _copy_from_udm_obj(self):  # type: () -> None
		"""
		TODO: doc

		:return: None
		"""
		self.dn = self._udm_object.dn
		self.options = self._udm_object.options
		self.policies = self._udm_object.policies
		if self.dn:
			self.position = self._lo.parentDn(self.dn)
			self._old_position = self.position
		else:
			self.position = self._udm_object.position.getDn()
		self.props = self.udm_prop_class(self)
		for k, v in self._udm_object.items():
			try:
				decode_func = getattr(self, '_decode_prop_{}'.format(k))
				assert callable(decode_func), 'Attribute {!r} of class {!r} must be callable.'.format(
					'_decode_prop_{}'.format(k), self.__class__.__name__)
				v = decode_func(v)
			except AttributeError:
				pass
			setattr(self.props, k, v)
		self._fresh = True

	def _copy_to_udm_obj(self):  # type: () -> None
		"""
		TODO: doc

		:return: None
		"""
		self._udm_object.options = self.options
		self._udm_object.policies = self.policies
		self._udm_object.position.setDn(self.position)
		for k, v in self._udm_object.items():
			new_val = getattr(self.props, k, None)
			if v != new_val:
				try:
					encode_func = getattr(self, '_encode_prop_{}'.format(k))
					assert callable(encode_func), 'Attribute {!r} of class {!r} must be callable.'.format(
						'encode_func{}'.format(k), self.__class__.__name__)
					new_val = encode_func(new_val)
				except AttributeError:
					pass
				self._udm_object[k] = new_val


class GenericUdmModule(BaseUdmModule):
	"""
	Simple API to use UDM modules. Basically a GenericUdmObject factory.

	Usage:
	1. Get an LDAP access object: import univention.admin.uldap; lo, po = univention.admin.uldap.getAdminConnection()
	2. Create a module object:
		user_mod = get_udm_module('users/user', lo)
	3. Create object(s):
	3.1 Fresh, not yet saved GenericUdmObject:
		new_user = user_mod.new()
	3.2 Load an existing object:
		group = group_mod.get('cn=test,cn=groups,dc=example,dc=com')
	3.3 Search and load existing objects:
		dc_slaves = dc_slave_mod.search(lo, filter_s='cn=s10*')
		campus_groups = group_mod.search(lo, base='ou=campus,dc=example,dc=com')

	There is a shortcut for creating or retrieving UdmObjects without handling
	UdmModule instances:
		new_group = get_udm_object('groups/group', lo)
		existing_user = get_udm_object('users/user', lo, 'uid=test,cn=users,dc=example,dc=com')
	"""
	_udm_module_cache = {}  # type: Dict[Tuple[str, str, str, str], univention.admin.handlers.simpleLdap]
	udm_object_class = GenericUdmObject

	def __init__(self, name, lo):  # type: (str, univention.admin.uldap.access) -> None
		super(GenericUdmModule, self).__init__(name, lo)
		self._udm_module = self._get_udm_module()

	def new(self):  # type: () -> GenericUdmObject
		"""
		TODO: doc

		:return: a new, unsaved BaseUdmObject object
		:rtype: BaseUdmObject
		"""
		return self._load_obj('')

	def get(self, dn):  # type: (str) -> GenericUdmObject
		"""
		TODO: doc

		:param str dn:
		:return: an existing GenericUdmObject object
		:rtype: GenericUdmObject
		:raises NoObject: if no object is found at `dn`
		:raises WrongObjectType: if the object found at `dn` is not of type :py:attr:`self.name`
		"""
		return self._load_obj(dn)

	def search(self, filter_s='', base='', scope='sub'):  # type: (str, str, str) -> Iterator[GenericUdmObject]
		"""
		TODO: doc

		:param str filter_s: LDAP filter (only object selector like uid=foo
			required, objectClasses will be set by the UDM module)
		:param str base:
		:param str scope:
		:return: iterator of BaseUdmObject objects
		:rtype: Iterator(BaseUdmObject)
		"""
		try:
			udm_module_lookup_filter = str(self._udm_module.lookup_filter(filter_s, self.lo))
		except AttributeError:
			# not all modules have 'lookup_filter'
			udm_module_lookup_filter = filter_s
		for dn in self.lo.searchDn(filter=udm_module_lookup_filter, base=base, scope=scope):
			yield self.get(dn)

	@property
	def identifying_property(self):  # type: () -> str
		"""Property that is used as first component in a DN."""
		for key, udm_property in self._udm_module.property_descriptions.iteritems():
			if udm_property.identifies:
				return key
		return ''

	@property
	def mapping(self):  # type: () -> UdmLdapMapping
		"""
		UDM properties to LDAP attributes mapping and vice versa.

		:return: a namedtuple containing two mappings: a) from UDM property to LDAP attribute and b) from LDAP attribute to UDM property
		:rtype: UdmLdapMapping
		"""
		return UdmLdapMapping(
			udm2ldap=dict((k, v[0]) for k, v in self._udm_module.mapping._map.iteritems()),
			ldap2udm=dict((k, v[0]) for k, v in self._udm_module.mapping._unmap.iteritems())
		)

	def _get_udm_module(self):  # type: () -> univention.admin.handlers.simpleLdap
		"""
		Load a UDM module, initializing it if required.

		:return: a UDM module
		:rtype: univention.admin.handlers.simpleLdap
		"""
		# While univention.admin.modules already implements a modules cache we
		# cannot know if update() or init() are required. So we'll also cache.
		key = (self.lo.base, self.lo.binddn, self.lo.host, self.name)
		if key not in self._udm_module_cache:
			if self.name not in [key[3] for key in self._udm_module_cache.keys()]:
				univention.admin.modules.update()
			udm_module = univention.admin.modules.get(self.name)
			po = univention.admin.uldap.position(self.lo.base)
			univention.admin.modules.init(self.lo, po, udm_module)
			self._udm_module_cache[key] = udm_module
		return self._udm_module_cache[key]

	def _get_udm_object(self, dn):  # type: (str) -> univention.admin.handlers.simpleLdap
		"""
		Retrieve UDM object from LDAP.

		May raise from NoObject if no object is found at DN or WrongObjectType
		if the object found is not of type :py:attr:`self.name`.

		:param str dn: the DN of the object to load
		:return: UDM object
		:rtype: univention.admin.handlers.simpleLdap
		:raises NoObject: if no object is found at `dn`
		:raises WrongObjectType: if the object found at `dn` is not of type :py:attr:`self.name`
		"""
		udm_module = self._get_udm_module()
		po = univention.admin.uldap.position(self.lo.base)
		try:
			obj = univention.admin.objects.get(udm_module, None, self.lo, po, dn=dn)
		except univention.admin.uexceptions.noObject:
			raise NoObject(dn=dn, module_name=self.name)
		uni_obj_type = getattr(obj, 'oldattr', {}).get('univentionObjectType')
		if uni_obj_type and self.name not in uni_obj_type:
			raise WrongObjectType(dn=dn, module_name=self.name)
		obj.open()
		return obj

	def _load_obj(self, dn):  # type: (str) -> GenericUdmObject
		"""
		GenericUdmObject factory.

		:param str dn: the DN of the UDM object to load, if '' a new one
		:return: a GenericUdmObject
		:rtype: GenericUdmObject
		:raises NoObject: if no object is found at `dn`
		:raises WrongObjectType: if the object found at `dn` is not of type :py:attr:`self.name`
		"""
		obj = self.udm_object_class()
		obj._lo = self.lo
		obj._simple_udm_module = self
		obj._udm_object = self._get_udm_object(dn)
		obj.props = obj.udm_prop_class(obj)
		obj._copy_from_udm_obj()
		return obj
