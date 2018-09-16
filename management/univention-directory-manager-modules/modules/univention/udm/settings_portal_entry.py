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
from .base import BaseUdmObjectProperties
from .encoders import Base64BinaryPropertyEncoder, StringBooleanPropertyEncoder, MultiLanguageTextPropertyEncoder
from .generic import GenericUdm1Module, GenericUdm1Object

try:
	from typing import Dict, List, Optional, Text
except ImportError:
	pass


class SettingsPortalEntryUdm1ObjectProperties(BaseUdmObjectProperties):
	"""settings/portal_entry UDM properties."""

	encoders = {
		'activated': StringBooleanPropertyEncoder,
		'description': MultiLanguageTextPropertyEncoder,
		'displayName': MultiLanguageTextPropertyEncoder,
		'icon': Base64BinaryPropertyEncoder,
	}


class SettingsPortalEntryUdm1Object(GenericUdm1Object):
	"""Better representation of settings/portal_entry properties."""
	udm_prop_class = SettingsPortalEntryUdm1ObjectProperties


class SettingsPortalEntryUdm1Module(GenericUdm1Module):
	"""SettingsPortalEntryUdm1Object factory"""
	_udm_object_class = SettingsPortalEntryUdm1Object
