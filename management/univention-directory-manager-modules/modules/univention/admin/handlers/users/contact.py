# SPDX-FileCopyrightText: 2018-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""|UDM| module for the user contact objects"""

from __future__ import annotations

from typing import Any

import univention.admin
import univention.admin.filter
import univention.admin.handlers
import univention.admin.localization
import univention.admin.uexceptions
from univention.admin.handlers.users.user import mapHomePostalAddress, unmapHomePostalAddress
from univention.admin.layout import Group, Tab


translation = univention.admin.localization.translation('univention.admin.handlers.users')
_ = translation.translate

module = 'users/contact'
operations = ['add', 'edit', 'remove', 'search', 'move']

childs = False
short_description = _('Contact')
object_name = _('Contact')
object_name_plural = _('Contact information')
long_description = _('Contact information')

# fmt: off
options = {
    'default': univention.admin.option(
        short_description=short_description,
        default=True,
        objectClasses=['top', 'person', 'inetOrgPerson', 'organizationalPerson'],
    ),
}
property_descriptions = {
    'cn': univention.admin.property(
        short_description=_('Name'),
        long_description='',
        syntax=univention.admin.syntax.TwoThirdsString,
        include_in_default_search=True,
        identifies=True,
        readonly_when_synced=True,
        copyable=True,
        ldap_attribute='cn',
    ),
    'lastname': univention.admin.property(
        short_description=_('Last name'),
        long_description='',
        syntax=univention.admin.syntax.string,
        include_in_default_search=True,
        required=True,
        readonly_when_synced=True,
        copyable=True,
        ldap_attribute='sn',
    ),
    'firstname': univention.admin.property(
        short_description=_('First name'),
        long_description='',
        syntax=univention.admin.syntax.TwoThirdsString,
        include_in_default_search=True,
        readonly_when_synced=True,
        copyable=True,
        ldap_attribute='givenName',
    ),
    'title': univention.admin.property(
        short_description=_('Title'),
        long_description='',
        syntax=univention.admin.syntax.OneThirdString,
        readonly_when_synced=True,
        copyable=True,
        ldap_attribute='title',
    ),
    'initials': univention.admin.property(
        short_description=_('Initials'),
        long_description='',
        syntax=univention.admin.syntax.string6,
        readonly_when_synced=True,
        copyable=True,
    ),
    'description': univention.admin.property(
        short_description=_('Description'),
        long_description='',
        syntax=univention.admin.syntax.string,
        include_in_default_search=True,
        readonly_when_synced=True,
        copyable=True,
        ldap_attribute='description',
    ),
    'displayName': univention.admin.property(
        short_description=_('Display name'),
        long_description='',
        syntax=univention.admin.syntax.string,
        default='<firstname> <lastname><:strip>',
        readonly_when_synced=True,
        copyable=True,
        ldap_attribute='displayName',
    ),
    'birthday': univention.admin.property(
        short_description=_('Birthdate'),
        long_description='',
        syntax=univention.admin.syntax.iso8601Date,
        copyable=True,
        ldap_attribute='univentionBirthday',
    ),
    'jpegPhoto': univention.admin.property(
        short_description=_("Picture of the user (JPEG format)"),
        long_description=_('Picture for user account in JPEG format'),
        syntax=univention.admin.syntax.jpegPhoto,
        dontsearch=True,
        copyable=True,
        ldap_attribute='jpegPhoto',
        map=mapBase64,
        unmap=unmapBase64,
    ),
    'organisation': univention.admin.property(
        short_description=_('Organisation'),
        long_description='',
        syntax=univention.admin.syntax.string64,
        readonly_when_synced=True,
        copyable=True,
        ldap_attribute='o',
    ),
    'employeeNumber': univention.admin.property(
        short_description=_('Employee number'),
        long_description='',
        syntax=univention.admin.syntax.string,
        copyable=True,
        ldap_attribute='employeeNumber',
    ),
    'employeeType': univention.admin.property(
        short_description=_('Employee type'),
        long_description='',
        syntax=univention.admin.syntax.string,
        copyable=True,
        ldap_attribute='employeeType',
    ),
    'secretary': univention.admin.property(
        short_description=_('Superior'),
        long_description='',
        syntax=univention.admin.syntax.UserDN,
        multivalue=True,
        copyable=True,
        ldap_attribute='secretary',
    ),
    'e-mail': univention.admin.property(
        short_description=_('E-mail address'),
        long_description='',
        syntax=univention.admin.syntax.emailAddress,
        multivalue=True,
        ldap_attribute='mail',
        encoding='ASCII',
    ),
    'phone': univention.admin.property(
        short_description=_('Telephone number'),
        long_description='',
        syntax=univention.admin.syntax.phone,
        multivalue=True,
        readonly_when_synced=True,
        copyable=True,
        ldap_attribute='telephoneNumber',
    ),
    'roomNumber': univention.admin.property(
        short_description=_('Room number'),
        long_description='',
        syntax=univention.admin.syntax.OneThirdString,
        multivalue=True,
        copyable=True,
        ldap_attribute='roomNumber',
    ),
    'departmentNumber': univention.admin.property(
        short_description=_('Department number'),
        long_description='',
        syntax=univention.admin.syntax.OneThirdString,
        multivalue=True,
        copyable=True,
        ldap_attribute='departmentNumber',
    ),
    'street': univention.admin.property(
        short_description=_('Street'),
        long_description='',
        syntax=univention.admin.syntax.string,
        readonly_when_synced=True,
        copyable=True,
        ldap_attribute='street',
    ),
    'postcode': univention.admin.property(
        short_description=_('Postal code'),
        long_description='',
        syntax=univention.admin.syntax.OneThirdString,
        readonly_when_synced=True,
        copyable=True,
        ldap_attribute='postalCode',
    ),
    'postOfficeBox': univention.admin.property(
        short_description=_('Post office box'),
        long_description='',
        syntax=univention.admin.syntax.string,
        multivalue=True,
        copyable=True,
        ldap_attribute='postOfficeBox',
    ),
    'preferredLanguage': univention.admin.property(
        short_description=_('Preferred language'),
        long_description='',
        syntax=univention.admin.syntax.string,
        copyable=True,
        ldap_attribute='preferredLanguage',
    ),
    'city': univention.admin.property(
        short_description=_('City'),
        long_description='',
        syntax=univention.admin.syntax.TwoThirdsString,
        readonly_when_synced=True,
        copyable=True,
        ldap_attribute='l',
    ),
    'country': univention.admin.property(
        short_description=_('Country'),
        long_description='',
        syntax=univention.admin.syntax.Country,
        readonly_when_synced=True,
        copyable=True,
        ldap_attribute='c',
    ),
    'state': univention.admin.property(
        short_description=_('State'),
        long_description=_('State / Province'),
        syntax=univention.admin.syntax.string,
        readonly_when_synced=True,
        copyable=True,
        ldap_attribute='st',
    ),
    'homeTelephoneNumber': univention.admin.property(
        short_description=_('Private telephone number'),
        long_description='',
        syntax=univention.admin.syntax.phone,
        multivalue=True,
        readonly_when_synced=True,
        copyable=True,
        ldap_attribute='homePhone',
    ),
    'mobileTelephoneNumber': univention.admin.property(
        short_description=_('Mobile phone number'),
        long_description='',
        syntax=univention.admin.syntax.phone,
        multivalue=True,
        readonly_when_synced=True,
        copyable=True,
        ldap_attribute='mobile',
    ),
    'pagerTelephoneNumber': univention.admin.property(
        short_description=_('Pager telephone number'),
        long_description='',
        syntax=univention.admin.syntax.phone,
        multivalue=True,
        readonly_when_synced=True,
        copyable=True,
        ldap_attribute='pager',
    ),
    'homePostalAddress': univention.admin.property(
        short_description=_('Private postal address'),
        long_description='',
        syntax=univention.admin.syntax.postalAddress,
        multivalue=True,
        copyable=True,
        ldap_attribute='homePostalAddress',
        map=mapHomePostalAddress,
        unmap=unmapHomePostalAddress,
    ),
    'preferredDeliveryMethod': univention.admin.property(
        short_description=_('Preferred delivery method'),
        long_description='',
        syntax=univention.admin.syntax.string,
        ldap_attribute='preferredDeliveryMethod',
    ),
    'physicalDeliveryOfficeName': univention.admin.property(
        short_description=_('Delivery office name'),
        long_description='',
        syntax=univention.admin.syntax.string,
        copyable=True,
        ldap_attribute='physicalDeliveryOfficeName',
    ),
}

