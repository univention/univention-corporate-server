# -*- coding: utf-8 -*-
#
# Copyright 2018-2020 Univention GmbH
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
Module and object specific for "portals/portal" UDM module.
"""

from __future__ import absolute_import, unicode_literals
from ..encoders import (
	dn_property_encoder_for, dn_list_property_encoder_for, Base64BinaryPropertyEncoder, StringCaseInsensitiveResultUpperBooleanPropertyEncoder,
	ListOfListOflTextToDictPropertyEncoder,
)
from .generic import GenericModule, GenericObject, GenericObjectProperties


class PortalsPortalObjectProperties(GenericObjectProperties):
	"""portals/portal UDM properties."""

	_encoders = {
		'displayName': ListOfListOflTextToDictPropertyEncoder,
		'showApps': StringCaseInsensitiveResultUpperBooleanPropertyEncoder,
		'portalComputers': dn_list_property_encoder_for("auto"),
		'ensureLogin': StringCaseInsensitiveResultUpperBooleanPropertyEncoder,
		'anonymousEmpty': StringCaseInsensitiveResultUpperBooleanPropertyEncoder,
		'autoLayoutCategories': StringCaseInsensitiveResultUpperBooleanPropertyEncoder,
		'background': Base64BinaryPropertyEncoder,
		'logo': Base64BinaryPropertyEncoder,
		'menuLinks': dn_list_property_encoder_for("portals/entry"),
		'categories': dn_list_property_encoder_for("portals/category"),
	}


class PortalsPortalObject(GenericObject):
	"""Better representation of portals/portal properties."""
	udm_prop_class = PortalsPortalObjectProperties


class PortalsPortalModule(GenericModule):
	"""PortalsPortalObject factory"""
	_udm_object_class = PortalsPortalObject

	class Meta:
		supported_api_versions = [1, 2]
		suitable_for = ['portals/portal']


class PortalsCategoryObjectProperties(GenericObjectProperties):
	"""portals/category UDM properties."""

	_encoders = {
		'entries': dn_list_property_encoder_for("portals/entry"),
		'displayName': ListOfListOflTextToDictPropertyEncoder,
	}


class PortalsCategoryObject(GenericObject):
	"""Better representation of portals/category properties."""
	udm_prop_class = PortalsCategoryObjectProperties


class PortalsCategoryModule(GenericModule):
	"""PortalsCategoryObject factory"""
	_udm_object_class = PortalsCategoryObject

	class Meta:
		supported_api_versions = [1, 2]
		suitable_for = ['portals/category']


class PortalsPortalEntryObjectProperties(GenericObjectProperties):
	"""portals/portal_entry UDM properties."""

	_encoders = {
		'activated': StringCaseInsensitiveResultUpperBooleanPropertyEncoder,
		'description': ListOfListOflTextToDictPropertyEncoder,
		'displayName': ListOfListOflTextToDictPropertyEncoder,
		'icon': Base64BinaryPropertyEncoder,
		'portal': dn_list_property_encoder_for('portals/portal'),
		'allowedGroups': dn_list_property_encoder_for('groups/group'),
	}


class PortalsPortalEntryObject(GenericObject):
	"""Better representation of portals/portal_entry properties."""
	udm_prop_class = PortalsPortalEntryObjectProperties


class PortalsPortalEntryModule(GenericModule):
	"""PortalsPortalEntryObject factory"""
	_udm_object_class = PortalsPortalEntryObject

	class Meta:
		supported_api_versions = [1, 2, 3]
		suitable_for = ['portals/entry']
