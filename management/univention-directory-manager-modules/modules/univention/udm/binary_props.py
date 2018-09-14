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
Classes for holding binary UDM  object porperties.
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

	Update
	"""
	def __init__(self, name, encoded_value=None, decoded_value=None):
		# type: (Text, Optional[Text], Optional[Text]) -> None
		assert not (encoded_value and decoded_value), 'Only one of "encoded_value" and "decoded_value" must be set.'
		assert (encoded_value or decoded_value), 'One of "encoded_value" or "decoded_value" must be set.'
		self._name = name
		self._value = None
		if encoded_value:
			self.encoded = encoded_value
		elif decoded_value:
			self.decoded = decoded_value

	def __repr__(self):  # type: () -> Text
		return '{}({!r})'.format(self.__class__.__name__, self._name)

	@property
	def encoded(self):  # type: () -> Text
		return self._value

	@encoded.setter
	def encoded(self, value):  # type: (Text) -> None
		self._value = value

	@property
	def decoded(self):  # type: () -> Text
		raise NotImplementedError()

	@decoded.setter
	def decoded(self, value):  # type: (Text) -> None
		raise NotImplementedError()


class Base64BinaryProperty(BaseBinaryProperty):
	"""Container for a binary UDM property encoded using base64."""

	@property
	def decoded(self):  # type: () -> Text
		return base64.b64decode(self._value)

	@decoded.setter
	def decoded(self, value):  # type: (Text) -> None
		self._value = base64.b64encode(value)
