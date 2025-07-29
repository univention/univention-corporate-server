#
# SPDX-FileCopyrightText: 2018-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""
FOR TESTING PURPOSES ONLY!

Module and object specific for "users/ldap" UDM module.
"""


from ..encoders import DisabledPropertyEncoder
from .generic import GenericModule, GenericObject, GenericObjectProperties


class UsersLdapObjectProperties(GenericObjectProperties):
    """users/ldap UDM properties."""

    _encoders = {
        'disabled': DisabledPropertyEncoder,
    }


class UsersLdapObject(GenericObject):
    """Better representation of users/ldap properties."""

    udm_prop_class = UsersLdapObjectProperties


class UsersLdapModule(GenericModule):
    """UsersLdapObject factory"""

    _udm_object_class = UsersLdapObject

    class Meta:
        supported_api_versions = [1, 2, 3]
        suitable_for = ['users/ldap']
