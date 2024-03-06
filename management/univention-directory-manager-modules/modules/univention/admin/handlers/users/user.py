# -*- coding: utf-8 -*-
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2004-2024 Univention GmbH
#
# https://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <https://www.gnu.org/licenses/>.

"""|UDM| module for the user objects"""

from __future__ import absolute_import

import builtins
import calendar
import copy
import os
import re
import time
import warnings
from datetime import datetime
from logging import getLogger
from typing import Any, Iterable, Sequence  # noqa: F401

import ldap
import passlib.hash
import six
import tzlocal
from ldap.filter import filter_format

import univention.admin
import univention.admin.allocators
import univention.admin.filter
import univention.admin.handlers
import univention.admin.handlers.settings.prohibited_username
import univention.admin.localization
import univention.admin.mapping
import univention.admin.modules
import univention.admin.password
import univention.admin.samba
import univention.admin.syntax
import univention.admin.uexceptions
import univention.admin.uldap
import univention.password
from univention.admin import configRegistry
from univention.admin.certificate import PKIIntegration, pki_option, pki_properties, pki_tab, register_pki_mapping
from univention.admin.layout import Group, Tab
from univention.lib.s4 import rids_for_well_known_security_identifiers


try:  # Python > 3.9
    import zoneinfo
    utc = zoneinfo.ZoneInfo('UTC')
except (ImportError, AttributeError):
    import pytz
    zoneinfo = None  # type: ignore[assignment]
    utc = pytz.utc  # type: ignore[assignment]

if not six.PY2:
    long = int

log = getLogger('ADMIN')

translation = univention.admin.localization.translation('univention.admin.handlers.users')
_ = translation.translate

module = 'users/user'
operations = ['add', 'edit', 'remove', 'search', 'move', 'copy']
template = 'settings/usertemplate'

childs = False
short_description = _('User')
object_name = _('User')
object_name_plural = _('Users')
long_description = _('POSIX, Samba, Kerberos and mail account')


