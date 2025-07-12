# SPDX-FileCopyrightText: 2002-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""|UDM| module for user template objects"""

import univention.admin.filter
import univention.admin.handlers
import univention.admin.localization
from univention.admin.layout import Group, Tab


translation = univention.admin.localization.translation('univention.admin.handlers.settings')
_ = translation.translate

module = 'settings/usertemplate'
operations = ['add', 'edit', 'remove', 'search', 'move']
superordinate = 'settings/cn'
childs = False
short_description = _('Settings: User Template')
object_name = _('User Template')
object_name_plural = _('User Templates')
long_description = ''
# fmt: off
options = {
    'default': univention.admin.option(
        short_description=short_description,
        default=True,
        objectClasses=['top', 'univentionUserTemplate'],
    ),
}
property_descriptions = {
    'name': univention.admin.property(
        short_description=_('Template name'),
        long_description='',
        syntax=univention.admin.syntax.string,
        include_in_default_search=True,
        required=True,
        identifies=True,
        ldap_attribute='cn',
    ),
    'title': univention.admin.property(
        short_description=_('Title'),
        long_description='',
        syntax=univention.admin.syntax.string,
        ldap_attribute='title',
    ),
    'initials': univention.admin.property(
        short_description=_('Initials'),
        long_description='',
        syntax=univention.admin.syntax.string6,
    ),
    'preferredDeliveryMethod': univention.admin.property(
        short_description=_('Preferred delivery method'),
        long_description='',
        syntax=univention.admin.syntax.string,
    ),
    'description': univention.admin.property(
        short_description=_('Description'),
        long_description='',
        syntax=univention.admin.syntax.string,
        include_in_default_search=True,
        ldap_attribute='description',
    ),
    'displayName': univention.admin.property(
        short_description=_('Display name'),
        long_description='',
        syntax=univention.admin.syntax.string,
        default='<firstname> <lastname><:strip>',
        ldap_attribute='displayName',
    ),
    'organisation': univention.admin.property(
        short_description=_('Organisation'),
        long_description='',
        syntax=univention.admin.syntax.string,
        ldap_attribute='o',
    ),
    'pwdChangeNextLogin': univention.admin.property(
        short_description=_('Change password on next login'),
        long_description=_('Change password on next login'),
        syntax=univention.admin.syntax.boolean,
        dontsearch=True,
        ldap_attribute='userPwdMustChangePreset',
        encoding='ASCII',
    ),
    'disabled': univention.admin.property(
        short_description=_('Account deactivation'),
        long_description='',
        syntax=univention.admin.syntax.boolean,
        show_in_lists=True,
        ldap_attribute='userDisabledPreset',
        encoding='ASCII',
    ),
    'e-mail': univention.admin.property(
        short_description=_('E-mail address'),
        long_description=_('This e-mail address serves only as contact information. This address has no effect on the UCS mail stack and is not related to a local mailbox.'),
        syntax=univention.admin.syntax.string,
        multivalue=True,
        ldap_attribute='mail',
        encoding='ASCII',
    ),
    'unixhome': univention.admin.property(
        short_description=_('Unix home directory'),
        long_description='',
        syntax=univention.admin.syntax.absolutePath,
        default='/home/<username>',
        ldap_attribute='homeDirectory',
    ),
    'homeShare': univention.admin.property(
        short_description=_('Home share'),
        long_description=_("Share, the user's home directory resides on"),
        syntax=univention.admin.syntax.WritableShare,
        dontsearch=True,
        ldap_attribute='userHomeSharePreset',
        encoding='ASCII',
    ),
    'homeSharePath': univention.admin.property(
        short_description=_('Home share path'),
        long_description=_('Path to the home directory on the home share'),
        syntax=univention.admin.syntax.string,
        dontsearch=True,
        ldap_attribute='userHomeSharePathPreset',
        encoding='ASCII',
    ),
    'shell': univention.admin.property(
        short_description=_('Login shell'),
        long_description='',
        syntax=univention.admin.syntax.string,
        default='/bin/bash',
        ldap_attribute='loginShell',
        encoding='ASCII',
    ),
    'sambahome': univention.admin.property(
        short_description=_('Windows home path'),
        long_description='',
        syntax=univention.admin.syntax.string,
        ldap_attribute='sambaHomePath',
    ),
    'scriptpath': univention.admin.property(
        short_description=_('Windows logon path'),
        long_description='',
        syntax=univention.admin.syntax.string,
        ldap_attribute='sambaLogonScript',
    ),
    'profilepath': univention.admin.property(
        short_description=_('Windows profile directory'),
        long_description='',
        syntax=univention.admin.syntax.string,
        ldap_attribute='sambaProfilePath',
    ),
    'homedrive': univention.admin.property(
        short_description=_('Windows home drive'),
        long_description='',
        syntax=univention.admin.syntax.string,
        ldap_attribute='sambaHomeDrive',
        encoding='ASCII',
    ),
    'street': univention.admin.property(
        short_description=_('Street'),
        long_description='',
        syntax=univention.admin.syntax.string,
        ldap_attribute='street',
    ),
    'postcode': univention.admin.property(
        short_description=_('Postal code'),
        long_description='',
        syntax=univention.admin.syntax.OneThirdString,
        ldap_attribute='postalCode',
    ),
    'city': univention.admin.property(
        short_description=_('City'),
        long_description='',
        syntax=univention.admin.syntax.TwoThirdsString,
        ldap_attribute='l',
    ),
    'country': univention.admin.property(
        short_description=_('Country'),
        long_description='',
        syntax=univention.admin.syntax.Country,
        ldap_attribute='c',
    ),
    'state': univention.admin.property(
        short_description=_('State'),
        long_description=_('State (province)'),
        syntax=univention.admin.syntax.string,
        readonly_when_synced=True,
        copyable=True,
        ldap_attribute='st',
    ),
    'phone': univention.admin.property(
        short_description=_('Telephone number'),
        long_description='',
        syntax=univention.admin.syntax.phone,
        multivalue=True,
        ldap_attribute='telephoneNumber',
    ),
    'employeeNumber': univention.admin.property(
        short_description=_('Employee number'),
        long_description='',
        syntax=univention.admin.syntax.string,
        ldap_attribute='employeeNumber',
    ),
    'roomNumber': univention.admin.property(
        short_description=_('Room number'),
        long_description='',
        syntax=univention.admin.syntax.OneThirdString,
        ldap_attribute='roomNumber',
    ),
    'secretary': univention.admin.property(
        short_description=_('Superior'),
        long_description='',
        syntax=univention.admin.syntax.UserDN,
        multivalue=True,
        ldap_attribute='secretary',
    ),
    'departmentNumber': univention.admin.property(
        short_description=_('Department number'),
        long_description='',
        syntax=univention.admin.syntax.OneThirdString,
        multivalue=True,
        ldap_attribute='departmentNumber',
    ),
    'employeeType': univention.admin.property(
        short_description=_('Employee type'),
        long_description='',
        syntax=univention.admin.syntax.string,
        ldap_attribute='employeeType',
    ),
    'groups': univention.admin.property(
        short_description=_('Groups'),
        long_description='',
        syntax=univention.admin.syntax.GroupDN,
        multivalue=True,
        ldap_attribute='userGroupsPreset',
        encoding='ASCII',
    ),
    'primaryGroup': univention.admin.property(
        short_description=_('Primary group'),
        long_description='',
        syntax=univention.admin.syntax.GroupDN,
        one_only=True,
        parent='groups',
        dontsearch=True,
        ldap_attribute='userPrimaryGroupPreset',
    ),
    'mailPrimaryAddress': univention.admin.property(
        short_description=_('Primary e-mail address (mailbox)'),
        long_description=_('E-mail address that will be used to create the IMAP/POP3 mailbox and that can be used as login for SMTP/IMAP/POP3 connections. The domain must be one of the UCS hosted e-mail domains.'),
        syntax=univention.admin.syntax.emailAddressTemplate,
        ldap_attribute='mailPrimaryAddress',
        unmap=ListToLowerString,
        encoding='ASCII',
    ),
    'mailAlternativeAddress': univention.admin.property(
        short_description=_('E-mail alias address'),
        long_description=_('Additional e-mail addresses for which e-mails will be delivered to the "Primary e-mail address". The domain must be one of the UCS hosted e-mail domains.'),
        syntax=univention.admin.syntax.emailAddressTemplate,
        multivalue=True,
        ldap_attribute='mailAlternativeAddress',
    ),
    'physicalDeliveryOfficeName': univention.admin.property(
        short_description=_('Delivery office name'),
        long_description='',
        syntax=univention.admin.syntax.string,
    ),
    'postOfficeBox': univention.admin.property(
        short_description=_('Post office box'),
        long_description='',
        syntax=univention.admin.syntax.string,
        multivalue=True,
        copyable=True,
    ),
    'preferredLanguage': univention.admin.property(
        short_description=_('Preferred language'),
        long_description='',
        syntax=univention.admin.syntax.string,
        copyable=True,
    ),
    '_options': univention.admin.property(
        short_description=_('Options'),
        long_description='',
        syntax=univention.admin.syntax.optionsUsersUser,
        multivalue=True,
        dontsearch=True,
        ldap_attribute='userOptionsPreset',
        encoding='ASCII',
    ),
}

