# SPDX-FileCopyrightText: 2013-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""|UDM| module for LDAP ACL extensions"""

import apt

import univention.admin.filter
import univention.admin.handlers
import univention.admin.localization
from univention.admin.layout import Group, Tab


translation = univention.admin.localization.translation('univention.admin.handlers.settings')
_ = translation.translate

module = 'settings/ldapacl'
superordinate = 'settings/cn'
childs = False
operations = ['add', 'edit', 'remove', 'search', 'move']
short_description = _('Settings: LDAP ACL Extension')
object_name = _('LDAP ACL Extension')
object_name_plural = _('LDAP ACL Extensions')
long_description = ''
# fmt: off
options = {
    'default': univention.admin.option(
        short_description=short_description,
        default=True,
        objectClasses=['top', 'univentionObjectMetadata', 'univentionLDAPExtensionACL'],
    ),
}
property_descriptions = {
    'name': univention.admin.property(
        short_description=_('ACL name'),
        long_description='',
        syntax=univention.admin.syntax.string,
        include_in_default_search=True,
        required=True,
        identifies=True,
        ldap_attribute='cn',
    ),
    'filename': univention.admin.property(
        short_description=_('ACL file name'),
        long_description='',
        syntax=univention.admin.syntax.BaseFilename,
        required=True,
        default='',
        ldap_attribute='univentionLDAPACLFilename',
    ),
    'data': univention.admin.property(
        short_description=_('ACL data'),
        long_description='',
        syntax=univention.admin.syntax.Base64Bzip2Text,
        required=True,
        ldap_attribute='univentionLDAPACLData',
        map=mapBase64,
        unmap=unmapBase64,
    ),
    'active': univention.admin.property(
        short_description=_('Active'),
        long_description='',
        syntax=univention.admin.syntax.TrueFalseUp,
        default='FALSE',
        ldap_attribute='univentionLDAPACLActive',
    ),
    'appidentifier': univention.admin.property(
        short_description=_('App identifier'),
        long_description='',
        syntax=univention.admin.syntax.TextArea,
        multivalue=True,
        ldap_attribute='univentionAppIdentifier',
    ),
    'package': univention.admin.property(
        short_description=_('Software package'),
        long_description='',
        syntax=univention.admin.syntax.string,
        ldap_attribute='univentionOwnedByPackage',
    ),
    'packageversion': univention.admin.property(
        short_description=_('Software package version'),
        long_description='',
        syntax=univention.admin.syntax.DebianPackageVersion,
        ldap_attribute='univentionOwnedByPackageVersion',
    ),
    'ucsversionstart': univention.admin.property(
        short_description=_('Minimal UCS version'),
        long_description='',
        syntax=univention.admin.syntax.UCSVersion,
        ldap_attribute='univentionUCSVersionStart',
    ),
    'ucsversionend': univention.admin.property(
        short_description=_('Maximal UCS version'),
        long_description='',
        syntax=univention.admin.syntax.UCSVersion,
        ldap_attribute='univentionUCSVersionEnd',
    ),
}

layout = [
    Tab(_('General'), _('Basic values'), layout=[
        Group(_('General LDAP ACL extension settings'), layout=[
            ["name"],
            ["filename"],
            ["data"],
        ]),
        Group(_('Metadata'), layout=[
            ["package"],
            ["packageversion"],
            ["appidentifier"],
        ]),
        Group(_('UCS Version Dependencies'), layout=[
            ["ucsversionstart"],
            ["ucsversionend"],
        ]),
        Group(_('Activated'), layout=[
            ["active"],
        ]),
    ]),
]

mapping = univention.admin.mapping.mapping()
mapping.from_properties(property_descriptions)
# fmt: on


class object(univention.admin.handlers.simpleLdap):
    module = module

    def _ldap_pre_modify(self):
        super()._ldap_pre_modify()
        diff_keys = [key for key in self.info.keys() if self.info.get(key) != self.oldinfo.get(key) and key not in ('active', 'appidentifier')]
        if not diff_keys:  # check for trivial change
            return
        if not self.hasChanged('package'):
            old_version = self.oldinfo.get('packageversion', '0')
            if not apt.apt_pkg.version_compare(self['packageversion'], old_version) > -1:
                raise univention.admin.uexceptions.valueInvalidSyntax(_('packageversion: Version must not be lower than the current one.'), property='packageversion')


lookup = object.lookup
lookup_filter = object.lookup_filter
identify = object.identify
