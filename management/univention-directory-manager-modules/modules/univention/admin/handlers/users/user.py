# -*- coding: utf-8 -*-
#
# Copyright 2004-2021 Univention GmbH
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

"""
|UDM| module for the user objects
"""

from __future__ import absolute_import

import base64
import calendar
import codecs
import copy
import hashlib
import os
import re
import time
from datetime import datetime

import ldap
import pytz
import six
from ldap.filter import filter_format
import tzlocal
from M2Crypto import X509

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
import univention.debug as ud
import univention.password
from univention.admin import configRegistry
from univention.admin.layout import Group, Tab
from univention.lib.s4 import rids_for_well_known_security_identifiers

from typing import List  # noqa: F401

try:
	from univention.admin.syntax import ActivationDateTimeTimezone
except ImportError:
	# workaround for errors during errata-updates. should be removable with UCS 5.0-1
	class ActivationDateTimeTimezone(univention.admin.syntax.complex):
		"""
		Syntax for YYYY-mm-dd HH:MM TZNAME
		"""
		delimiter = ' '
		subsyntaxes = [('Date', univention.admin.syntax.iso8601Date), ('Time', univention.admin.syntax.TimeString), ('Timezone', univention.admin.syntax.string)]
		subsyntax_names = ('date', 'time', 'timezone')
		subsyntax_names = ('activation-date', 'activation-time', 'activation-timezone')
		size = ('TwoThirds', 'TwoThirds', 'TwoThirds')
		all_required = False
		min_elements = 0
	univention.admin.syntax.ActivationDateTimeTimezone = ActivationDateTimeTimezone

if not six.PY2:
	long = int

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
		objectClasses=['top', 'person', 'univentionPWHistory', 'posixAccount', 'shadowAccount', 'sambaSamAccount', 'krb5Principal', 'krb5KDCEntry', 'univentionMail', 'organizationalPerson', 'inetOrgPerson']
	),
	'pki': univention.admin.option(
		short_description=_('Public key infrastructure account'),
		default=False,
		editable=True,
		objectClasses=['pkiUser'],
	),
}
property_descriptions = {
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
		default=[[None, None, tzlocal.get_localzone().zone], []],
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
		include_in_default_search=True,
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
		default='/home/<username>'
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
		long_description=_('The directory path which is used as the user\'s Windows home directory, e.g. \\\\ucs-file-server\\smith.'),
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
		long_description=_('Share, the user\'s home directory resides on'),
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
	'userCertificate': univention.admin.property(
		short_description=_("PKI user certificate (DER format)"),
		long_description=_('Public key infrastructure - user certificate '),
		syntax=univention.admin.syntax.Base64Upload,
		dontsearch=True,
		options=['pki'],
	),
	'certificateIssuerCountry': univention.admin.property(
		short_description=_('Issuer Country'),
		long_description=_('Certificate Issuer Country'),
		syntax=univention.admin.syntax.string,
		dontsearch=True,
		editable=False,
		options=['pki'],
	),
	'certificateIssuerState': univention.admin.property(
		short_description=_('Issuer State'),
		long_description=_('Certificate Issuer State'),
		syntax=univention.admin.syntax.string,
		dontsearch=True,
		editable=False,
		options=['pki'],
	),
	'certificateIssuerLocation': univention.admin.property(
		short_description=_('Issuer Location'),
		long_description=_('Certificate Issuer Location'),
		syntax=univention.admin.syntax.string,
		dontsearch=True,
		editable=False,
		options=['pki'],
	),
	'certificateIssuerOrganisation': univention.admin.property(
		short_description=_('Issuer Organisation'),
		long_description=_('Certificate Issuer Organisation'),
		syntax=univention.admin.syntax.string,
		dontsearch=True,
		editable=False,
		options=['pki'],
	),
	'certificateIssuerOrganisationalUnit': univention.admin.property(
		short_description=_('Issuer Organisational Unit'),
		long_description=_('Certificate Issuer Organisational Unit'),
		syntax=univention.admin.syntax.string,
		dontsearch=True,
		editable=False,
		options=['pki'],
	),
	'certificateIssuerCommonName': univention.admin.property(
		short_description=_('Issuer Common Name'),
		long_description=_('Certificate Issuer Common Name'),
		syntax=univention.admin.syntax.string,
		dontsearch=True,
		editable=False,
		options=['pki'],
	),
	'certificateIssuerMail': univention.admin.property(
		short_description=_('Issuer Mail'),
		long_description=_('Certificate Issuer Mail'),
		syntax=univention.admin.syntax.string,
		dontsearch=True,
		editable=False,
		options=['pki'],
	),
	'certificateSubjectCountry': univention.admin.property(
		short_description=_('Subject Country'),
		long_description=_('Certificate Subject Country'),
		syntax=univention.admin.syntax.string,
		dontsearch=True,
		editable=False,
		options=['pki'],
	),
	'certificateSubjectState': univention.admin.property(
		short_description=_('Subject State'),
		long_description=_('Certificate Subject State'),
		syntax=univention.admin.syntax.string,
		dontsearch=True,
		editable=False,
		options=['pki'],
	),
	'certificateSubjectLocation': univention.admin.property(
		short_description=_('Subject Location'),
		long_description=_('Certificate Subject Location'),
		syntax=univention.admin.syntax.string,
		dontsearch=True,
		editable=False,
		options=['pki'],
	),
	'certificateSubjectOrganisation': univention.admin.property(
		short_description=_('Subject Organisation'),
		long_description=_('Certificate Subject Organisation'),
		syntax=univention.admin.syntax.string,
		dontsearch=True,
		editable=False,
		options=['pki'],
	),
	'certificateSubjectOrganisationalUnit': univention.admin.property(
		short_description=_('Subject Organisational Unit'),
		long_description=_('Certificate Subject Organisational Unit'),
		syntax=univention.admin.syntax.string,
		dontsearch=True,
		editable=False,
		options=['pki'],
	),
	'certificateSubjectCommonName': univention.admin.property(
		short_description=_('Subject Common Name'),
		long_description=_('Certificate Subject Common Name'),
		syntax=univention.admin.syntax.string,
		dontsearch=True,
		editable=False,
		options=['pki'],
	),
	'certificateSubjectMail': univention.admin.property(
		short_description=_('Subject Mail'),
		long_description=_('Certificate Subject Mail'),
		syntax=univention.admin.syntax.string,
		dontsearch=True,
		editable=False,
		options=['pki'],
	),
	'certificateDateNotBefore': univention.admin.property(
		short_description=_('Valid from'),
		long_description=_('Certificate valid from'),
		syntax=univention.admin.syntax.date,
		dontsearch=True,
		editable=False,
		options=['pki'],
	),
	'certificateDateNotAfter': univention.admin.property(
		short_description=_('Valid until'),
		long_description=_('Certificate valid until'),
		syntax=univention.admin.syntax.date,
		dontsearch=True,
		editable=False,
		options=['pki'],
	),
	'certificateVersion': univention.admin.property(
		short_description=_('Version'),
		long_description=_('Certificate Version'),
		syntax=univention.admin.syntax.string,
		dontsearch=True,
		editable=False,
		options=['pki'],
	),
	'certificateSerial': univention.admin.property(
		short_description=_('Serial'),
		long_description=_('Certificate Serial'),
		syntax=univention.admin.syntax.string,
		dontsearch=True,
		editable=False,
		options=['pki'],
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
}

default_property_descriptions = copy.deepcopy(property_descriptions)  # for later reset of descriptions

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
			'sambaUserWorkstations'
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
		], ),
		Group(_('Mail forwarding'), layout=[
			'mailForwardCopyToSelf',
			'mailForwardAddress',
		], ),
	]),
	Tab(_('Contact'), _('Contact information'), layout=[
		Group(_('Business'), layout=[
			'e-mail',
			'phone',
			['roomNumber', 'departmentNumber'],
			['street', 'postcode', 'city'],
			['country']
		]),
		Group(_('Private'), layout=[
			'homeTelephoneNumber',
			'mobileTelephoneNumber',
			'pagerTelephoneNumber',
			'homePostalAddress'
		]),
	]),
	Tab('Apps'),  # not translated!
	Tab(_('UMC preferences'), _('UMC preferences'), advanced=True, layout=[
		Group(_('UMC preferences'), layout=[
			'umcProperty',
		]),
	]),
	Tab(_('Certificate'), _('Certificate'), advanced=True, layout=[
		Group(_('General'), '', [
			'userCertificate',
		]),
		Group(_('Subject'), '', [
			['certificateSubjectCommonName', 'certificateSubjectMail'],
			['certificateSubjectOrganisation', 'certificateSubjectOrganisationalUnit'],
			'certificateSubjectLocation',
			['certificateSubjectState', 'certificateSubjectCountry'],
		]),
		Group(_('Issuer'), '', [
			['certificateIssuerCommonName', 'certificateIssuerMail'],
			['certificateIssuerOrganisation', 'certificateIssuerOrganisationalUnit'],
			'certificateIssuerLocation',
			['certificateIssuerState', 'certificateIssuerCountry'],
		]),
		Group(_('Validity'), '', [
			['certificateDateNotBefore', 'certificateDateNotAfter']
		]),
		Group(_('Misc'), '', [
			['certificateVersion', 'certificateSerial']
		])
	])
]