options = {
    'default': univention.admin.option(
        short_description=_('POSIX, Samba, Kerberos and mail account'),
        default=True,
        objectClasses=['top', 'person', 'univentionPWHistory', 'posixAccount', 'shadowAccount', 'sambaSamAccount', 'krb5Principal', 'krb5KDCEntry', 'univentionMail', 'organizationalPerson', 'inetOrgPerson'],
    ),
    'pki': pki_option(),
}
property_descriptions = dict({
    'username': univention.admin.property(
        short_description=_('User name'),
        long_description='',
        syntax=univention.admin.syntax.uid_umlauts,
        include_in_default_search=True,
        required=True,
        identifies=True,
        readonly_when_synced=True,
    ),
    'uidNumber': univention.admin.property(
        short_description=_('User ID'),
        long_description='',
        syntax=univention.admin.syntax.integer,
        may_change=False,
        dontsearch=True,
    ),
    'gidNumber': univention.admin.property(
        short_description=_('Group ID of the primary group'),
        long_description='',
        syntax=univention.admin.syntax.integer,
        may_change=False,
        editable=False,
        dontsearch=True,
        readonly_when_synced=True,
    ),
    'firstname': univention.admin.property(
        short_description=_('First name'),
        long_description='',
        syntax=univention.admin.syntax.TwoThirdsString,
        include_in_default_search=True,
        readonly_when_synced=True,
    ),
    'lastname': univention.admin.property(
        short_description=_('Last name'),
        long_description='',
        syntax=univention.admin.syntax.string,
        include_in_default_search=True,
        required=True,
        readonly_when_synced=True,
    ),
    'gecos': univention.admin.property(
        short_description=_('GECOS'),
        long_description='',
        syntax=univention.admin.syntax.IA5string,
        default='<firstname> <lastname><:umlauts,strip>',
        dontsearch=True,
    ),
    'displayName': univention.admin.property(
        short_description=_('Display name'),
        long_description='',
        syntax=univention.admin.syntax.string,
        default='<firstname> <lastname><:strip>',
        readonly_when_synced=True,
    ),
    'title': univention.admin.property(
        short_description=_('Title'),
        long_description='',
        syntax=univention.admin.syntax.OneThirdString,
        readonly_when_synced=True,
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
    'sambaPrivileges': univention.admin.property(
        short_description=_('Samba privilege'),
        long_description=_('Manage Samba privileges'),
        syntax=univention.admin.syntax.SambaPrivileges,
        multivalue=True,
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
    ),
    'organisation': univention.admin.property(
        short_description=_('Organisation'),
        long_description='',
        syntax=univention.admin.syntax.string64,
        readonly_when_synced=True,
        copyable=True,
    ),
    'userexpiry': univention.admin.property(
        short_description=_('Account expiry date'),
        long_description=_('Specifies the date from when the user is not allowed to login anymore. Enter date as "day.month.year".'),
        syntax=univention.admin.syntax.date2,
        dontsearch=True,
        copyable=True,
    ),
    'passwordexpiry': univention.admin.property(
        short_description=_('Password expiry date'),
        long_description=_('Specified the date from when the user must change his password. Enter date as "day.month.year".'),
        syntax=univention.admin.syntax.date,
        editable=False,
        dontsearch=True,
        readonly_when_synced=True,
    ),
    'pwdChangeNextLogin': univention.admin.property(
        short_description=_('User has to change password on next login'),
        long_description=_('If enabled, the user has to change his password the next time when he logs in.'),
        syntax=univention.admin.syntax.boolean,
        dontsearch=True,
        readonly_when_synced=True,
        size='Two',
    ),
    'preferredLanguage': univention.admin.property(
        short_description=_('Preferred language'),
        long_description=_('Preferred written or spoken language for the person.'),
        syntax=univention.admin.syntax.string,
        copyable=True,
    ),
    'disabled': univention.admin.property(
        short_description=_('Account is deactivated'),
        long_description=_('Disable the user account for Windows, Kerberos and POSIX.'),
        syntax=univention.admin.syntax.disabled,
        show_in_lists=True,
        copyable=True,
        default='0',
        size='Two',
    ),
    'accountActivationDate': univention.admin.property(
        short_description=_('Activate user account starting from'),
        long_description=_('This disables the account until the specified time.'),
        syntax=univention.admin.syntax.ActivationDateTimeTimezone,
        dontsearch=True,
        default=([None, None, str(tzlocal.get_localzone())], []),
    ),
    'locked': univention.admin.property(  # This property only serves two purposes: 1) filtering 2) artificial simulation of lockout
        short_description=_('Locked state of account'),
        long_description=_('This indicates if the account is locked out due to too many authentication failures.'),
        syntax=univention.admin.syntax.locked,
        show_in_lists=True,
        default='0',
    ),
    'lockedTime': univention.admin.property(
        short_description=_('Lockout time'),
        long_description=_('Timestamp when account lockout happened.'),
        syntax=univention.admin.syntax.string,
        default=0,
        may_change=False,  # caution! this gets overwritten by some scripts
        editable=False,  # caution! this gets overwritten by some scripts
        dontsearch=True,
    ),
    'unlock': univention.admin.property(  # Just a trigger to reset self['locked']
        short_description=_('Unlock account'),
        long_description=_('If the account is locked out due to too many login failures, this checkbox allows unlocking.'),
        syntax=univention.admin.syntax.boolean,
        show_in_lists=True,
        default='0',
        prevent_umc_default_popup=True,
    ),
    'unlockTime': univention.admin.property(
        short_description=_('Lockout till'),
        long_description=_('Shows the time when the account gets unlocked again according to policy.'),
        syntax=univention.admin.syntax.string,  # see posixSecondsToLocaltimeDate
        may_change=False,
        editable=False,
        show_in_lists=True,
        dontsearch=True,
    ),
    'password': univention.admin.property(
        short_description=_('Password'),
        long_description='',
        syntax=univention.admin.syntax.userPasswd,
        required=True,
        dontsearch=True,
        readonly_when_synced=True,
    ),
    'street': univention.admin.property(
        short_description=_('Street'),
        long_description='',
        syntax=univention.admin.syntax.string,
        readonly_when_synced=True,
        copyable=True,
    ),
    'e-mail': univention.admin.property(
        short_description=_('E-mail address'),
        long_description=_('This e-mail address serves only as contact information. This address has no effect on the UCS mail stack and is not related to a local mailbox.'),
        syntax=univention.admin.syntax.emailAddress,
        multivalue=True,
    ),
    'postcode': univention.admin.property(
        short_description=_('Postal code'),
        long_description='',
        syntax=univention.admin.syntax.OneThirdString,
        readonly_when_synced=True,
        copyable=True,
    ),
    'postOfficeBox': univention.admin.property(
        short_description=_('Post office box'),
        long_description='',
        syntax=univention.admin.syntax.string,
        multivalue=True,
        copyable=True,
    ),
    'city': univention.admin.property(
        short_description=_('City'),
        long_description='',
        syntax=univention.admin.syntax.TwoThirdsString,
        readonly_when_synced=True,
        copyable=True,
    ),
    'country': univention.admin.property(
        short_description=_('Country'),
        long_description='',
        syntax=univention.admin.syntax.Country,
        readonly_when_synced=True,
        copyable=True,
    ),
    'state': univention.admin.property(
        short_description=_('State'),
        long_description=_('State / Province'),
        syntax=univention.admin.syntax.string,
        readonly_when_synced=True,
        copyable=True,
    ),
    'phone': univention.admin.property(
        short_description=_('Telephone number'),
        long_description='',
        syntax=univention.admin.syntax.phone,
        multivalue=True,
        readonly_when_synced=True,
        copyable=True,
    ),
    'employeeNumber': univention.admin.property(
        short_description=_('Employee number'),
        long_description='',
        syntax=univention.admin.syntax.string,
    ),
    'roomNumber': univention.admin.property(
        short_description=_('Room number'),
        long_description='',
        syntax=univention.admin.syntax.OneThirdString,
        multivalue=True,
        copyable=True,
    ),
    'secretary': univention.admin.property(
        short_description=_('Superior'),
        long_description='',
        syntax=univention.admin.syntax.UserDN,
        multivalue=True,
        copyable=True,
    ),
    'departmentNumber': univention.admin.property(
        short_description=_('Department number'),
        long_description='',
        syntax=univention.admin.syntax.OneThirdString,
        multivalue=True,
        copyable=True,
    ),
    'employeeType': univention.admin.property(
        short_description=_('Employee type'),
        long_description='',
        syntax=univention.admin.syntax.string,
        copyable=True,
    ),
    'homePostalAddress': univention.admin.property(
        short_description=_('Private postal address'),
        long_description='',
        syntax=univention.admin.syntax.postalAddress,
        multivalue=True,
    ),
    'physicalDeliveryOfficeName': univention.admin.property(
        short_description=_('Delivery office name'),
        long_description='',
        syntax=univention.admin.syntax.string,
        copyable=True,
    ),
    'homeTelephoneNumber': univention.admin.property(
        short_description=_('Private telephone number'),
        long_description='',
        syntax=univention.admin.syntax.phone,
        multivalue=True,
        readonly_when_synced=True,
    ),
    'mobileTelephoneNumber': univention.admin.property(
        short_description=_('Mobile phone number'),
        long_description='',
        syntax=univention.admin.syntax.phone,
        multivalue=True,
        readonly_when_synced=True,
    ),
    'pagerTelephoneNumber': univention.admin.property(
        short_description=_('Pager telephone number'),
        long_description='',
        syntax=univention.admin.syntax.phone,
        multivalue=True,
        readonly_when_synced=True,
    ),
    'birthday': univention.admin.property(
        short_description=_('Birthdate'),
        long_description=_('Date of birth'),
        syntax=univention.admin.syntax.iso8601Date,
    ),
    'unixhome': univention.admin.property(
        short_description=_('Unix home directory'),
        long_description='',
        syntax=univention.admin.syntax.absolutePath,
        required=True,
        default='/home/<username>',
    ),
    'shell': univention.admin.property(
        short_description=_('Login shell'),
        long_description='',
        syntax=univention.admin.syntax.OneThirdString,
        default='/bin/bash',
        copyable=True,
    ),
    'sambahome': univention.admin.property(
        short_description=_('Windows home path'),
        long_description=_("The directory path which is used as the user's Windows home directory, e.g. \\\\ucs-file-server\\smith."),
        syntax=univention.admin.syntax.string,
        readonly_when_synced=True,
        copyable=True,
    ),
    'scriptpath': univention.admin.property(
        short_description=_('Windows logon script'),
        long_description=_('The user-specific logon script relative to the NETLOGON share, e.g. user.bat.'),
        syntax=univention.admin.syntax.string,
        readonly_when_synced=True,
        copyable=True,
    ),
    'profilepath': univention.admin.property(
        short_description=_('Windows profile directory'),
        long_description=_('The directory path (resolvable by windows clients) e.g. %LOGONSERVER%\\%USERNAME%\\windows-profiles\\default which is used to configure a roaming profile.'),
        syntax=univention.admin.syntax.string,
        readonly_when_synced=True,
        copyable=True,
    ),
    'homedrive': univention.admin.property(
        short_description=_('Windows home drive'),
        long_description=_('The drive letter (with trailing colon) where the Windows home directory of this user lies, e.g. M:. Needs only be specified if it is different to the Samba configuration.'),
        syntax=univention.admin.syntax.string,
        readonly_when_synced=True,
        copyable=True,
    ),
    'sambaRID': univention.admin.property(
        short_description=_('Relative ID'),
        long_description=_('The relative ID (RID) is the local part of the SID and will be assigned automatically to next available RID. It can not be subsequently changed. Valid values are numbers upwards 1000. RIDs below 1000 are reserved to standard groups and other special objects.'),
        syntax=univention.admin.syntax.integer,
        dontsearch=True,
        readonly_when_synced=True,
    ),
    'groups': univention.admin.property(
        short_description=_('Groups'),
        long_description='',
        syntax=univention.admin.syntax.GroupDN,
        multivalue=True,
        readonly_when_synced=True,
        copyable=True,
    ),
    'primaryGroup': univention.admin.property(
        short_description=_('Primary group'),
        long_description='',
        syntax=univention.admin.syntax.GroupDN,
        required=True,
        dontsearch=True,
        readonly_when_synced=True,
        copyable=True,
    ),
    'mailHomeServer': univention.admin.property(
        short_description=_('Mail home server'),
        long_description='',
        syntax=univention.admin.syntax.MailHomeServer,
        nonempty_is_default=True,
        copyable=True,
    ),
    'mailPrimaryAddress': univention.admin.property(
        short_description=_('Primary e-mail address (mailbox)'),
        long_description=_('E-mail address that will be used to create the IMAP/POP3 mailbox and that can be used as login for SMTP/IMAP/POP3 connections. The domain must be one of the UCS hosted e-mail domains.'),
        syntax=univention.admin.syntax.primaryEmailAddressValidDomain,
        include_in_default_search=True,
        readonly_when_synced=True,
    ),
    'mailAlternativeAddress': univention.admin.property(
        short_description=_('E-mail alias address'),
        long_description=_('Additional e-mail addresses for which e-mails will be delivered to the "Primary e-mail address". The domain must be one of the UCS hosted e-mail domains.'),
        syntax=univention.admin.syntax.emailAddressValidDomain,
        multivalue=True,
        copyable=True,
    ),
    'mailForwardAddress': univention.admin.property(
        short_description=_('Forward e-mail address'),
        long_description=_("Incoming e-mails for this user are copied/redirected to the specified forward e-mail addresses. Depending on the forwarding setting, a local copy of each e-mail is kept. If no forwarding e-mail addresses are specified, the e-mails are always kept in the user's mailbox."),
        syntax=univention.admin.syntax.emailAddress,
        multivalue=True,
        copyable=True,
    ),
    'mailForwardCopyToSelf': univention.admin.property(
        short_description=_('Forwarding setting'),
        long_description=_("Specifies if a local copy of each incoming e-mail is kept for this user. If no forwarding e-mail addresses are specified, the e-mails are always kept in the user's mailbox."),
        syntax=univention.admin.syntax.emailForwardSetting,
        dontsearch=True,
        copyable=True,
        default='0',
        prevent_umc_default_popup=True,
    ),
    'overridePWHistory': univention.admin.property(
        short_description=_('Override password history'),
        long_description=_('No check if the password was already used is performed.'),
        syntax=univention.admin.syntax.boolean,
        dontsearch=True,
        readonly_when_synced=True,
        copyable=True,
    ),
    'overridePWLength': univention.admin.property(
        short_description=_('Override password check'),
        long_description=_('No check for password quality and minimum length is performed.'),
        syntax=univention.admin.syntax.boolean,
        dontsearch=True,
        readonly_when_synced=True,
        copyable=True,
    ),
    'homeShare': univention.admin.property(
        short_description=_('Home share'),
        long_description=_("Share, the user's home directory resides on"),
        syntax=univention.admin.syntax.WritableShare,
        dontsearch=True,
        copyable=True,
    ),
    'homeSharePath': univention.admin.property(
        short_description=_('Home share path'),
        long_description=_('Path to the home directory on the home share'),
        syntax=univention.admin.syntax.HalfString,
        dontsearch=True,
        default='<username>',
        prevent_umc_default_popup=True,
    ),
    'sambaUserWorkstations': univention.admin.property(
        short_description=_('Allow the authentication only on this Microsoft Windows host'),
        long_description=(''),
        syntax=univention.admin.syntax.string,
        multivalue=True,
        readonly_when_synced=True,
        copyable=True,
    ),
    'sambaLogonHours': univention.admin.property(
        short_description=_('Permitted times for Windows logins'),
        long_description=(""),
        syntax=univention.admin.syntax.SambaLogonHours,
        dontsearch=True,
        readonly_when_synced=True,
        copyable=True,
    ),
    'jpegPhoto': univention.admin.property(
        short_description=_("Picture of the user (JPEG format)"),
        long_description=_('Picture for user account in JPEG format'),
        syntax=univention.admin.syntax.jpegPhoto,
        dontsearch=True,
    ),
    'umcProperty': univention.admin.property(
        short_description=_('UMC user preferences'),
        long_description=_('Key value pairs storing user preferences for UMC'),
        syntax=univention.admin.syntax.keyAndValue,
        dontsearch=True,
        multivalue=True,
        copyable=True,
    ),
    'serviceSpecificPassword': univention.admin.property(
        short_description=_('Service Specific Password'),
        long_description=_('Virtual attribute to set different Service Specific Passwords via UDM'),
        syntax=univention.admin.syntax.string,
        dontsearch=True,
        show_in_lists=False,
        cli_enabled=False,
    ),
    'univentionObjectIdentifier': univention.admin.property(
        short_description=_('Immutable Object Identifier'),
        long_description=_('Immutable attribute to track the identity of an object in UDM'),
        syntax=univention.admin.syntax.string,
        may_change=False,
        dontsearch=True,
    ),
    'univentionSourceIAM': univention.admin.property(
        short_description=_('Immutable Identifier of the source IAM'),
        long_description=_('Immutable attribute to identfy source IAM'),
        syntax=univention.admin.syntax.string,
        may_change=False,
        dontsearch=True,
    ),
}, **pki_properties())

layout = [
    Tab(_('General'), _('Basic settings'), layout=[
        Group(_('User account'), layout=[
            ['title', 'firstname', 'lastname'],
            ['username', 'description'],
            'password',
            ['overridePWHistory', 'overridePWLength'],
            'mailPrimaryAddress',
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
    Tab(_('Groups'), _('Groups'), layout=[
        Group(_('Primary group'), layout=[
            'primaryGroup',
        ]),
        Group(_('Additional groups'), layout=[
            'groups',
        ]),
    ]),
    Tab(_('Account'), _('Account settings'), layout=[
        Group(_('Deactivation'), layout=[
            ['disabled'],
            ['userexpiry'],
        ]),
        Group(_('Locked login'), layout=[
            ['pwdChangeNextLogin'],
            ['passwordexpiry'],
            ['unlock'],
            ['unlockTime'],
        ]),
        Group(_('Activation'), layout=[
            ['accountActivationDate'],
        ]),
        Group(_('Windows'), layout=[
            ['homedrive', 'sambahome'],
            ['scriptpath', 'profilepath'],
            'sambaRID',
            'sambaPrivileges',
            'sambaLogonHours',
            'sambaUserWorkstations',
        ]),
        Group(_('POSIX (Linux/UNIX)'), layout=[
            ['unixhome', 'shell'],
            ['uidNumber', 'gidNumber'],
            ['homeShare', 'homeSharePath'],
        ]),
    ]),
    Tab(_('Mail'), _('Mail preferences'), advanced=True, layout=[
        Group(_('Advanced settings'), layout=[
            'mailAlternativeAddress',
            'mailHomeServer',
        ]),
        Group(_('Mail forwarding'), layout=[
            'mailForwardCopyToSelf',
            'mailForwardAddress',
        ]),
    ]),
    Tab(_('Contact'), _('Contact information'), layout=[
        Group(_('Business'), layout=[
            'e-mail',
            'phone',
            ['roomNumber', 'departmentNumber'],
            ['street', 'postcode', 'city'],
            ['state', 'country'] if not configRegistry.is_true('directory/manager/web/modules/users/user/map-country-to-st') else ['country'],
        ]),
        Group(_('Private'), layout=[
            'homeTelephoneNumber',
            'mobileTelephoneNumber',
            'pagerTelephoneNumber',
            'homePostalAddress',
        ]),
    ]),
    Tab('Apps'),  # not translated!
    Tab(_('UMC preferences'), _('UMC preferences'), advanced=True, layout=[
        Group(_('UMC preferences'), layout=[
            'umcProperty',
        ]),
    ]),
    pki_tab(),
]


@univention.admin._ldap_cache(ttl=10, cache_none=False)
def get_primary_group_dn(lo, gid_number):  # type: (univention.admin.uldap.access, int) -> str | None
    groups = lo.searchDn(filter=filter_format(u'(&(|(objectClass=posixGroup)(objectClass=sambaGroupMapping))(gidNumber=%s))', [gid_number]))
    return groups[0] if groups else None


def check_prohibited_username(lo, username):  # type: (univention.admin.uldap.access, str) -> None
    """check if the username is allowed"""
    module = univention.admin.modules._get('settings/prohibited_username')
    for prohibited_object in (module.lookup(None, lo, u'') or []):
        if username in prohibited_object['usernames']:
            raise univention.admin.uexceptions.prohibitedUsername(username)


def case_insensitive_in_list(dn, list):  # type: (str, Sequence[str]) -> bool
    assert isinstance(dn, six.text_type)
    for element in list:
        assert isinstance(element, six.text_type)
        if dn.lower() == element.lower():
            return True
    return False


def posixSecondsToLocaltimeDate(seconds):  # type: (int) -> str
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(seconds))


def posixDaysToDate(days):  # type: (int) -> str
    return time.strftime("%Y-%m-%d", time.gmtime(long(days) * 3600 * 24))


def sambaWorkstationsMap(workstations, encoding=()):  # type: (Sequence[str], Sequence[str]) -> bytes
    return u','.join(workstations).encode(*encoding)


def sambaWorkstationsUnmap(workstations, encoding=()):  # type: (Sequence[bytes], Sequence[str]) -> list[str]
    return workstations[0].decode(*encoding).split(u',')


def logonHoursMap(logontimes):  # type: (Sequence[int]) -> bytes | None
    """
    Convert list-of-bit to the respective hex string.
    >>> logonHoursMap([])
    b'000000000000000000000000000000000000000000'
    >>> logonHoursMap([0])  # Sun 00
    b'010000000000000000000000000000000000000000'
    >>> logonHoursMap([23])  # Sun 23
    b'000080000000000000000000000000000000000000'
    >>> logonHoursMap([24 * 7 - 1])  # Sat 23
    b'000000000000000000000000000000000000000080'
    """
    if logontimes == '':
        # if unsetting it, see Bug #33703
        return None

    # the order of the bits of each byte has to be reversed. The reason for this is that
    # consecutive bytes mean consecutive 8-hrs-intervals, but the MSB stands for
    # the last hour in that interval, the 2nd but leftmost bit for the second-to-last
    # hour and so on. We want to hide this from anybody using this feature.
    # See <http://ma.ph-freiburg.de/tng/tng-technical/2003-04/msg00015.html> for details.
    ret = '%042x' % sum(1 << (24 * 7 - 8 + 2 * (i % 8) - i) for i in logontimes)
    return ret.encode('ASCII')


def logonHoursUnmap(logontimes):  # type: (list[bytes]) -> list[int]
    """
    Convert hex-string to an array of bits set.
    >>> logonHoursUnmap([b"000000000000000000000000000000000000000000"])
    []
    >>> logonHoursUnmap([b"010000000000000000000000000000000000000000"])
    [0]
    >>> logonHoursUnmap([b"000080000000000000000000000000000000000000"])
    [23]
    >>> logonHoursUnmap([b"000000000000000000000000000000000000000080"])
    [167]
    """
    times = logontimes[0].ljust(42, b"0")[:42]
    octets = [int(times[i:i + 2], 16) for i in range(0, 42, 2)]
    return [
        idx * 8 + bit
        for idx, value in enumerate(octets)
        for bit in range(8)
        if value & (1 << bit)
    ]


def GMTOffset():  # type: () -> int
    # returns the difference in hours between local time and GMT (is -1 for CET and CEST)
    return time.timezone // 3600


def mapHomePostalAddress(old, encoding=()):  # type: (Sequence[str], Sequence[str]) -> list[bytes]
    """
    Map address to LDAP encoding.

    >>> mapHomePostalAddress([["a", "b", "c"]])
    [b'a$b$c']
    """
    new = []
    for i in old:
        new.append(u'$'.join(i).encode(*encoding))
    return new


def unmapHomePostalAddress(old, encoding=()):  # type: (Sequence[bytes], Sequence[str]) -> list[list[str]]
    """
    Expand LDAP encoded address.
    >>> unmapHomePostalAddress([b'foo'])
    [['foo', ' ', ' ']]
    >>> unmapHomePostalAddress([b'foo$bar$baz'])
    [['foo', 'bar', 'baz']]
    """
    new = []
    for i in old:
        if b'$' in i:
            new.append(i.decode(*encoding).split(u'$'))
        else:
            new.append([i.decode(*encoding), u" ", u" "])
    return new


def unmapUserExpiry(oldattr):  # type: (dict[str, list[bytes]]) -> str | None
    return unmapKrb5ValidEndToUserexpiry(oldattr) or unmapSambaKickoffTimeToUserexpiry(oldattr) or unmapShadowExpireToUserexpiry(oldattr)


def unmapShadowExpireToUserexpiry(oldattr):  # type: (dict[str, list[bytes]]) -> str | None
    # The shadowLastChange attribute is the amount of days between 1/1/1970 up to the day that password was modified,
    # shadowMax is the number of days a password is valid. So the password expires on 1/1/1970 + shadowLastChange + shadowMax.
    # shadowExpire contains the absolute date to expire the account.

    expire = oldattr.get('shadowExpire')
    if expire:
        date = posixDaysToDate(expire[0])
        log.debug('userexpiry: %s', date)
        if expire[0] != b'1':
            return date


def unmapKrb5ValidEndToUserexpiry(oldattr):  # type: (dict[str, list[bytes]]) -> str | None
    if 'krb5ValidEnd' in oldattr:
        krb5validend = oldattr['krb5ValidEnd'][0].decode('ASCII')
        log.debug('krb5validend is: %s', krb5validend)
        return "%s-%s-%s" % (krb5validend[0:4], krb5validend[4:6], krb5validend[6:8])


def unmapSambaKickoffTimeToUserexpiry(oldattr):  # type: (dict[str, list[bytes]]) -> str | None
    if 'sambaKickoffTime' in oldattr:
        log.debug('sambaKickoffTime is: %s', oldattr['sambaKickoffTime'][0].decode('ASCII'))
        return time.strftime("%Y-%m-%d", time.gmtime(long(oldattr['sambaKickoffTime'][0]) + (3600 * 24)))


def _mapUserExpiryToShadowExpire(userexpiry):  # type: (str) -> str
    return u"%d" % long(time.mktime(time.strptime(userexpiry, "%Y-%m-%d")) / 3600 / 24 + 1)


def _mapUserExpiryToKrb5ValidEnd(userexpiry):  # type: (str) -> str
    return u"%s%s%s000000Z" % (userexpiry[0:4], userexpiry[5:7], userexpiry[8:10])


def _mapUserExpiryToSambaKickoffTime(userexpiry):  # type: (str) -> str
    return u"%d" % long(time.mktime(time.strptime(userexpiry, "%Y-%m-%d")))


def unmapPasswordExpiry(oldattr):  # type: (dict[str, list[bytes]]) -> str
    if oldattr.get('shadowLastChange') and oldattr.get('shadowMax'):
        shadow_max = int(oldattr['shadowMax'][0])
        shadow_last_change = 0
        try:
            shadow_last_change = int(oldattr['shadowLastChange'][0])
        except ValueError:
            log.warning('users/user: failed to calculate password expiration correctly, use only shadowMax instead')
        return posixDaysToDate(shadow_last_change + shadow_max)


def unmapDisabled(oldattr):  # type: (dict[str, list[bytes]]) -> str
    if all([
            unmapSambaDisabled(oldattr),
            unmapKerberosDisabled(oldattr),
            unmapPosixDisabled(oldattr) or isPosixLocked(oldattr),
    ]):
        return '1'
    return '0'


def inconsistentDisabledState(oldattr):  # type: (dict[str, list[bytes]]) -> bool
    disabled = [
        unmapSambaDisabled(oldattr),
        unmapKerberosDisabled(oldattr),
        unmapPosixDisabled(oldattr),
        isPosixLocked(oldattr),
    ]
    return len(set(map(bool, disabled))) > 1


def unmapSambaDisabled(oldattr):  # type: (dict[str, list[bytes]]) -> bool
    flags = oldattr.get('sambaAcctFlags', None)
    if flags:
        acctFlags = univention.admin.samba.acctFlags(flags[0].decode('ASCII'))
        try:
            return acctFlags['D'] == 1
        except KeyError:
            pass
    return False


def unmapKerberosDisabled(oldattr):  # type: (dict[str, list[bytes]]) -> bool
    try:
        kdcflags = int(oldattr.get('krb5KDCFlags', [b'0'])[0])
    except ValueError:
        kdcflags = 0
    return kdcflags & (1 << 7) == (1 << 7)


def unmapPosixDisabled(oldattr):  # type: (dict[str, list[bytes]]) -> bool
    try:
        shadowExpire = int(oldattr['shadowExpire'][0])
    except (KeyError, ValueError):
        return False
    return shadowExpire == 1 or shadowExpire < int(time.time() / 3600 / 24)


def unmapLocked(oldattr):  # type: (dict[str, list[bytes]]) -> str
    if isSambaLocked(oldattr) or isKerberosLocked(oldattr):  # or isLDAPLocked(oldattr)
        return '1'
    return '0'


def inconsistentLockedState(oldattr):  # type: (dict[str, list[bytes]]) -> int
    return isSambaLocked(oldattr) ^ isKerberosLocked(oldattr)


def isPosixLocked(oldattr):  # type: (dict[str, list[bytes]]) -> bool
    userPassword = oldattr.get('userPassword', [b''])[0].decode('ASCII')
    return userPassword and univention.admin.password.is_locked(userPassword)


def isSambaLocked(oldattr):  # type: (dict[str, list[bytes]]) -> bool
    flags = oldattr.get('sambaAcctFlags', None)
    if flags:
        acctFlags = univention.admin.samba.acctFlags(flags[0].decode('ASCII'))
        try:
            return acctFlags['L'] == 1
        except KeyError:
            pass
    return False


def isKerberosLocked(oldattr):  # type: (dict[str, list[bytes]]) -> bool
    flags = oldattr.get('krb5KDCFlags', [b'0'])[0]
    try:
        state = 1 << 17
        return int(flags) & state == state
    except ValueError:
        return False


def isLDAPLocked(oldattr):  # type: (dict[str, list[bytes]]) -> bool
    return bool(oldattr.get('pwdAccountLockedTime', [b''])[0])


def unmapSambaRid(oldattr):  # type: (dict[str, list[bytes]]) -> str
    sid = oldattr.get('sambaSID', [b''])[0]
    pos = sid.rfind(b'-')
    return sid[pos + 1:].decode('ASCII')


def mapKeyAndValue(old, encoding=()):  # type: (Sequence[str], Sequence[str]) -> list[bytes]
    """
    Map (key, value) list to key=value list.

    >>> mapKeyAndValue([("a", "b")])
    [b'a=b']
    """
    return [u'='.join(entry).encode(*encoding) for entry in old]


def unmapKeyAndValue(old, encoding=()):  # type: (Sequence[bytes], Sequence[str]) -> list[list[str]]
    """
    Map (key=value) list to (key, value) list.

    >>> unmapKeyAndValue([b"a=b"])
    [['a', 'b']]
    """
    return [entry.decode(*encoding).split(u'=', 1) for entry in old]


def mapWindowsFiletime(old, encoding=()):  # type: (str, Sequence[str]) -> list[bytes]
    if old:
        if old == "0":
            return [old.encode(*encoding)]
        unixtime = time.strptime(old, '%Y%m%d%H%M%SZ')
        d = long(116444736000000000)  # difference between 1601 and 1970
        windows_filetime = long(calendar.timegm(unixtime)) * 10000000 + d
        return [str(int(windows_filetime)).encode('ASCII')]
    return []


def unmapWindowsFiletime(old, encoding=()):  # type: (Sequence[bytes], Sequence[str]) -> str
    if old and old[0]:
        password_time = int(old[0].decode(*encoding))
        if password_time == 0:
            return u'%d' % (password_time,)
        d = long(116444736000000000)  # difference between 1601 and 1970
        unixtime = (password_time - d) // 10000000
        try:
            return time.strftime('%Y%m%d%H%M%SZ', time.gmtime(unixtime))
        except ValueError:
            # already unixtime, happens in environments with Samba3
            log.debug('Value of sambaBadPasswordTime is not set to a Windows Filetime (100 nanoseconds since January 1, 1601.)\nInstead its set to %s', password_time)
            return time.strftime('%Y%m%d%H%M%SZ', time.gmtime(password_time))
    return u''


def datetime_from_local_datetimetimezone_tuple(local_datetimetimezone_tuple):  # type: (Sequence[str]) -> datetime
    d, t, tz = local_datetimetimezone_tuple
    # dttz_str = module.property_descriptions[key].syntax.tostring(local_datetimetimezone_tuple)
    native_dt = datetime.strptime("%s %s" % (d, t), "%Y-%m-%d %H:%M")
    if zoneinfo:
        return native_dt.replace(tzinfo=zoneinfo.ZoneInfo(tz))
    return pytz.timezone(tz).localize(native_dt)


def mapDateTimeTimezoneTupleToUTCDateTimeString(local_datetimetimezone_tuple, encoding=()):  # type: (Sequence[str], Sequence[str]) -> list[bytes]
    if local_datetimetimezone_tuple and all(local_datetimetimezone_tuple):
        dt = datetime_from_local_datetimetimezone_tuple(local_datetimetimezone_tuple)
        return [dt.astimezone(utc).strftime("%Y%m%d%H%M%SZ").encode(*encoding)]
    return []


def unmapUTCDateTimeToLocaltime(attribute_value, encoding=()):  # type: (Sequence[bytes], Sequence[str]) -> list[str]
    if attribute_value and attribute_value[0]:
        generalizedtime = attribute_value[0].decode(*encoding)
        try:
            utc_datetime = datetime.strptime(generalizedtime, "%Y%m%d%H%M%SZ")
        except ValueError:
            log.error('Value of krb5ValidStart is not in generalizedTime format: %s', generalizedtime)
            raise
        local_datetimetimezone_tuple = datetime.strftime(utc_datetime, "%Y-%m-%d %H:%M UTC").split()
        return local_datetimetimezone_tuple
    return []


mapping = univention.admin.mapping.mapping()
mapping.register('username', 'uid', None, univention.admin.mapping.ListToString)
mapping.register('uidNumber', 'uidNumber', None, univention.admin.mapping.ListToString)
mapping.register('gidNumber', 'gidNumber', None, univention.admin.mapping.ListToString)
mapping.register('title', 'title', None, univention.admin.mapping.ListToString)
mapping.register('initials', 'initials', None, univention.admin.mapping.ListToString)
mapping.register('description', 'description', None, univention.admin.mapping.ListToString)
mapping.register('organisation', 'o', None, univention.admin.mapping.ListToString)

mapping.register('mailPrimaryAddress', 'mailPrimaryAddress', None, univention.admin.mapping.ListToLowerString, encoding='ASCII')
mapping.register('mailAlternativeAddress', 'mailAlternativeAddress', encoding='ASCII')
mapping.register('mailHomeServer', 'univentionMailHomeServer', None, univention.admin.mapping.ListToString)
mapping.register('mailForwardAddress', 'mailForwardAddress')
if configRegistry.is_true('directory/manager/user/activate_ldap_attribute_mailForwardCopyToSelf', False):
    mapping.register('mailForwardCopyToSelf', 'mailForwardCopyToSelf', None, univention.admin.mapping.ListToString)

mapping.register('preferredLanguage', 'preferredLanguage', None, univention.admin.mapping.ListToString)
mapping.register('street', 'street', None, univention.admin.mapping.ListToString)
mapping.register('e-mail', 'mail', encoding='ASCII')
mapping.register('postcode', 'postalCode', None, univention.admin.mapping.ListToString)
mapping.register('postOfficeBox', 'postOfficeBox')
mapping.register('city', 'l', None, univention.admin.mapping.ListToString)
if configRegistry.is_true('directory/manager/web/modules/users/user/map-country-to-st'):  # old broken behavior
    mapping.register('country', 'st', None, univention.admin.mapping.ListToString)
else:
    mapping.register('country', 'c', None, univention.admin.mapping.ListToString)
    mapping.register('state', 'st', None, univention.admin.mapping.ListToString)
mapping.register('phone', 'telephoneNumber')
mapping.register('roomNumber', 'roomNumber')
mapping.register('employeeNumber', 'employeeNumber', None, univention.admin.mapping.ListToString)
mapping.register('employeeType', 'employeeType', None, univention.admin.mapping.ListToString)
mapping.register('secretary', 'secretary')
mapping.register('departmentNumber', 'departmentNumber')
mapping.register('mobileTelephoneNumber', 'mobile')
mapping.register('pagerTelephoneNumber', 'pager')
mapping.register('homeTelephoneNumber', 'homePhone')
mapping.register('homePostalAddress', 'homePostalAddress', mapHomePostalAddress, unmapHomePostalAddress)
mapping.register('physicalDeliveryOfficeName', 'physicalDeliveryOfficeName', None, univention.admin.mapping.ListToString)
mapping.register('preferredDeliveryMethod', 'preferredDeliveryMethod', None, univention.admin.mapping.ListToString)
mapping.register('unixhome', 'homeDirectory', None, univention.admin.mapping.ListToString)
mapping.register('shell', 'loginShell', None, univention.admin.mapping.ListToString, encoding='ASCII')
mapping.register('sambahome', 'sambaHomePath', None, univention.admin.mapping.ListToString)
mapping.register('sambaUserWorkstations', 'sambaUserWorkstations', sambaWorkstationsMap, sambaWorkstationsUnmap)
mapping.register('sambaLogonHours', 'sambaLogonHours', logonHoursMap, logonHoursUnmap, encoding='ASCII')
mapping.register('sambaPrivileges', 'univentionSambaPrivilegeList', encoding='ASCII')
mapping.register('scriptpath', 'sambaLogonScript', None, univention.admin.mapping.ListToString)
mapping.register('profilepath', 'sambaProfilePath', None, univention.admin.mapping.ListToString)
mapping.register('homedrive', 'sambaHomeDrive', None, univention.admin.mapping.ListToString, encoding='ASCII')
mapping.register('gecos', 'gecos', None, univention.admin.mapping.ListToString, encoding='ASCII')
mapping.register('displayName', 'displayName', None, univention.admin.mapping.ListToString)
mapping.register('birthday', 'univentionBirthday', None, univention.admin.mapping.ListToString)
mapping.register('lastname', 'sn', None, univention.admin.mapping.ListToString)
mapping.register('firstname', 'givenName', None, univention.admin.mapping.ListToString)
mapping.register('jpegPhoto', 'jpegPhoto', univention.admin.mapping.mapBase64, univention.admin.mapping.unmapBase64)
mapping.register('umcProperty', 'univentionUMCProperty', mapKeyAndValue, unmapKeyAndValue)
mapping.register('lockedTime', 'sambaBadPasswordTime', mapWindowsFiletime, unmapWindowsFiletime)
mapping.register('accountActivationDate', 'krb5ValidStart', mapDateTimeTimezoneTupleToUTCDateTimeString, unmapUTCDateTimeToLocaltime, encoding='ASCII')
mapping.register('univentionObjectIdentifier', 'univentionObjectIdentifier', None, univention.admin.mapping.ListToString)
mapping.register('univentionSourceIAM', 'univentionSourceIAM', None, univention.admin.mapping.ListToString)

mapping.registerUnmapping('sambaRID', unmapSambaRid)
mapping.registerUnmapping('passwordexpiry', unmapPasswordExpiry)
mapping.registerUnmapping('userexpiry', unmapUserExpiry)
mapping.registerUnmapping('disabled', unmapDisabled)
mapping.registerUnmapping('locked', unmapLocked)
mapping.register('password', 'userPassword', univention.admin.mapping.dontMap(), univention.admin.mapping.ListToString)
register_pki_mapping(mapping)

default_property_descriptions = copy.deepcopy(property_descriptions)  # for later reset of descriptions

_sentinel = builtins.object()


class object(univention.admin.handlers.simpleLdap, PKIIntegration):
    module = module

    use_performant_ldap_search_filter = True

    def __init__(
        self,
        co,  # type: None
        lo,  # type: univention.admin.uldap.access
        position,  # type: univention.admin.uldap.position
        dn=u'',  # type: str
        superordinate=None,  # type: univention.admin.handlers.simpleLdap | None
        attributes=None,  # type: dict[str, bytes | list[bytes]] | None
    ):  # type: (...) -> None
        self.__groups_loaded = True
        self.password_length = 8

        univention.admin.handlers.simpleLdap.__init__(self, co, lo, position, dn, superordinate, attributes=attributes)

    def _simulate_legacy_options(self):  # type: () -> None
        """simulate old options behavior to provide backward compatibility for udm extensions"""
        options = {
            "posix": b'posixAccount',
            "samba": b'sambaSamAccount',
            "kerberos": b'krb5Principal',
            "mail": b'univentionMail',
            "person": b'person',
        }
        for opt, oc in options.items():
            # existing object
            if self.oldattr:
                if oc in self.oldattr.get('objectClass', []):
                    self.options.append(opt)
            # new object
            else:
                self.options.append(opt)

    def _post_unmap(self, info, values):
        # type: (univention.admin.handlers._Properties, univention.admin.handlers._Attributes) -> univention.admin.handlers._Properties
        info = super(object, self)._post_unmap(info, values)
        if configRegistry.is_true('directory/manager/user/group-memberships-via-memberof', True):
            info['groups'] = [x.decode('UTF-8') for x in values.get('memberOf', [])]
            self.__groups_loaded = True
        self._unmap_mail_forward(info, values)
        self._unmap_pwd_change_next_login(info, values)
        return info

    def open(self, loadGroups=_sentinel):  # type: (builtins.object) -> None
        if loadGroups is not _sentinel:
            warnings.warn('UDM users/user:open() called with deprecated loadGroups!', DeprecationWarning)  # noqa: B028
        univention.admin.handlers.simpleLdap.open(self)
        self.pki_open()
        if self.exists():
            self._unmap_automount_information()
            self._unmapUnlockTime()
            self._load_groups(loadGroups)
            self._unmap_gid_number()
        self.save()
        # self.save() must not be called after this point in self.open()
        # otherwise self.__primary_group doesn't add a new user to the
        # univentionDefaultGroup because "not self.hasChanged('primaryGroup')"
        if not self.exists():
            self._set_default_group()

    def _load_groups(self, loadGroups):  # type: (bool) -> None
        if configRegistry.is_true('directory/manager/user/group-memberships-via-memberof', True):
            return
        if loadGroups:  # this is optional because it can take much time on larger installations, default is true
            self['groups'] = [x.decode('UTF-8') if six.PY2 else x for x in self.lo.searchDn(filter=filter_format(u'(&(|(objectClass=univentionGroup)(objectClass=sambaGroupMapping))(uniqueMember=%s))', [self.dn]))]
        else:  # TODO: document where it is needed and used
            log.debug('user: open with loadGroups=false for user %s', self['username'])
        self.__groups_loaded = bool(loadGroups)

    def _unmap_gid_number(self):  # type: () -> None
        primaryGroupNumber = self.oldattr.get('gidNumber', [b''])[0].decode('ASCII')
        if not primaryGroupNumber:
            self.info['primaryGroup'] = None
            self.save()
            raise univention.admin.uexceptions.primaryGroup(self.dn)

        primary_group = get_primary_group_dn(self.lo, primaryGroupNumber)
        if primary_group:
            self['primaryGroup'] = primary_group
            return

        log.error('No primary group was found with gidNumber=%s for %s as %s', primaryGroupNumber, self.dn, self.lo.binddn)

    def _set_default_group(self):  # type: () -> None
        if not self['primaryGroup']:
            for _dn, attrs in self.lo.search(filter='(objectClass=univentionDefault)', base=u'cn=univention,' + self.position.getDomain(), attr=['univentionDefaultGroup']):
                primary_group = attrs['univentionDefaultGroup'][0].decode('UTF-8')
                log.debug('user: setting primaryGroup to %s', primary_group)
                if self.lo.get(primary_group):
                    self['primaryGroup'] = primary_group

        if not self['primaryGroup']:
            raise univention.admin.uexceptions.primaryGroup(self.dn)

    def _unmap_pwd_change_next_login(self, info, oldattr):
        info['pwdChangeNextLogin'] = '0'
        if oldattr.get('shadowLastChange', [b''])[0] == b'0':
            info['pwdChangeNextLogin'] = '1'
        elif info['passwordexpiry']:
            today = time.strftime('%Y-%m-%d').split('-')
            expiry = info['passwordexpiry'].split('-')
            # expiry.reverse()
            # today.reverse()
            if int(''.join(today)) >= int(''.join(expiry)):
                info['pwdChangeNextLogin'] = '1'

    def _unmap_mail_forward(self, info, oldattr):
        if configRegistry.is_true('directory/manager/user/activate_ldap_attribute_mailForwardCopyToSelf', False):
            return
        # mailForwardCopyToSelf is a "virtual" property. The boolean value is set to True, if
        # the LDAP attribute mailForwardAddress contains the mailPrimaryAddress. The mailPrimaryAddress
        # is removed from oldattr for correct display in CLI/UMC and for proper detection of changes.
        # Remark: By setting the ucr-v the attribute is saved directly to LDAP.
        if info.get('mailPrimaryAddress') in info.get('mailForwardAddress', []):
            oldattr['mailForwardAddress'] = oldattr.get('mailForwardAddress', [])[:]
            info['mailForwardAddress'].remove(info['mailPrimaryAddress'])
            info['mailForwardCopyToSelf'] = '1'
        else:
            info['mailForwardCopyToSelf'] = '0'

    def _unmap_automount_information(self):  # type: () -> None
        if 'automountInformation' not in self.oldattr:
            return
        try:
            _flags, unc = re.split(b' +', self.oldattr['automountInformation'][0], 1)  # noqa: B034
            host, path = unc.split(b':', 1)
        except ValueError:
            return

        host, path = host.decode('ASCII'), path.decode('ASCII')

        sharepath = path
        while len(sharepath) > 1:
            filter_ = univention.admin.filter.conjunction('&', [
                univention.admin.filter.expression('univentionShareHost', host, escape=True),
                univention.admin.filter.conjunction('|', [
                    univention.admin.filter.expression('univentionSharePath', sharepath.rstrip(u'/'), escape=True),
                    univention.admin.filter.expression('univentionSharePath', u'%s/' % (sharepath.rstrip(u'/')), escape=True),
                ]),
            ])
            res = univention.admin.modules.lookup(univention.admin.modules._get('shares/share'), None, self.lo, filter=filter_, scope='domain')
            if len(res) == 1:
                self['homeShare'] = res[0].dn
                # Py3.9+: self['homeSharePath'] = path.removeprefix(sharepath).lstrip("/")
                assert path.startswith(sharepath)
                self['homeSharePath'] = path[len(sharepath):].lstrip("/")
                break
            elif len(res) > 1:
                break
            elif not res:
                sharepath = os.path.dirname(sharepath)

    def _unmapUnlockTime(self):  # type: () -> None
        self.info['unlockTime'] = ''
        locked_timestamp = self['lockedTime']
        if locked_timestamp and locked_timestamp != "0":
            try:
                locked_unixtime = long(calendar.timegm(time.strptime(locked_timestamp, '%Y%m%d%H%M%SZ')))
                lockout_duration = int(self.lo.search(filter='objectClass=sambaDomain', attr=['sambaLockoutDuration'])[0][1].get('sambaLockoutDuration', [0])[0])
            except (ValueError, KeyError, IndexError, AttributeError):
                return

            if lockout_duration == 0:
                self.info['unlockTime'] = _("unlimited")
            else:
                self.info['unlockTime'] = posixSecondsToLocaltimeDate(lockout_duration + locked_unixtime)

    def modify(self, *args, **kwargs):
        try:
            return super(object, self).modify(*args, **kwargs)
        except univention.admin.uexceptions.licenseDisableModify:
            # it has to be possible to deactivate an user account when the license is exceeded
            if self['disabled'] != '1' or not self.hasChanged('disabled'):
                raise
            kwargs['ignore_license'] = True
            return super(object, self).modify(*args, **kwargs)

    def hasChanged(self, key):  # type: (str | Iterable[str]) -> bool
        if key == 'disabled' and inconsistentDisabledState(self.oldattr):
            return True
        if key == 'locked' and inconsistentLockedState(self.oldattr):
            return True
        return super(object, self).hasChanged(key)

#        if key == 'disabled':
#            acctFlags = univention.admin.samba.acctFlags(self.oldattr.get("sambaAcctFlags", [b''])[0].decode('ASCII')).decode()
#            krb5Flags = self.oldattr.get('krb5KDCFlags', [])
#            shadowExpire = self.oldattr.get('shadowExpire', [])
#
#            if not acctFlags and not krb5Flags and not shadowExpire:
#                return False
#            if self['disabled'] == 'all':
#                return 'D' not in acctFlags or b'126' in krb5Flags or b'1' not in shadowExpire
#            elif self['disabled'] == 'windows':
#                return 'D' not in acctFlags or b'254' in krb5Flags or b'1' in shadowExpire
#            elif self['disabled'] == 'kerberos':
#                return 'D' in acctFlags or b'126' in krb5Flags or b'1' in shadowExpire
#            elif self['disabled'] == 'posix':
#                return 'D' in acctFlags or b'254' in krb5Flags or b'1' not in shadowExpire
#            elif self['disabled'] == 'windows_kerberos':
#                return 'D' not in acctFlags or b'126' in krb5Flags or b'1' in shadowExpire
#            elif self['disabled'] == 'windows_posix':
#                return 'D' not in acctFlags or b'254' in krb5Flags or b'1' not in shadowExpire
#            elif self['disabled'] == 'posix_kerberos':
#                return 'D' in acctFlags or b'126' in krb5Flags or b'1' not in shadowExpire
#            else:  # enabled
#                return 'D' in acctFlags or b'254' in krb5Flags or b'1' in shadowExpire
#        elif key == 'locked':
#            password = self['password']
#            acctFlags = univention.admin.samba.acctFlags(self.oldattr.get("sambaAcctFlags", [b''])[0].decode('ASCII')).decode()
#            if not password and not acctFlags:
#                return False
#            if self['locked'] == 'all':
#                return not univention.admin.password.is_locked(password) or 'L' not in acctFlags
#            elif self['locked'] == 'windows':
#                return univention.admin.password.is_locked(password) or 'L' not in acctFlags
#            elif self['locked'] == 'posix':
#                return not univention.admin.password.is_locked(password) or 'L' in acctFlags
#            else:
#                return univention.admin.password.is_locked(password) or 'L' in acctFlags
#
#        return super(object, self).hasChanged(key)

    def __update_groups(self):
        # type: () -> None
        if not self.__groups_loaded:
            return

        if self.exists():
            old_groups = self.oldinfo.get('groups', [])
            old_uid = self.oldinfo.get('username', '')
        else:
            old_groups = []
            old_uid = ""
        new_uid = self.info.get('username', '')
        new_groups = self.info.get('groups', [])

        # change memberUid if we have a new username
        if old_uid and old_uid != new_uid and self.exists():
            log.debug('users/user: rewrite memberuid after rename')
            for group in new_groups:
                self.__rewrite_member_uid(group)

        group_mod = univention.admin.modules._get('groups/group')

        log.debug('users/user: check groups in old_groups')
        for group in old_groups:
            if group and not case_insensitive_in_list(group, self.info.get('groups', [])) and group.lower() != self['primaryGroup'].lower():
                grpobj = group_mod.object(None, self.lo, self.position, group)
                grpobj.fast_member_remove([self.old_dn], [old_uid])
                if self.dn != self.old_dn:
                    # we change our DN _before_ removing it from the group
                    # so if we changed it and if we use refint overlay, it already updated the uniqueMember of the group and we will not catch it with old_dn
                    grpobj.fast_member_remove([self.dn], [old_uid])

        log.debug('users/user: check groups in info[groups]')
        for group in self.info.get('groups', []):
            if group and not case_insensitive_in_list(group, old_groups):
                grpobj = group_mod.object(None, self.lo, self.position, group)
                grpobj.fast_member_add([self.dn], [new_uid])

        if configRegistry.is_true("directory/manager/user/primarygroup/update", True):
            log.debug('users/user: check primaryGroup')
            if not self.exists() and self.info.get('primaryGroup'):
                grpobj = group_mod.object(None, self.lo, self.position, self.info.get('primaryGroup'))
                grpobj.fast_member_add([self.dn], [new_uid])

    def __rewrite_member_uid(self, group, members=[]):
        uids = self.lo.getAttr(group, 'memberUid')
        if not members:
            members = self.lo.getAttr(group, 'uniqueMember')
        new_uids = []
        for memberDNstr in members:
            memberDN = ldap.dn.str2dn(memberDNstr)
            if memberDN[0][0][0] == 'uid':  # UID is stored in DN --> use UID directly
                new_uids.append(memberDN[0][0][1].encode('UTF-8'))
            else:
                UIDs = self.lo.getAttr(memberDNstr.decode('UTF-8'), 'uid')
                if UIDs:
                    new_uids.append(UIDs[0])
                    if len(UIDs) > 1:
                        log.warning('users/user: A groupmember has multiple UIDs (%s %r)', memberDNstr, UIDs)
        self.lo.modify(group, [('memberUid', uids, new_uids)])  # TODO: check if encoding is correct

    def __primary_group(self):
        # type: () -> None
        if not self.hasChanged('primaryGroup'):
            return

        if configRegistry.is_true("directory/manager/user/primarygroup/update", True):
            new_uid = self.info.get('username')
            group_mod = univention.admin.modules._get('groups/group')
            grpobj = group_mod.object(None, self.lo, self.position, self['primaryGroup'])
            grpobj.fast_member_add([self.dn], [new_uid])
            log.debug('users/user: adding to new primaryGroup %s (uid=%s)', self['primaryGroup'], new_uid)

    def krb5_principal(self):
        # type: () -> str
        domain = univention.admin.uldap.domain(self.lo, self.position)
        realm = domain.getKerberosRealm()
        if not realm:
            raise univention.admin.uexceptions.noKerberosRealm()
        return self['username'] + '@' + realm

    def _check_uid_gid_uniqueness(self):
        # type: () -> None
        if not configRegistry.is_true("directory/manager/uid_gid/uniqueness", True):
            return
        # POSIX, Samba
        fg = univention.admin.filter.expression('gidNumber', self['uidNumber'])
        group_objects = univention.admin.handlers.groups.group.lookup(self.co, self.lo, filter_s=fg)
        if group_objects:
            raise univention.admin.uexceptions.uidNumberAlreadyUsedAsGidNumber(repr(self["uidNumber"]))

    def _ldap_pre_create(self):
        # type: () -> None
        super(object, self)._ldap_pre_create()
        log.debug('users/user: dn was set to %s', self.dn)

        # request a new uidNumber or get lock for manually set uidNumber
        if self['uidNumber']:
            univention.admin.allocators.acquireUnique(self.lo, self.position, 'uidNumber', self['uidNumber'], 'uidNumber', scope='base')
            # "False" ==> do not update univentionLastUsedValue in LDAP if a specific value has been specified
            self.alloc.append(('uidNumber', self['uidNumber'], False))
        else:
            self['uidNumber'] = self.request_lock('uidNumber')

        if self['univentionObjectIdentifier']:
            univention.admin.allocators.acquireUnique(self.lo, self.position, 'univentionObjectIdentifier', self['univentionObjectIdentifier'], 'univentionObjectIdentifier', scope='base')
            # "False" ==> do not update univentionLastUsedValue in LDAP if a specific value has been specified
            self.alloc.append(('univentionObjectIdentifier', self['univentionObjectIdentifier'], False))

        self._check_uid_gid_uniqueness()

    def _ldap_pre_ready(self):
        # type: () -> None
        super(object, self)._ldap_pre_ready()

        if self.exists() and not self.oldinfo.get('password') and not self['password']:
            # password property is required but LDAP ACL's disallow reading them
            self.info['password'] = self.oldinfo['password'] = u'*'
            self.info['disabled'] = self.oldinfo['disabled']

        self._set_default_group()
        if not self.exists() or self.hasChanged('primaryGroup'):
            # Ensure the primary Group has the samba option enabled
            if self['primaryGroup'] and not self.lo.getAttr(self['primaryGroup'], 'sambaSID'):
                raise univention.admin.uexceptions.primaryGroupWithoutSamba(self['primaryGroup'])

        if not self.exists() or self.hasChanged('username') and self['username'].lower() != self.oldinfo['username'].lower():
            check_prohibited_username(self.lo, self['username'])

            # get lock for username
            try:
                if self['username']:  # might not be set when using CLI without --set username=
                    self.request_lock('uid', self['username'])
            except univention.admin.uexceptions.noLock:
                raise univention.admin.uexceptions.uidAlreadyUsed(self['username'])

        # get lock for mailPrimaryAddress
        if not self.exists() or self.hasChanged('mailPrimaryAddress'):
            if self['mailPrimaryAddress']:
                self['mailPrimaryAddress'] = self['mailPrimaryAddress'].lower()

            # ignore case in change of mailPrimaryAddress, we only store the lowercase address anyway
            if self['mailPrimaryAddress'] and self['mailPrimaryAddress'].lower() != (self.oldinfo.get('mailPrimaryAddress', None) or '').lower():
                try:
                    self.request_lock('mailPrimaryAddress', self['mailPrimaryAddress'])
                except univention.admin.uexceptions.noLock:
                    raise univention.admin.uexceptions.mailAddressUsed(self['mailPrimaryAddress'])

        # get lock for mailAlternativeAddress
        if (not self.exists() or self.hasChanged('mailAlternativeAddress')) and self['mailAlternativeAddress']:
            old_maas, new_maas = ({addr.lower() for addr in info.get('mailAlternativeAddress', [])} for info in (self.oldinfo, self.info))
            for added_maa in (new_maas - old_maas):
                # uniqueness for mailAlternativeAddress
                try:
                    self.request_lock('mailAlternativeAddress', added_maa)
                except univention.admin.uexceptions.noLock:
                    raise univention.admin.uexceptions.mailAddressUsed(added_maa)

        if self['unlock'] == '1':
            self['locked'] = u'0'
        if self.hasChanged('disabled') and self['disabled'] == '0' and not self.hasChanged('accountActivationDate'):
            self['accountActivationDate'] = self.descriptions['accountActivationDate'].default(self)
        if self['accountActivationDate'] and all(self['accountActivationDate']) and datetime.now(tz=utc) < datetime_from_local_datetimetimezone_tuple(self['accountActivationDate']):
            self['disabled'] = '1'
        if self['disabled'] == '1':
            self['locked'] = u'0'  # Samba/AD behavior

        # legacy options to make old hooks happy (46539)
        self._simulate_legacy_options()

    def _ldap_addlist(self):
        # type: () -> list[tuple[str, Any]]
        al = super(object, self)._ldap_addlist()

        # Kerberos
        al.append((u'krb5MaxLife', b'86400'))
        al.append((u'krb5MaxRenew', b'604800'))

        return al

    def _ldap_post_create(self):
        # type: () -> None
        super(object, self)._ldap_post_create()
        self.__update_groups()
        self.__primary_group()

    def _ldap_post_modify(self):
        # type: () -> None
        super(object, self)._ldap_post_modify()
        # POSIX
        self.__update_groups()
        self.__primary_group()

    def _ldap_pre_rename(self, newdn):
        # type: (str) -> None
        super(object, self)._ldap_pre_rename(newdn)
        try:
            self.move(newdn)
        finally:
            univention.admin.allocators.release(self.lo, self.position, 'uid', self['username'])

    def _ldap_pre_modify(self):
        # type: () -> None
        super(object, self)._ldap_pre_modify()
        if not self.oldattr.get('mailForwardCopyToSelf') and self['mailForwardCopyToSelf'] == '0' and not self['mailForwardAddress']:
            self['mailForwardCopyToSelf'] = None

        if self.hasChanged("uidNumber"):
            # this should never happen, as uidNumber is marked as unchangeable
            self._check_uid_gid_uniqueness()

    def _ldap_modlist(self):
        # type: () -> list[tuple[str, Any, Any]]
        ml = univention.admin.handlers.simpleLdap._ldap_modlist(self)

        ml = self._modlist_pwd_account_locked_time(ml)
        ml = self._modlist_samba_privileges(ml)
        ml = self._modlist_cn(ml)
        ml = self._modlist_gecos(ml)
        ml = self._modlist_display_name(ml)
        ml = self._modlist_krb_principal(ml)
        ml = self._modlist_krb5kdc_flags(ml)
        ml = self._modlist_posix_password(ml)
        ml = self._modlist_kerberos_password(ml)
        if not self.exists() or self.hasChanged(['password', 'pwdChangeNextLogin']):
            pwhistoryPolicy = univention.admin.password.PasswortHistoryPolicy(self.loadPolicyObject('policies/pwhistory'))
            ml = self._check_password_history(ml, pwhistoryPolicy)
            self._check_password_complexity(pwhistoryPolicy)
            ml = self._modlist_samba_password(ml, pwhistoryPolicy)
            ml = self._modlist_password_expiry(ml, pwhistoryPolicy)
        ml = self._modlist_samba_bad_pw_count(ml)
        ml = self._modlist_sambaAcctFlags(ml)
        ml = self._modlist_samba_kickoff_time(ml)
        ml = self._modlist_krb5_valid_end(ml)
        ml = self._modlist_shadow_expire(ml)
        ml = self._modlist_mail_forward(ml)
        ml = self._modlist_home_share(ml)
        ml = self._modlist_samba_sid(ml)
        ml = self._modlist_primary_group(ml)
        ml = self._modlist_service_specific_password(ml)
        ml = self._modlist_univention_person(ml)

        return ml

    def _modlist_samba_privileges(self, ml):
        # type: (list[tuple[str, Any, Any]]) -> list[tuple[str, Any, Any]]
        if self.hasChanged('sambaPrivileges'):
            # add univentionSambaPrivileges objectclass
            if self['sambaPrivileges'] and b'univentionSambaPrivileges' not in self.oldattr.get('objectClass', []):
                ml.append(('objectClass', b'', b'univentionSambaPrivileges'))
        return ml

    def _modlist_cn(self, ml):
        # type: (list[tuple[str, Any, Any]]) -> list[tuple[str, Any, Any]]
        cnAtts = configRegistry.get('directory/manager/usercn/attributes', "<firstname> <lastname>")
        prop = univention.admin.property()
        old_cn = self.oldattr.get('cn', [b''])[0]
        cn = prop._replace(cnAtts, self)  # TODO: prop._replace() must return unicode
        cn = cn.strip() or cn
        cn = cn.encode('UTF-8')
        if cn != old_cn:
            ml.append(('cn', old_cn, cn))
        return ml

    def _modlist_gecos(self, ml):
        # type: (list[tuple[str, Any, Any]]) -> list[tuple[str, Any, Any]]
        if self.hasChanged(['firstname', 'lastname']):
            prop = self.descriptions['gecos']
            old_gecos = self.oldattr.get('gecos', [b''])[0]
            gecos = prop._replace(prop.base_default, self)
            if old_gecos:
                current_gecos = prop._replace(prop.base_default, self.oldinfo)
                current_gecos = current_gecos.encode('utf-8')
                if current_gecos == old_gecos:
                    ml.append(('gecos', old_gecos, [gecos.encode('utf-8')]))
        return ml

    def _modlist_display_name(self, ml):
        # type: (list[tuple[str, Any, Any]]) -> list[tuple[str, Any, Any]]
        # update displayName automatically if no custom value has been entered by the user and the name changed
        if self.info.get('displayName') == self.oldinfo.get('displayName') and (self.info.get('firstname') != self.oldinfo.get('firstname') or self.info.get('lastname') != self.oldinfo.get('lastname')):
            prop_displayName = self.descriptions['displayName']
            old_default_displayName = prop_displayName._replace(prop_displayName.base_default, self.oldinfo)
            # does old displayName match with old default displayName?
            if self.oldinfo.get('displayName', '') == old_default_displayName:
                # yes ==> update displayName automatically
                new_displayName = prop_displayName._replace(prop_displayName.base_default, self)
                ml.append(('displayName', self.oldattr.get('displayName', [b''])[0], new_displayName.encode('utf-8')))
        return ml

    def _modlist_krb_principal(self, ml):
        # type: (list[tuple[str, Any, Any]]) -> list[tuple[str, Any, Any]]
        if not self.exists() or self.hasChanged('username'):
            ml.append(('krb5PrincipalName', self.oldattr.get('krb5PrincipalName', []), [self.krb5_principal().encode('utf-8')]))  # TODO: decide to let krb5_principal return bytestring?!
        return ml

    # If you change anything here, please also check users/ldap.py
    def _check_password_history(self, ml, pwhistoryPolicy):
        # type: (list[tuple[str, Any, Any]], univention.admin.password.PasswortHistoryPolicy) -> list[tuple[str, Any, Any]]
        if self.exists() and not self.hasChanged('password'):
            return ml

        pwhistory = self.oldattr.get('pwhistory', [b''])[0].decode('ASCII')
        if univention.admin.password.password_already_used(self['password'], pwhistory):
            if self['overridePWHistory'] == '1':
                return ml
            raise univention.admin.uexceptions.pwalreadyused()

        if pwhistoryPolicy.pwhistoryLength is not None:
            newPWHistory = univention.admin.password.get_password_history(self['password'], pwhistory, pwhistoryPolicy.pwhistoryLength)
            ml.append(('pwhistory', self.oldattr.get('pwhistory', [b''])[0], newPWHistory.encode('ASCII')))

        return ml

    # If you change anything here, please also check users/ldap.py
    def _check_password_complexity(self, pwhistoryPolicy):
        # type: (univention.admin.password.PasswortHistoryPolicy) -> None
        if self.exists() and not self.hasChanged('password'):
            return
        if self['overridePWLength'] == '1':
            return

        password_minlength = max(0, pwhistoryPolicy.pwhistoryPasswordLength) or self.password_length
        if len(self['password']) < password_minlength:
            raise univention.admin.uexceptions.pwToShort(_('The password is too short, at least %d characters needed!') % (password_minlength,))

        if pwhistoryPolicy.pwhistoryPasswordCheck:
            pwdCheck = univention.password.Check(self.lo)
            pwdCheck.enableQualityCheck = True
            try:
                pwdCheck.check(self['password'], username=self['username'], displayname=self['displayName'])
            except univention.password.CheckFailed as exc:
                raise univention.admin.uexceptions.pwQuality(str(exc))

    def _modlist_samba_password(self, ml, pwhistoryPolicy):
        # type: (list[tuple[str, Any, Any]], univention.admin.password.PasswortHistoryPolicy) -> list[tuple[str, Any, Any]]
        if self.exists() and not self.hasChanged('password'):
            return ml

        password_nt, password_lm = univention.admin.password.ntlm(self['password'])  # TODO: decide to let ntlm() return bytestring?!
        password_nt, password_lm = password_nt.encode('ASCII'), password_lm.encode('ASCII')
        ml.append(('sambaNTPassword', self.oldattr.get('sambaNTPassword', [b''])[0], password_nt))
        ml.append(('sambaLMPassword', self.oldattr.get('sambaLMPassword', [b''])[0], password_lm))
        return ml

    def _modlist_kerberos_password(self, ml):
        # type: (list[tuple[str, Any, Any]]) -> list[tuple[str, Any, Any]]
        if self.exists() and not self.hasChanged('password'):
            return ml

        krb_keys = univention.admin.password.krb5_asn1(self.krb5_principal(), self['password'])
        krb_key_version = str(int(self.oldattr.get('krb5KeyVersionNumber', ['0'])[0]) + 1).encode('ASCII')
        ml.append(('krb5Key', self.oldattr.get('krb5Key', []), krb_keys))
        ml.append(('krb5KeyVersionNumber', self.oldattr.get('krb5KeyVersionNumber', []), krb_key_version))
        return ml

    def _modlist_password_expiry(self, ml, pwhistoryPolicy):
        # type: (list[tuple[str, Any, Any]], univention.admin.password.PasswortHistoryPolicy) -> list[tuple[str, Any, Any]]
        pwd_change_next_login = self.hasChanged('pwdChangeNextLogin') and self['pwdChangeNextLogin'] == '1'
        unset_pwd_change_next_login = self.hasChanged('pwdChangeNextLogin') and self['pwdChangeNextLogin'] == '0'

        now = (long(time.time()) / 3600 / 24)
        shadowLastChange = str(int(now))
        shadowMax = str(pwhistoryPolicy.expiryInterval or u'')  # FIXME: is pwhistoryPolicy.expiryInterval a unicode or bytestring?
        if pwd_change_next_login:
            # force user to change password on next login
            shadowMax = shadowMax or '1'
            shadowLastChange = str(int(now) - int(shadowMax) - 1)
        elif unset_pwd_change_next_login:
            shadowMax = u''

        if not pwhistoryPolicy.expiryInterval and not self.hasChanged('pwdChangeNextLogin'):
            # An empty field means that password aging features are disabled.
            shadowLastChange = u''

        shadowMax = shadowMax.encode('ASCII')
        old_shadowMax = self.oldattr.get('shadowMax', [b''])[0]
        if old_shadowMax != shadowMax:
            ml.append(('shadowMax', old_shadowMax, shadowMax))

        shadowLastChange = shadowLastChange.encode('ASCII')
        if shadowLastChange:  # FIXME: this check causes, that the value is not unset. Is this correct?
            ml.append(('shadowLastChange', self.oldattr.get('shadowLastChange', [b''])[0], shadowLastChange))

        # if pwdChangeNextLogin has been set, set sambaPwdLastSet to 0 (see UCS Bug #17890)
        # OLD behavior was: set sambaPwdLastSet to 1 (see UCS Bug #8292 and Samba Bug #4313)
        sambaPwdLastSetValue = u'0' if pwd_change_next_login else str(long(time.time()))
        log.debug('sambaPwdLastSetValue: %s', sambaPwdLastSetValue)
        sambaPwdLastSetValue = sambaPwdLastSetValue.encode('UTF-8')
        ml.append(('sambaPwdLastSet', self.oldattr.get('sambaPwdLastSet', [b''])[0], sambaPwdLastSetValue))

        krb5PasswordEnd = u''
        if pwhistoryPolicy.expiryInterval or pwd_change_next_login:
            expiry = long(time.time())
            if not pwd_change_next_login:
                expiry = expiry + (pwhistoryPolicy.expiryInterval * 3600 * 24)
            krb5PasswordEnd = time.strftime("%Y%m%d000000Z", time.gmtime(expiry))

        log.debug('krb5PasswordEnd: %s', krb5PasswordEnd)
        old_krb5PasswordEnd = self.oldattr.get('krb5PasswordEnd', [b''])[0]
        krb5PasswordEnd = krb5PasswordEnd.encode('ASCII')
        if old_krb5PasswordEnd != krb5PasswordEnd:
            ml.append(('krb5PasswordEnd', old_krb5PasswordEnd, krb5PasswordEnd))

        return ml

    def _modlist_krb5kdc_flags(self, ml):
        # type: (list[tuple[str, Any, Any]]) -> list[tuple[str, Any, Any]]
        """
        Set the krb5KDCFlags.
        default = 1 << 6 | 1 << 5 | 1 << 4 | 1 << 3 | 1 << 2 | 1 << 1 = 126

        initial(0), -- require as-req
        forwardable(1), -- may issue forwardable
        proxiable(2), -- may issue proxiable
        renewable(3), -- may issue renewable
        postdate(4),-- may issue postdatable
        server(5),-- may be server
        client(6),-- may be client
        invalid(7), -- entry is invalid
        require-preauth(8), -- must use preauth
        change-pw(9), -- change password service
        require-hwauth(10), -- must use hwauth
        ok-as-delegate(11), -- as in TicketFlags
        user-to-user(12), -- may use user-to-user auth
        immutable(13),-- may not be deleted
        trusted-for-delegation(14), -- Trusted to print forwardabled tickets
        allow-kerberos4(15),-- Allow Kerberos 4 requests
        allow-digest(16), -- Allow digest requests
        locked-out(17), -- Account is locked out, authentication will be denied
        require-pwchange(18), -- require a passwd change
        do-not-store(31)-- Not to be modified and stored in HDB
        """
        if not self.exists() or self.hasChanged(['disabled', 'locked']):
            try:
                old_kdcflags = int(self.oldattr.get('krb5KDCFlags', [b'0'])[0])
            except ValueError:
                old_kdcflags = 0
            krb_kdcflags = old_kdcflags
            if not self.exists():
                krb_kdcflags |= 126
            if self['disabled'] == '1':
                krb_kdcflags |= (1 << 7)
            else:  # enable kerberos account
                krb_kdcflags &= ~(1 << 7)

            if self['locked'] == '0':  # unlock kerberos password
                krb_kdcflags &= ~(1 << 17)
#            elif self['locked'] == '1':  # lock kerberos password
#                krb_kdcflags |= (1 << 17)

            ml.append(('krb5KDCFlags', self.oldattr.get('krb5KDCFlags', []), str(krb_kdcflags).encode('ASCII')))
        return ml

    # If you change anything here, please also check users/ldap.py
    def _modlist_posix_password(self, ml):
        # type: (list[tuple[str, Any, Any]]) -> list[tuple[str, Any, Any]]
        if not self.exists() or self.hasChanged(['disabled', 'password']):
            old_password = self.oldattr.get('userPassword', [b''])[0].decode('ASCII')
            password = self['password']

            if self.hasChanged('password') and univention.admin.password.RE_PASSWORD_SCHEME.match(password):
                # hacking attempt. user tries to change the password to e.g. {KINIT} or {crypt}$6$...
                raise univention.admin.uexceptions.valueError(_('Invalid password.'), property='password')

            if univention.admin.password.password_is_auth_saslpassthrough(old_password):
                # do not change {SASL} password, but lock it if necessary
                password = old_password

            password_hash = univention.admin.password.lock_password(password)  # TODO: decode to let lock_password() and unlock_passowrd() return bytestring?!
            if self['disabled'] != '1':
                password_hash = univention.admin.password.unlock_password(password_hash)
            ml.append(('userPassword', old_password.encode('ASCII'), password_hash.encode('ASCII')))
        return ml

    def _modlist_pwd_account_locked_time(self, ml):
        # type: (list[tuple[str, Any, Any]]) -> list[tuple[str, Any, Any]]
        # remove pwdAccountLockedTime during unlocking
        if self.hasChanged('locked') and self['locked'] == '0':
            pwdAccountLockedTime = self.oldattr.get('pwdAccountLockedTime', [b''])[0]
            if pwdAccountLockedTime:
                ml.append(('pwdAccountLockedTime', pwdAccountLockedTime, b''))
        return ml

    def _modlist_samba_bad_pw_count(self, ml):
        # type: (list[tuple[str, Any, Any]]) -> list[tuple[str, Any, Any]]
        if self.hasChanged('locked') and self['locked'] == '0':
            # reset bad pw count
            ml.append(('sambaBadPasswordCount', self.oldattr.get('sambaBadPasswordCount', [b''])[0], b"0"))
            ml.append(('sambaBadPasswordTime', self.oldattr.get('sambaBadPasswordTime', [b''])[0], b'0'))
        return ml

    def _modlist_samba_kickoff_time(self, ml):
        # type: (list[tuple[str, Any, Any]]) -> list[tuple[str, Any, Any]]
        if self.hasChanged('userexpiry'):
            sambaKickoffTime = b''
            if self['userexpiry']:
                sambaKickoffTime = _mapUserExpiryToSambaKickoffTime(self['userexpiry']).encode("ASCII")
                log.debug('sambaKickoffTime: %s', sambaKickoffTime)
            old_sambaKickoffTime = self.oldattr.get('sambaKickoffTime', [b''])[0]
            if old_sambaKickoffTime != sambaKickoffTime:
                ml.append(('sambaKickoffTime', self.oldattr.get('sambaKickoffTime', [b''])[0], sambaKickoffTime))
        return ml

    def _modlist_krb5_valid_end(self, ml):
        # type: (list[tuple[str, Any, Any]]) -> list[tuple[str, Any, Any]]
        if self.hasChanged('userexpiry'):
            krb5ValidEnd = u''
            if self['userexpiry']:
                krb5ValidEnd = _mapUserExpiryToKrb5ValidEnd(self['userexpiry'])
                log.debug('krb5ValidEnd: %s', krb5ValidEnd)
            krb5ValidEnd = krb5ValidEnd.encode('ASCII')
            old_krb5ValidEnd = self.oldattr.get('krb5ValidEnd', [b''])[0]
            if old_krb5ValidEnd != krb5ValidEnd:
                if not self['userexpiry']:
                    ml.append(('krb5ValidEnd', old_krb5ValidEnd, None))
                else:
                    ml.append(('krb5ValidEnd', self.oldattr.get('krb5ValidEnd', [b''])[0], krb5ValidEnd))
        return ml

    def _modlist_shadow_expire(self, ml):
        # type: (list[tuple[str, Any, Any]]) -> list[tuple[str, Any, Any]]
        if self.hasChanged('disabled') or self.hasChanged('userexpiry'):
            if self['disabled'] == '1' and self.hasChanged('disabled') and not self.hasChanged('userexpiry'):
                shadowExpire = u'1'
            elif self['userexpiry']:
                shadowExpire = _mapUserExpiryToShadowExpire(self['userexpiry'])
            elif self['disabled'] == '1':
                shadowExpire = u'1'
            else:
                shadowExpire = u''

            old_shadowExpire = self.oldattr.get('shadowExpire', [b''])[0]
            shadowExpire = shadowExpire.encode('ASCII')
            if old_shadowExpire != shadowExpire:
                ml.append(('shadowExpire', old_shadowExpire, shadowExpire))
        return ml

    def _modlist_mail_forward(self, ml):
        # type: (list[tuple[str, Any, Any]]) -> list[tuple[str, Any, Any]]
        if self['mailForwardAddress'] and not self['mailPrimaryAddress']:
            raise univention.admin.uexceptions.missingInformation(_('Primary e-mail address must be set, if messages should be forwarded for it.'))
        if self.get('mailForwardCopyToSelf') == '1' and not self['mailPrimaryAddress']:
            raise univention.admin.uexceptions.missingInformation(_('Primary e-mail address must be set, if a copy of forwarded messages should be stored in its mailbox.'))
        if configRegistry.is_true('directory/manager/user/activate_ldap_attribute_mailForwardCopyToSelf', False):
            return ml

        try:
            new = [x[2] if isinstance(x[2], (list, tuple)) else [x[2]] for x in ml if x[0] == 'mailForwardAddress' and x[2]][0]  # noqa: RUF015
        except IndexError:  # mailForwardAddress was not changed, nevertheless we might need to change it
            new = self.mapping.mapValue('mailForwardAddress', self['mailForwardAddress']) or []  # FIXME: mapValue returns b'' instead of [b'']

        if self.hasChanged('mailPrimaryAddress') and self.oldattr.get('mailPrimaryAddress'):
            try:
                new.remove(self.oldattr['mailPrimaryAddress'][0])
            except ValueError:
                pass

        if self['mailPrimaryAddress']:
            mail_primary_address = self.mapping.mapValue('mailPrimaryAddress', self['mailPrimaryAddress'])
            if self.get('mailForwardCopyToSelf') == '1' and self['mailForwardAddress']:
                new.append(mail_primary_address)
            elif mail_primary_address in new:
                new.remove(mail_primary_address)

        ml = [(key_, old_, new_) for (key_, old_, new_) in ml if key_ != u'mailForwardAddress']
        if self.oldattr.get('mailForwardAddress', []) != new:
            ml.append(('mailForwardAddress', self.oldattr.get('mailForwardAddress'), new))
        return ml

    def _modlist_univention_person(self, ml):
        # type: (list[tuple[str, Any, Any]]) -> list[tuple[str, Any, Any]]
        # make sure that univentionPerson is set as objectClass when needed
        if any(self.hasChanged(ikey) and self[ikey] for ikey in ('umcProperty', 'birthday', 'serviceSpecificPassword', 'country')) and b'univentionPerson' not in self.oldattr.get('objectClass', []):
            ml.append(('objectClass', b'', b'univentionPerson'))  # TODO: check if exists already
        return ml

    def _modlist_home_share(self, ml):
        # type: (list[tuple[str, Any, Any]]) -> list[tuple[str, Any, Any]]
        if self.hasChanged('homeShare') or self.hasChanged('homeSharePath'):
            if self['homeShare']:
                share_mod = univention.admin.modules._get('shares/share')
                try:
                    share = share_mod.object(None, self.lo, self.position, self['homeShare'])
                    share.open()
                except Exception:  # FIXME: specify correct exception
                    raise univention.admin.uexceptions.noObject(_('DN given as share is not valid.'))

                if share['host'] and share['path']:
                    if b'automount' not in self.oldattr.get('objectClass', []):
                        ml.append(('objectClass', b'', b'automount'))

                    am_host = share['host']
                    if not self['homeSharePath'] or not isinstance(self['homeSharePath'], six.string_types):
                        raise univention.admin.uexceptions.missingInformation(_('%(homeSharePath)s must be given if %(homeShare)s is given.') % {'homeSharePath': _('Home share path'), 'homeShare': _('Home share')})
                    else:
                        am_path = os.path.abspath(os.path.join(share['path'], self['homeSharePath']))
                        if not am_path.startswith(share['path']):
                            raise univention.admin.uexceptions.valueError(_('%s: Invalid path') % _('Home share path'), property='homeShare')

                    am_old = self.oldattr.get('automountInformation', [b''])[0]
                    am_new = b'-rw %s:%s' % (am_host.encode('UTF-8'), am_path.encode('UTF-8'))  # TODO: check if automountInformation is really UTF-8
                    ml.append(('automountInformation', am_old, am_new))
                else:
                    raise univention.admin.uexceptions.noObject(_('Given DN is no share.'))

            if not self['homeShare'] or not share['host'] or not share['path']:
                if b'automount' not in self.oldattr.get('objectClass', []):
                    ml.append(('objectClass', b'', b'automount'))
                am_old = self.oldattr.get('automountInformation', [b''])[0]
                if am_old:
                    ml.append(('automountInformation', am_old, b''))
        return ml

    def _modlist_samba_sid(self, ml):
        # type: (list[tuple[str, Any, Any]]) -> list[tuple[str, Any, Any]]
        if not self.exists() or self.hasChanged('sambaRID'):
            sid = self.__generate_user_sid(self['uidNumber'])
            sid = sid.encode('ASCII')
            ml.append(('sambaSID', self.oldattr.get('sambaSID', [b'']), [sid]))
        return ml

    def _modlist_primary_group(self, ml):
        # type: (list[tuple[str, Any, Any]]) -> list[tuple[str, Any, Any]]
        if not self.exists() or self.hasChanged('primaryGroup'):
            # Posix
            ml.append(('gidNumber', self.oldattr.get('gidNumber', [b'']), [self.get_gid_for_primary_group().encode('ASCII')]))
            # Samba
            ml.append(('sambaPrimaryGroupSID', self.oldattr.get('sambaPrimaryGroupSID', [b'']), [self.get_sid_for_primary_group().encode('ASCII')]))
        return ml

    def _modlist_sambaAcctFlags(self, ml):
        # type: (list[tuple[str, Any, Any]]) -> list[tuple[str, Any, Any]]
        if self.exists() and not self.hasChanged(['disabled', 'locked']):
            return ml

        old_flags = self.oldattr.get('sambaAcctFlags', [b''])[0]
        acctFlags = univention.admin.samba.acctFlags(old_flags.decode('ASCII'))
        if self['disabled'] == '1':
            # disable samba account
            acctFlags.set('D')
        else:
            # enable samba account
            acctFlags.unset('D')

        if self['locked'] == '1':
            # lock samba account
            acctFlags.set('L')
        else:
            acctFlags.unset('L')

        new_flags = acctFlags.decode().encode('ASCII')
        if old_flags != new_flags:
            ml.append(('sambaAcctFlags', old_flags, new_flags))
        return ml

    def _modlist_service_specific_password(self, ml):
        # type: (list[tuple[str, Any, Any]]) -> list[tuple[str, Any, Any]]
        new_password = self.info.get('serviceSpecificPassword', None)
        if new_password:
            service = new_password.get('service', None)
            password = new_password.get('password', None)
            if service != 'radius':
                raise univention.admin.uexceptions.valueError(_('Service does not support service specific passwords'), property='serviceSpecificPassword')
            if service:
                nt = passlib.hash.nthash.hash(password).upper().encode('ASCII')
                ml.append(('univentionRadiusPassword', self.oldattr.get('univentionRadiusPassword', [b'']), [nt]))
        return ml

    def _ldap_post_remove(self):
        # type: () -> None
        self.alloc.append(('sid', self.oldattr['sambaSID'][0].decode('ASCII')))
        self.alloc.append(('uid', self.oldattr['uid'][0].decode('UTF-8')))
        self.alloc.append(('uidNumber', self.oldattr['uidNumber'][0].decode('ASCII')))
        if self['mailPrimaryAddress']:
            self.alloc.append(('mailPrimaryAddress', self['mailPrimaryAddress']))
        super(object, self)._ldap_post_remove()

        for group in self.oldinfo.get('groups', []):
            groupObject = univention.admin.objects.get(univention.admin.modules._get('groups/group'), self.co, self.lo, self.position, group)
            groupObject.fast_member_remove([self.dn], [x.decode('UTF-8') for x in self.oldattr.get('uid', [])], ignore_license=True)

    def _move(self, newdn, modify_childs=True, ignore_license=False):
        # type: (str, bool, bool) -> str
        olddn = self.dn
        tmpdn = u'cn=%s-subtree,cn=temporary,cn=univention,%s' % (ldap.dn.escape_dn_chars(self['username']), self.lo.base)
        al = [('objectClass', [b'top', b'organizationalRole']), ('cn', [b'%s-subtree' % (self['username'].encode('UTF-8'),)])]
        subelements = self.lo.search(base=self.dn, scope='one', attr=['objectClass'])  # FIXME: identify may fail, but users will raise decode-exception
        if subelements:
            try:
                self.lo.add(tmpdn, al)
            except ldap.LDAPError:
                # real errors will be caught later
                pass
            moved = dict(self.move_subelements(olddn, tmpdn, subelements, ignore_license))
            subelements = [(moved[subdn], subattrs) for (subdn, subattrs) in subelements]

        try:
            dn = super(object, self)._move(newdn, modify_childs, ignore_license)
        except BaseException:
            # self couldn't be moved
            # move back subelements and reraise
            self.move_subelements(tmpdn, olddn, subelements, ignore_license)
            raise

        if subelements:
            try:
                moved = dict(self.move_subelements(tmpdn, newdn, subelements, ignore_license))
                subelements = [(moved[subdn], subattrs) for (subdn, subattrs) in subelements]
            except BaseException:
                # subelements couldn't be moved to self
                # subelements were already moved back to temporary position
                # move back self, move back subelements to self and reraise
                super(object, self)._move(olddn, modify_childs, ignore_license)
                self.move_subelements(tmpdn, olddn, subelements, ignore_license)
                raise

        return dn

    def __allocate_rid(self, rid):
        # type: (str) -> str
        searchResult = self.lo.search(filter='objectClass=sambaDomain', attr=['sambaSID'])
        domainsid = searchResult[0][1]['sambaSID'][0]
        sid = domainsid.decode('ASCII') + u'-' + rid
        try:
            return self.request_lock('sid', sid)
        except univention.admin.uexceptions.noLock:
            raise univention.admin.uexceptions.sidAlreadyUsed(rid)

    def __generate_user_sid(self, uidNum):
        # type: (str) -> str
        if self['sambaRID']:
            return self.__allocate_rid(self['sambaRID'])
        elif self.s4connector_present:
            # In this case Samba 4 must create the SID, the s4 connector will sync the
            # new sambaSID back from Samba 4.
            return 'S-1-4-%s' % (uidNum,)

        rid = rids_for_well_known_security_identifiers.get(self['username'].lower())
        if rid:
            return self.__allocate_rid(rid)

        while True:
            try:
                return self.request_lock('sid+user', uidNum)
            except univention.admin.uexceptions.noLock:
                uidNum = str(int(uidNum) + 1)

    @classmethod
    def unmapped_lookup_filter(cls):
        # type: () -> univention.admin.filter.conjunction
        filter_p = super(object, cls).unmapped_lookup_filter()
        filter_p.expressions.extend([
            univention.admin.filter.conjunction(u'!', [univention.admin.filter.expression(u'uidNumber', u'0')]),
            univention.admin.filter.conjunction(u'!', [univention.admin.filter.expression(u'univentionObjectFlag', u'functional')]),
        ])
        return filter_p

    @classmethod
    def _ldap_attributes(cls):
        # type: () -> list[str]
        return super(object, cls)._ldap_attributes() + ['pwdAccountLockedTime', 'memberOf']

    @classmethod
    def rewrite_filter(cls, filter, mapping):
        # type: (univention.admin.filter.expression, univention.admin.mapping.mapping) -> None
        if filter.variable == u'primaryGroup':
            filter.variable = u'gidNumber'
        elif filter.variable == u'groups':
            filter.variable = u'memberOf'
        elif filter.variable == u'disabled':
            # substring match for userPassword is not possible
            if filter.value == u'1':
                filter.transform_to_conjunction(univention.admin.filter.parse(u'(&(shadowExpire=1)(krb5KDCFlags:1.2.840.113556.1.4.803:=128)(|(sambaAcctFlags=[UD       ])(sambaAcctFlags=[ULD       ])))'))
            elif filter.value == u'0':
                filter.transform_to_conjunction(univention.admin.filter.parse(u'(&(!(shadowExpire=1))(!(krb5KDCFlags:1.2.840.113556.1.4.803:=128))(!(|(sambaAcctFlags=[UD       ])(sambaAcctFlags=[ULD       ]))))'))
            elif filter.value == u'none':
                filter.transform_to_conjunction(univention.admin.filter.parse(u'(&(!(shadowExpire=1))(!(krb5KDCFlags:1.2.840.113556.1.4.803:=128))(!(|(sambaAcctFlags=[UD       ])(sambaAcctFlags=[ULD       ]))))'))
            elif filter.value == u'all':
                filter.transform_to_conjunction(univention.admin.filter.parse(u'(&(shadowExpire=1)(krb5KDCFlags:1.2.840.113556.1.4.803:=128)(|(sambaAcctFlags=[UD       ])(sambaAcctFlags=[ULD       ])))'))
            elif filter.value == u'posix':
                filter.variable = u'shadowExpire'
                filter.value = u'1'
            elif filter.value == u'kerberos':
                filter.transform_to_conjunction(univention.admin.filter.parse(u'(&(krb5KDCFlags:1.2.840.113556.1.4.803:=128))'))
            elif filter.value == u'windows':
                filter.transform_to_conjunction(univention.admin.filter.parse(u'(|(sambaAcctFlags=[UD       ])(sambaAcctFlags==[ULD       ]))'))
            elif filter.value == u'windows_kerberos':
                filter.transform_to_conjunction(univention.admin.filter.parse(u'(&(krb5KDCFlags:1.2.840.113556.1.4.803:=128)(|(sambaAcctFlags=[UD       ])(sambaAcctFlags==[ULD       ])))'))
            elif filter.value == u'windows_posix':
                filter.transform_to_conjunction(univention.admin.filter.parse(u'(&(shadowExpire=1)(|(sambaAcctFlags=[UD       ])(sambaAcctFlags==[ULD       ])))'))
            elif filter.value == u'posix_kerberos':
                filter.transform_to_conjunction(univention.admin.filter.parse(u'(&(shadowExpire=1)(krb5KDCFlags=254))'))
            elif filter.operator == u'=*':
                filter.variable = u'uid'
        elif filter.variable == 'userexpiry':
            try:
                userexpiry = property_descriptions['userexpiry'].syntax.parse(filter.value)
            except univention.admin.uexceptions.valueError:
                # allow to search for userexpiry=*
                # TODO: should we allow to search for e.g. userexpiry=2021-* ?
                userexpiry_filter = filter_format(u'(|(shadowExpire=%s)(krb5ValidEnd=%s)(sambaKickoffTime=%s))', [filter.value or '*', filter.value or '*', filter.value or '*'])
                userexpiry_filter = userexpiry_filter.replace(filter_format('%s', ['*']), '*')
            else:
                userexpiry_filter = filter_format(u'(|(shadowExpire=%s)(krb5ValidEnd=%s)(sambaKickoffTime=%s))', [
                    _mapUserExpiryToShadowExpire(userexpiry),
                    _mapUserExpiryToKrb5ValidEnd(userexpiry),
                    _mapUserExpiryToSambaKickoffTime(userexpiry),
                ])
            filter.transform_to_conjunction(univention.admin.filter.parse(userexpiry_filter))
        elif filter.variable == u'locked':
            if filter.value == u'1':
                filter.transform_to_conjunction(univention.admin.filter.parse(u'(|(krb5KDCFlags:1.2.840.113556.1.4.803:=131072)(sambaAcctFlags=[UL       ])(sambaAcctFlags=[ULD       ]))'))
            elif filter.value == u'0':
                filter.transform_to_conjunction(univention.admin.filter.parse(u'(&(!(krb5KDCFlags:1.2.840.113556.1.4.803:=131072))(!(sambaAcctFlags=[UL       ]))(!(sambaAcctFlags=[ULD       ])))'))
            elif filter.value in [u'posix', u'windows', u'all', u'none']:
                if filter.value == 'all':
                    filter.transform_to_conjunction(univention.admin.filter.parse(u'(|(sambaAcctFlags=[UL       ])(sambaAcctFlags=[ULD       ]))'))
                    # filter.transform_to_conjunction(univention.admin.filter.parse(u'(|(sambaAcctFlags=[UL       ])(sambaAcctFlags=[ULD       ])(userPassword={crypt}!*))'))
                elif filter.value == u'windows':
                    filter.transform_to_conjunction(univention.admin.filter.parse(u'(|(sambaAcctFlags=[UL       ])(sambaAcctFlags=[ULD       ]))'))
                # elif filter.value == u'posix':
                #    filter.variable = u'userPassword'
                #    filter.value = u'{crypt}!*'
                elif filter.value == u'none':
                    # filter.transform_to_conjunction(univention.admin.filter.parse(u'(&(!(sambaAcctFlags=[UL       ]))(!(sambaAcctFlags=[ULD       ]))(!(userPassword={crypt}!*)))'))
                    filter.transform_to_conjunction(univention.admin.filter.parse(u'(&(!(sambaAcctFlags=[UL       ]))(!(sambaAcctFlags=[ULD       ])))'))
            elif filter.value == u'*':
                filter.variable = u'uid'
        else:
            super(object, cls).rewrite_filter(filter, mapping)

    @classmethod
    def identify(cls, dn, attr, canonical=False):
        # type: (str, univention.admin.handlers._Attributes, bool) -> bool
        if b'0' in attr.get('uidNumber', []) or b'$' in attr.get('uid', [b''])[0] or b'univentionHost' in attr.get('objectClass', []) or b'functional' in attr.get('univentionObjectFlag', []):
            return False
        required_ocs = {b'posixAccount', b'shadowAccount', b'sambaSamAccount', b'person', b'krb5KDCEntry', b'krb5Principal'}
        ocs = set(attr.get('objectClass', []))
        return ocs & required_ocs == required_ocs


lookup = object.lookup
lookup_filter = object.lookup_filter
identify = object.identify
