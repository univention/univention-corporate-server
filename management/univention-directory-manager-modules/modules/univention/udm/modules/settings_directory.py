# SPDX-FileCopyrightText: 2018-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""Module and object specific for "settings/directory" UDM module."""


from ..encoders import dn_list_property_encoder_for
from .generic import GenericModule, GenericObject, GenericObjectProperties


class SettingsDirectoryObjectProperties(GenericObjectProperties):
    """settings/directory UDM properties."""

    _encoders = {
        'computers': dn_list_property_encoder_for('container/cn'),
        'dhcp': dn_list_property_encoder_for('container/cn'),
        'dns': dn_list_property_encoder_for('container/cn'),
        'groups': dn_list_property_encoder_for('container/cn'),
        'license': dn_list_property_encoder_for('container/cn'),
        'mail': dn_list_property_encoder_for('container/cn'),
        'networks': dn_list_property_encoder_for('container/cn'),
        'policies': dn_list_property_encoder_for('auto'),
        'printers': dn_list_property_encoder_for('container/cn'),
        'shares': dn_list_property_encoder_for('container/cn'),
        'users': dn_list_property_encoder_for('container/cn'),
    }


class SettingsDirectoryObject(GenericObject):
    """Better representation of settings/directory properties."""

    udm_prop_class = SettingsDirectoryObjectProperties


class SettingsDirectoryModule(GenericModule):
    """SettingsDirectoryObject factory"""

    _udm_object_class = SettingsDirectoryObject

    class Meta:
        supported_api_versions = [1, 2, 3]
        suitable_for = ['settings/directory']