layout = [
    Tab(_('General'), _('Basic values'), layout=[
        Group(_('General user template settings'), layout=[
            "name",
        ]),
        Group(_('User account'), layout=[
            "title",
            "description",
            "mailPrimaryAddress",
            "mailAlternativeAddress",
        ]),
        Group(_('Personal information'), layout=[
            ["displayName"],
        ]),
        Group(_('Organisation'), layout=[
            'organisation',
            ['employeeNumber', 'employeeType'],
            "secretary",
        ]),
    ]),
    Tab(_('Groups'), _('Group Memberships'), layout=[
        Group(_('Groups'), layout=[
            ["primaryGroup"],
            ["groups"],
        ]),
    ]),
    Tab(_('Account'), _('Account settings'), layout=[
        Group(_('Locking and deactivation'), layout=[
            ["disabled", "pwdChangeNextLogin"],
        ]),
        Group(_('Windows'), layout=[
            ['homedrive', 'sambahome'],
            ["scriptpath", "profilepath"],
        ]),
        Group(_('POSIX (Linux/UNIX)'), layout=[
            ["unixhome", "shell"],
            ["homeShare", "homeSharePath"],
        ]),
    ]),
    Tab(_('Contact'), _('Contact Information'), layout=[
        Group(_('Business'), layout=[
            "e-mail",
            "phone",
            ['roomNumber', 'departmentNumber'],
            ['street', 'postcode', 'city'],
            ['state', 'country'],
        ]),
    ]),
]

