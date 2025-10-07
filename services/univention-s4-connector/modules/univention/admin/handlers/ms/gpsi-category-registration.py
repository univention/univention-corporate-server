#
# Univention S4 Connector
#  UDM module for Software Installation Group Policy
#
# SPDX-FileCopyrightText: 2019-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import univention.admin.handlers
import univention.admin.localization
import univention.admin.syntax
from univention.admin.layout import Group, Tab


translation = univention.admin.localization.translation('univention.admin.handlers.ms')
_ = translation.translate

module = 'ms/gpsi-category-registration'
operations = ['add', 'edit', 'remove', 'search', 'move', 'subtree_move']
childs = True
short_description = _('MS Software Installation Group Policy: Category Registration')
long_description = ''
# fmt: off
options = {
    'default': univention.admin.option(
        short_description=short_description,
        default=True,
        objectClasses=['categoryRegistration', 'leaf'],
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
    'managedBy': univention.admin.property(
        short_description=_('managed by'),
        long_description='',
        syntax=univention.admin.syntax.string,
    ),
    'localizedDescription': univention.admin.property(
        short_description=_('localized description'),
        long_description='',
        multivalue=True,
        syntax=univention.admin.syntax.string,
    ),
    'localeID': univention.admin.property(
        short_description=_('locale ID'),
        long_description='',
        multivalue=True,
        syntax=univention.admin.syntax.integer,
    ),
    'categoryId': univention.admin.property(
        short_description=_('category ID'),
        long_description='',
        syntax=univention.admin.syntax.TextArea,
    ),
}

layout = [
    Tab(_('General'), _('Basic settings'), layout=[
        Group(_('General'), layout=[
            ["name", "description"],
            'managedBy',
            'localizedDescription',
            'localeID',
            'categoryId',
        ]),
    ]),
]

mapping = univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('description', 'description', None, univention.admin.mapping.ListToString)
mapping.register('managedBy', 'managedBy', None, univention.admin.mapping.ListToString)
mapping.register('localizedDescription', 'localizedDescription')
mapping.register('localeID', 'localeID')
mapping.register('categoryId', 'categoryId', univention.admin.mapping.mapBase64, univention.admin.mapping.unmapBase64)
# fmt: on


class object(univention.admin.handlers.simpleLdap):
    module = module

    def _ldap_pre_modify(self):
        if self.hasChanged('name'):
            self.move(self._ldap_dn())


identify = object.identify
lookup = object.lookup
