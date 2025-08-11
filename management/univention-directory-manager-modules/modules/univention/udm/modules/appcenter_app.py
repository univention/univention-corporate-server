# SPDX-FileCopyrightText: 2018-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""Module and object specific for "appcenter/app" UDM module."""


from ..encoders import Base64BinaryPropertyEncoder, MultiLanguageTextAppcenterPropertyEncoder
from .generic import GenericModule, GenericObject, GenericObjectProperties


class AppcenterAppObjectProperties(GenericObjectProperties):
    """appcenter/app UDM properties."""

    _encoders = {
        'icon': Base64BinaryPropertyEncoder,
        'longDescription': MultiLanguageTextAppcenterPropertyEncoder,
        'name': MultiLanguageTextAppcenterPropertyEncoder,
        'shortDescription': MultiLanguageTextAppcenterPropertyEncoder,
        'website': MultiLanguageTextAppcenterPropertyEncoder,
        'websiteVendor': MultiLanguageTextAppcenterPropertyEncoder,
    }


class AppcenterAppObject(GenericObject):
    """Better representation of appcenter/app properties."""

    udm_prop_class = AppcenterAppObjectProperties


class AppcenterAppModule(GenericModule):
    """AppcenterAppObject factory"""

    _udm_object_class = AppcenterAppObject

    class Meta:
        supported_api_versions = [1, 2, 3]
        suitable_for = ['appcenter/app']
