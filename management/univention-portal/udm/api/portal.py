# -*- coding: utf-8 -*-
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2018-2022 Univention GmbH
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
	dn_list_property_encoder_for, Base64BinaryPropertyEncoder, StringCaseInsensitiveResultUpperBooleanPropertyEncoder,
	ListOfListOflTextToDictPropertyEncoder, BaseEncoder
)
from .generic import GenericModule, GenericObject, GenericObjectProperties


class ListOfListOflTextToListofDictPropertyEncoder(BaseEncoder):
	static = True

	@staticmethod
	def decode(value=None):
		if value:
			return [{'locale': v[0], 'value': v[1]} for v in value]
		else:
			return value

	@staticmethod
	def encode(value=None):
		if value:
			return [[v['locale'], v['value']] for v in value]
		else:
			return value


class PortalsPortalObjectProperties(GenericObjectProperties):
	"""portals/portal UDM properties."""

	_encoders = {
		'displayName': ListOfListOflTextToDictPropertyEncoder,
		'showUmc': StringCaseInsensitiveResultUpperBooleanPropertyEncoder,
		'background': Base64BinaryPropertyEncoder,
		'logo': Base64BinaryPropertyEncoder,
		'ensureLogin': StringCaseInsensitiveResultUpperBooleanPropertyEncoder,
		'userLinks': dn_list_property_encoder_for("auto"),
		'menuLinks': dn_list_property_encoder_for("auto"),
		'categories': dn_list_property_encoder_for("portals/category"),
	}


class PortalsPortalObject(GenericObject):
	"""Better representation of portals/portal properties."""
	udm_prop_class = PortalsPortalObjectProperties


class PortalsPortalModule(GenericModule):
	"""PortalsPortalObject factory"""
	_udm_object_class = PortalsPortalObject

	class Meta:
		supported_api_versions = [1, 2, 3]
		suitable_for = ['portals/portal']


class PortalsCategoryObjectProperties(GenericObjectProperties):
	"""portals/category UDM properties."""

	_encoders = {
		'entries': dn_list_property_encoder_for("auto"),
		'displayName': ListOfListOflTextToDictPropertyEncoder,
	}


class PortalsCategoryObject(GenericObject):
	"""Better representation of portals/category properties."""
	udm_prop_class = PortalsCategoryObjectProperties


class PortalsCategoryModule(GenericModule):
	"""PortalsCategoryObject factory"""
	_udm_object_class = PortalsCategoryObject

	class Meta:
		supported_api_versions = [1, 2, 3]
		suitable_for = ['portals/category']


class PortalsPortalEntryObjectProperties(GenericObjectProperties):
	"""portals/entry UDM properties."""

	_encoders = {
		'activated': StringCaseInsensitiveResultUpperBooleanPropertyEncoder,
		'anonymous': StringCaseInsensitiveResultUpperBooleanPropertyEncoder,
		'description': ListOfListOflTextToDictPropertyEncoder,
		'keywords': ListOfListOflTextToDictPropertyEncoder,
		'displayName': ListOfListOflTextToDictPropertyEncoder,
		'link': ListOfListOflTextToListofDictPropertyEncoder,
		'icon': Base64BinaryPropertyEncoder,
		'portal': dn_list_property_encoder_for('portals/portal'),
		'allowedGroups': dn_list_property_encoder_for('groups/group'),
	}


class PortalsPortalEntryObject(GenericObject):
	"""Better representation of portals/entry properties."""
	udm_prop_class = PortalsPortalEntryObjectProperties


class PortalsPortalEntryModule(GenericModule):
	"""PortalsPortalEntryObject factory"""
	_udm_object_class = PortalsPortalEntryObject

	class Meta:
		supported_api_versions = [1, 2, 3]
		suitable_for = ['portals/entry']


class PortalsPortalFolderObjectProperties(GenericObjectProperties):
	"""portals/folder UDM properties."""

	_encoders = {
		'displayName': ListOfListOflTextToDictPropertyEncoder,
		'entries': dn_list_property_encoder_for("auto"),
	}


class PortalsPortalFolderObject(GenericObject):
	"""Better representation of portals/folder properties."""
	udm_prop_class = PortalsPortalFolderObjectProperties


class PortalsPortalFolderModule(GenericModule):
	"""PortalsPortalFolderObject factory"""
	_udm_object_class = PortalsPortalFolderObject

	class Meta:
		supported_api_versions = [1, 2, 3]
		suitable_for = ['portals/folder']
