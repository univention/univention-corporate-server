# SPDX-FileCopyrightText: 2004-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only


"""|UDM| module for the Domain Component containers"""

import univention.admin.filter
import univention.admin.handlers
import univention.admin.localization
from univention.admin import configRegistry
from univention.admin.layout import Group, Tab


translation = univention.admin.localization.translation('univention.admin.handlers.container')
_ = translation.translate


# Note: this is not a "objectClass: domain" container but only the ldap base!
module = 'container/dc'
childs = True
operations = ['search', 'edit']
short_description = _('Container: Domain')
object_name = _('Domain Container')
object_name_plural = _('Domain Containers')
long_description = ''
# fmt: off
options = {
    'default': univention.admin.option(
        short_description=short_description,
        default=True,
        objectClasses=['top', 'univentionBase'],
    ),
    'kerberos': univention.admin.option(
        short_description=_('Kerberos realm'),
        objectClasses=['krb5Realm'],
        default=True,
    ),
    'samba': univention.admin.option(
        short_description=_('Samba'),
        objectClasses=['sambaDomain'],
        default=True,
    ),
    'group-settings': univention.admin.option(
        short_description=_('Default Group Settings'),
        objectClasses=['univentionContainerDefault'],
        default=False,
        editable=True,
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
        ldap_attribute='dc',
    ),
    'dnsForwardZone': univention.admin.property(
        short_description=_('DNS forward lookup zone'),
        long_description='',
        syntax=univention.admin.syntax.DNS_ForwardZone,
        multivalue=True,
        may_change=False,
    ),
    'dnsReverseZone': univention.admin.property(
        short_description=_('DNS reverse lookup zone'),
        long_description='',
        syntax=univention.admin.syntax.DNS_ReverseZone,
        multivalue=True,
        may_change=False,
    ),
    'sambaDomainName': univention.admin.property(
        short_description=_('Samba domain name'),
        long_description='',
        syntax=univention.admin.syntax.string,
        multivalue=True,
        options=['samba'],
        required=True,
        default=(configRegistry.get('domainname', '').upper(), []),
        ldap_attribute='sambaDomainName',
    ),
    'sambaSID': univention.admin.property(
        short_description=_('Samba SID'),
        long_description='',
        syntax=univention.admin.syntax.string,
        options=['samba'],
        required=True,
        may_change=False,
        ldap_attribute='sambaSID',
        encoding='ASCII',
    ),
    'sambaNextUserRid': univention.admin.property(
        short_description=_('Samba Next User RID'),
        long_description='',
        syntax=univention.admin.syntax.string,
        options=['samba'],
        default=('1000', []),
        ldap_attribute='sambaNextUserRid',
    ),
    'sambaNextGroupRid': univention.admin.property(
        short_description=_('Samba Next Group RID'),
        long_description='',
        syntax=univention.admin.syntax.string,
        options=['samba'],
        default=('1000', []),
        ldap_attribute='sambaNextGroupRid',
    ),
    'kerberosRealm': univention.admin.property(
        short_description=_('Kerberos realm'),
        long_description='',
        syntax=univention.admin.syntax.string,
        options=['kerberos'],
        required=True,
        may_change=False,
        default=(configRegistry.get('domainname', '').upper(), []),
        ldap_attribute='krb5RealmName',
    ),
    'defaultGroup': univention.admin.property(
        short_description=_('Default Primary Group'),
        long_description='',
        syntax=univention.admin.syntax.GroupDNOrEmpty,
        options=['group-settings'],
        dontsearch=True,
        required=False,
        ldap_attribute='univentionDefaultGroup',
    ),
    'defaultComputerGroup': univention.admin.property(
        short_description=_('Default Group for Computers'),
        long_description='',
        syntax=univention.admin.syntax.GroupDNOrEmpty,
        options=['group-settings'],
        dontsearch=True,
        required=False,
        ldap_attribute='univentionDefaultComputerGroup',
    ),
    'defaultDomainControllerGroup': univention.admin.property(
        short_description=_('Default Group for Replica Directory Nodes'),
        long_description='',
        syntax=univention.admin.syntax.GroupDNOrEmpty,
        options=['group-settings'],
        dontsearch=True,
        required=False,
        ldap_attribute='univentionDefaultDomainControllerGroup',
    ),
    'defaultDomainControllerMBGroup': univention.admin.property(
        short_description=_('Default Group for Primary and Backup Directory Nodes'),
        long_description='',
        syntax=univention.admin.syntax.GroupDNOrEmpty,
        options=['group-settings'],
        dontsearch=True,
        required=False,
        ldap_attribute='univentionDefaultDomainControllerMasterGroup',
    ),
    'defaultMemberServerGroup': univention.admin.property(
        short_description=_('Default Group for Managed Nodes'),
        long_description='',
        syntax=univention.admin.syntax.GroupDNOrEmpty,
        options=['group-settings'],
        dontsearch=True,
        required=False,
        ldap_attribute='univentionDefaultMemberserverGroup',
    ),
    'defaultClientGroup': univention.admin.property(
        short_description=_('Default Group for Client Computers'),
        long_description='',
        syntax=univention.admin.syntax.GroupDNOrEmpty,
        options=['group-settings'],
        dontsearch=True,
        required=False,
        ldap_attribute='univentionDefaultClientGroup',
    ),
}

