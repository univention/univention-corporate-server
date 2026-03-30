# SPDX-FileCopyrightText: 2004-2026 Univention GmbH
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
        default=False,
    ),
    'Version 2': univention.admin.option(
        short_description=_('Version 2 license'),
        editable=False,
        default=True,
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
    ),
    'expires': univention.admin.property(
        short_description=_('Expiry date'),
        long_description=_('License Expiration Date'),
        syntax=univention.admin.syntax.string,
        required=True,
        may_change=False,
    ),
    'base': univention.admin.property(
        short_description=_('Base DN'),
        long_description=_('Base DN the license is valid for'),
        syntax=univention.admin.syntax.string,
        include_in_default_search=True,
        required=True,
        may_change=False,
    ),
    'signature': univention.admin.property(
        short_description=_('Signature'),
        long_description=_('This Signature is used to verify the authenticity of the license.'),
        syntax=univention.admin.syntax.string,
        required=True,
        may_change=False,
    ),
    'oemProductTypes': univention.admin.property(
        short_description=_('Valid OEM product types'),
        long_description=_('OEM Product types this license allows.'),
        syntax=univention.admin.syntax.string,
        multivalue=True,
        may_change=False,
    ),
    'product': univention.admin.property(
        short_description=_('Product type'),
        long_description=_('Product type this license allows.'),
        syntax=univention.admin.syntax.string,
        multivalue=True,
        may_change=False,
    ),
    'keyID': univention.admin.property(
        short_description=_('Key ID'),
        long_description=_('Key ID of this license.'),
        syntax=univention.admin.syntax.string,
        options=['Version 2'],
        may_change=False,
    ),
    'servers': univention.admin.property(
        short_description=_('Servers'),
        long_description=_('Maximum number of servers this license allows.'),
        syntax=univention.admin.syntax.string,
        options=['Version 2'],
        may_change=False,
    ),
    'support': univention.admin.property(
        short_description=_('Servers with standard support'),
        long_description=_('Servers with standard support.'),
        syntax=univention.admin.syntax.string,
        options=['Version 2'],
        may_change=False,
    ),
    'premiumsupport': univention.admin.property(
        short_description=_('Premium Support'),
        long_description=_('Servers with premium support.'),
        syntax=univention.admin.syntax.string,
        options=['Version 2'],
        may_change=False,
    ),
    'managedclients': univention.admin.property(
        short_description=_('Managed Clients'),
        long_description=_('Maximum number of managed clients this license allows.'),
        syntax=univention.admin.syntax.string,
        options=['Version 2'],
        may_change=False,
    ),
    'users': univention.admin.property(
        short_description=_('Users'),
        long_description=_('Maximum number of users this license allows.'),
        syntax=univention.admin.syntax.string,
        options=['Version 2'],
        may_change=False,
    ),
    'version': univention.admin.property(
        short_description=_('Version'),
        long_description=_('Version format of this license.'),
        syntax=univention.admin.syntax.string,
        options=['Version 2'],
        may_change=False,
    ),

}

layout = [
    Tab(_('License'), _('Licensing Information'), layout=[
        Group(_('General license settings'), layout=[
            'name',
            'expires',
            'base',
            'oemProductTypes',
            'signature',
        ]),
        Group(_('Version 2 license informations'), layout=[
            'keyID',
            ['users', 'servers'],
            ['managedclients'],
            ['support', 'premiumsupport'],
            'version',
        ]),
    ]),
]

mapping = univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('expires', 'univentionLicenseEndDate', None, univention.admin.mapping.ListToString, encoding='ASCII')
mapping.register('base', 'univentionLicenseBaseDN', None, univention.admin.mapping.ListToString, encoding='ASCII')
mapping.register('signature', 'univentionLicenseSignature', None, univention.admin.mapping.ListToString, encoding='ASCII')
mapping.register('oemProductTypes', 'univentionLicenseOEMProduct', encoding='ASCII')
mapping.register('product', 'univentionLicenseProduct', None, univention.admin.mapping.ListToString, encoding='ASCII')
mapping.register('keyID', 'univentionLicenseKeyID', None, univention.admin.mapping.ListToString, encoding='ASCII')
mapping.register('servers', 'univentionLicenseServers', None, univention.admin.mapping.ListToString, encoding='ASCII')
mapping.register('support', 'univentionLicenseSupport', None, univention.admin.mapping.ListToString, encoding='ASCII')
mapping.register('premiumsupport', 'univentionLicensePremiumSupport', None, univention.admin.mapping.ListToString, encoding='ASCII')
mapping.register('managedclients', 'univentionLicenseManagedClients', None, univention.admin.mapping.ListToString, encoding='ASCII')
mapping.register('users', 'univentionLicenseUsers', None, univention.admin.mapping.ListToString, encoding='ASCII')
mapping.register('version', 'univentionLicenseVersion', None, univention.admin.mapping.ListToString, encoding='ASCII')
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
