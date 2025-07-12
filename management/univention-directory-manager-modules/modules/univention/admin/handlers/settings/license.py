# SPDX-FileCopyrightText: 2004-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""|UDM| module for license handling"""

import univention.admin.filter
import univention.admin.handlers
import univention.admin.localization
import univention.admin.syntax
from univention.admin.layout import Group, Tab


translation = univention.admin.localization.translation('univention.admin.handlers.settings')
_ = translation.translate

module = 'settings/license'
superordinate = 'settings/cn'
operations = ['remove', 'search']

childs = False
short_description = _('Settings: License')
object_name = _('License')
object_name_plural = _('Licenses')
long_description = _('Univention License')
# fmt: off
options = {
    'default': univention.admin.option(
        short_description=short_description,
        default=True,
        objectClasses=['top', 'univentionLicense'],
    ),
    'Version 1': univention.admin.option(
        short_description=_('Version 1 license'),
        editable=False,
        default=0,
    ),
    'Version 2': univention.admin.option(
        short_description=_('Version 2 license'),
        editable=False,
        default=1,
    ),
}
property_descriptions = {
    'name': univention.admin.property(
        short_description=_('Name'),
        long_description=_('Name'),
        syntax=univention.admin.syntax.string,
        include_in_default_search=True,
        required=True,
        may_change=False,
        identifies=True,
        ldap_attribute='cn',
    ),
    'expires': univention.admin.property(
        short_description=_('Expiry date'),
        long_description=_('License Expiration Date'),
        syntax=univention.admin.syntax.string,
        required=True,
        may_change=False,
        ldap_attribute='univentionLicenseEndDate',
        encoding='ASCII',
    ),
    'module': univention.admin.property(
        short_description=_('Module'),
        long_description=_('Module the license is valid for'),
        syntax=univention.admin.syntax.string,
        options=['Version 1'],
        required=True,
        may_change=False,
        ldap_attribute='univentionLicenseModule',
        encoding='ASCII',
    ),
    'base': univention.admin.property(
        short_description=_('Base DN'),
        long_description=_('Base DN the license is valid for'),
        syntax=univention.admin.syntax.string,
        include_in_default_search=True,
        required=True,
        may_change=False,
        ldap_attribute='univentionLicenseBaseDN',
        encoding='ASCII',
    ),
    'signature': univention.admin.property(
        short_description=_('Signature'),
        long_description=_('This Signature is used to verify the authenticity of the license.'),
        syntax=univention.admin.syntax.string,
        required=True,
        may_change=False,
        ldap_attribute='univentionLicenseSignature',
        encoding='ASCII',
    ),
    'accounts': univention.admin.property(
        short_description=_('Max. user accounts'),
        long_description=_('Maximum number of user accounts managed with the UCS infrastructure'),
        syntax=univention.admin.syntax.string,
        options=['Version 1'],
        may_change=False,
        ldap_attribute='univentionLicenseAccounts',
        encoding='ASCII',
    ),
    'clients': univention.admin.property(
        short_description=_('Max. clients'),
        long_description=_('Maximum number of client hosts managed with the UCS infrastructure'),
        syntax=univention.admin.syntax.string,
        options=['Version 1'],
        may_change=False,
        ldap_attribute='univentionLicenseClients',
        encoding='ASCII',
    ),
    'groupwareaccounts': univention.admin.property(
        short_description=_('Max. groupware accounts'),
        long_description=_('Maximum number of groupware accounts managed with the UCS infrastructure'),
        syntax=univention.admin.syntax.string,
        options=['Version 1'],
        may_change=False,
        ldap_attribute='univentionLicenseGroupwareAccounts',
        encoding='ASCII',
    ),
    'desktops': univention.admin.property(
        short_description=_('Max. desktops'),
        long_description=_('Maximum number of Univention desktop accounts managed with the UCS infrastructure'),
        syntax=univention.admin.syntax.string,
        options=['Version 1'],
        may_change=False,
        ldap_attribute='univentionLicenseuniventionDesktops',
        encoding='ASCII',
    ),
    'productTypes': univention.admin.property(
        short_description=_('Valid product types'),
        long_description=_('Product types this license allows.'),
        syntax=univention.admin.syntax.string,
        multivalue=True,
        options=['Version 1'],
        may_change=False,
        ldap_attribute='univentionLicenseType',
        encoding='ASCII',
    ),
    'oemProductTypes': univention.admin.property(
        short_description=_('Valid OEM product types'),
        long_description=_('OEM Product types this license allows.'),
        syntax=univention.admin.syntax.string,
        multivalue=True,
        may_change=False,
        ldap_attribute='univentionLicenseOEMProduct',
        encoding='ASCII',
    ),
    'product': univention.admin.property(
        short_description=_('Product type'),
        long_description=_('Product type this license allows.'),
        syntax=univention.admin.syntax.string,
        multivalue=True,
        may_change=False,
        ldap_attribute='univentionLicenseProduct',
        unmap=ListToString,
        encoding='ASCII',
    ),
    'keyID': univention.admin.property(
        short_description=_('Key ID'),
        long_description=_('Key ID of this license.'),
        syntax=univention.admin.syntax.string,
        options=['Version 2'],
        may_change=False,
        ldap_attribute='univentionLicenseKeyID',
        encoding='ASCII',
    ),
    'servers': univention.admin.property(
        short_description=_('Servers'),
        long_description=_('Maximum number of servers this license allows.'),
        syntax=univention.admin.syntax.string,
        options=['Version 2'],
        may_change=False,
        ldap_attribute='univentionLicenseServers',
        encoding='ASCII',
    ),
    'support': univention.admin.property(
        short_description=_('Servers with standard support'),
        long_description=_('Servers with standard support.'),
        syntax=univention.admin.syntax.string,
        options=['Version 2'],
        may_change=False,
        ldap_attribute='univentionLicenseSupport',
        encoding='ASCII',
    ),
    'premiumsupport': univention.admin.property(
        short_description=_('Premium Support'),
        long_description=_('Servers with premium support.'),
        syntax=univention.admin.syntax.string,
        options=['Version 2'],
        may_change=False,
        ldap_attribute='univentionLicensePremiumSupport',
        encoding='ASCII',
    ),
    'managedclients': univention.admin.property(
        short_description=_('Managed Clients'),
        long_description=_('Maximum number of managed clients this license allows.'),
        syntax=univention.admin.syntax.string,
        options=['Version 2'],
        may_change=False,
        ldap_attribute='univentionLicenseManagedClients',
        encoding='ASCII',
    ),
    'users': univention.admin.property(
        short_description=_('Users'),
        long_description=_('Maximum number of users this license allows.'),
        syntax=univention.admin.syntax.string,
        options=['Version 2'],
        may_change=False,
        ldap_attribute='univentionLicenseUsers',
        encoding='ASCII',
    ),
    'virtualdesktopusers': univention.admin.property(
        short_description=_('DVS users'),
        long_description=_('Maximum number of DVS users this license allows.'),
        syntax=univention.admin.syntax.string,
        options=['Version 2'],
        may_change=False,
        ldap_attribute='univentionLicenseVirtualDesktopUsers',
        encoding='ASCII',
    ),
    'virtualdesktopclients': univention.admin.property(
        short_description=_('DVS clients'),
        long_description=_('Maximum number of DVS clients this license allows.'),
        syntax=univention.admin.syntax.string,
        options=['Version 2'],
        may_change=False,
        ldap_attribute='univentionLicenseVirtualDesktopClients',
        encoding='ASCII',
    ),
    'corporateclients': univention.admin.property(
        short_description=_('Corporate clients'),
        long_description=_('Maximum number of corporate clients this license allows.'),
        syntax=univention.admin.syntax.string,
        options=['Version 2'],
        may_change=False,
        ldap_attribute='univentionLicenseCorporateClients',
        encoding='ASCII',
    ),
    'version': univention.admin.property(
        short_description=_('Version'),
        long_description=_('Version format of this license.'),
        syntax=univention.admin.syntax.string,
        options=['Version 2'],
        may_change=False,
        ldap_attribute='univentionLicenseVersion',
        encoding='ASCII',
    ),

}

layout = [
    Tab(_('License'), _('Licensing Information'), layout=[
        Group(_('General license settings'), layout=[
            'name',
            'module',
            'expires',
            'base',
            'oemProductTypes',
            'signature',
        ]),
        Group(_('Version 1 license informations'), layout=[
            'productTypes',
            ['accounts', 'groupwareaccounts'],
            ['clients', 'desktops'],
        ]),
        Group(_('Version 2 license informations'), layout=[
            'keyID',
            ['users', 'servers'],
            ['corporateclients', 'managedclients'],
            ['virtualdesktopusers', 'virtualdesktopclients'],
            ['support', 'premiumsupport'],
            'version',
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
        if self.oldattr.get('univentionLicenseVersion', []) == [b'2']:
            self.options.append('Version 2')
        else:
            self.options.append('Version 1')
        self.save()


lookup = object.lookup
lookup_filter = object.lookup_filter
identify = object.identify
