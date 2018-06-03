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

from __future__ import absolute_import
from ldap.dn import dn2str, str2dn
import univention.admin.objects
import univention.admin.modules
import univention.admin.uexceptions
import univention.admin.uldap

#
# TODO: ucs-test
# TODO: log to univention.debug.ADMIN
# TODO: search() should not be in a UDM object, just in the module/class -> factory
# TODO: _get_udm_object() and _get_udm_module() should be in the module/class -> factory
#


class UdmError(Exception):
	def __init__(self, msg, dn=None, module_name=None):
		self.dn = dn
		self.module_name = module_name
		super(UdmError, self).__init__(msg)


class FirstUseError(UdmError):
	def __init__(self, msg=None, dn=None, module_name=None):
		msg = msg or 'Object has not been created/loaded yet.'
		super(FirstUseError, self).__init__(msg, dn, module_name)


class NoObject(UdmError):
	def __init__(self, msg=None, dn=None, module_name=None):
		msg = msg or 'No object found at DN {!r}.'.format(dn)
		super(NoObject, self).__init__(msg, dn, module_name)


class UnknownAttribute(UdmError):
	pass


class WrongObjectType(UdmError):
	def __init__(self, msg=None, dn=None, module_name=None):
		msg = msg or 'Wrong UDM module: {!r} is not a {!r}.'.format(dn, module_name)
		super(WrongObjectType, self).__init__(msg, dn, module_name)


