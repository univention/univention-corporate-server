# SPDX-FileCopyrightText: 2012-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""|UDM| module for kerberos KDC entries"""

import random
import string

import ldap

import univention.admin.handlers
import univention.admin.localization
import univention.admin.password
import univention.admin.uldap
from univention.admin.layout import Group, Tab


translation = univention.admin.localization.translation('univention.admin.handlers.kerberos')
_ = translation.translate

module = 'kerberos/kdcentry'
operations = ['add', 'edit', 'remove', 'search', 'move']
childs = False
short_description = _('Kerberos: KDC Entry')
object_name = _('KDC Entry')
object_name_plural = _('KDC Entries')
long_description = ''
# fmt: off
options = {
    'default': univention.admin.option(
        short_description=short_description,
        default=True,
        objectClasses=['top', 'account', 'krb5Principal', 'krb5KDCEntry'],
    ),
}
property_descriptions = {
    'name': univention.admin.property(
        short_description=_('Principal name'),
        long_description='',
        syntax=univention.admin.syntax.string,
        include_in_default_search=True,
        required=True,
        identifies=True,
        ldap_attribute='uid',
    ),
    'description': univention.admin.property(
        short_description=_('Description'),
        long_description='',
        syntax=univention.admin.syntax.string,
        include_in_default_search=True,
        ldap_attribute='description',
    ),
    'password': univention.admin.property(
        short_description=_('Password'),
        long_description='',
        syntax=univention.admin.syntax.passwd,
        dontsearch=True,
    ),
    'generateRandomPassword': univention.admin.property(
        short_description=_('Generate random password'),
        long_description='',
        syntax=univention.admin.syntax.boolean,
        dontsearch=True,
    ),
    'keyVersionNumber': univention.admin.property(
        short_description=_('Key version'),
        long_description='',
        syntax=univention.admin.syntax.integer,
        dontsearch=True,
        default='1',
        ldap_attribute='krb5KeyVersionNumber',
    ),
    'KDCFlags': univention.admin.property(
        short_description=_('KDC Flags'),
        long_description='',
        syntax=univention.admin.syntax.integer,
        dontsearch=True,
        default='126',
        ldap_attribute='krb5KDCFlags',
    ),
    'maxLife': univention.admin.property(
        short_description=_('Maximum life time'),
        long_description='',
        syntax=univention.admin.syntax.integer,
        dontsearch=True,
        default='86400',
        ldap_attribute='krb5MaxLife',
    ),
    'maxRenew': univention.admin.property(
        short_description=_('Maximum renew time'),
        long_description='',
        syntax=univention.admin.syntax.integer,
        dontsearch=True,
        default='604800',
        ldap_attribute='krb5MaxRenew',
    ),
}

layout = [
    Tab(_('General'), _('Basic settings'), layout=[
        Group(_('KDC entry'), layout=[
            ['name', 'description'],
            'password',
            'generateRandomPassword',
            'keyVersionNumber',
            'KDCFlags',
            'maxLife',
            'maxRenew',
        ]),
    ]),
]

mapping = univention.admin.mapping.mapping()
mapping.from_properties(property_descriptions)
# fmt: on


class object(univention.admin.handlers.simpleLdap):
    module = module

    def description(self):
        # Use the name by default, otherwise the rdn will be used
        return self['name']

    def _set_principal(self):
        if self.hasChanged('name') or not hasattr(self, 'krb5PrincipalName'):
            domain = univention.admin.uldap.domain(self.lo, self.position)
            realm = domain.getKerberosRealm()
            try:
                self['name'].index('@')
            except ValueError:
                # does not contain an @
                self.krb5PrincipalName = '%s@%s' % (self['name'], realm)
            else:
                self.krb5PrincipalName = self['name']

    def _ldap_pre_create(self):
        self._set_principal()
        super()._ldap_pre_create()

    def _ldap_dn(self):
        dn = ldap.dn.str2dn(super()._ldap_dn())
        dn[0] = [('krb5PrincipalName', self.krb5PrincipalName, dn[0][0][2])]
        return ldap.dn.dn2str(dn)

    def _ldap_modlist(self):
        ml = univention.admin.handlers.simpleLdap._ldap_modlist(self)

        self._set_principal()

        if self.hasChanged('name'):
            ml.append(('krb5PrincipalName', self.oldattr.get('krb5PrincipalName', []), [self.krb5PrincipalName.encode('UTF-8')]))

        if self.info.get('generateRandomPassword', '').lower() in ['true', 'yes', '1']:
            self['password'] = ''.join(random.sample(string.ascii_letters + string.digits, 24))

        if self.hasChanged('password'):
            krb_keys = univention.admin.password.krb5_asn1(self.krb5PrincipalName, self['password'])
            ml.append(('krb5Key', self.oldattr.get('krb5Key', []), krb_keys))

        return ml


lookup = object.lookup
lookup_filter = object.lookup_filter
identify = object.identify
