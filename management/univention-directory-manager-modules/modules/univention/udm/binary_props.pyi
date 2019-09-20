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

"""
Classes for holding binary UDM  object properties.
"""

from __future__ import absolute_import, unicode_literals
from collections import namedtuple
from typing import BinaryIO, Optional, Text, Union


FileType = namedtuple('namedtuple', ['mime_type', 'encoding', 'text'])


def get_file_type(filename_or_file):  # type: (Union[str, BinaryIO]) -> FileType
	...

class BaseBinaryProperty(object):
	def __init__(self, name, encoded_value=None, raw_value=None):
		# type: (Text, Optional[Text], Optional[Text]) -> None
		...

	def __repr__(self):  # type: () -> Text
		...

	@property
	def encoded(self):  # type: () -> Text
		...

	@encoded.setter
	def encoded(self, value):  # type: (Text) -> None
		...

	@property
	def raw(self):  # type: () -> Text
		...

	@raw.setter
	def raw(self, value):  # type: (Text) -> None
		...

	@property
	def content_type(self):  # type: () -> FileType
		...


class Base64BinaryProperty(BaseBinaryProperty):
	@property
	def raw(self):  # type: () -> Text
		...

	@raw.setter
	def raw(self, value):  # type: (Text) -> None
		...


class Base64Bzip2BinaryProperty(BaseBinaryProperty):
	@property
	def raw(self):  # type: () -> Text
		...

	@raw.setter
	def raw(self, value):  # type: (Text) -> None
		...