class UdmObject(object):
	"""
	Simple API to use UDM objects.

	Usage:
	* create a fresh, not yet saved, object by initializing with an empty dn:
		user = UdmObject('users/user', lo, '')
	* load existing object:
		group = UdmObject('groups/group', lo, 'cn=test,cn=groups,dc=example,dc=com')
	* search and load existing objects:
		dc_slaves = UdmObject.search('computers/domaincontroller_slave', lo, filter_s='cn=s10*')
		campus_groups = UdmObject.search('groups/group', lo, base='ou=campus,dc=example,dc=com')
	* modify object:
		user.attr.firstname = 'Peter'
		user.attr.lastname = 'Pan'
		user.save()
	* move object:
		user.position = 'cn=users,ou=Company,dc=example,dc=com'
		user.save()
	* delete object:
		obj.delete()

	Please be aware that UDM hooks and listener modules often add, modify or
	remove attributes when saving to LDAP. When continuing to use a UDM object
	after save(), it is *strongly* recommended to reload() it.

	Methods can be chained:
	* UdmObject(dn, ...).delete()
	* obj.reload().delete()
	* fresh_obj = obj.save().reload()
	"""

	_udm_module_cache = dict()

	class _Attr(object):
		def __init__(self, obj, udm_object):  # type: (UdmObject, univention.admin.handlers.simpleLdap) -> None
			self._obj = obj
			self._udm_object = udm_object

		def __repr__(self):
			return repr(dict((k, v) for k, v in self.__dict__.items() if not str(k).startswith('_')))

		def __setattr__(self, key, value):
			if not str(key).startswith('_') and key not in self._udm_object:
				raise UnknownAttribute(
					'Unknown attribute {!r} for UDM module {!r}.'.format(key, self._obj.module_name),
					self._obj.dn,
					self._obj.module_name
				)
			super(UdmObject._Attr, self).__setattr__(key, value)

	def __init__(self, module_name, lo, dn):  # type: (str, univention.admin.uldap.access, str) -> None
		"""
		TODO: doc

		:param module_name:
		:param lo:
		:param dn:
		"""
		self.dn = dn
		self.module_name = module_name
		self._lo = lo

		self.options = []
		self.policies = []
		self.position = ''

		self._old_position = ''
		self._udm_object = self._get_udm_object(dn)

		self.attr = UdmObject._Attr(self, self._udm_object)

		self._copy_from_udm_obj()
		self._fresh = True

	def reload(self):  # type: () -> UdmObject
		"""
		TODO: doc
		:return:
		"""
		if not self.dn or not self._udm_object:
			raise FirstUseError()
		self._udm_object = self._get_udm_object(self.dn)
		self._copy_from_udm_obj()
		self._fresh = True
		return self

	def save(self):  # type: () -> UdmObject
		"""
		TODO: doc
		:return:
		"""
		if not self._fresh:
			# TODO: where to log the warning to?
			pass
		self._copy_to_udm_obj()
		if self.dn:
			if self._old_position and self._old_position != self.position:
				new_dn_li = [str2dn(self._udm_object.dn)[0]]
				new_dn_li.extend(str2dn(self.position))
				new_dn = dn2str(new_dn_li)
				self.dn = self._udm_object.move(new_dn)
				assert self.dn == self._udm_object.dn
				self.position = self._lo.parentDn(self.dn)
				self._old_position = self.position
				self._udm_object.position.setDn(self.position)
			self.dn = self._udm_object.modify()
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
		if not self.dn or not self._udm_object:
			raise FirstUseError()
		self._udm_object.remove()
		if univention.admin.objects.wantsCleanup(self._udm_object):
			univention.admin.objects.performCleanup(self._udm_object)
		# prevent further use of object
		self._udm_object = self.save = self.delete = self.reload = None

	@classmethod
	def search(cls, module_name, lo, filter_s='', base='', scope='sub'):
		# type: (str, univention.admin.uldap.access, Optional[str]) -> List[UdmObject]
		"""
		TODO: doc

		:param module_name:
		:param lo:
		:param filter_s: str: LDAP filter (only object selector like uid=foo
			required, objectClasses will be set by the UDM module)
		:param base:
		:param scope:
		:return: list of UdmObject objects
		"""
		udm_module = cls._get_udm_module(module_name, lo)
		try:
			udm_module_lookup_filter = str(udm_module.lookup_filter(filter_s, lo))
		except AttributeError:
			# not all modules have 'lookup_filter'
			udm_module_lookup_filter = filter_s
		res = lo.search(filter=udm_module_lookup_filter, base=base, scope=scope, attr=['dn'])
		return [UdmObject(module_name, lo, dn) for dn, attr in res]

	def _copy_from_udm_obj(self):  # type: () -> None
		"""
		TODO: doc
		:return:
		"""
		self.dn = self._udm_object.dn
		self.options = self._udm_object.options
		self.policies = self._udm_object.policies
		if self.dn:
			self.position = self._lo.parentDn(self.dn)
			self._old_position = self.position
		else:
			self.position = self._udm_object.position.getDn()
		self.attr = UdmObject._Attr(self, self._udm_object)
		for k, v in self._udm_object.items():
			setattr(self.attr, k, v)

	def _copy_to_udm_obj(self):  # type: () -> None
		"""
		TODO: doc
		:return:
		"""
		self._udm_object.options = self.options
		self._udm_object.policies = self.policies
		self._udm_object.position.setDn(self.position)
		for k, v in self._udm_object.items():
			if v != getattr(self.attr, k, None):
				self._udm_object[k] = getattr(self.attr, k, None)

	@classmethod
	def _get_udm_module(cls, module_name, lo):
		# type: (str, univention.admin.uldap.access) -> univention.admin.handlers.simpleLdap
		"""
		TODO: doc
		:param module_name:
		:param lo:
		:return:
		"""
		key = (lo.base, lo.binddn, lo.host, module_name)
		if key not in cls._udm_module_cache:
			if module_name not in [key[3] for key in cls._udm_module_cache.keys()]:
				univention.admin.modules.update()
			udm_module = univention.admin.modules.get(module_name)
			po = univention.admin.uldap.position(lo.base)
			univention.admin.modules.init(lo, po, udm_module)
			cls._udm_module_cache[key] = udm_module
		return cls._udm_module_cache[key]

	def _get_udm_object(self, dn):  # type: (str) -> univention.admin.handlers.simpleLdap
		"""
		Retrieve UDM object from LDAP.

		May raise from NoObject if no object is found at DN or WrongObjectType
		if the object found is not of type self.module_name.

		:param dn: str
		:return: univention.admin.handlers.simpleLdap: UDM object
		"""
		udm_module = self._get_udm_module(self.module_name, self._lo)
		po = univention.admin.uldap.position(self.position or self._lo.base)
		try:
			obj = univention.admin.objects.get(udm_module, None, self._lo, po, dn=dn)
		except univention.admin.uexceptions.noObject:
			raise NoObject(dn=dn, module_name=self.module_name)
		uni_obj_type = getattr(obj, 'oldattr', {}).get('univentionObjectType')
		if uni_obj_type and self.module_name not in uni_obj_type:
			raise WrongObjectType(dn=dn, module_name=self.module_name)
		obj.open()
		return obj
