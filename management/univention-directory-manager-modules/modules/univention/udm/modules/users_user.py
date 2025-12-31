# SPDX-FileCopyrightText: 2018-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""Module and object specific for "users/user" UDM module."""


from ..encoders import (
    Base64BinaryPropertyEncoder, DatePropertyEncoder, DisabledPropertyEncoder, HomePostalAddressPropertyEncoder,
    SambaLogonHoursPropertyEncoder, StringIntPropertyEncoder, dn_list_property_encoder_for, dn_property_encoder_for,
)
from .generic import GenericModule, GenericObject, GenericObjectProperties


class UsersUserObjectProperties(GenericObjectProperties):
    """users/user UDM properties."""

    _encoders = {
        'birthday': DatePropertyEncoder,
        'disabled': DisabledPropertyEncoder,
        'gidNumber': StringIntPropertyEncoder,
        'groups': dn_list_property_encoder_for('groups/group'),
        'homePostalAddress': HomePostalAddressPropertyEncoder,
        'jpegPhoto': Base64BinaryPropertyEncoder,
        'mailForwardCopyToSelf': DisabledPropertyEncoder,
        'mailUserQuota': StringIntPropertyEncoder,
        'primaryGroup': dn_property_encoder_for('groups/group'),
        'sambaLogonHours': SambaLogonHoursPropertyEncoder,
        'sambaRID': StringIntPropertyEncoder,
        'secretary': dn_list_property_encoder_for('users/user'),
        'uidNumber': StringIntPropertyEncoder,
        'userexpiry': DatePropertyEncoder,
    }


class UsersUserObject(GenericObject):
    """Better representation of users/user properties."""

    udm_prop_class = UsersUserObjectProperties


class UsersUserModule(GenericModule):
    """UsersUserObject factory"""

    _udm_object_class = UsersUserObject

    class Meta:
        supported_api_versions = [1, 2, 3]
        suitable_for = ['users/user']
        default_positions_property = 'users'
