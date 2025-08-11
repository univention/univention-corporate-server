# SPDX-FileCopyrightText: 2018-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""Module and object specific for "nagios/service" UDM module."""


from ..encoders import DisabledPropertyEncoder, dn_list_property_encoder_for
from .generic import GenericModule, GenericObject, GenericObjectProperties


class NagiosServiceObjectProperties(GenericObjectProperties):
    """nagios/service UDM properties."""

    _encoders = {
        'assignedHosts': dn_list_property_encoder_for('auto'),  # can be different types of computer/* objects
        'useNRPE': DisabledPropertyEncoder,
    }


class NagiosServiceObject(GenericObject):
    """Better representation of nagios/service properties."""

    udm_prop_class = NagiosServiceObjectProperties


class NagiosServiceModule(GenericModule):
    """NagiosServiceObject factory"""

    _udm_object_class = NagiosServiceObject

    class Meta:
        supported_api_versions = [1, 2, 3]
        suitable_for = ['nagios/service']
