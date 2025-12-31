# SPDX-FileCopyrightText: 2018-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""Module and object specific for "policies/share_userquota" UDM module."""


from ..encoders import StringCaseInsensitiveResultUpperBooleanPropertyEncoder
from .generic import GenericModule, GenericObject, GenericObjectProperties


class PoliciesShareUserquotaObjectProperties(GenericObjectProperties):
    """policies/share_userquota UDM properties."""

    _encoders = {
        'reapplyeverylogin': StringCaseInsensitiveResultUpperBooleanPropertyEncoder,
    }


class PoliciesShareUserquotaObject(GenericObject):
    """Better representation of policies/share_userquota properties."""

    udm_prop_class = PoliciesShareUserquotaObjectProperties


class PoliciesShareUserquotaModule(GenericModule):
    """PoliciesShareUserquotaObject factory"""

    _udm_object_class = PoliciesShareUserquotaObject

    class Meta:
        supported_api_versions = [1, 2, 3]
        suitable_for = ['policies/share_userquota']
