# SPDX-FileCopyrightText: 2018-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""Module and object specific for "container/dc" UDM module."""


from ..encoders import DnsEntryZoneForwardListSinglePropertyEncoder, DnsEntryZoneReverseListSinglePropertyEncoder
from .generic import GenericModule, GenericObject, GenericObjectProperties


class ContainerDcObjectProperties(GenericObjectProperties):
    """container/dc UDM properties."""

    _encoders = {
        'dnsForwardZone': DnsEntryZoneForwardListSinglePropertyEncoder,
        'dnsReverseZone': DnsEntryZoneReverseListSinglePropertyEncoder,
    }


class ContainerDcObject(GenericObject):
    """Better representation of container/dc properties."""

    udm_prop_class = ContainerDcObjectProperties


class ContainerDcModule(GenericModule):
    """ContainerDcObject factory"""

    _udm_object_class = ContainerDcObject

    class Meta:
        supported_api_versions = [1, 2, 3]
        suitable_for = ['containers/dc']
