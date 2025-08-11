# SPDX-FileCopyrightText: 2018-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""Module and object specific for "policies/registry" UDM module."""


from ..encoders import ListOfListOflTextToDictPropertyEncoder
from .generic import GenericModule, GenericObject, GenericObjectProperties


class PoliciesRegistryObjectProperties(GenericObjectProperties):
    """policies/registry UDM properties."""

    _encoders = {
        'registry': ListOfListOflTextToDictPropertyEncoder,
    }


class PoliciesRegistryObject(GenericObject):
    """Better representation of policies/registry properties."""

    udm_prop_class = PoliciesRegistryObjectProperties


class PoliciesRegistryModule(GenericModule):
    """PoliciesRegistryObject factory"""

    _udm_object_class = PoliciesRegistryObject

    class Meta:
        supported_api_versions = [1, 2, 3]
        suitable_for = ['policies/registry']
