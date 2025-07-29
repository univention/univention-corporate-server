#
# SPDX-FileCopyrightText: 2018-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""Module and object specific for "groups/group" UDM module."""


from ..encoders import (
    SambaGroupTypePropertyEncoder, StringIntBooleanPropertyEncoder, StringIntPropertyEncoder,
    dn_list_property_encoder_for,
)
from .generic import GenericModule, GenericObject, GenericObjectProperties


class GroupsGroupObjectProperties(GenericObjectProperties):
    """groups/group UDM properties."""

    _encoders = {
        'UVMMGroup': StringIntBooleanPropertyEncoder,
        'allowedEmailGroups': dn_list_property_encoder_for('groups/group'),
        'allowedEmailUsers': dn_list_property_encoder_for('users/user'),
        'gidNumber': StringIntPropertyEncoder,
        'hosts': dn_list_property_encoder_for('auto'),  # can be different types of computer/* objects
        'memberOf': dn_list_property_encoder_for('groups/group'),
        'nestedGroup': dn_list_property_encoder_for('groups/group'),
        'sambaGroupType': SambaGroupTypePropertyEncoder,
        'sambaRID': StringIntPropertyEncoder,
        'users': dn_list_property_encoder_for('users/user'),
    }


class GroupsGroupObject(GenericObject):
    """Better representation of groups/group properties."""

    udm_prop_class = GroupsGroupObjectProperties


class GroupsGroupModule(GenericModule):
    """GroupsGroupObject factory"""

    _udm_object_class = GroupsGroupObject

    class Meta:
        supported_api_versions = [1, 2, 3]
        suitable_for = ['groups/group']
        default_positions_property = 'groups'
