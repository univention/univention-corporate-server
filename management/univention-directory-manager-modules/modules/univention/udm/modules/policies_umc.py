# SPDX-FileCopyrightText: 2018-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""Module and object specific for "policies/umc" UDM module."""


from ..encoders import dn_list_property_encoder_for
from .generic import GenericModule, GenericObject, GenericObjectProperties


class PoliciesUmcObjectProperties(GenericObjectProperties):
    """policies/umc UDM properties."""

    _encoders = {
        'allow': dn_list_property_encoder_for('settings/umc_operationset'),
    }


class PoliciesUmcObject(GenericObject):
    """Better representation of policies/umc properties."""

    udm_prop_class = PoliciesUmcObjectProperties


class PoliciesUmcModule(GenericModule):
    """PoliciesUmcObject factory"""

    _udm_object_class = PoliciesUmcObject

    class Meta:
        supported_api_versions = [1, 2, 3]
        suitable_for = ['policies/umc']