def check_prohibited_username(lo, username):
	"""check if the username is allowed"""
	module = univention.admin.modules.get('settings/prohibited_username')
	for prohibited_object in (module.lookup(None, lo, u'') or []):
		if username in prohibited_object['usernames']:
			raise univention.admin.uexceptions.prohibitedUsername(username)


def case_insensitive_in_list(dn, list):
	assert isinstance(dn, six.text_type)
	for element in list:
		assert isinstance(element, six.text_type)
		if dn.lower() == element.lower():
			return True
	return False


def posixSecondsToLocaltimeDate(seconds):
	return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(seconds))


def posixDaysToDate(days):
	return time.strftime("%Y-%m-%d", time.gmtime(long(days) * 3600 * 24))


def sambaWorkstationsMap(workstations, encoding=()):
	return u','.join(workstations).encode(*encoding)


def sambaWorkstationsUnmap(workstations, encoding=()):
	return workstations[0].decode(*encoding).split(u',')


def logonHoursMap(logontimes):
	"converts the bitfield 001110010110...100 to the respective hex string"

	# convert list of bit numbers to bit-string
	# bitstring = '0' * 168

	if logontimes == '':
		# if unsetting it, see Bug #33703
		return None

	bitstring = ''.join(map(lambda x: x in logontimes and '1' or '0', range(168)))

	# for idx in logontimes:
	# 	bitstring[ idx ] = '1'

	logontimes = bitstring

	# the order of the bits of each byte has to be reversed. The reason for this is that
	# consecutive bytes mean consecutive 8-hrs-intervals, but the MSB stands for
	# the last hour in that interval, the 2nd but leftmost bit for the second-to-last
	# hour and so on. We want to hide this from anybody using this feature.
	# See <http://ma.ph-freiburg.de/tng/tng-technical/2003-04/msg00015.html> for details.

	newtimes = ""
	for i in range(0, 21):
		bitlist = list(logontimes[(i * 8):(i * 8) + 8])
		bitlist.reverse()
		newtimes += "".join(bitlist)
	logontimes = newtimes

	# create a hexnumber from each 8-bit-segment
	ret = ""
	for i in range(0, 21):
		val = 0
		exp = 7
		for j in range((i * 8), (i * 8) + 8):
			if not (logontimes[j] == "0"):
				val += 2 ** exp
			exp -= 1
		# we now have: 0<=val<=255
		hx = hex(val)[2:4]
		if len(hx) == 1:
			hx = "0" + hx
		ret += hx

	return ret.encode('ASCII')


def logonHoursUnmap(logontimes):
	"""Converts hex-string to an array of bits set."""

	times = logontimes[0][:42]
	while len(times) < 42:
		times = times
	ret = ""
	for i in range(0, 42, 2):
		val = int(times[i:i + 2], 16)
		ret += intToBinary(val)

	# reverse order of the bits in each byte. See above for details
	newtime = ""
	for i in range(0, 21):
		bitlist = list(ret[(i * 8):(i * 8) + 8])
		bitlist.reverse()
		newtime += "".join(bitlist)

	# convert bit-string to list
	return [i for i in range(168) if newtime[i] == '1']


def intToBinary(val):
	ret = ""
	while val > 0:
		ret = str(val & 1) + ret
		val = val >> 1
	# pad with leading 0s until length is n*8
	if ret == "":
		ret = "0"
	while not (len(ret) % 8 == 0):
		ret = "0" + ret
	return ret


def GMTOffset():
	# returns the difference in hours between local time and GMT (is -1 for CET and CEST)
	return time.timezone // 3600


def load_certificate(user_certificate):
	"""Import a certificate in DER format"""
	if not user_certificate:
		return {}
	try:
		certificate = base64.b64decode(user_certificate)
	except base64.binascii.Error:
		return {}
	try:
		x509 = X509.load_cert_string(certificate, X509.FORMAT_DER)

		values = {
			'certificateDateNotBefore': x509.get_not_before().get_datetime().date().isoformat(),
			'certificateDateNotAfter': x509.get_not_after().get_datetime().date().isoformat(),
			'certificateVersion': str(x509.get_version()),
			'certificateSerial': str(x509.get_serial_number()),
		}
		X509.m2.XN_FLAG_SEP_MULTILINE & ~X509.m2.ASN1_STRFLGS_ESC_MSB | X509.m2.ASN1_STRFLGS_UTF8_CONVERT
		for entity, prefix in (
			(x509.get_issuer(), "certificateIssuer"),
			(x509.get_subject(), "certificateSubject"),
		):
			for key, attr in load_certificate.ATTR.items():
				try:
					value = getattr(entity, key)
				except TypeError:  # not expecting type '<class 'NoneType'>'
					value = None
				values[prefix + attr] = value
	except (X509.X509Error, AttributeError):
		return {}

	ud.debug(ud.ADMIN, ud.INFO, 'value=%s' % values)
	return values


load_certificate.ATTR = {
	"C": "Country",
	"ST": "State",
	"L": "Location",
	"O": "Organisation",
	"OU": "OrganisationalUnit",
	"CN": "CommonName",
	"emailAddress": "Mail",
}


