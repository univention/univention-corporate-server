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
import univention.admin.objects
import univention.admin.modules
import univention.admin.uexceptions
import univention.admin.uldap

#
# TODO: ucs-test
# TODO: log to univention.debug.ADMIN
#


class UdmError(Exception):
	def __init__(self, msg, dn=None, module_name=None):
		self.dn = dn
		self.module_name = module_name
		super(UdmError, self).__init__(msg)


class NoObject(UdmError):
	def __init__(self, msg=None, dn=None, module_name=None):
		msg = msg or 'No object found at DN {!r}.'.format(dn)
		super(NoObject, self).__init__(msg, dn, module_name)


class WrongObjectType(UdmError):
	def __init__(self, msg=None, dn=None, module_name=None):
		msg = msg or 'Wrong UDM module: {!r} is not a {!r}.'.format(dn, module_name)
		super(WrongObjectType, self).__init__(msg, dn, module_name)


class UdmHandler(object):
	"""
	Simple functional API to UDM.
	"""
	_udm_module_cache = dict()

	def __init__(self, module_name, lo, po):
		# type: (str, univention.admin.uldap.access, univention.admin.uldap.position) -> None
		"""
		TODO
		:param module_name:
		:param lo:
		:param po:
		"""
		self.module_name = module_name
		self.lo = lo
		self.po = po

	def create(self, _position=None, **kwargs):  # type: (Optional[str], **str) -> str
		"""
		Create a new UDM object.

		:param _position: str: LDAP position to create object in
		:param kwargs: attributes to set on new object
		:return: str: DN of new UDM object
		"""
		obj = self._fetch_udm_obj(dn='', _position=_position, **kwargs)
		obj.create()
		return obj.dn

	def get(self, dn):  # type: (str) -> univention.admin.handlers.simpleLdap
		"""
		Retrieve UDM object from LDAP.

		May raise from NoObject if no object is found at DN or WrongObjectType
		if the object found is not of type self.module_name.

		:param dn: str
		:return: univention.admin.handlers.simpleLdap: UDM object
		"""
		udm_module = self.get_udm_module()
		try:
			obj = univention.admin.objects.get(udm_module, None, self.lo, self.po, dn=dn)
		except univention.admin.uexceptions.noObject:
			raise NoObject(dn, self.module_name)
		uni_obj_type = getattr(obj, 'oldattr', {}).get('univentionObjectType')
		if uni_obj_type and self.module_name not in uni_obj_type:
			raise WrongObjectType(dn, self.module_name)
		return obj

	def search(self, filter_s='', **kwargs):
		# type: (Optional[str], **str) -> List[univention.admin.handlers.simpleLdap]
		"""

		:param filter_s: str: LDAP filter
		:param kwargs: dict: arguments to pass to udm_module.lookup()
		:return: list of UDM modules
		"""
		udm_module = self.get_udm_module()
		return udm_module.lookup(None, self.lo, filter_s=filter_s, **kwargs)

	def modify(self, dn, _position=None, **kwargs):  # type: (str, **str) -> str
		"""
		TODO
		:param dn:
		:param _position:
		:param kwargs:
		:return: str: DN of modified UDM object
		"""
		obj = self._fetch_udm_obj(dn, _position, **kwargs)
		obj.modify()
		return obj.dn

	def remove(self, dn):  # type: (str) -> None
		"""
		TODO
		:param dn:
		:return:
		"""
		obj = self.get(dn)
		obj.remove()
		if univention.admin.objects.wantsCleanup(obj):
			univention.admin.objects.performCleanup(obj)

	def get_udm_module(self):  # type: () -> univention.admin.handlers.simpleLdap
		"""
		TODO
		:return:
		"""
		key = (self.lo.base, self.lo.binddn, self.lo.host, self.module_name)
		if key not in self._udm_module_cache:
			univention.admin.modules.update()
			udm_module = univention.admin.modules.get(self.module_name)
			univention.admin.modules.init(self.lo, self.po, udm_module)
			self._udm_module_cache[key] = udm_module
		return self._udm_module_cache[key]

	def _fetch_udm_obj(self, dn, _position=None, **kwargs):
		# type: (str, Optional[str], **str) -> univention.admin.handlers.simpleLdap
		"""
		TODO

		:param dn:
		:param _position:
		:param kwargs:
		:return:
		"""
		obj = self.get(dn)
		if _position:
			obj.position = _position
		try:
			obj.policies = kwargs.pop('policies')
		except KeyError:
			pass
		for k, v in kwargs.items():
			obj[k] = v
		return obj
