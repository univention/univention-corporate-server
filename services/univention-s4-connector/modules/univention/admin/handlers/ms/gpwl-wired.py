#
# Univention S4 Connector
#  UDM module for XML-based wired Group Policy
#
# SPDX-FileCopyrightText: 2019-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import univention.admin.handlers
import univention.admin.localization
import univention.admin.syntax
from univention.admin.layout import Group, Tab


translation = univention.admin.localization.translation('univention.admin.handlers.ms')
_ = translation.translate

module = 'ms/gpwl-wired'
operations = ['add', 'edit', 'remove', 'search', 'move', 'subtree_move']
childs = True
short_description = _('MS wired Group Policy')
long_description = ''
# fmt: off
options = {
    'default': univention.admin.option(
        short_description=short_description,
        default=True,
        objectClasses=['ms-net-ieee-8023-GroupPolicy', 'top'],
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
    'ms-net-ieee-8023-GP-PolicyReserved': univention.admin.property(
        short_description=_('Policy Reserved'),
        long_description='',
        syntax=univention.admin.syntax.TextArea,
    ),
    'ms-net-ieee-8023-GP-PolicyData': univention.admin.property(
        short_description=_('Policy Data'),
        long_description='',
        syntax=univention.admin.syntax.TextArea,
        size='Two',
    ),
    'ms-net-ieee-8023-GP-PolicyGUID': univention.admin.property(
        short_description=_('Policy GUID'),
        long_description='',
        syntax=univention.admin.syntax.string,
    ),
}

layout = [
    Tab(_('General'), _('Basic settings'), layout=[
        Group(_('General'), layout=[
            ["name", "description"],
        ]),
        Group(_('Policy settings'), layout=[
            "ms-net-ieee-8023-GP-PolicyGUID",
            'ms-net-ieee-8023-GP-PolicyData',
            "ms-net-ieee-8023-GP-PolicyReserved",
        ]),
    ]),
]

mapping = univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('description', 'description', None, univention.admin.mapping.ListToString)
mapping.register('ms-net-ieee-8023-GP-PolicyReserved', 'ms-net-ieee-8023-GP-PolicyReserved', univention.admin.mapping.mapBase64, univention.admin.mapping.unmapBase64)
mapping.register('ms-net-ieee-8023-GP-PolicyData', 'ms-net-ieee-8023-GP-PolicyData', None, univention.admin.mapping.ListToString)
mapping.register('ms-net-ieee-8023-GP-PolicyGUID', 'ms-net-ieee-8023-GP-PolicyGUID', None, univention.admin.mapping.ListToString)
# fmt: on


class object(univention.admin.handlers.simpleLdap):
    module = module

    def _ldap_pre_modify(self):
        if self.hasChanged('name'):
            self.move(self._ldap_dn())


identify = object.identify
lookup = object.lookup
