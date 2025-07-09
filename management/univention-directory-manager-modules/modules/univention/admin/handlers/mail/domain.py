# SPDX-FileCopyrightText: 2004-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""|UDM| module for the mail domain objects"""

import ldap

import univention.admin.filter
import univention.admin.handlers
import univention.admin.localization
from univention.admin.handlers.dns import stripDot
from univention.admin.layout import Group, Tab


translation = univention.admin.localization.translation('univention.admin.handlers.mail')
_ = translation.translate

module = 'mail/domain'
operations = ['add', 'edit', 'remove', 'search', 'move']
childs = False
short_description = _('Mail domain')
object_name = _('Mail domain')
object_name_plural = _('Mail domains')
long_description = ''

# fmt: off
options = {
    'default': univention.admin.option(
        short_description=short_description,
        default=True,
        objectClasses=['top', 'univentionMailDomainname'],
    ),
}

property_descriptions = {
    'name': univention.admin.property(
        short_description=_('Mail domain name'),
        long_description='',
        syntax=univention.admin.syntax.dnsName,
        include_in_default_search=True,
        required=True,
        identifies=True,
    ),
}

layout = [
    Tab(_('General'), _('Basic settings'), layout=[
        Group(_('Mail domain description'), layout=[
            "name",
        ]),
    ]),
]

mapping = univention.admin.mapping.mapping()
mapping.register('name', 'cn', stripDot, univention.admin.mapping.ListToString)
# fmt: on


class object(univention.admin.handlers.simpleLdap):
    module = module

    def _ldap_dn(self):
        dn = ldap.dn.str2dn(super()._ldap_dn())
        dn[0] = [(dn[0][0][0], dn[0][0][1].lower(), dn[0][0][2])]
        return ldap.dn.dn2str(dn)

    def _ldap_modlist(self):
        ml = univention.admin.handlers.simpleLdap._ldap_modlist(self)
        ml = [(a, b, c.lower()) if a == 'cn' else (a, b, c) for (a, b, c) in ml]
        return ml


lookup = object.lookup
lookup_filter = object.lookup_filter
identify = object.identify
