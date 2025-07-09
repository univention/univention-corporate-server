# SPDX-FileCopyrightText: 2004-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""|UDM| module for |DHCP| services"""

from __future__ import annotations

import univention.admin.filter
import univention.admin.handlers
import univention.admin.localization
from univention.admin.layout import Group, Tab

from .__common import DHCPBase, add_dhcp_options


translation = univention.admin.localization.translation('univention.admin.handlers.dhcp')
_ = translation.translate

module = 'dhcp/service'
operations = ['add', 'edit', 'remove', 'search']
childs = True
childmodules = ('dhcp/host', 'dhcp/server', 'dhcp/shared', 'dhcp/subnet')
short_description = _('DHCP: Service')
object_name = _('DHCP service')
object_name_plural = _('DHCP services')
long_description = _('The top-level container for a DHCP configuration.')
# fmt: off
options = {
    'default': univention.admin.option(
        short_description=short_description,
        default=True,
        objectClasses=['top', 'univentionDhcpService'],
    ),
}
property_descriptions = {
    'service': univention.admin.property(
        short_description=_('Service name'),
        long_description=_('A unique name for this DHCP service.'),
        syntax=univention.admin.syntax.string,
        include_in_default_search=True,
        required=True,
        may_change=False,
        identifies=True,
    ),
}

layout = [
    Tab(_('General'), _('Basic settings'), layout=[
        Group(_('DHCP service description'), layout=[
            'service',
        ]),
    ]),
]

mapping = univention.admin.mapping.mapping()
mapping.register('service', 'cn', None, univention.admin.mapping.ListToString)
# fmt: on

add_dhcp_options(__name__)


class object(DHCPBase):
    module = module

    def __init__(
        self,
        co: None,
        lo: univention.admin.uldap.access,
        position: univention.admin.uldap.position | None,
        dn: str = '',
        superordinate: univention.admin.handlers.simpleLdap | None = None,
        attributes: univention.admin.handlers._Attributes | None = None,
    ) -> None:
        univention.admin.handlers.simpleLdap.__init__(self, co, lo, position, dn, superordinate, attributes=attributes)
        if not self.dn and not self.position:
            raise univention.admin.uexceptions.insufficientInformation(_('Neither DN nor position given.'))

    @staticmethod
    def unmapped_lookup_filter() -> univention.admin.filter.conjunction:
        return univention.admin.filter.conjunction('&', [
            univention.admin.filter.conjunction('|', [
                univention.admin.filter.expression('objectClass', 'dhcpService'),
                univention.admin.filter.expression('objectClass', 'univentionDhcpService'),
            ]),
        ])  # fmt: skip


def identify(dn: str, attr: univention.admin.handlers._Attributes) -> bool:
    return b'dhcpService' in attr.get('objectClass', []) \
        or b'univentionDhcpService' in attr.get('objectClass', [])


lookup_filter = object.lookup_filter
lookup = object.lookup
