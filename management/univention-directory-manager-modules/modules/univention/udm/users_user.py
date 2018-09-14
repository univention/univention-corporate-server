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
TEST module and object specific for "users/user" UDM module.
"""

from __future__ import absolute_import, unicode_literals
import time
import datetime
from univention.admin.uexceptions import valueInvalidSyntax
from .generic import GenericUdm1Module, GenericUdm1Object

try:
	from typing import Dict, List, Optional, Text
except ImportError:
	pass


class UsersUserUdm1Object(GenericUdm1Object):
	"""Better representation of users/user properties."""

	_weekdays = ('Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat')

	def _decode_prop_homePostalAddress(self, value):  # type: (List[List[Text]]) -> List[Dict[Text, Text]]
		return [{'street': v[0], 'zipcode': v[1], 'city': v[2]} for v in value]

	def _encode_prop_homePostalAddress(self, value):  # type: (List[Dict[str, Text]]) -> List[List[Text]]
		return [[v['street'], v['zipcode'], v['city']] for v in value]

	def _decode_prop_disabled(self, value):  # type: (str) -> bool
		return value == '1'

	def _encode_prop_disabled(self, value):  # type: (bool) -> Text
		return '1' if value else '0'

	def _decode_prop_sambaLogonHours(self, value):  # type: (List[int]) -> List[Text]
		return ['{} {}-{}'.format(self._weekdays[v/24], v % 24, v % 24 + 1) for v in value]

	def _encode_prop_sambaLogonHours(self, value):  # type: (List[Text]) -> List[int]
		try:
			values = [v.split() for v in value]
			return [self._weekdays.index(w) * 24 + int(h.split('-', 1)[0]) for w, h in values]
		except (IndexError, ValueError):
			raise valueInvalidSyntax('One or more entries in sambaLogonHours have invalid syntax.')

	def _decode_prop_birthday(self, value):  # type: (Optional[str]) -> Optional[datetime.date]
		if value:
			return datetime.date(*time.strptime(value, '%Y-%m-%d')[0:3])
		else:
			return value

	def _encode_prop_birthday(self, value):  # type: (Optional[datetime.date]) -> Optional[str]
		if value:
			return value.strftime('%Y-%m-%d')
		else:
			return value

	_decode_prop_userexpiry = _decode_prop_birthday
	_encode_prop_userexpiry = _encode_prop_birthday

class UsersUserUdm1Module(GenericUdm1Module):
	"""Test dynamic factory"""
	_udm_object_class = UsersUserUdm1Object
