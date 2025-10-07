#
# Univention S4 Connector
#  UDM module for BLOB-based wireless Group Policy
#
# SPDX-FileCopyrightText: 2019-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import univention.admin.handlers
import univention.admin.localization
import univention.admin.syntax
from univention.admin.layout import Group, Tab


translation = univention.admin.localization.translation('univention.admin.handlers.ms')
_ = translation.translate

module = 'ms/gpwl-wireless-blob'
operations = ['add', 'edit', 'remove', 'search', 'move', 'subtree_move']
childs = True
short_description = _('MS wireless Group Policy blob')
long_description = ''
# fmt: off
options = {
    'default': univention.admin.option(
        short_description=short_description,
        default=True,
        objectClasses=['msieee80211-Policy', 'top'],
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
    'msieee80211-ID': univention.admin.property(
        short_description=_('ID'),
        long_description='',
        syntax=univention.admin.syntax.string,
    ),
    'msieee80211-DataType': univention.admin.property(
        short_description=_('Data type'),
        long_description='',
        syntax=univention.admin.syntax.integer,
    ),
    'msieee80211-Data': univention.admin.property(
        short_description=_('Data'),
        long_description='',
        syntax=univention.admin.syntax.TextArea,
        size='Two',
    ),
}

layout = [
    Tab(_('General'), _('Basic settings'), layout=[
        Group(_('General'), layout=[
            ["name", "description"],
        ]),
        Group(_('Policy settings'), layout=[
            'msieee80211-ID',
            'msieee80211-DataType',
            'msieee80211-Data',
        ]),
    ]),
]

mapping = univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('description', 'description', None, univention.admin.mapping.ListToString)
mapping.register('msieee80211-ID', 'msieee80211-ID', None, univention.admin.mapping.ListToString)
mapping.register('msieee80211-DataType', 'msieee80211-DataType', None, univention.admin.mapping.ListToString)
mapping.register('msieee80211-Data', 'msieee80211-Data', univention.admin.mapping.mapBase64, univention.admin.mapping.unmapBase64)
# fmt: on


class object(univention.admin.handlers.simpleLdap):
    module = module

    def _ldap_pre_modify(self):
        if self.hasChanged('name'):
            self.move(self._ldap_dn())


identify = object.identify
lookup = object.lookup
