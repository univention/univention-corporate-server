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
Classes for holding binary UDM  object properties.
"""

from __future__ import absolute_import, unicode_literals
import base64

try:
	from typing import Optional, Text
except ImportError:
	pass


class BaseBinaryProperty(object):
	"""
	Container for a binary UDM property.

	Data can be set and retrieved in both its raw form or encoded for LDAP.

	Internally data is held in the encoded state (the form in which it will be
	saved to LDAP).
	"""
	def __init__(self, name, encoded_value=None, raw_value=None):
		# type: (Text, Optional[Text], Optional[Text]) -> None
		assert not (encoded_value and raw_value), 'Only one of "encoded_value" and "raw_value" must be set.'
		assert (encoded_value or raw_value), 'One of "encoded_value" or "raw_value" must be set.'
		self._name = name
		self._value = None
		if encoded_value:
			self.encoded = encoded_value
		elif raw_value:
			self.raw = raw_value

	def __repr__(self):  # type: () -> Text
		return '{}({})'.format(self.__class__.__name__, self._name)

	@property
	def encoded(self):  # type: () -> Text
		return self._value

	@encoded.setter
	def encoded(self, value):  # type: (Text) -> None
		self._value = value

	@property
	def raw(self):  # type: () -> Text
		raise NotImplementedError()

	@raw.setter
	def raw(self, value):  # type: (Text) -> None
		raise NotImplementedError()


class Base64BinaryProperty(BaseBinaryProperty):
	"""
	Container for a binary UDM property encoded using base64.

	obj.props.<prop>.encoded == base64.b64encode(obj.props.<prop>.decoded)

	>>> binprop = Base64BinaryProperty('example', raw_value='raw value')
	>>> Base64BinaryProperty('example', encoded_value=binprop.encoded).raw == 'raw value'
	True
	>>> import base64
	>>> binprop.encoded == base64.b64encode(binprop.raw)
	True
	"""
	@property
	def raw(self):  # type: () -> Text
		return base64.b64decode(self._value)

	@raw.setter
	def raw(self, value):  # type: (Text) -> None
		self._value = base64.b64encode(value)
