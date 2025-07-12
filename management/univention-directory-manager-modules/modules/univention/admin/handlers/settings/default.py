# SPDX-FileCopyrightText: 2004-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""|UDM| module for default paths"""

import univention.admin.handlers
import univention.admin.localization
from univention.admin.layout import Group, Tab


translation = univention.admin.localization.translation('univention.admin.handlers.settings')
_ = translation.translate

module = 'settings/default'
superordinate = 'settings/cn'
childs = False
operations = ['search', 'edit']
short_description = _('Preferences: Default')
object_name = _('Default preference')
object_name_plural = _('Default preferences')
long_description = ''
# fmt: off
options = {
    'default': univention.admin.option(
        short_description=short_description,
        default=True,
        objectClasses=['top', 'univentionDefault'],
    ),
}
property_descriptions = {
    'name': univention.admin.property(
        short_description=_('Name'),
        long_description='',
        syntax=univention.admin.syntax.string,
        include_in_default_search=True,
        required=True,
        may_change=False,
        identifies=True,
        default=('univention', []),
        ldap_attribute='cn',
    ),
    'defaultGroup': univention.admin.property(
        short_description=_('Default Primary Group'),
        long_description='',
        syntax=univention.admin.syntax.GroupDN,
        dontsearch=True,
        required=True,
        ldap_attribute='univentionDefaultGroup',
    ),
    'defaultComputerGroup': univention.admin.property(
        short_description=_('Default Group for Computers'),
        long_description='',
        syntax=univention.admin.syntax.GroupDN,
        dontsearch=True,
        required=True,
        ldap_attribute='univentionDefaultComputerGroup',
    ),
    'defaultDomainControllerGroup': univention.admin.property(
        short_description=_('Default Group for Replica Directory Nodes'),
        long_description='',
        syntax=univention.admin.syntax.GroupDN,
        dontsearch=True,
        required=True,
        ldap_attribute='univentionDefaultDomainControllerGroup',
    ),
    'defaultDomainControllerMBGroup': univention.admin.property(
        short_description=_('Default Group for Primary and Backup Directory Nodes'),
        long_description='',
        syntax=univention.admin.syntax.GroupDN,
        dontsearch=True,
        required=True,
        ldap_attribute='univentionDefaultDomainControllerMasterGroup',
    ),
    'defaultMemberServerGroup': univention.admin.property(
        short_description=_('Default Group for Managed Nodes'),
        long_description='',
        syntax=univention.admin.syntax.GroupDN,
        dontsearch=True,
        required=True,
        ldap_attribute='univentionDefaultMemberserverGroup',
    ),
    'defaultClientGroup': univention.admin.property(
        short_description=_('Default Group for Client Computers'),
        long_description='',
        syntax=univention.admin.syntax.GroupDN,
        dontsearch=True,
        required=True,
        ldap_attribute='univentionDefaultClientGroup',
    ),
    'defaultKdeProfiles': univention.admin.property(
        short_description=_('Default KDE Profiles'),
        long_description='',
        syntax=univention.admin.syntax.string,
        multivalue=True,
        ldap_attribute='univentionDefaultKdeProfiles',
        encoding='ASCII',
    ),
}

layout = [
    Tab(_('General'), _('Basic values'), layout=[
        Group(_('Default settings description'), layout=[
            "name",
        ]),
    ]),
    Tab(_('Primary Groups'), _('Primary Groups'), layout=[
        Group(_('Primary Groups'), layout=[
            "defaultGroup",
            "defaultComputerGroup",
            "defaultDomainControllerMBGroup",
            "defaultDomainControllerGroup",
            "defaultMemberServerGroup",
            "defaultClientGroup",
        ]),
    ]),
    Tab(_('KDE Profiles'), _('KDE Profiles'), layout=[
        Group(_('KDE Profiles'), layout=[
            "defaultKdeProfiles",
        ]),
    ]),
]

mapping = univention.admin.mapping.mapping()
mapping.from_properties(property_descriptions)
# fmt: on


class object(univention.admin.handlers.simpleLdap):
    module = module

    def _ldap_dn(self):
        return 'cn=default containers,cn=univention,%s' % (self.position.getDomain())


lookup = object.lookup
lookup_filter = object.lookup_filter
identify = object.identify
