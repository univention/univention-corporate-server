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
from typing import Iterable, Optional, Text


class UdmError(Exception):
	def __init__(self, msg=None, dn=None, module_name=None):
		# type: (Optional[Text], Optional[Text], Optional[Text]) -> None
		...

class ApiVersionMustNotChange(UdmError):
	...

class ConnectionError(UdmError):
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
	...

class DeletedError(UdmError):
	def __init__(self, msg=None, dn=None, module_name=None):
		# type: (Optional[Text], Optional[Text], Optional[Text]) -> None
		...

class DeleteError(UdmError):
	def __init__(self, msg=None, dn=None, module_name=None):
		# type: (Optional[Text], Optional[Text], Optional[Text]) -> None
		...

class NotYetSavedError(UdmError):
	def __init__(self, msg=None, dn=None, module_name=None):
		# type: (Optional[Text], Optional[Text], Optional[Text]) -> None
		...

class ModifyError(UdmError):
	...

class MoveError(UdmError):
	...

class NoApiVersionSet(UdmError):
	...

class NoObject(UdmError):
	def __init__(self, msg=None, dn=None, module_name=None):
		# type: (Optional[Text], Optional[Text], Optional[Text]) -> None
		...

class NoSuperordinate(UdmError):
	def __init__(self, msg=None, dn=None, module_name=None, superordinate_types=None):
		...

class MultipleObjects(UdmError):
	...

class UnknownModuleType(UdmError):
	def __init__(self, msg=None, dn=None, module_name=None):
		# type: (Optional[Text], Optional[Text], Optional[Text]) -> None
		...

class UnknownProperty(UdmError):
	...

class WrongObjectType(UdmError):
	def __init__(self, msg=None, dn=None, module_name=None, univention_object_type=None):
		# type: (Optional[Text], Optional[Text], Optional[Text], Optional[Text]) -> None
		...
