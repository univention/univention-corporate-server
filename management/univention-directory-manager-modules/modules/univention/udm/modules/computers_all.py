#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# SPDX-FileCopyrightText: 2018-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

r"""Module and object for all `computers/\*` UDM modules."""


from ..encoders import (
    CnameListPropertyEncoder, DnsEntryZoneAliasListPropertyEncoder, DnsEntryZoneForwardListMultiplePropertyEncoder,
    DnsEntryZoneReverseListMultiplePropertyEncoder, StringIntBooleanPropertyEncoder, StringIntPropertyEncoder,
    dn_list_property_encoder_for, dn_property_encoder_for,
)
from .generic import GenericModule, GenericObject, GenericObjectProperties


class ComputersAllObjectProperties(GenericObjectProperties):
    r"""`computers/\*` UDM properties."""

    _encoders = {
        'dnsAlias': CnameListPropertyEncoder,  # What is this? Isn't this data in dnsEntryZoneAlias already?
        'dnsEntryZoneAlias': DnsEntryZoneAliasListPropertyEncoder,
        'dnsEntryZoneForward': DnsEntryZoneForwardListMultiplePropertyEncoder,
        'dnsEntryZoneReverse': DnsEntryZoneReverseListMultiplePropertyEncoder,
        'groups': dn_list_property_encoder_for('groups/group'),
        'nagiosServices': dn_list_property_encoder_for('nagios/service'),
        'network': dn_property_encoder_for('networks/network'),
        'primaryGroup': dn_property_encoder_for('groups/group'),
        'reinstall': StringIntBooleanPropertyEncoder,
        'sambaRID': StringIntPropertyEncoder,
    }


class ComputersAllObject(GenericObject):
    r"""Better representation of `computers/\*` properties."""

    udm_prop_class = ComputersAllObjectProperties


class ComputersAllModule(GenericModule):
    """ComputersAllObject factory"""

    _udm_object_class = ComputersAllObject

    class Meta:
        supported_api_versions = [1, 2, 3]
        default_positions_property = 'computers'
        suitable_for = ['computers/*']


class ComputersDCModule(ComputersAllModule):
    """ComputersAllObject factory with an adjusted default position"""

    class Meta:
        supported_api_versions = [1, 2, 3]
        default_positions_property = 'domaincontroller'
        suitable_for = ['computers/domaincontroller_master', 'computers/domaincontroller_backup', 'computers/domaincontroller_slave']


class ComputersMemberModule(ComputersAllModule):
    """ComputersAllObject factory with an adjusted default position"""

    def _get_default_object_positions(self) -> list[str]:
        ret = super()._get_default_object_positions()
        if f'cn=computers,{self.connection.base}' in ret and \
                f'cn=memberserver,cn=computers,{self.connection.base}' in ret and \
                f'cn=dc,cn=computers,{self.connection.base}' in ret and \
                self.connection.base in ret:
            ret.remove(f'cn=memberserver,cn=computers,{self.connection.base}')
            ret.insert(0, f'cn=memberserver,cn=computers,{self.connection.base}')
        return ret

    class Meta:
        supported_api_versions = [1, 2, 3]
        default_positions_property = 'computers'
        suitable_for = ['computers/memberserver']
