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

from __future__ import unicode_literals


class UdmError(Exception):
	"""Base class of Exceptions raised by (simplified) UDM modules."""
	msg = ''

	def __init__(self, msg=None, dn=None, module_name=None):
		msg = msg or self.msg
		super(UdmError, self).__init__(msg)
		self.dn = dn
		self.module_name = module_name


class ApiVersionMustNotChange(UdmError):
	"""Raised when UDM.version() is called twice."""
	msg = 'The version of an UDM instance must not be changed.'


class ConnectionError(UdmError):
	"""Raised when something goes wrong getting a connection."""
	pass


class ApiVersionNotSupported(UdmError):
	def __init__(
		self,
		msg=None,
		module_name=None,
		requested_version=None,
	):
		self.requested_version = requested_version
		msg = msg or 'Module {!r} is not supported in API version {!r}.'.format(
			module_name, requested_version)
		super(ApiVersionNotSupported, self).__init__(msg, module_name=module_name)


class CreateError(UdmError):
	"""Raised when an error occurred when creating an object."""
	pass


class DeletedError(UdmError):
	def __init__(self, msg=None, dn=None, module_name=None):
		msg = msg or 'Object{} has already been deleted.'.format(' {!r}'.format(dn) if dn else '')
		super(DeletedError, self).__init__(msg, dn, module_name)


class DeleteError(UdmError):
	"""
	Raised when a client tries to delete a UDM object but fails.
	"""
	def __init__(self, msg=None, dn=None, module_name=None):
		msg = msg or 'Object{} could not be deleted.'.format(' {!r}'.format(dn) if dn else '')
		super(DeleteError, self).__init__(msg, dn, module_name)


class NotYetSavedError(UdmError):
	"""
	Raised when a client tries to delete or reload a UDM object that is not
	yet saved.
	"""
	msg = 'Object has not been created/loaded yet.'


class ModifyError(UdmError):
	"""Raised if an error occurred when modifying an object."""
	pass


class MoveError(UdmError):
	"""Raised if an error occurred when moving an object."""
	pass


class NoApiVersionSet(UdmError):
	"""
	Raised when UDM.get() or UDM.obj_by_id() is used before setting an API
	version.
	"""
	msg = 'No API version has been set.'


class NoObject(UdmError):
	"""Raised when a UDM object could not be found at a DN."""
	def __init__(self, msg=None, dn=None, module_name=None):
		msg = msg or 'No object found at DN {!r}.'.format(dn)
		super(NoObject, self).__init__(msg, dn, module_name)


class NoSuperordinate(UdmError):
	"""Raised when no superordinate was supplied but one is needed."""
	def __init__(self, msg=None, dn=None, module_name=None, superordinate_types=None):
		msg = msg or 'No superordinate was supplied, but one of type{} {} is required to create/save a {} object.'.format(
			's' if len(superordinate_types) > 1 else '', ', '.join(superordinate_types), module_name)
		super(NoSuperordinate, self).__init__(msg, dn, module_name)


class MultipleObjects(UdmError):
	"""
	Raised when more than one UDM object was found when there should be at
	most one.
	"""
	pass


class UnknownModuleType(UdmError):
	"""
	Raised when an LDAP object has no or empty attribute univentionObjectType.
	"""
	def __init__(self, msg=None, dn=None, module_name=None):
		msg = msg or 'No or empty attribute "univentionObjectType" found at DN {!r}.'.format(dn)
		super(UnknownModuleType, self).__init__(msg, dn, module_name)


class UnknownProperty(UdmError):
	"""
	Raised when a client tries to set a property on :py:attr:`BaseObject.props`,
	that it does not support.
	"""
	pass


class WrongObjectType(UdmError):
	"""
	Raised when the LDAP object to be loaded does not match the module type
	(:py:attr:`BaseModule.name`).
	"""
	def __init__(self, msg=None, dn=None, module_name=None, univention_object_type=None):
		msg = msg or 'Wrong UDM module: {!r} is not a {!r}, but a {!r}.'.format(dn, module_name, univention_object_type)
		super(WrongObjectType, self).__init__(msg, dn, module_name)
