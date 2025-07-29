#
# SPDX-FileCopyrightText: 2004-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""|UDM| module for |DHCP| hosts"""

from logging import getLogger

import univention.admin.filter
import univention.admin.handlers
import univention.admin.localization
from univention.admin.layout import Group, Tab

from .__common import DHCPBase, add_dhcp_options


log = getLogger('ADMIN')

translation = univention.admin.localization.translation('univention.admin.handlers.dhcp')
_ = translation.translate

module = 'dhcp/host'
operations = ['add', 'edit', 'remove', 'search']
superordinate = 'dhcp/service'
childs = False
short_description = _('DHCP: Host')
object_name = _('DHCP host')
object_name_plural = _('DHCP hosts')
long_description = _('Configure a host identified by its hardware MAC address.')
options = {
    'default': univention.admin.option(
        short_description=short_description,
        default=True,
        objectClasses=['top', 'univentionDhcpHost'],
    ),
}
property_descriptions = {
    'host': univention.admin.property(
        short_description=_('Hostname'),
        long_description=_('A unique name for this DHCP host entry. Using the hostname is recommended.'),
        syntax=univention.admin.syntax.string,
        include_in_default_search=True,
        required=True,
        identifies=True,
    ),
    'hwaddress': univention.admin.property(
        short_description=_('Hardware address'),
        long_description=_('Currently, only the ethernet and token-ring types are recognized. \
The hardware-address should be a set of hexadecimal octets (numbers from 0 through ff) separated by colons.'),
        syntax=univention.admin.syntax.DHCP_HardwareAddress,
        required=True,
    ),
    'fixedaddress': univention.admin.property(
        short_description=_('Fixed IP addresses'),
        long_description=_('Assign one or more fixed IP addresses. \
Each address should be either an IP address or a domain name that resolves to one or more IP addresses.'),
        syntax=univention.admin.syntax.hostOrIP,
        multivalue=True,
    ),
}
layout = [
    Tab(_('General'), _('Basic settings'), layout=[
        Group(_('General DHCP host settings'), layout=[
            'host',
            'hwaddress',
            'fixedaddress',
        ]),
    ]),
]


def unmapHWAddress(old, encoding=()):
    """

    >>> unmapHWAddress([b'ethernet 11:11:11:11:11:11'])
    ['ethernet', '11:11:11:11:11:11']
    >>> unmapHWAddress([])
    ['', '']
    """
    log.debug('host.py: unmapHWAddress: old: %s', old)
    if not old:
        return ['', '']
    return old[0].decode(*encoding).split(' ')


def mapHWAddress(old, encoding=()):
    """

    >>> mapHWAddress(['ethernet', '11:11:11:11:11:11'])
    b'ethernet 11:11:11:11:11:11'
    >>> mapHWAddress(['', ''])
    b''
    >>> mapHWAddress(['11:11:11:11:11:11'])
    b'11:11:11:11:11:11'
    >>> mapHWAddress('11:11:11:11:11:11')
    b'11:11:11:11:11:11'
    """
    log.debug('host.py: mapHWAddress: old: %s', old)
    if not isinstance(old, list):
        old = [old]
    if not old[0]:
        return b''

    if len(old) > 1:
        value = '%s %s' % (old[0], old[1])
        return value.encode(*encoding)

    return old[0].encode(*encoding)


mapping = univention.admin.mapping.mapping()
mapping.register('host', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('hwaddress', 'dhcpHWAddress', mapHWAddress, unmapHWAddress)
mapping.register('fixedaddress', 'univentionDhcpFixedAddress', encoding='ASCII')

add_dhcp_options(__name__)


class object(DHCPBase):
    module = module

    @classmethod
    def rewrite_filter(cls, filter, mapping):
        if filter.variable == 'hwaddress' and not isinstance(filter.value, list) and filter.value:
            # unmap() the value to a list so that the following rewrite_filter() map()s it
            filter.value = unmapHWAddress([filter.value.encode('UTF-8')])
        super().rewrite_filter(filter, mapping)


lookup_filter = object.lookup_filter
lookup = object.lookup
identify = object.identify
