# SPDX-FileCopyrightText: 2018-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""Module and object specific for "portals/portal" UDM module."""


from ..encoders import (
    Base64BinaryPropertyEncoder, BaseEncoder, DatePropertyEncoder, ListOfListOflTextToDictPropertyEncoder,
    StringCaseInsensitiveResultUpperBooleanPropertyEncoder, dn_list_property_encoder_for,
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
        'announcements': dn_list_property_encoder_for("portals/announcement"),
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


class PortalsPortalAnnouncementObjectProperties(GenericObjectProperties):
    """portals/announcement UDM properties."""

    _encoders = {
        'allowedGroups': dn_list_property_encoder_for('groups/group'),
        'needsConfirmation': StringCaseInsensitiveResultUpperBooleanPropertyEncoder,
        'isSticky': StringCaseInsensitiveResultUpperBooleanPropertyEncoder,
        'title': ListOfListOflTextToDictPropertyEncoder,
        'message': ListOfListOflTextToDictPropertyEncoder,
        'visibleFrom': DatePropertyEncoder,
        'visibleUntil': DatePropertyEncoder,
    }


class PortalsPortalAnnouncementObject(GenericObject):
    """Better representation of portals/announcement properties."""

    udm_prop_class = PortalsPortalAnnouncementObjectProperties


class PortalsPortalAnnouncementModule(GenericModule):
    """PortalsPortalAnnouncementObject factory"""

    _udm_object_class = PortalsPortalAnnouncementObject

    class Meta:
        supported_api_versions = [1, 2, 3]
        suitable_for = ['portals/announcement']
