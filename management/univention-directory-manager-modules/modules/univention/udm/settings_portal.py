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
Module and object specific for "settings/portal" UDM module.
"""

from __future__ import absolute_import, unicode_literals
from .encoders import Base64BinaryPropertyEncoder, StringBooleanPropertyEncoder, MultiLanguageTextPropertyEncoder
from .generic import GenericUdm1Module, GenericUdm1Object, GenericUdm1ObjectProperties

try:
	from typing import Dict, List, Optional, Text
except ImportError:
	pass


class SettingsPortalUdm1ObjectProperties(GenericUdm1ObjectProperties):
	"""settings/portal UDM properties."""

	_encoders = {
		'background': Base64BinaryPropertyEncoder,
		'displayName': MultiLanguageTextPropertyEncoder,
		'logo': Base64BinaryPropertyEncoder,
		'showApps': StringBooleanPropertyEncoder,
		'showLogin': StringBooleanPropertyEncoder,
		'showMenu': StringBooleanPropertyEncoder,
		'showSearch': StringBooleanPropertyEncoder,
		'showServers': StringBooleanPropertyEncoder,
	}


class SettingsPortalUdm1Object(GenericUdm1Object):
	"""Better representation of settings/portal properties."""
	udm_prop_class = SettingsPortalUdm1ObjectProperties


class SettingsPortalUdm1Module(GenericUdm1Module):
	"""SettingsPortalUdm1Object factory"""
	_udm_object_class = SettingsPortalUdm1Object
