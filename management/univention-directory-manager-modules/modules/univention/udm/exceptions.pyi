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

from __future__ import unicode_literals
from typing import Iterable, Optional, Text


class UdmError(Exception):
	"""Base class of Exceptions raised by (simplified) UDM modules."""
	def __init__(self, msg, dn=None, module_name=None):
		# type: (Text, Optional[Text], Optional[Text]) -> None
		...


class ConnectionError(UdmError):
	"""Raised when something goes wrong getting a connection."""
	...


class ApiVersionNotSupported(UdmError):
	def __init__(
		self,
		msg=None,  # type: Text
		module_name=None,  # type: Text
		module_cls=None,  # type: type
		requested_version=None,  # type: int
		supported_versions=None,  # type: Iterable
	):
		#  type: (...) -> None
		...


class CreateError(UdmError):
	"""Raised when an error occurred when creating an object."""
	...


class DeletedError(UdmError):
	def __init__(self, msg=None, dn=None, module_name=None):
		# type: (Optional[Text], Optional[Text], Optional[Text]) -> None
		...


class DeleteError(UdmError):
	"""
	Raised when a client tries to delete a UdmObject but fails.
	"""
	def __init__(self, msg=None, dn=None, module_name=None):
		# type: (Optional[Text], Optional[Text], Optional[Text]) -> None
		...


class NotYetSavedError(UdmError):
	"""
	Raised when a client tries to delete or reload a UdmObject that is not yet
	saved.
	"""
	def __init__(self, msg=None, dn=None, module_name=None):
		# type: (Optional[Text], Optional[Text], Optional[Text]) -> None
		...


class ModifyError(UdmError):
	"""Raised if an error occurred when modifying an object."""
	...


class MoveError(UdmError):
	"""Raised if an error occurred when moving an object."""
	...


class NoObject(UdmError):
	"""Raised when a UdmObject could not be found at a DN."""
	def __init__(self, msg=None, dn=None, module_name=None):
		# type: (Optional[Text], Optional[Text], Optional[Text]) -> None
		...


class MultipleObjects(UdmError):
	"""Raised when more than one UdmObject was found when there should be at most one."""
	...


class UnknownUdmModuleType(UdmError):
	"""
	Raised when an LDAP object has no or empty attribute univentionObjectType.
	"""
	def __init__(self, msg=None, dn=None, module_name=None):
		# type: (Optional[Text], Optional[Text], Optional[Text]) -> None
		...


class UnknownProperty(UdmError):
	"""
	Raised when a client tries to set a property on UdmObject.props, that it
	does not support.
	"""
	...


class WrongObjectType(UdmError):
	"""
	Raised when the LDAP object to be loaded does not match the UdmModule type.
	"""
	def __init__(self, msg=None, dn=None, module_name=None, univention_object_type=None):
		# type: (Optional[Text], Optional[Text], Optional[Text], Optional[Text]) -> None
		...
