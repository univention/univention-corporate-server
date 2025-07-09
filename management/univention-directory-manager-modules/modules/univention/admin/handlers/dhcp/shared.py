#
# SPDX-FileCopyrightText: 2004-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""|UDM| module for the |DHCP| shared networks"""

import univention.admin.filter
import univention.admin.handlers
import univention.admin.localization
from univention.admin.layout import Group, Tab

from .__common import DHCPBase, add_dhcp_options


translation = univention.admin.localization.translation('univention.admin.handlers.dhcp')
_ = translation.translate

module = 'dhcp/shared'
operations = ['add', 'edit', 'remove', 'search']
superordinate = 'dhcp/service'
childs = True
childmodules = ('dhcp/sharedsubnet',)
short_description = _('DHCP: Shared network')
object_name = _('Shared network')
object_name_plural = _('Shared network')
long_description = _('A shared physical network, where multiple IP address ranges are used.')
# fmt: off
options = {
    'default': univention.admin.option(
        short_description=short_description,
        default=True,
        objectClasses=['top', 'dhcpSharedNetwork'],
    ),
}
property_descriptions = {
    'name': univention.admin.property(
        short_description=_('Shared network name'),
        long_description=_('A unique name for this shared network.'),
        syntax=univention.admin.syntax.uid,
        include_in_default_search=True,
        required=True,
        may_change=False,
        identifies=True,
    ),
}

layout = [
    Tab(_('General'), _('Basic settings'), layout=[
        Group(_('DHCP shared network description'), layout=[
            'name',
        ]),
    ]),
]

mapping = univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
# fmt: on

add_dhcp_options(__name__)


class object(DHCPBase):
    module = module


lookup_filter = object.lookup_filter
lookup = object.lookup
identify = object.identify
