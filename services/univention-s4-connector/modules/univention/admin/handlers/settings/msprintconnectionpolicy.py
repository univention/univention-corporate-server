#
# Univention S4 Connector
#  UDM module for msPrint-ConnectionPolicy
#
# SPDX-FileCopyrightText: 2012-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import univention.admin.handlers
import univention.admin.localization
import univention.admin.syntax
from univention.admin.layout import Tab


translation = univention.admin.localization.translation('univention.admin.handlers.settings.msprintconnectionpolicy')
_ = translation.translate

module = 'settings/msprintconnectionpolicy'
operations = ['add', 'edit', 'remove', 'search', 'move', 'subtree_move']
childs = True
short_description = _('Settings: MS Print Connection Policy')
long_description = ''
# fmt: off
options = {
    'default': univention.admin.option(
        short_description=short_description,
        default=True,
        objectClasses=['msPrintConnectionPolicy', 'top'],
    ),
}
property_descriptions = {
    'name': univention.admin.property(
        short_description=_('Name'),
        long_description='',
        syntax=univention.admin.syntax.string,
        required=True,
        identifies=True,
    ),
    'description': univention.admin.property(
        short_description=_('Description'),
        long_description='',
        syntax=univention.admin.syntax.string,
    ),
    'displayName': univention.admin.property(
        short_description=_('Display name'),
        long_description='',
        syntax=univention.admin.syntax.string,
    ),
    'msPrintAttributes': univention.admin.property(
        short_description=_('Print attributes'),
        long_description=_('A bitmask of printer attributes.'),
        syntax=univention.admin.syntax.integer,
    ),
    'msPrinterName': univention.admin.property(
        short_description=_('Printer name'),
        long_description=_('The display name of an attached printer.'),
        syntax=univention.admin.syntax.string,
    ),
    'msPrintServerName': univention.admin.property(
        short_description=_('Server name'),
        long_description=_('The name of a server.'),
        syntax=univention.admin.syntax.string,
    ),
    'msPrintUNCName': univention.admin.property(
        short_description=_('UNC name'),
        long_description=_('The universal naming convention name for shared volumes and printers.'),
        syntax=univention.admin.syntax.string,
    ),
}

layout = [
    Tab(_('General'), _('Basic settings'), layout=[
        ['name'],
        ['description'],
        ['displayName'],
    ]),
    Tab(_('Printer connection settings'), advanced=True, layout=[
        ['msPrintAttributes'],
        ['msPrinterName'],
        ['msPrintServerName'],
        ['msPrintUNCName'],
    ]),
]

mapping = univention.admin.mapping.mapping()
mapping.register('description', 'description', None, univention.admin.mapping.ListToString)
mapping.register('displayName', 'displayName', None, univention.admin.mapping.ListToString)
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('msPrintAttributes', 'msPrintAttributes', None, univention.admin.mapping.ListToString)
mapping.register('msPrinterName', 'msPrinterName', None, univention.admin.mapping.ListToString)
mapping.register('msPrintServerName', 'msPrintServerName', None, univention.admin.mapping.ListToString)
mapping.register('msPrintUNCName', 'msPrintUNCName', None, univention.admin.mapping.ListToString)
# fmt: on


class object(univention.admin.handlers.simpleLdap):
    module = module

    def _ldap_pre_modify(self):
        if self.hasChanged('name'):
            self.move(self._ldap_dn())


identify = object.identify
lookup = object.lookup