mapping = univention.admin.mapping.mapping()
mapping.from_properties(property_descriptions)
# mapping.register('initials', 'initials', None, univention.admin.mapping.ListToString)
mapping.register('userexpiry', 'shadowMax', None, univention.admin.mapping.ListToString)
mapping.register('passwordexpiry', 'shadowExpire', None, univention.admin.mapping.ListToString)
# mapping.register('physicalDeliveryOfficeName', 'physicalDeliveryOfficeName', None, univention.admin.mapping.ListToString)
# mapping.register('preferredLanguage', 'preferredLanguage', None, univention.admin.mapping.ListToString)
# mapping.register('postOfficeBox', 'postOfficeBox')
# fmt: on

BLACKLISTED_OBJECT_CLASSES = {b'inetOrgPerson'}


class object(univention.admin.handlers.simpleLdap):
    module = module

    def __init__(self, co, lo, position, dn='', superordinate=None, attributes=[]):
        super().__init__(co, lo, position, dn, superordinate, attributes=attributes)
        univention.admin.syntax.optionsUsersUser.update_choices()  # woraround: somehow init() didn't do it
        self.options.extend(self['_options'])

    def _ldap_object_classes(self, ml):
        ml = super()._ldap_object_classes(ml)
        return self.filter_object_classes(ml)

    def _ldap_object_classes_add(self, al):
        al = super()._ldap_object_classes_add(al)
        return self.filter_object_classes(al)

    @classmethod
    def filter_object_classes(cls, ml):
        """
        Remove blacklisted object classes

        >>> object.filter_object_classes([('objectClass', b'bar', b'inetOrgPerson'), ('objectClass', b'foo', [b'inetOrgPerson', b'baz'])])
        [('objectClass', b'bar', None), ('objectClass', b'foo', [b'baz'])]
        """

        def _iter_ml():
            for x in ml:
                if x[0].lower() != 'objectClass'.lower():
                    yield x
                elif isinstance(x[-1], bytes | str):
                    if x[-1] not in BLACKLISTED_OBJECT_CLASSES:
                        yield x
                    elif len(x) == 3:
                        yield (x[0], x[1], None)
                elif isinstance(x[-1], list | tuple):
                    yield (*list(x[:-1]), [z for z in x[-1] if z not in BLACKLISTED_OBJECT_CLASSES])
                else:
                    yield x

        return list(_iter_ml())

    def _ldap_pre_modify(self):
        super()._ldap_pre_modify()
        self['_options'].extend(self.options)
        self['_options'] = list(set(self['_options']) - {'default'})

    def _ldap_pre_create(self):
        super()._ldap_pre_create()
        self['_options'].extend(self.options)
        self['_options'] = list(set(self['_options']) - {'default'})


lookup = object.lookup
lookup_filter = object.lookup_filter
identify = object.identify