layout = [
    Tab(_('General'), _('Basic settings'), layout=[
        Group(_('User account'), layout=[
            ['title', 'firstname', 'lastname'],
            ['description'],
        ]),
        Group(_('Personal information'), layout=[
            'displayName',
            'birthday',
            'jpegPhoto',
        ]),
        Group(_('Organisation'), layout=[
            'organisation',
            ['employeeNumber', 'employeeType'],
            'secretary',
        ]),
    ]),
    Tab(_('Contact'), _('Contact information'), layout=[
        Group(_('Business'), layout=[
            'e-mail',
            'phone',
            ['roomNumber', 'departmentNumber'],
            ['street', 'postcode', 'city'],
            ['state', 'country'],
        ]),
        Group(_('Private'), layout=[
            'homeTelephoneNumber',
            'mobileTelephoneNumber',
            'pagerTelephoneNumber',
            'homePostalAddress',
        ]),
    ]),
]

mapping = univention.admin.mapping.mapping()
mapping.from_properties(property_descriptions)
# fmt: on


class object(univention.admin.handlers.simpleLdap):
    module = module

    def description(self) -> str:
        description = '%s %s' % (self['firstname'] or '', self['lastname'])
        return description.strip()

    def get_candidate_dn(self) -> str:
        dn = self._ldap_dn()
        if self.exists():
            rdn = self.lo.explodeDn(dn)[0]
            dn = '%s,%s' % (rdn, self.lo.parentDn(self.dn))
        return dn

    def unique_dn(self) -> bool:
        candidate_dn = self.get_candidate_dn()
        try:
            self.lo.authz_connection.searchDn(base=candidate_dn, scope='base')
        except univention.admin.uexceptions.noObject:
            return True
        else:
            return False

    def acquire_unique_dn(self) -> str:
        nonce = 1
        cn = '%s %s %d' % (self['firstname'] or '', self['lastname'], nonce)
        self['cn'] = cn.strip()
        while not self.unique_dn():
            nonce += 1
            cn = '%s %s %d' % (self['firstname'] or '', self['lastname'], nonce)
            self['cn'] = cn.strip()
        return self.get_candidate_dn()

    def _ldap_pre_ready(self) -> None:
        super()._ldap_pre_ready()

        if not self.exists() or self.hasChanged(('firstname', 'lastname')):
            self.acquire_unique_dn()

    def _ldap_modlist(self) -> list[tuple[str, Any, Any]]:
        ml = univention.admin.handlers.simpleLdap._ldap_modlist(self)
        ml = self._modlist_display_name(ml)
        ml = self._modlist_univention_person(ml)
        return ml

    def _modlist_display_name(self, ml: list[tuple[str, Any, Any]]) -> list[tuple[str, Any, Any]]:
        # update displayName automatically if no custom value has been entered by the user and the name changed
        if self.info.get('displayName') == self.oldinfo.get('displayName') and (
            self.info.get('firstname') != self.oldinfo.get('firstname') or self.info.get('lastname') != self.oldinfo.get('lastname')
        ):
            prop_displayName = self.descriptions['displayName']
            old_default_displayName = prop_displayName._replace(prop_displayName.base_default, self.oldinfo)
            # does old displayName match with old default displayName?
            if self.oldinfo.get('displayName', '') == old_default_displayName:
                # yes ==> update displayName automatically
                new_displayName = prop_displayName._replace(prop_displayName.base_default, self)
                ml.append(('displayName', self.oldattr.get('displayName', [b''])[0], new_displayName.encode('UTF-8')))
        return ml

    def _modlist_univention_person(self, ml: list[tuple[str, Any, Any]]) -> list[tuple[str, Any, Any]]:
        univention_person_property_names = ('birthday', 'country')
        if any(self.hasChanged(ikey) for ikey in univention_person_property_names):
            if any(self[ikey] for ikey in univention_person_property_names):
                if b'univentionPerson' not in self.oldattr.get('objectClass', []):
                    ml.append(('objectClass', b'', b'univentionPerson'))
            elif b'univentionPerson' in self.oldattr.get('objectClass', []):
                ml.append(('objectClass', b'univentionPerson', b''))
        return ml

    def _move(self, newdn: str, modify_childs: bool = True, ignore_license: bool = False) -> str:
        olddn = self.dn

        # acquire unique dn in new position
        self.dn = newdn
        newdn = self.acquire_unique_dn()
        self.dn = olddn

        self.lo.authz_connection.rename(self.dn, newdn)
        self.dn = newdn

        try:
            self._move_in_groups(olddn)  # can be done always, will do nothing if oldinfo has no attribute 'groups'
            self._move_in_subordinates(olddn)
            self._ldap_post_move(olddn)
        except BaseException:
            # move back
            self.log.warning('ldap_post_move failed, move object back', dn=newdn, old_dn=olddn)
            self.lo.authz_connection.rename(self.dn, olddn)
            self.dn = olddn
            raise
        return self.dn

    @classmethod
    def unmapped_lookup_filter(cls) -> univention.admin.filter.conjunction:
        return univention.admin.filter.conjunction('&', [
            univention.admin.filter.expression('objectClass', 'person'),
            univention.admin.filter.expression('objectClass', 'inetOrgPerson'),
            univention.admin.filter.expression('objectClass', 'organizationalPerson'),
            univention.admin.filter.conjunction('!', [univention.admin.filter.expression('objectClass', 'posixAccount')]),
            univention.admin.filter.conjunction('!', [univention.admin.filter.expression('objectClass', 'shadowAccount')]),
            univention.admin.filter.conjunction('!', [univention.admin.filter.expression('objectClass', 'sambaSamAccount')]),
            univention.admin.filter.conjunction('!', [univention.admin.filter.expression('objectClass', 'krb5Principal')]),
            univention.admin.filter.conjunction('!', [univention.admin.filter.expression('objectClass', 'krb5KDCEntry')]),
            univention.admin.filter.conjunction('!', [univention.admin.filter.expression('objectClass', 'univentionMail')]),
            univention.admin.filter.conjunction('!', [univention.admin.filter.expression('objectClass', 'simpleSecurityObject')]),
            univention.admin.filter.conjunction('!', [univention.admin.filter.expression('objectClass', 'uidObject')]),
            univention.admin.filter.conjunction('!', [univention.admin.filter.expression('objectClass', 'pkiUser')]),
        ])  # fmt: skip


lookup = object.lookup
lookup_filter = object.lookup_filter


def identify(dn: str, attr: univention.admin.handlers._Attributes, canonical: bool = False) -> bool:
    # FIXME: is this if block needed? copy pasted from users/user
    if (
        b'0' in attr.get('uidNumber', [])
        or b'$' in attr.get('uid', [b''])[0]
        or b'univentionHost' in attr.get('objectClass', [])
        or b'functional' in attr.get('univentionObjectFlag', [])
    ):
        return False

    required_ocs = {b'person', b'inetOrgPerson', b'organizationalPerson'}
    forbidden_ocs = {b'posixAccount', b'shadowAccount', b'sambaSamAccount', b'krb5Principal', b'krb5KDCEntry', b'univentionMail', b'simpleSecurityObject', b'uidObject', b'pkiUser'}
    ocs = set(attr.get('objectClass', []))
    return (ocs & required_ocs == required_ocs) and not (ocs & forbidden_ocs)
