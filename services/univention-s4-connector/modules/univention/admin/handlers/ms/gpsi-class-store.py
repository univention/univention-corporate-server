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

module = 'ms/gpsi-class-store'
operations = ['add', 'edit', 'remove', 'search', 'move', 'subtree_move']
childs = True
short_description = _('Software Installation Group Policy: Class Store')
long_description = ''
options = {
    'default': univention.admin.option(
        short_description=short_description,
        default=True,
        objectClasses=['classStore', 'top'],
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
    'displayName': univention.admin.property(
        short_description=_('Display name'),
        long_description='',
        syntax=univention.admin.syntax.string,
    ),
    'description': univention.admin.property(
        short_description=_('Description'),
        long_description='',
        syntax=univention.admin.syntax.string,
    ),
    'versionNumber': univention.admin.property(
        short_description=_('Version number'),
        long_description='',
        syntax=univention.admin.syntax.integer,
    ),
    'nextLevelStore': univention.admin.property(
        short_description=_('Next level store'),
        long_description='',
        syntax=univention.admin.syntax.string,
    ),
    'lastUpdateSequence': univention.admin.property(
        short_description=_('Last update sequence'),
        long_description='',
        syntax=univention.admin.syntax.string,
    ),
    'extensionName': univention.admin.property(
        short_description=_('Extension name'),
        long_description='',
        syntax=univention.admin.syntax.string,
        multivalue=True,
    ),
    'appSchemaVersion': univention.admin.property(
        short_description=_('App schema version'),
        long_description='',
        syntax=univention.admin.syntax.integer,
    ),
}

layout = [
    Tab(_('General'), _('Basic settings'), layout=[
        Group(_('General'), layout=[
            ["name", "displayName"],
            ["description"],
            'versionNumber',
            'nextLevelStore',
            'lastUpdateSequence',
            'extensionName',
            'appSchemaVersion',
        ]),
    ]),
]

mapping = univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('displayName', 'displayName', None, univention.admin.mapping.ListToString)
mapping.register('description', 'description', None, univention.admin.mapping.ListToString)
mapping.register('versionNumber', 'versionNumber', None, univention.admin.mapping.ListToString)
mapping.register('nextLevelStore', 'nextLevelStore', None, univention.admin.mapping.ListToString)
mapping.register('lastUpdateSequence', 'lastUpdateSequence', None, univention.admin.mapping.ListToString)
mapping.register('extensionName', 'extensionName')
mapping.register('appSchemaVersion', 'appSchemaVersion', None, univention.admin.mapping.ListToString)


class object(univention.admin.handlers.simpleLdap):
    module = module

    def _ldap_pre_modify(self):
        if self.hasChanged('name'):
            self.move(self._ldap_dn())


identify = object.identify
lookup = object.lookup