layout = [
    Tab(_('General'), _('Basic settings'), layout=[
        Group(_('Domain container description'), layout=[
            "name",
        ]),
    ]),
    Tab(_('DNS'), _('DNS Zones'), advanced=True, layout=[
        ["dnsForwardZone", "dnsReverseZone"],
    ]),
    Tab(_('Samba'), _('Samba Settings'), advanced=True, layout=[
        ["sambaDomainName", "sambaSID"],
        ["sambaNextUserRid", "sambaNextGroupRid"],
    ]),
    Tab(_('Kerberos'), _('Kerberos Settings'), advanced=True, layout=[
        'kerberosRealm',
    ]),
    Tab(_('Default Primary Groups'), _('Default Primary Groups'), layout=[
        Group(_('Default Primary Groups'), layout=[
            "defaultGroup",
            "defaultComputerGroup",
            "defaultDomainControllerMBGroup",
            "defaultDomainControllerGroup",
            "defaultMemberServerGroup",
            "defaultClientGroup",
        ]),
    ]),
]

mapping = univention.admin.mapping.mapping()
mapping.from_properties(property_descriptions)
# fmt: on


class object(univention.admin.handlers.simpleLdap):
    module = module

    def __init__(self, co, lo, position, dn='', superordinate=None, attributes=None):
        super().__init__(co, lo, position, dn, superordinate, attributes)
        if not self.info.get('name'):
            self.info['name'] = self.oldattr.get('l', self.oldattr.get('o', self.oldattr.get('c', self.oldattr.get('ou', self.oldattr.get('dc', [b''])))))[0].decode('UTF-8')
            self.save()

    def open(self):
        univention.admin.handlers.simpleLdap.open(self)

        if self.exists():
            self['dnsForwardZone'] = self.lo.authz_connection.searchDn(
                base=self.dn, scope='domain', filter='(&(objectClass=dNSZone)(sOARecord=*)(!(zoneName=*.in-addr.arpa))(!(zoneName=*.ip6.arpa)))',
            )
            self['dnsReverseZone'] = self.lo.authz_connection.searchDn(
                base=self.dn, scope='domain', filter='(&(objectClass=dNSZone)(sOARecord=*)(|(zoneName=*.in-addr.arpa)(zoneName=*.ip6.arpa)))',
            )
            self.save()

    @classmethod
    def unmapped_lookup_filter(cls):
        return univention.admin.filter.conjunction('&', [
            univention.admin.filter.expression('objectClass', 'univentionBase'),
        ])  # fmt: skip


lookup = object.lookup
lookup_filter = object.lookup_filter
identify = object.identify
