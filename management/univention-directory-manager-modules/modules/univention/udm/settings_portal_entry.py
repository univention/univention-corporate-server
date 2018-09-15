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
Module and object specific for "settings/portal_entry" UDM module.
"""

from __future__ import absolute_import, unicode_literals
from .binary_props import Base64BinaryProperty
from .generic import GenericUdm1Module, GenericUdm1Object

try:
	from typing import Dict, List, Optional, Text
except ImportError:
	pass


class SettingsPortalEntryUdm1Object(GenericUdm1Object):
	"""Better representation of settings/portal_entry properties."""

	def _decode_prop_activated(self, value):  # type: (str) -> bool
		return value == 'TRUE'

	def _encode_prop_activated(self, value):  # type: (bool) -> Text
		if value:
			return 'TRUE'
		else:
			return 'FALSE'

	def _decode_prop_description(self, value):  # type: (List[List[Text]]) -> Dict[Text, Text]
		return dict(value)

	def _encode_prop_description(self, value):  # type: (Dict[str, Text]) -> List[List[Text]]
		return [[k, v] for k, v in value.items()]

	_decode_prop_displayName = _decode_prop_description
	_encode_prop_displayName = _encode_prop_description

	def _decode_prop_icon(self, value):  # type: (Optional[Text]) -> Optional[Base64BinaryProperty]
		if value:
			return Base64BinaryProperty('icon', value)
		else:
			return value

	def _encode_prop_icon(self, value):  # type: (Optional[Base64BinaryProperty]) -> Optional[Text]
		if value:
			return value.encoded
		else:
			return value


class SettingsPortalEntryUdm1Module(GenericUdm1Module):
	"""SettingsPortalEntryUdm1Object factory"""
	_udm_object_class = SettingsPortalEntryUdm1Object