def mapHomePostalAddress(old, encoding=()):
	"""Map address to LDAP encoding.

	>>> mapHomePostalAddress([["a", "b", "c"]])
	[b'a$b$c']
	"""
	new = []
	for i in old:
		new.append(u'$'.join(i).encode(*encoding))
	return new


def unmapHomePostalAddress(old, encoding=()):
	"""Expand LDAP encoded address.
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


def unmapUserExpiry(oldattr):
	return unmapKrb5ValidEndToUserexpiry(oldattr) or unmapSambaKickoffTimeToUserexpiry(oldattr) or unmapShadowExpireToUserexpiry(oldattr)


def unmapShadowExpireToUserexpiry(oldattr):
	# The shadowLastChange attribute is the amount of days between 1/1/1970 up to the day that password was modified,
	# shadowMax is the number of days a password is valid. So the password expires on 1/1/1970 + shadowLastChange + shadowMax.
	# shadowExpire contains the absolute date to expire the account.

	if 'shadowExpire' in oldattr and len(oldattr['shadowExpire']) > 0:
		ud.debug(ud.ADMIN, ud.INFO, 'userexpiry: %s' % posixDaysToDate(oldattr['shadowExpire'][0]))
		if oldattr['shadowExpire'][0] != b'1':
			return posixDaysToDate(oldattr['shadowExpire'][0])


def unmapKrb5ValidEndToUserexpiry(oldattr):
	if 'krb5ValidEnd' in oldattr:
		krb5validend = oldattr['krb5ValidEnd'][0].decode('ASCII')
		ud.debug(ud.ADMIN, ud.INFO, 'krb5validend is: %s' % krb5validend)
		return "%s-%s-%s" % (krb5validend[0:4], krb5validend[4:6], krb5validend[6:8])


def unmapSambaKickoffTimeToUserexpiry(oldattr):
	if 'sambaKickoffTime' in oldattr:
		ud.debug(ud.ADMIN, ud.INFO, 'sambaKickoffTime is: %s' % oldattr['sambaKickoffTime'][0].decode('ASCII'))
		return time.strftime("%Y-%m-%d", time.gmtime(long(oldattr['sambaKickoffTime'][0]) + (3600 * 24)))


def unmapPasswordExpiry(oldattr):
	if oldattr.get('shadowLastChange') and oldattr.get('shadowMax'):
		shadow_max = int(oldattr['shadowMax'][0])
		shadow_last_change = 0
		try:
			shadow_last_change = int(oldattr['shadowLastChange'][0])
		except ValueError:
			ud.debug(ud.ADMIN, ud.WARN, 'users/user: failed to calculate password expiration correctly, use only shadowMax instead')
		return posixDaysToDate(shadow_last_change + shadow_max)


def unmapDisabled(oldattr):
	if all([
		unmapSambaDisabled(oldattr),
		unmapKerberosDisabled(oldattr),
		unmapPosixDisabled(oldattr) or isPosixLocked(oldattr),
	]):
		return '1'
	return '0'


def inconsistentDisabledState(oldattr):
	disabled = [
		unmapSambaDisabled(oldattr),
		unmapKerberosDisabled(oldattr),
		unmapPosixDisabled(oldattr),
		isPosixLocked(oldattr),
	]
	return len(set(map(bool, disabled))) > 1


def unmapSambaDisabled(oldattr):
	flags = oldattr.get('sambaAcctFlags', None)
	if flags:
		acctFlags = univention.admin.samba.acctFlags(flags[0].decode('ASCII'))
		try:
			return acctFlags['D'] == 1
		except KeyError:
			pass
	return False


def unmapKerberosDisabled(oldattr):
	try:
		kdcflags = int(oldattr.get('krb5KDCFlags', [b'0'])[0])
	except ValueError:
		kdcflags = 0
	return kdcflags & (1 << 7) == (1 << 7)


def unmapPosixDisabled(oldattr):
	try:
		shadowExpire = int(oldattr['shadowExpire'][0])
	except (KeyError, ValueError):
		return False
	return shadowExpire == 1 or shadowExpire < int(time.time() / 3600 / 24)


def unmapLocked(oldattr):
	if isSambaLocked(oldattr) or isKerberosLocked(oldattr):  # or isLDAPLocked(oldattr)
		return '1'
	return '0'


def inconsistentLockedState(oldattr):
	return isSambaLocked(oldattr) ^ isKerberosLocked(oldattr)


def isPosixLocked(oldattr):
	userPassword = oldattr.get('userPassword', [b''])[0].decode('ASCII')
	return userPassword and univention.admin.password.is_locked(userPassword)


def isSambaLocked(oldattr):
	flags = oldattr.get('sambaAcctFlags', None)
	if flags:
		acctFlags = univention.admin.samba.acctFlags(flags[0].decode('ASCII'))
		try:
			return acctFlags['L'] == 1
		except KeyError:
			pass
	return False


def isKerberosLocked(oldattr):
	flags = oldattr.get('krb5KDCFlags', [b'0'])[0]
	try:
		state = 1 << 17
		return int(flags) & state == state
	except ValueError:
		return False


def isLDAPLocked(oldattr):
	return bool(oldattr.get('pwdAccountLockedTime', [b''])[0])


def unmapSambaRid(oldattr):
	sid = oldattr.get('sambaSID', [b''])[0]
	pos = sid.rfind(b'-')
	return sid[pos + 1:].decode('ASCII')


def mapKeyAndValue(old, encoding=()):
	"""Map (key, value) list to key=value list.
	>>> mapKeyAndValue([("a", "b")])
	[b'a=b']
	"""
	return [u'='.join(entry).encode(*encoding) for entry in old]


def unmapKeyAndValue(old, encoding=()):
	"""Map (key=value) list to (key, value) list.
	>>> unmapKeyAndValue([b"a=b"])
	[['a', 'b']]
	"""
	return [entry.decode(*encoding).split(u'=', 1) for entry in old]


def mapWindowsFiletime(old, encoding=()):  # type: (str) -> List[bytes]
	if old:
		if old == "0":
			return [old.encode(*encoding)]
		unixtime = time.strptime(old, '%Y%m%d%H%M%SZ')
		d = long(116444736000000000)  # difference between 1601 and 1970
		windows_filetime = long(calendar.timegm(unixtime)) * 10000000 + d
		return [str(int(windows_filetime)).encode('ASCII')]
	return []


def unmapWindowsFiletime(old, encoding=()):  # type: (List[bytes]) -> str
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
			ud.debug(ud.ADMIN, ud.INFO, 'Value of sambaBadPasswordTime is not set to a Windows Filetime (100 nanoseconds since January 1, 1601.)\nInstead its set to %s' % (password_time,))
			return time.strftime('%Y%m%d%H%M%SZ', time.gmtime(password_time))
	return u''


def datetime_from_local_datetimetimezone_tuple(local_datetimetimezone_tuple):  # type: (List[str]) -> datetime.datetime
	d, t, tz = local_datetimetimezone_tuple
	# dttz_str = module.property_descriptions[key].syntax.tostring(local_datetimetimezone_tuple)
	naive_dt = datetime.strptime("%s %s" % (d, t), "%Y-%m-%d %H:%M")
	return pytz.timezone(tz).localize(naive_dt)


def mapDateTimeTimezoneTupleToUTCDateTimeString(local_datetimetimezone_tuple, encoding=()):  # type: (List[str]) -> List[bytes]
	if local_datetimetimezone_tuple and all(local_datetimetimezone_tuple):
		dt = datetime_from_local_datetimetimezone_tuple(local_datetimetimezone_tuple)
		return [dt.astimezone(pytz.utc).strftime("%Y%m%d%H%M%SZ").encode(*encoding)]
	return []


def unmapUTCDateTimeToLocaltime(attribute_value, encoding=()):  # type: (List[bytes]) -> List[str]
	if attribute_value and attribute_value[0]:
		generalizedtime = attribute_value[0].decode(*encoding)
		try:
			utc_datetime = datetime.strptime(generalizedtime, "%Y%m%d%H%M%SZ")
		except ValueError:
			ud.debug(ud.ADMIN, ud.ERROR, 'Value of krb5ValidStart is not in generalizedTime format: %s' % (generalizedtime,))
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
mapping.register('country', 'st', None, univention.admin.mapping.ListToString)
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
mapping.register('userCertificate', 'userCertificate;binary', univention.admin.mapping.mapBase64, univention.admin.mapping.unmapBase64)
mapping.register('jpegPhoto', 'jpegPhoto', univention.admin.mapping.mapBase64, univention.admin.mapping.unmapBase64)
mapping.register('umcProperty', 'univentionUMCProperty', mapKeyAndValue, unmapKeyAndValue)
mapping.register('lockedTime', 'sambaBadPasswordTime', mapWindowsFiletime, unmapWindowsFiletime)
mapping.register('accountActivationDate', 'krb5ValidStart', mapDateTimeTimezoneTupleToUTCDateTimeString, unmapUTCDateTimeToLocaltime, encoding='ASCII')

mapping.registerUnmapping('sambaRID', unmapSambaRid)
mapping.registerUnmapping('passwordexpiry', unmapPasswordExpiry)
mapping.registerUnmapping('userexpiry', unmapUserExpiry)
mapping.registerUnmapping('disabled', unmapDisabled)
mapping.registerUnmapping('locked', unmapLocked)
mapping.register('password', 'userPassword', univention.admin.mapping.dontMap(), univention.admin.mapping.ListToString)


class object(univention.admin.handlers.simpleLdap):
	module = module

	use_performant_ldap_search_filter = True

	def __init__(self, co, lo, position, dn=u'', superordinate=None, attributes=None):
		self.groupsLoaded = True
		self.password_length = 8

		univention.admin.handlers.simpleLdap.__init__(self, co, lo, position, dn, superordinate, attributes=attributes)

	def _simulate_legacy_options(self):
		'''simulate old options behavior to provide backward compatibility for udm extensions'''
		options = dict(
			posix=b'posixAccount',
			samba=b'sambaSamAccount',
			kerberos=b'krb5Principal',
			mail=b'univentionMail',
			person=b'person',
		)
		for opt, oc in options.items():
			# existing object
			if self.oldattr:
				if oc in self.oldattr.get('objectClass', []):
					self.options.append(opt)
			# new object
			else:
				self.options.append(opt)

	def open(self, loadGroups=True):
		univention.admin.handlers.simpleLdap.open(self)
		if self.exists():
			self._unmap_mail_forward()
			self._unmap_pwd_change_next_login()
			self._unmap_automount_information()
			self._unmapUnlockTime()
			self.reload_certificate()
			self._load_groups(loadGroups)
		self.save()
		if not self.exists():  # TODO: move this block into _ldap_pre_create!
			self._set_default_group()

	def _load_groups(self, loadGroups):
		if self.exists():
			if loadGroups:  # this is optional because it can take much time on larger installations, default is true
				self['groups'] = [x.decode('UTF-8') if six.PY2 else x for x in self.lo.searchDn(filter=filter_format(u'(&(cn=*)(|(objectClass=univentionGroup)(objectClass=sambaGroupMapping))(uniqueMember=%s))', [self.dn]))]
			else:
				ud.debug(ud.ADMIN, ud.INFO, 'user: open with loadGroups=false for user %s' % self['username'])
			self.groupsLoaded = loadGroups
			primaryGroupNumber = self.oldattr.get('gidNumber', [b''])[0].decode('ASCII')
			if primaryGroupNumber:
				primaryGroupResult = self.lo.searchDn(filter=filter_format(u'(&(cn=*)(|(objectClass=posixGroup)(objectClass=sambaGroupMapping))(gidNumber=%s))', [primaryGroupNumber]))
				if primaryGroupResult:
					self['primaryGroup'] = primaryGroupResult[0]
				else:
					try:
						primaryGroup = self.lo.search(filter='(objectClass=univentionDefault)', base='cn=univention,' + self.position.getDomain(), attr=['univentionDefaultGroup'])
						try:
							primaryGroup = primaryGroup[0][1]["univentionDefaultGroup"][0].decode('UTF-8')
						except Exception:
							primaryGroup = None
					except Exception:
						primaryGroup = None

					ud.debug(ud.ADMIN, ud.INFO, 'user: could not find primaryGroup, setting primaryGroup to %s' % primaryGroup)

					if not primaryGroup:
						raise univention.admin.uexceptions.primaryGroup(self.dn)
					self.info['primaryGroup'] = primaryGroup
					self.__primary_group()
			else:
				self.info['primaryGroup'] = None
				self.save()
				raise univention.admin.uexceptions.primaryGroup(self.dn)

	def _set_default_group(self):
		primary_group_from_template = self['primaryGroup']
		if not primary_group_from_template:
			searchResult = self.lo.search(filter=u'(objectClass=univentionDefault)', base=u'cn=univention,' + self.position.getDomain(), attr=['univentionDefaultGroup'])
			if not searchResult or not searchResult[0][1]:
				self.info['primaryGroup'] = None
				self.save()
				raise univention.admin.uexceptions.primaryGroup(self.dn)

			for tmp, number in searchResult:
				primaryGroupResult = self.lo.searchDn(filter=filter_format(u'(&(objectClass=posixGroup)(cn=%s))', (univention.admin.uldap.explodeDn(number['univentionDefaultGroup'][0].decode('UTF-8'), 1)[0],)), base=self.position.getDomain(), scope='domain')
				if primaryGroupResult:
					self['primaryGroup'] = primaryGroupResult[0]
					# self.save() must not be called after this point in self.open()
					# otherwise self.__primary_group doesn't add a new user to the
					# univentionDefaultGroup because "not self.hasChanged('primaryGroup')"

	def _unmap_pwd_change_next_login(self):
		if self.oldattr.get('shadowLastChange', [b''])[0] == b'0':
			self['pwdChangeNextLogin'] = '1'
		elif self['passwordexpiry']:
			today = time.strftime('%Y-%m-%d').split('-')
			expiry = self['passwordexpiry'].split('-')
			# expiry.reverse()
			# today.reverse()
			if int(''.join(today)) >= int(''.join(expiry)):
				self['pwdChangeNextLogin'] = '1'

	def _unmap_mail_forward(self):
		if configRegistry.is_true('directory/manager/user/activate_ldap_attribute_mailForwardCopyToSelf', False):
			return
		# mailForwardCopyToSelf is a "virtual" property. The boolean value is set to True, if
		# the LDAP attribute mailForwardAddress contains the mailPrimaryAddress. The mailPrimaryAddress
		# is removed from oldattr for correct display in CLI/UMC and for proper detection of changes.
		# Remark: By setting the ucr-v the attribute is saved directly to LDAP.
		if self.get('mailPrimaryAddress') in self.get('mailForwardAddress', []):
			self.oldattr['mailForwardAddress'] = self.oldattr.get('mailForwardAddress', [])[:]
			self['mailForwardAddress'].remove(self['mailPrimaryAddress'])
			self['mailForwardCopyToSelf'] = '1'
		else:
			self['mailForwardCopyToSelf'] = '0'

	def _unmap_automount_information(self):
		if 'automountInformation' not in self.oldattr:
			return
		try:
			flags, unc = re.split(b' +', self.oldattr['automountInformation'][0], 1)
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
				])
			])
			res = univention.admin.modules.lookup(univention.admin.modules.get('shares/share'), None, self.lo, filter=filter_, scope='domain')
			if len(res) == 1:
				self['homeShare'] = res[0].dn
				relpath = path.replace(sharepath, u'')
				if len(relpath) > 0 and relpath[0] == u'/':
					relpath = relpath[1:]
				self['homeSharePath'] = relpath
				break
			elif len(res) > 1:
				break
			elif len(res) < 1:
				sharepath = os.path.split(sharepath)[0]

	def _unmapUnlockTime(self):
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
			if '1' != self['disabled'] or not self.hasChanged('disabled'):
				raise
			kwargs['ignore_license'] = True
			return super(object, self).modify(*args, **kwargs)

	def reload_certificate(self):
		"""Reload user certificate."""
		if 'pki' not in self.options:
			return
		self.info['certificateSubjectCountry'] = ''
		self.info['certificateSubjectState'] = ''
		self.info['certificateSubjectLocation'] = ''
		self.info['certificateSubjectOrganisation'] = ''
		self.info['certificateSubjectOrganisationalUnit'] = ''
		self.info['certificateSubjectCommonName'] = ''
		self.info['certificateSubjectMail'] = ''
		self.info['certificateIssuerCountry'] = ''
		self.info['certificateIssuerState'] = ''
		self.info['certificateIssuerLocation'] = ''
		self.info['certificateIssuerOrganisation'] = ''
		self.info['certificateIssuerOrganisationalUnit'] = ''
		self.info['certificateIssuerCommonName'] = ''
		self.info['certificateIssuerMail'] = ''
		self.info['certificateDateNotBefore'] = ''
		self.info['certificateDateNotAfter'] = ''
		self.info['certificateVersion'] = ''
		self.info['certificateSerial'] = ''
		certificate = self.info.get('userCertificate')
		values = load_certificate(certificate)
		if values:
			self.info.update(values)
		else:
			self.info['userCertificate'] = ''

	def hasChanged(self, key):
		if key == 'disabled' and inconsistentDisabledState(self.oldattr):
			return True
		if key == 'locked' and inconsistentLockedState(self.oldattr):
			return True
		return super(object, self).hasChanged(key)

#		if key == 'disabled':
#			acctFlags = univention.admin.samba.acctFlags(self.oldattr.get("sambaAcctFlags", [b''])[0].decode('ASCII')).decode()
#			krb5Flags = self.oldattr.get('krb5KDCFlags', [])
#			shadowExpire = self.oldattr.get('shadowExpire', [])
#
#			if not acctFlags and not krb5Flags and not shadowExpire:
#				return False
#			if self['disabled'] == 'all':
#				return 'D' not in acctFlags or b'126' in krb5Flags or b'1' not in shadowExpire
#			elif self['disabled'] == 'windows':
#				return 'D' not in acctFlags or b'254' in krb5Flags or b'1' in shadowExpire
#			elif self['disabled'] == 'kerberos':
#				return 'D' in acctFlags or b'126' in krb5Flags or b'1' in shadowExpire
#			elif self['disabled'] == 'posix':
#				return 'D' in acctFlags or b'254' in krb5Flags or b'1' not in shadowExpire
#			elif self['disabled'] == 'windows_kerberos':
#				return 'D' not in acctFlags or b'126' in krb5Flags or b'1' in shadowExpire
#			elif self['disabled'] == 'windows_posix':
#				return 'D' not in acctFlags or b'254' in krb5Flags or b'1' not in shadowExpire
#			elif self['disabled'] == 'posix_kerberos':
#				return 'D' in acctFlags or b'126' in krb5Flags or b'1' not in shadowExpire
#			else:  # enabled
#				return 'D' in acctFlags or b'254' in krb5Flags or b'1' in shadowExpire
#		elif key == 'locked':
#			password = self['password']
#			acctFlags = univention.admin.samba.acctFlags(self.oldattr.get("sambaAcctFlags", [b''])[0].decode('ASCII')).decode()
#			if not password and not acctFlags:
#				return False
#			if self['locked'] == 'all':
#				return not univention.admin.password.is_locked(password) or 'L' not in acctFlags
#			elif self['locked'] == 'windows':
#				return univention.admin.password.is_locked(password) or 'L' not in acctFlags
#			elif self['locked'] == 'posix':
#				return not univention.admin.password.is_locked(password) or 'L' in acctFlags
#			else:
#				return univention.admin.password.is_locked(password) or 'L' in acctFlags
#
#		return super(object, self).hasChanged(key)

	def __update_groups(self):
		if not self.groupsLoaded:
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
			ud.debug(ud.ADMIN, ud.INFO, 'users/user: rewrite memberuid after rename')
			for group in new_groups:
				self.__rewrite_member_uid(group)

		group_mod = univention.admin.modules.get('groups/group')

		ud.debug(ud.ADMIN, ud.INFO, 'users/user: check groups in old_groups')
		for group in old_groups:
			if group and not case_insensitive_in_list(group, self.info.get('groups', [])) and group.lower() != self['primaryGroup'].lower():
				grpobj = group_mod.object(None, self.lo, self.position, group)
				grpobj.fast_member_remove([self.old_dn], [old_uid])
				if self.dn != self.old_dn:
					# we change our DN _before_ removing it from the group
					# so if we changed it and if we use refint overlay, it already updated the uniqueMember of the group and we will not catch it with old_dn
					grpobj.fast_member_remove([self.dn], [old_uid])

		ud.debug(ud.ADMIN, ud.INFO, 'users/user: check groups in info[groups]')
		for group in self.info.get('groups', []):
			if group and not case_insensitive_in_list(group, old_groups):
				grpobj = group_mod.object(None, self.lo, self.position, group)
				grpobj.fast_member_add([self.dn], [new_uid])

		if configRegistry.is_true("directory/manager/user/primarygroup/update", True):
			ud.debug(ud.ADMIN, ud.INFO, 'users/user: check primaryGroup')
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
						ud.debug(ud.ADMIN, ud.WARN, 'users/user: A groupmember has multiple UIDs (%s %r)' % (memberDNstr, UIDs))
		self.lo.modify(group, [('memberUid', uids, new_uids)])  # TODO: check if encoding is correct

	def __primary_group(self):
		if not self.hasChanged('primaryGroup'):
			return

		if configRegistry.is_true("directory/manager/user/primarygroup/update", True):
			new_uid = self.info.get('username')
			group_mod = univention.admin.modules.get('groups/group')
			grpobj = group_mod.object(None, self.lo, self.position, self['primaryGroup'])
			grpobj.fast_member_add([self.dn], [new_uid])
			ud.debug(ud.ADMIN, ud.INFO, 'users/user: adding to new primaryGroup %s (uid=%s)' % (self['primaryGroup'], new_uid))

	def krb5_principal(self):
		domain = univention.admin.uldap.domain(self.lo, self.position)
		realm = domain.getKerberosRealm()
		if not realm:
			raise univention.admin.uexceptions.noKerberosRealm()
		return self['username'] + '@' + realm

	def _check_uid_gid_uniqueness(self):
		if not configRegistry.is_true("directory/manager/uid_gid/uniqueness", True):
			return
		# POSIX, Samba
		fg = univention.admin.filter.expression('gidNumber', self['uidNumber'])
		group_objects = univention.admin.handlers.groups.group.lookup(self.co, self.lo, filter_s=fg)
		if group_objects:
			raise univention.admin.uexceptions.uidNumberAlreadyUsedAsGidNumber(repr(self["uidNumber"]))

	def _ldap_pre_create(self):
		super(object, self)._ldap_pre_create()
		ud.debug(ud.ADMIN, ud.INFO, 'users/user: dn was set to %s' % (self.dn,))

		if self['mailPrimaryAddress']:
			self['mailPrimaryAddress'] = self['mailPrimaryAddress'].lower()

		# request a new uidNumber or get lock for manually set uidNumber
		if self['uidNumber']:
			univention.admin.allocators.acquireUnique(self.lo, self.position, 'uidNumber', self['uidNumber'], 'uidNumber', scope='base')
			# "False" ==> do not update univentionLastUsedValue in LDAP if a specific value has been specified
			self.alloc.append(('uidNumber', self['uidNumber'], False))
		else:
			self['uidNumber'] = self.request_lock('uidNumber')

		self._check_uid_gid_uniqueness()

	def _ldap_pre_ready(self):
		super(object, self)._ldap_pre_ready()

		if self.exists() and not self.oldinfo.get('password') and not self['password']:
			# password property is required but LDAP ACL's disallow reading them
			self.info['password'] = self.oldinfo['password'] = u'*'
			self.info['disabled'] = self.oldinfo['disabled']

		if not self.exists() or self.hasChanged('primaryGroup'):
			# Ensure the primary Group has the samba option enabled
			if self['primaryGroup'] and not self.lo.getAttr(self['primaryGroup'], 'sambaSID'):
				raise univention.admin.uexceptions.primaryGroupWithoutSamba(self['primaryGroup'])

		if not self.exists() or self.hasChanged('username'):
			check_prohibited_username(self.lo, self['username'])

			# get lock for username
			try:
				if self['username']:  # might not be set when using CLI without --set username=
					self.request_lock('uid', self['username'])
			except univention.admin.uexceptions.noLock:
				raise univention.admin.uexceptions.uidAlreadyUsed(self['username'])

		# get lock for mailPrimaryAddress
		if not self.exists() or self.hasChanged('mailPrimaryAddress'):
			# ignore case in change of mailPrimaryAddress, we only store the lowercase address anyway
			if self['mailPrimaryAddress'] and self['mailPrimaryAddress'].lower() != (self.oldinfo.get('mailPrimaryAddress', None) or '').lower():
				try:
					self.request_lock('mailPrimaryAddress', self['mailPrimaryAddress'])
				except univention.admin.uexceptions.noLock:
					raise univention.admin.uexceptions.mailAddressUsed(self['mailPrimaryAddress'])

		if self['unlock'] == '1':
			self['locked'] = u'0'
		if self.hasChanged('disabled') and self['disabled'] == '0' and not self.hasChanged('accountActivationDate'):
			self['accountActivationDate'] = self.descriptions['accountActivationDate'].default(self)
		if self['accountActivationDate'] and all(self['accountActivationDate']) and datetime.now(tz=pytz.utc) < datetime_from_local_datetimetimezone_tuple(self['accountActivationDate']):
			self['disabled'] = '1'
		if self['disabled'] == '1':
			self['locked'] = u'0'  # Samba/AD behavior

		# legacy options to make old hooks happy (46539)
		self._simulate_legacy_options()

	def _ldap_addlist(self):
		al = super(object, self)._ldap_addlist()

		# Kerberos
		al.append((u'krb5MaxLife', b'86400'))
		al.append((u'krb5MaxRenew', b'604800'))

		return al

	def _ldap_post_create(self):
		super(object, self)._ldap_post_create()
		self.__update_groups()
		self.__primary_group()

	def _ldap_post_modify(self):
		super(object, self)._ldap_post_modify()
		# POSIX
		self.__update_groups()
		self.__primary_group()

	def _ldap_pre_rename(self, newdn):
		super(object, self)._ldap_pre_rename(newdn)
		try:
			self.move(newdn)
		finally:
			univention.admin.allocators.release(self.lo, self.position, 'uid', self['username'])

	def _ldap_pre_modify(self):
		super(object, self)._ldap_pre_modify()
		if not self.oldattr.get('mailForwardCopyToSelf') and self['mailForwardCopyToSelf'] == '0' and not self['mailForwardAddress']:
			self['mailForwardCopyToSelf'] = None

		if self.hasChanged('mailPrimaryAddress'):
			if self['mailPrimaryAddress']:
				self['mailPrimaryAddress'] = self['mailPrimaryAddress'].lower()

		if self.hasChanged("uidNumber"):
			# this should never happen, as uidNumber is marked as unchangeable
			self._check_uid_gid_uniqueness()

	def _ldap_modlist(self):
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
		if self.hasChanged('sambaPrivileges'):
			# add univentionSambaPrivileges objectclass
			if self['sambaPrivileges'] and b'univentionSambaPrivileges' not in self.oldattr.get('objectClass', []):
				ml.append(('objectClass', b'', b'univentionSambaPrivileges'))
		return ml

	def _modlist_cn(self, ml):
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
		if not self.exists() or self.hasChanged('username'):
			ml.append(('krb5PrincipalName', self.oldattr.get('krb5PrincipalName', []), [self.krb5_principal().encode('utf-8')]))  # TODO: decide to let krb5_principal return bytestring?!
		return ml

	# If you change anything here, please also check users/ldap.py
	def _check_password_history(self, ml, pwhistoryPolicy):
		if self.exists() and not self.hasChanged('password'):
			return ml
		if self['overridePWHistory'] == '1':
			return ml

		pwhistory = self.oldattr.get('pwhistory', [b''])[0].decode('ASCII')

		if univention.admin.password.password_already_used(self['password'], pwhistory):
			raise univention.admin.uexceptions.pwalreadyused()

		if pwhistoryPolicy.pwhistoryLength is not None:
			newPWHistory = univention.admin.password.get_password_history(self['password'], pwhistory, pwhistoryPolicy.pwhistoryLength)
			ml.append(('pwhistory', self.oldattr.get('pwhistory', [b''])[0], newPWHistory.encode('ASCII')))

		return ml

	# If you change anything here, please also check users/ldap.py
	def _check_password_complexity(self, pwhistoryPolicy):
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
		if self.exists() and not self.hasChanged('password'):
			return ml

		password_nt, password_lm = univention.admin.password.ntlm(self['password'])  # TODO: decide to let ntlm() return bytestring?!
		password_nt, password_lm = password_nt.encode('ASCII'), password_lm.encode('ASCII')
		ml.append(('sambaNTPassword', self.oldattr.get('sambaNTPassword', [b''])[0], password_nt))
		ml.append(('sambaLMPassword', self.oldattr.get('sambaLMPassword', [b''])[0], password_lm))

		if pwhistoryPolicy.pwhistoryLength is not None:
			smbpwhistory = self.oldattr.get('sambaPasswordHistory', [b''])[0].decode('ASCII')
			newsmbPWHistory = self._get_samba_password_history(password_nt, smbpwhistory, pwhistoryPolicy.pwhistoryLength)
			ml.append(('sambaPasswordHistory', self.oldattr.get('sambaPasswordHistory', [b''])[0], newsmbPWHistory.encode('ASCII')))
		return ml

	def _modlist_kerberos_password(self, ml):
		if self.exists() and not self.hasChanged('password'):
			return ml

		krb_keys = univention.admin.password.krb5_asn1(self.krb5_principal(), self['password'])
		krb_key_version = str(int(self.oldattr.get('krb5KeyVersionNumber', ['0'])[0]) + 1).encode('ASCII')
		ml.append(('krb5Key', self.oldattr.get('krb5Key', []), krb_keys))
		ml.append(('krb5KeyVersionNumber', self.oldattr.get('krb5KeyVersionNumber', []), krb_key_version))
		return ml

	def _modlist_password_expiry(self, ml, pwhistoryPolicy):
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
		ud.debug(ud.ADMIN, ud.INFO, 'sambaPwdLastSetValue: %s' % sambaPwdLastSetValue)
		sambaPwdLastSetValue = sambaPwdLastSetValue.encode('UTF-8')
		ml.append(('sambaPwdLastSet', self.oldattr.get('sambaPwdLastSet', [b''])[0], sambaPwdLastSetValue))

		krb5PasswordEnd = u''
		if pwhistoryPolicy.expiryInterval or pwd_change_next_login:
			expiry = long(time.time())
			if not pwd_change_next_login:
				expiry = expiry + (pwhistoryPolicy.expiryInterval * 3600 * 24)
			krb5PasswordEnd = time.strftime("%Y%m%d000000Z", time.gmtime(expiry))

		ud.debug(ud.ADMIN, ud.INFO, 'krb5PasswordEnd: %s' % krb5PasswordEnd)
		old_krb5PasswordEnd = self.oldattr.get('krb5PasswordEnd', [b''])[0]
		krb5PasswordEnd = krb5PasswordEnd.encode('ASCII')
		if old_krb5PasswordEnd != krb5PasswordEnd:
			ml.append(('krb5PasswordEnd', old_krb5PasswordEnd, krb5PasswordEnd))

		return ml

	def _modlist_krb5kdc_flags(self, ml):
		"""Set the krb5KDCFlags.
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
#			elif self['locked'] == '1':  # lock kerberos password
#				krb_kdcflags |= (1 << 17)

			ml.append(('krb5KDCFlags', self.oldattr.get('krb5KDCFlags', []), str(krb_kdcflags).encode('ASCII')))
		return ml

	# If you change anything here, please also check users/ldap.py
	def _modlist_posix_password(self, ml):
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
		# remove pwdAccountLockedTime during unlocking
		if self.hasChanged('locked') and self['locked'] == '0':
			pwdAccountLockedTime = self.oldattr.get('pwdAccountLockedTime', [b''])[0]
			if pwdAccountLockedTime:
				ml.append(('pwdAccountLockedTime', pwdAccountLockedTime, b''))
		return ml

	def _modlist_samba_bad_pw_count(self, ml):
		if self.hasChanged('locked') and self['locked'] == '0':
			# reset bad pw count
			ml.append(('sambaBadPasswordCount', self.oldattr.get('sambaBadPasswordCount', [b''])[0], b"0"))
			ml.append(('sambaBadPasswordTime', self.oldattr.get('sambaBadPasswordTime', [b''])[0], b'0'))
		return ml

	def _modlist_samba_kickoff_time(self, ml):
		if self.hasChanged('userexpiry'):
			sambaKickoffTime = b''
			if self['userexpiry']:
				sambaKickoffTime = b"%d" % long(time.mktime(time.strptime(self['userexpiry'], "%Y-%m-%d")))
				ud.debug(ud.ADMIN, ud.INFO, 'sambaKickoffTime: %s' % sambaKickoffTime)
			old_sambaKickoffTime = self.oldattr.get('sambaKickoffTime', [b''])[0]
			if old_sambaKickoffTime != sambaKickoffTime:
				ml.append(('sambaKickoffTime', self.oldattr.get('sambaKickoffTime', [b''])[0], sambaKickoffTime))
		return ml

	def _modlist_krb5_valid_end(self, ml):
		if self.hasChanged('userexpiry'):
			krb5ValidEnd = u''
			if self['userexpiry']:
				krb5ValidEnd = u"%s%s%s000000Z" % (self['userexpiry'][0:4], self['userexpiry'][5:7], self['userexpiry'][8:10])
				ud.debug(ud.ADMIN, ud.INFO, 'krb5ValidEnd: %s' % krb5ValidEnd)
			krb5ValidEnd = krb5ValidEnd.encode('ASCII')
			old_krb5ValidEnd = self.oldattr.get('krb5ValidEnd', [b''])[0]
			if old_krb5ValidEnd != krb5ValidEnd:
				if not self['userexpiry']:
					ml.append(('krb5ValidEnd', old_krb5ValidEnd, None))
				else:
					ml.append(('krb5ValidEnd', self.oldattr.get('krb5ValidEnd', [b''])[0], krb5ValidEnd))
		return ml

	def _modlist_shadow_expire(self, ml):
		if self.hasChanged('disabled') or self.hasChanged('userexpiry'):
			if self['disabled'] == '1' and self.hasChanged('disabled') and not self.hasChanged('userexpiry'):
				shadowExpire = u'1'
			elif self['userexpiry']:
				shadowExpire = u"%d" % long(time.mktime(time.strptime(self['userexpiry'], "%Y-%m-%d")) / 3600 / 24 + 1)
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
		if self['mailForwardAddress'] and not self['mailPrimaryAddress']:
			raise univention.admin.uexceptions.missingInformation(_('Primary e-mail address must be set, if messages should be forwarded for it.'))
		if self.get('mailForwardCopyToSelf') == '1' and not self['mailPrimaryAddress']:
			raise univention.admin.uexceptions.missingInformation(_('Primary e-mail address must be set, if a copy of forwarded messages should be stored in its mailbox.'))
		if configRegistry.is_true('directory/manager/user/activate_ldap_attribute_mailForwardCopyToSelf', False):
			return ml

		try:
			new = [x[2] if isinstance(x[2], (list, tuple)) else [x[2]] for x in ml if x[0] == 'mailForwardAddress' and x[2]][0]
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
		# make sure that univentionPerson is set as objectClass when needed
		if any(self.hasChanged(ikey) and self[ikey] for ikey in ('umcProperty', 'birthday', 'serviceSpecificPassword')) and b'univentionPerson' not in self.oldattr.get('objectClass', []):
			ml.append(('objectClass', b'', b'univentionPerson'))  # TODO: check if exists already
		return ml

	def _modlist_home_share(self, ml):
		if self.hasChanged('homeShare') or self.hasChanged('homeSharePath'):
			if self['homeShare']:
				share_mod = univention.admin.modules.get('shares/share')
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
		if not self.exists() or self.hasChanged('sambaRID'):
			sid = self.__generate_user_sid(self['uidNumber'])
			sid = sid.encode('ASCII')
			ml.append(('sambaSID', self.oldattr.get('sambaSID', [b'']), [sid]))
		return ml

	def _modlist_primary_group(self, ml):
		if not self.exists() or self.hasChanged('primaryGroup'):
			# Posix
			ml.append(('gidNumber', self.oldattr.get('gidNumber', [b'']), [self.get_gid_for_primary_group().encode('ASCII')]))
			# Samba
			ml.append(('sambaPrimaryGroupSID', self.oldattr.get('sambaPrimaryGroupSID', [b'']), [self.get_sid_for_primary_group().encode('ASCII')]))
		return ml

	def _modlist_sambaAcctFlags(self, ml):
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
		udm_new = self.info.get('serviceSpecificPassword', None)
		if udm_new:
			service = udm_new.get('service', None)
			password = udm_new.get('password', None)
			if service != 'radius':
				raise univention.admin.uexceptions.unsupportedService(service)
			if service:
				import passlib.hash
				nt = passlib.hash.nthash.hash(password).upper().encode('utf-8')
				ml.append(('univentionRadiusPassword', self.oldattr.get('univentionRadiusPassword', [b'']), [nt]))
		return ml

	def _ldap_post_remove(self):
		self.alloc.append(('sid', self.oldattr['sambaSID'][0].decode('ASCII')))
		self.alloc.append(('uid', self.oldattr['uid'][0].decode('UTF-8')))
		self.alloc.append(('uidNumber', self.oldattr['uidNumber'][0].decode('ASCII')))
		if self['mailPrimaryAddress']:
			self.alloc.append(('mailPrimaryAddress', self['mailPrimaryAddress']))
		super(object, self)._ldap_post_remove()

		for group in self.oldinfo.get('groups', []):
			groupObject = univention.admin.objects.get(univention.admin.modules.get('groups/group'), self.co, self.lo, self.position, group)
			groupObject.fast_member_remove([self.dn], [x.decode('UTF-8') for x in self.oldattr.get('uid', [])], ignore_license=True)

	def _move(self, newdn, modify_childs=True, ignore_license=False):
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

	@classmethod
	def _get_samba_password_history(cls, newpassword, smbpwhistory, smbpwhlen):
		"""Get history of previously used passwords.

#		>>> object._get_samba_password_history('186CB09181E2C2ECAAC768C47C729904', 'A047EE4A9DB8BC8B4F3F8A03D72DEB80', 0)
#		...
#		>>> object._get_samba_password_history('186CB09181E2C2ECAAC768C47C729904', '', 1)
#		...
#		>>> object._get_samba_password_history('186CB09181E2C2ECAAC768C47C729904', 'A047EE4A9DB8BC8B4F3F8A03D72DEB80', 1)
#		...
#		>>> object._get_samba_password_history('186CB09181E2C2ECAAC768C47C729904', 'A047EE4A9DB8BC8B4F3F8A03D72DEB80', 2)
#		...
		"""

		# calculate the password hash & salt
		# in binary for calculating the md5:
		salt = os.urandom(16)
		# we have to have that in hex:
		hexsalt = codecs.encode(salt, 'hex').upper().decode('ASCII')
		# we need the ntpwd binary data to
		pwd = codecs.decode(newpassword, 'hex')
		# calculating hash. stored as a 32byte hex in sambaPasswordHistory,
		# syntax like that: [Salt][MD5(Salt+Hash)]
		#	First 16bytes ^		^ last 16bytes.
		pwdhash = hashlib.md5(salt + pwd).hexdigest().upper()
		smbpwhash = hexsalt + pwdhash

		# split the history
		pwlist = smbpwhistory.strip().split(' ')
		# append new hash
		pwlist.append(smbpwhash)
		# strip old hashes
		pwlist = pwlist[-smbpwhlen:]
		# build history
		smbpwhistory = ''.join(pwlist)
		return smbpwhistory

	def __allocate_rid(self, rid):
		searchResult = self.lo.search(filter='objectClass=sambaDomain', attr=['sambaSID'])
		domainsid = searchResult[0][1]['sambaSID'][0]
		sid = domainsid.decode('ASCII') + u'-' + rid
		try:
			return self.request_lock('sid', sid)
		except univention.admin.uexceptions.noLock:
			raise univention.admin.uexceptions.sidAlreadyUsed(rid)

	def __generate_user_sid(self, uidNum):
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
		filter_p = super(object, cls).unmapped_lookup_filter()
		filter_p.expressions.extend([
			univention.admin.filter.conjunction(u'!', [univention.admin.filter.expression(u'uidNumber', u'0')]),
			univention.admin.filter.conjunction(u'!', [univention.admin.filter.expression(u'univentionObjectFlag', u'functional')]),
		])
		return filter_p

	@classmethod
	def _ldap_attributes(cls):
		return [u'*', u'pwdAccountLockedTime']

	@classmethod
	def rewrite_filter(cls, filter, mapping):
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
			elif filter.value == u'*':
				filter.variable = u'uid'
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
				#	filter.variable = u'userPassword'
				#	filter.value = u'{crypt}!*'
				elif filter.value == u'none':
					# filter.transform_to_conjunction(univention.admin.filter.parse(u'(&(!(sambaAcctFlags=[UL       ]))(!(sambaAcctFlags=[ULD       ]))(!(userPassword={crypt}!*)))'))
					filter.transform_to_conjunction(univention.admin.filter.parse(u'(&(!(sambaAcctFlags=[UL       ]))(!(sambaAcctFlags=[ULD       ])))'))
			elif filter.value == u'*':
				filter.variable = u'uid'
		else:
			super(object, cls).rewrite_filter(filter, mapping)

	@classmethod
	def identify(cls, dn, attr, canonical=False):
		if b'0' in attr.get('uidNumber', []) or b'$' in attr.get('uid', [b''])[0] or b'univentionHost' in attr.get('objectClass', []) or b'functional' in attr.get('univentionObjectFlag', []):
			return False
		required_ocs = {b'posixAccount', b'shadowAccount', b'sambaSamAccount', b'person', b'krb5KDCEntry', b'krb5Principal'}
		ocs = set(attr.get('objectClass', []))
		return ocs & required_ocs == required_ocs


lookup = object.lookup
lookup_filter = object.lookup_filter
identify = object.identify
