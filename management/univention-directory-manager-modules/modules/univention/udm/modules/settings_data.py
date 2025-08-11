# SPDX-FileCopyrightText: 2018-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""Module and object specific for "settings/data" UDM module."""


from ..encoders import Base64Bzip2BinaryPropertyEncoder
from .generic import GenericModule, GenericObject, GenericObjectProperties


class SettingsDataObjectProperties(GenericObjectProperties):
    """settings/data UDM properties."""

    _encoders = {
        'data': Base64Bzip2BinaryPropertyEncoder,
    }


class SettingsDataObject(GenericObject):
    """Better representation of settings/data properties."""

    udm_prop_class = SettingsDataObjectProperties


class SettingsDataModule(GenericModule):
    """SettingsDataObject factory"""

    _udm_object_class = SettingsDataObject

    class Meta:
        supported_api_versions = [1, 2, 3]
        suitable_for = ['settings/data']
