# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin module for the user objects
#
# Copyright 2004-2019 Univention GmbH
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

from __future__ import absolute_import

import hashlib
import os
import string
import re
import copy
import time
import struct
import calendar
import base64

from M2Crypto import X509
import ldap
import six
from ldap.filter import filter_format

import univention.admin
from univention.admin.layout import Tab, Group
import univention.admin.filter
import univention.admin.handlers
import univention.admin.handlers.groups.group
import univention.admin.password
import univention.admin.samba
import univention.admin.allocators
import univention.admin.localization
import univention.admin.uexceptions
import univention.admin.uldap
import univention.admin.handlers.settings.prohibited_username
from univention.admin import configRegistry
from univention.lib.s4 import rids_for_well_known_security_identifiers

import univention.debug as ud
import univention.password

translation = univention.admin.localization.translation('univention.admin.handlers.users')
_ = translation.translate

module = 'users/user'
operations = ['add', 'edit', 'remove', 'search', 'move', 'copy']
template = 'settings/usertemplate'

childs = 0
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
		copyable=True,
	),
	'lastname': univention.admin.property(
		short_description=_('Last name'),
		long_description='',
		syntax=univention.admin.syntax.string,
		include_in_default_search=True,
		required=True,
		readonly_when_synced=True,
		copyable=True,
	),
	'gecos': univention.admin.property(
		short_description=_('GECOS'),
		long_description='',
		syntax=univention.admin.syntax.IA5string,
		default='<firstname> <lastname><:umlauts,strip>',
		dontsearch=True,
		copyable=True,
	),
	'displayName': univention.admin.property(
		short_description=_('Display name'),
		long_description='',
		syntax=univention.admin.syntax.string,
		default='<firstname> <lastname><:strip>',
		readonly_when_synced=True,
		copyable=True,
	),
	'title': univention.admin.property(
		short_description=_('Title'),
		long_description='',
		syntax=univention.admin.syntax.OneThirdString,
		readonly_when_synced=True,
		copyable=True,
	),
	'initials': univention.admin.property(
		short_description=_('Initials'),
		long_description='',
		syntax=univention.admin.syntax.string6,
		copyable=True,
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
		copyable=True,
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
		long_description=_(''),
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
		long_description='',
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
		copyable=True,
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
		copyable=True,
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
		copyable=True,
	),
	'mobileTelephoneNumber': univention.admin.property(
		short_description=_('Mobile phone number'),
		long_description='',
		syntax=univention.admin.syntax.phone,
		multivalue=True,
		readonly_when_synced=True,
		copyable=True,
	),
	'pagerTelephoneNumber': univention.admin.property(
		short_description=_('Pager telephone number'),
		long_description='',
		syntax=univention.admin.syntax.phone,
		multivalue=True,
		readonly_when_synced=True,
		copyable=True,
	),
	'birthday': univention.admin.property(
		short_description=_('Birthdate'),
		long_description=_('Date of birth'),
		syntax=univention.admin.syntax.iso8601Date,
		copyable=True,
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
		short_description=_('Primary e-mail address'),
		long_description='',
		syntax=univention.admin.syntax.primaryEmailAddressValidDomain,
		include_in_default_search=True,
		readonly_when_synced=True,
	),
	'mailAlternativeAddress': univention.admin.property(
		short_description=_('Alternative e-mail address'),
		long_description='',
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
		copyable=True,
	),
	'userCertificate': univention.admin.property(
		short_description=_("PKI user certificate (DER format)"),
		long_description=_('Public key infrastructure - user certificate '),
		syntax=univention.admin.syntax.Base64Upload,
		dontsearch=True,
		options=['pki'],
		copyable=True,
	),
	'certificateIssuerCountry': univention.admin.property(
		short_description=_('Issuer Country'),
		long_description=_('Certificate Issuer Country'),
		syntax=univention.admin.syntax.string,
		dontsearch=True,
		editable=False,
		options=['pki'],
		copyable=True,
	),
	'certificateIssuerState': univention.admin.property(
		short_description=_('Issuer State'),
		long_description=_('Certificate Issuer State'),
		syntax=univention.admin.syntax.string,
		dontsearch=True,
		editable=False,
		options=['pki'],
		copyable=True,
	),
	'certificateIssuerLocation': univention.admin.property(
		short_description=_('Issuer Location'),
		long_description=_('Certificate Issuer Location'),
		syntax=univention.admin.syntax.string,
		dontsearch=True,
		editable=False,
		options=['pki'],
		copyable=True,
	),
	'certificateIssuerOrganisation': univention.admin.property(
		short_description=_('Issuer Organisation'),
		long_description=_('Certificate Issuer Organisation'),
		syntax=univention.admin.syntax.string,
		dontsearch=True,
		editable=False,
		options=['pki'],
		copyable=True,
	),
	'certificateIssuerOrganisationalUnit': univention.admin.property(
		short_description=_('Issuer Organisational Unit'),
		long_description=_('Certificate Issuer Organisational Unit'),
		syntax=univention.admin.syntax.string,
		dontsearch=True,
		editable=False,
		options=['pki'],
		copyable=True,
	),
	'certificateIssuerCommonName': univention.admin.property(
		short_description=_('Issuer Common Name'),
		long_description=_('Certificate Issuer Common Name'),
		syntax=univention.admin.syntax.string,
		dontsearch=True,
		editable=False,
		options=['pki'],
		copyable=True,
	),
	'certificateIssuerMail': univention.admin.property(
		short_description=_('Issuer Mail'),
		long_description=_('Certificate Issuer Mail'),
		syntax=univention.admin.syntax.string,
		dontsearch=True,
		editable=False,
		options=['pki'],
		copyable=True,
	),
	'certificateSubjectCountry': univention.admin.property(
		short_description=_('Subject Country'),
		long_description=_('Certificate Subject Country'),
		syntax=univention.admin.syntax.string,
		dontsearch=True,
		editable=False,
		options=['pki'],
		copyable=True,
	),
	'certificateSubjectState': univention.admin.property(
		short_description=_('Subject State'),
		long_description=_('Certificate Subject State'),
		syntax=univention.admin.syntax.string,
		dontsearch=True,
		editable=False,
		options=['pki'],
		copyable=True,
	),
	'certificateSubjectLocation': univention.admin.property(
		short_description=_('Subject Location'),
		long_description=_('Certificate Subject Location'),
		syntax=univention.admin.syntax.string,
		dontsearch=True,
		editable=False,
		options=['pki'],
		copyable=True,
	),
	'certificateSubjectOrganisation': univention.admin.property(
		short_description=_('Subject Organisation'),
		long_description=_('Certificate Subject Organisation'),
		syntax=univention.admin.syntax.string,
		dontsearch=True,
		editable=False,
		options=['pki'],
		copyable=True,
	),
	'certificateSubjectOrganisationalUnit': univention.admin.property(
		short_description=_('Subject Organisational Unit'),
		long_description=_('Certificate Subject Organisational Unit'),
		syntax=univention.admin.syntax.string,
		dontsearch=True,
		editable=False,
		options=['pki'],
		copyable=True,
	),
	'certificateSubjectCommonName': univention.admin.property(
		short_description=_('Subject Common Name'),
		long_description=_('Certificate Subject Common Name'),
		syntax=univention.admin.syntax.string,
		dontsearch=True,
		editable=False,
		options=['pki'],
		copyable=True,
	),
	'certificateSubjectMail': univention.admin.property(
		short_description=_('Subject Mail'),
		long_description=_('Certificate Subject Mail'),
		syntax=univention.admin.syntax.string,
		dontsearch=True,
		editable=False,
		options=['pki'],
		copyable=True,
	),
	'certificateDateNotBefore': univention.admin.property(
		short_description=_('Valid from'),
		long_description=_('Certificate valid from'),
		syntax=univention.admin.syntax.date,
		dontsearch=True,
		editable=False,
		options=['pki'],
		copyable=True,
	),
	'certificateDateNotAfter': univention.admin.property(
		short_description=_('Valid until'),
		long_description=_('Certificate valid until'),
		syntax=univention.admin.syntax.date,
		dontsearch=True,
		editable=False,
		options=['pki'],
		copyable=True,
	),
	'certificateVersion': univention.admin.property(
		short_description=_('Version'),
		long_description=_('Certificate Version'),
		syntax=univention.admin.syntax.string,
		dontsearch=True,
		editable=False,
		options=['pki'],
		copyable=True,
	),
	'certificateSerial': univention.admin.property(
		short_description=_('Serial'),
		long_description=_('Certificate Serial'),
		syntax=univention.admin.syntax.string,
		dontsearch=True,
		editable=False,
		options=['pki'],
		copyable=True,
	),
	'umcProperty': univention.admin.property(
		short_description=_('UMC user preferences'),
		long_description=_('Key value pairs storing user preferences for UMC'),
		syntax=univention.admin.syntax.keyAndValue,
		dontsearch=True,
		multivalue=True,
		copyable=True,
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
			['street', 'postcode', 'city', 'country'],
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
	for prohibited_object in (module.lookup(None, lo, '') or []):
		if username in prohibited_object['usernames']:
			raise univention.admin.uexceptions.prohibitedUsername(username)


def case_insensitive_in_list(dn, list):
	for element in list:
		if dn.decode('utf8').lower() == element.decode('utf8').lower():
			return True
	return False


def posixSecondsToLocaltimeDate(seconds):
	return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(seconds))


def posixDaysToDate(days):
	return time.strftime("%Y-%m-%d", time.gmtime(long(days) * 3600 * 24))


def sambaWorkstationsMap(workstations):
	ud.debug(ud.ADMIN, ud.ALL, 'samba: sambaWorkstationMap: in=%s; out=%s' % (workstations, string.join(workstations, ',')))
	return string.join(workstations, ',')


def sambaWorkstationsUnmap(workstations):
	ud.debug(ud.ADMIN, ud.ALL, 'samba: sambaWorkstationUnmap: in=%s; out=%s' % (workstations[0], string.split(workstations[0], ',')))
	return string.split(workstations[0], ',')


def logonHoursMap(logontimes):
	"converts the bitfield 001110010110...100 to the respective string"

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
	# consecutive bytes mean consecutive 8-hrs-intervals, but the leftmost bit stands for
	# the last hour in that interval, the 2nd but leftmost bit for the second-but-last
	# hour and so on. We want to hide this from anybody using this feature.
	# See http://ma.ph-freiburg.de/tng/tng-technical/2003-04/msg00015.html for details.

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
				val += 2**exp
			exp -= 1
		# we now have: 0<=val<=255
		hx = hex(val)[2:4]
		if len(hx) == 1:
			hx = "0" + hx
		ret += hx

	return ret


def logonHoursUnmap(logontimes):
	"converts the string to a bit array"

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
	return filter(lambda i: newtime[i] == '1', range(168))


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
	return time.timezone / 3600


def load_certificate(user_certificate):
	"""Import a certificate in DER format"""
	if not user_certificate:
		return {}
	try:
		certificate = base64.decodestring(user_certificate)
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
				value = getattr(entity, key)
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


def mapHomePostalAddress(old):
	new = []
	for i in old:
		new.append(string.join(i, '$'))
	return new


def unmapHomePostalAddress(old):
	new = []
	for i in old:
		if '$' in i:
			new.append(i.split('$'))
		else:
			new.append([i, " ", " "])

	return new


def unmapUserExpiry(oldattr):
	return unmapKrb5ValidEndToUserexpiry(oldattr) or unmapSambaKickoffTimeToUserexpiry(oldattr) or unmapShadowExpireToUserexpiry(oldattr)


def unmapShadowExpireToUserexpiry(oldattr):
	# The shadowLastChange attribute is the amount of days between 1/1/1970 up to the day that password was modified,
	# shadowMax is the number of days a password is valid. So the password expires on 1/1/1970 + shadowLastChange + shadowMax.
	# shadowExpire contains the absolute date to expire the account.

	if 'shadowExpire' in oldattr and len(oldattr['shadowExpire']) > 0:
		ud.debug(ud.ADMIN, ud.INFO, 'userexpiry: %s' % posixDaysToDate(oldattr['shadowExpire'][0]))
		if oldattr['shadowExpire'][0] != '1':
			return posixDaysToDate(oldattr['shadowExpire'][0])


def unmapKrb5ValidEndToUserexpiry(oldattr):
	if 'krb5ValidEnd' in oldattr:
		krb5validend = oldattr['krb5ValidEnd'][0]
		ud.debug(ud.ADMIN, ud.INFO, 'krb5validend is: %s' % krb5validend)
		return "%s-%s-%s" % (krb5validend[0:4], krb5validend[4:6], krb5validend[6:8])


def unmapSambaKickoffTimeToUserexpiry(oldattr):
	if 'sambaKickoffTime' in oldattr:
		ud.debug(ud.ADMIN, ud.INFO, 'sambaKickoffTime is: %s' % oldattr['sambaKickoffTime'][0])
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
		acctFlags = univention.admin.samba.acctFlags(flags[0])
		try:
			return acctFlags['D'] == 1
		except KeyError:
			pass
	return False


def unmapKerberosDisabled(oldattr):
	try:
		kdcflags = int(oldattr.get('krb5KDCFlags', ['0'])[0])
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
	userPassword = oldattr.get('userPassword', [''])[0]
	return userPassword and univention.admin.password.is_locked(userPassword)


def isSambaLocked(oldattr):
	flags = oldattr.get('sambaAcctFlags', None)
	if flags:
		acctFlags = univention.admin.samba.acctFlags(flags[0])
		try:
			return acctFlags['L'] == 1
		except KeyError:
			pass
	return False


def isKerberosLocked(oldattr):
	flags = oldattr.get('krb5KDCFlags', ['0'])[0]
	try:
		state = 1 << 17
		return int(flags) & state == state
	except ValueError:
		return False


def isLDAPLocked(oldattr):
	return bool(oldattr.get('pwdAccountLockedTime', [''])[0])


def unmapSambaRid(oldattr):
	sid = oldattr.get('sambaSID', [''])[0]
	pos = sid.rfind('-')
	return sid[pos + 1:]


def mapKeyAndValue(old):
	return ['='.join(entry) for entry in old]


def unmapKeyAndValue(old):
	return [entry.split('=', 1) for entry in old]


def mapWindowsFiletime(old):
	if old:
		if old == "0":
			return [old]
		unixtime = time.strptime(old, '%Y%m%d%H%M%SZ')
		d = long(116444736000000000)  # difference between 1601 and 1970
		windows_filetime = long(calendar.timegm(unixtime)) * 10000000 + d
		return [str(int(windows_filetime))]
	return []


def unmapWindowsFiletime(old):
	if old and old[0]:
		if old[0] == "0":
			return old[0]
		d = long(116444736000000000)  # difference between 1601 and 1970
		unixtime = (int(old[0]) - d) / 10000000
		return time.strftime('%Y%m%d%H%M%SZ', time.gmtime(unixtime))
	return ''


mapping = univention.admin.mapping.mapping()
mapping.register('username', 'uid', None, univention.admin.mapping.ListToString)
mapping.register('uidNumber', 'uidNumber', None, univention.admin.mapping.ListToString)
mapping.register('gidNumber', 'gidNumber', None, univention.admin.mapping.ListToString)
mapping.register('title', 'title', None, univention.admin.mapping.ListToString)
mapping.register('initials', 'initials', None, univention.admin.mapping.ListToString)
mapping.register('description', 'description', None, univention.admin.mapping.ListToString)
mapping.register('organisation', 'o', None, univention.admin.mapping.ListToString)

mapping.register('mailPrimaryAddress', 'mailPrimaryAddress', None, univention.admin.mapping.ListToLowerString)
mapping.register('mailAlternativeAddress', 'mailAlternativeAddress')
mapping.register('mailHomeServer', 'univentionMailHomeServer', None, univention.admin.mapping.ListToString)
mapping.register('mailForwardAddress', 'mailForwardAddress')
mapping.register('mailForwardCopyToSelf', 'mailForwardCopyToSelf', None, univention.admin.mapping.ListToString)

mapping.register('preferredLanguage', 'preferredLanguage', None, univention.admin.mapping.ListToString)
mapping.register('street', 'street', None, univention.admin.mapping.ListToString)
mapping.register('e-mail', 'mail')
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
mapping.register('shell', 'loginShell', None, univention.admin.mapping.ListToString)
mapping.register('sambahome', 'sambaHomePath', None, univention.admin.mapping.ListToString)
mapping.register('sambaUserWorkstations', 'sambaUserWorkstations', sambaWorkstationsMap, sambaWorkstationsUnmap)
mapping.register('sambaLogonHours', 'sambaLogonHours', logonHoursMap, logonHoursUnmap)
mapping.register('sambaPrivileges', 'univentionSambaPrivilegeList')
mapping.register('scriptpath', 'sambaLogonScript', None, univention.admin.mapping.ListToString)
mapping.register('profilepath', 'sambaProfilePath', None, univention.admin.mapping.ListToString)
mapping.register('homedrive', 'sambaHomeDrive', None, univention.admin.mapping.ListToString)
mapping.register('gecos', 'gecos', None, univention.admin.mapping.ListToString)
mapping.register('displayName', 'displayName', None, univention.admin.mapping.ListToString)
mapping.register('birthday', 'univentionBirthday', None, univention.admin.mapping.ListToString)
mapping.register('lastname', 'sn', None, univention.admin.mapping.ListToString)
mapping.register('firstname', 'givenName', None, univention.admin.mapping.ListToString)
mapping.register('userCertificate', 'userCertificate;binary', univention.admin.mapping.mapBase64, univention.admin.mapping.unmapBase64)
mapping.register('jpegPhoto', 'jpegPhoto', univention.admin.mapping.mapBase64, univention.admin.mapping.unmapBase64)
mapping.register('umcProperty', 'univentionUMCProperty', mapKeyAndValue, unmapKeyAndValue)
mapping.register('lockedTime', 'sambaBadPasswordTime', mapWindowsFiletime, unmapWindowsFiletime)

mapping.registerUnmapping('sambaRID', unmapSambaRid)
mapping.registerUnmapping('passwordexpiry', unmapPasswordExpiry)
mapping.registerUnmapping('userexpiry', unmapUserExpiry)
mapping.registerUnmapping('disabled', unmapDisabled)
mapping.registerUnmapping('locked', unmapLocked)
mapping.register('password', 'userPassword', univention.admin.mapping.dontMap(), univention.admin.mapping.ListToString)


class object(univention.admin.handlers.simpleLdap):
	module = module

	use_performant_ldap_search_filter = True

	@property
	def __forward_copy_to_self(self):
		return self.get('mailForwardCopyToSelf') == '1'

	def __remove_old_mpa(self, forward_list):
		if forward_list and self.oldattr.get('mailPrimaryAddress') and self.oldattr['mailPrimaryAddress'] != self['mailPrimaryAddress']:
			try:
				forward_list.remove(self.oldattr['mailPrimaryAddress'])
			except ValueError:
				pass

	def __set_mpa_for_forward_copy_to_self(self, forward_list):
		if self.__forward_copy_to_self and self['mailForwardAddress']:
			forward_list.append(self['mailPrimaryAddress'])
		else:
			try:
				forward_list.remove(self['mailPrimaryAddress'])
			except ValueError:
				pass

	def __init__(self, co, lo, position, dn='', superordinate=None, attributes=None):
		self.groupsLoaded = True
		self.password_length = 8

		univention.admin.handlers.simpleLdap.__init__(self, co, lo, position, dn, superordinate, attributes=attributes)

	def _simulate_legacy_options(self):
		'''simulate old options behavior to provide backward compatibility for udm extensions'''
		options = dict(
			posix='posixAccount',
			samba='sambaSamAccount',
			kerberos='krb5Principal',
			mail='univentionMail',
			person='person',
		)
		for opt, oc in options.iteritems():
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
				self['groups'] = self.lo.searchDn(filter=filter_format('(&(cn=*)(|(objectClass=univentionGroup)(objectClass=sambaGroupMapping))(uniqueMember=%s))', [self.dn]))
			else:
				ud.debug(ud.ADMIN, ud.INFO, 'user: open with loadGroups=false for user %s' % self['username'])
			self.groupsLoaded = loadGroups
			primaryGroupNumber = self.oldattr.get('gidNumber', [''])[0]
			if primaryGroupNumber:
				primaryGroupResult = self.lo.searchDn(filter=filter_format('(&(cn=*)(|(objectClass=posixGroup)(objectClass=sambaGroupMapping))(gidNumber=%s))', [primaryGroupNumber]))
				if primaryGroupResult:
					self['primaryGroup'] = primaryGroupResult[0]
				else:
					try:
						primaryGroup = self.lo.search(filter='(objectClass=univentionDefault)', base='cn=univention,' + self.position.getDomain(), attr=['univentionDefaultGroup'])
						try:
							primaryGroup = primaryGroup[0][1]["univentionDefaultGroup"][0]
						except:
							primaryGroup = None
					except:
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
			searchResult = self.lo.search(filter='(objectClass=univentionDefault)', base='cn=univention,' + self.position.getDomain(), attr=['univentionDefaultGroup'])
			if not searchResult or not searchResult[0][1]:
				self.info['primaryGroup'] = None
				self.save()
				raise univention.admin.uexceptions.primaryGroup(self.dn)

			for tmp, number in searchResult:
				primaryGroupResult = self.lo.searchDn(filter=filter_format('(&(objectClass=posixGroup)(cn=%s))', (univention.admin.uldap.explodeDn(number['univentionDefaultGroup'][0], 1)[0],)), base=self.position.getDomain(), scope='domain')
				if primaryGroupResult:
					self['primaryGroup'] = primaryGroupResult[0]
					# self.save() must not be called after this point in self.open()
					# otherwise self.__primary_group doesn't add a new user to the
					# univentionDefaultGroup because "not self.hasChanged('primaryGroup')"

	def _unmap_pwd_change_next_login(self):
		if self.oldattr.get('shadowLastChange', [''])[0] == '0':
			self['pwdChangeNextLogin'] = '1'
		elif self['passwordexpiry']:
			today = time.strftime('%Y-%m-%d').split('-')
			expiry = self['passwordexpiry'].split('-')
			# expiry.reverse()
			# today.reverse()
			if int(''.join(today)) >= int(''.join(expiry)):
				self['pwdChangeNextLogin'] = '1'

	def _unmap_mail_forward(self):
		# mailForwardCopyToSelf is a "virtual" property. The boolean value is set to True, if
		# the LDAP attribute mailForwardAddress contains the mailPrimaryAddress. The mailPrimaryAddress
		# is removed from oldattr for correct display in CLI/UMC and for proper detection of changes.
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
			flags, unc = re.split(' *', self.oldattr['automountInformation'][0], 1)
			host, path = unc.split(':', 1)
		except ValueError:
			return

		sharepath = path
		while len(sharepath) > 1:
			filter_ = univention.admin.filter.conjunction('&', [
				univention.admin.filter.expression('univentionShareHost', host, escape=True),
				univention.admin.filter.conjunction('|', [
					univention.admin.filter.expression('univentionSharePath', sharepath.rstrip('/'), escape=True),
					univention.admin.filter.expression('univentionSharePath', '%s/' % (sharepath.rstrip('/')), escape=True),
				])
			])
			res = univention.admin.modules.lookup(univention.admin.modules.get('shares/share'), None, self.lo, filter=filter_, scope='domain')
			if len(res) == 1:
				self['homeShare'] = res[0].dn
				relpath = path.replace(sharepath, '')
				if len(relpath) > 0 and relpath[0] == '/':
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
#			acctFlags = univention.admin.samba.acctFlags(self.oldattr.get("sambaAcctFlags", [''])[0]).decode()
#			krb5Flags = self.oldattr.get('krb5KDCFlags', [])
#			shadowExpire = self.oldattr.get('shadowExpire', [])
#
#			if not acctFlags and not krb5Flags and not shadowExpire:
#				return False
#			if self['disabled'] == 'all':
#				return 'D' not in acctFlags or '126' in krb5Flags or '1' not in shadowExpire
#			elif self['disabled'] == 'windows':
#				return 'D' not in acctFlags or '254' in krb5Flags or '1' in shadowExpire
#			elif self['disabled'] == 'kerberos':
#				return 'D' in acctFlags or '126' in krb5Flags or '1' in shadowExpire
#			elif self['disabled'] == 'posix':
#				return 'D' in acctFlags or '254' in krb5Flags or '1' not in shadowExpire
#			elif self['disabled'] == 'windows_kerberos':
#				return 'D' not in acctFlags or '126' in krb5Flags or '1' in shadowExpire
#			elif self['disabled'] == 'windows_posix':
#				return 'D' not in acctFlags or '254' in krb5Flags or '1' not in shadowExpire
#			elif self['disabled'] == 'posix_kerberos':
#				return 'D' in acctFlags or '126' in krb5Flags or '1' not in shadowExpire
#			else:  # enabled
#				return 'D' in acctFlags or '254' in krb5Flags or '1' in shadowExpire
#		elif key == 'locked':
#			password = self['password']
#			acctFlags = univention.admin.samba.acctFlags(self.oldattr.get("sambaAcctFlags", [''])[0]).decode()
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

		ud.debug(ud.ADMIN, ud.INFO, 'users/user: check groups in info[groups]')
		for group in self.info.get('groups', []):
			if group and not case_insensitive_in_list(group, old_groups):
				grpobj = group_mod.object(None, self.lo, self.position, group)
				grpobj.fast_member_add([self.dn], [new_uid])

		if univention.admin.configRegistry.is_true("directory/manager/user/primarygroup/update", True):
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
				new_uids.append(memberDN[0][0][1])
			else:
				UIDs = self.lo.getAttr(memberDNstr, 'uid')
				if UIDs:
					new_uids.append(UIDs[0])
					if len(UIDs) > 1:
						ud.debug(ud.ADMIN, ud.WARN, 'users/user: A groupmember has multiple UIDs (%s %r)' % (memberDNstr, UIDs))
		self.lo.modify(group, [('memberUid', uids, new_uids)])

	def __primary_group(self):
		if not self.hasChanged('primaryGroup'):
			return

		if univention.admin.configRegistry.is_true("directory/manager/user/primarygroup/update", True):
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
			raise univention.admin.uexceptions.uidNumberAlreadyUsedAsGidNumber('%r' % self["uidNumber"])

	def _ldap_pre_create(self):
		super(object, self)._ldap_pre_create()
		ud.debug(ud.ADMIN, ud.INFO, 'users/user: dn was set to %s' % self.dn)

		if self['mailPrimaryAddress']:
			self['mailPrimaryAddress'] = self['mailPrimaryAddress'].lower()

		# request a new uidNumber or get lock for manually set uidNumber
		if self['uidNumber']:
			univention.admin.allocators.acquireUnique(self.lo, self.position, 'uidNumber', self['uidNumber'], 'uidNumber', scope='base')
			# "False" ==> do not update univentionLastUsedValue in LDAP if a specific value has been specified
			self.alloc.append(('uidNumber', self['uidNumber'], False))
		else:
			self['uidNumber'] = univention.admin.allocators.request(self.lo, self.position, 'uidNumber')
			self.alloc.append(('uidNumber', self['uidNumber']))

		self._check_uid_gid_uniqueness()

	def _ldap_pre_ready(self):
		super(object, self)._ldap_pre_ready()

		if self.exists() and not self.oldinfo.get('password') and not self['password']:
			# password property is required but LDAP ACL's disallow reading them
			self.info['password'] = '*'
			self.oldinfo['password'] = '*'
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
					self.alloc.append(('uid', univention.admin.allocators.request(self.lo, self.position, 'uid', value=self['username'])))
			except univention.admin.uexceptions.noLock:
				raise univention.admin.uexceptions.uidAlreadyUsed(self['username'])

		# get lock for mailPrimaryAddress
		if not self.exists() or self.hasChanged('mailPrimaryAddress'):
			# ignore case in change of mailPrimaryAddress, we only store the lowercase address anyway
			if self['mailPrimaryAddress'] and self['mailPrimaryAddress'].lower() != self.oldinfo.get('mailPrimaryAddress', '').lower():
				try:
					self.alloc.append(('mailPrimaryAddress', univention.admin.allocators.request(self.lo, self.position, 'mailPrimaryAddress', value=self['mailPrimaryAddress'])))
				except univention.admin.uexceptions.noLock:
					raise univention.admin.uexceptions.mailAddressUsed(self['mailPrimaryAddress'])

		if self['unlock'] == '1':
			self['locked'] = '0'
		if self['disabled'] == '1':
			self['locked'] = '0'  # Samba/AD behavior

		# legacy options to make old hooks happy (46539)
		self._simulate_legacy_options()

	def _ldap_addlist(self):
		al = super(object, self)._ldap_addlist()

		# Kerberos
		al.append(('krb5MaxLife', '86400'))
		al.append(('krb5MaxRenew', '604800'))

		return al

	def _ldap_post_create(self):
		self._confirm_locks()
		self.__update_groups()
		self.__primary_group()

	def _ldap_post_modify(self):
		# POSIX
		self.__update_groups()
		self.__primary_group()

		if self.hasChanged('mailPrimaryAddress'):
			if self['mailPrimaryAddress']:
				univention.admin.allocators.confirm(self.lo, self.position, 'mailPrimaryAddress', self['mailPrimaryAddress'])
			else:  # FIXME: why is this in the else block? it needs to be done always!
				univention.admin.allocators.release(self.lo, self.position, 'mailPrimaryAddress', self.oldinfo['mailPrimaryAddress'])

		# Samba
		if self.hasChanged('sambaRID'):
			old_sid = self.oldattr.get('sambaSID', [''])[0]
			if old_sid:
				univention.admin.allocators.release(self.lo, self.position, 'sid', old_sid)

	def _ldap_pre_modify(self):
		if self.hasChanged('mailPrimaryAddress'):
			if self['mailPrimaryAddress']:
				self['mailPrimaryAddress'] = self['mailPrimaryAddress'].lower()

		if self.hasChanged('username'):
			username = self['username']
			try:
				newdn = 'uid=%s,%s' % (ldap.dn.escape_dn_chars(username), self.lo.parentDn(self.dn))
				self._move(newdn)
			finally:
				univention.admin.allocators.release(self.lo, self.position, 'uid', username)

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
		ml = self._modlist_univention_person(ml)
		ml = self._modlist_home_share(ml)
		ml = self._modlist_samba_sid(ml)
		ml = self._modlist_primary_group(ml)

		return ml

	def _modlist_samba_privileges(self, ml):
		if self.hasChanged('sambaPrivileges'):
			# add univentionSambaPrivileges objectclass
			if self['sambaPrivileges'] and 'univentionSambaPrivileges' not in self.oldattr.get('objectClass', []):
				ml.append(('objectClass', '', 'univentionSambaPrivileges'))
		return ml

	def _modlist_cn(self, ml):
		cnAtts = univention.admin.configRegistry.get('directory/manager/usercn/attributes', "<firstname> <lastname>")
		prop = univention.admin.property()
		old_cn = self.oldattr.get('cn', [''])[0]
		cn = prop._replace(cnAtts, self)
		cn = cn.strip() or cn
		if cn != old_cn:
			ml.append(('cn', old_cn, cn))
		return ml

	def _modlist_gecos(self, ml):
		if self.hasChanged(['firstname', 'lastname']):
			prop = self.descriptions['gecos']
			old_gecos = self.oldattr.get('gecos', [''])[0]
			gecos = prop._replace(prop.base_default, self)
			if old_gecos:
				current_gecos = prop._replace(prop.base_default, self.oldinfo)
				if current_gecos == old_gecos:
					ml.append(('gecos', old_gecos, gecos))
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
				ml.append(('displayName', self.oldattr.get('displayName', [''])[0], new_displayName))
		return ml

	def _modlist_krb_principal(self, ml):
		if not self.exists() or self.hasChanged('username'):
			ml.append(('krb5PrincipalName', self.oldattr.get('krb5PrincipalName', []), [self.krb5_principal()]))
		return ml

	# If you change anything here, please also check users/ldap.py
	def _check_password_history(self, ml, pwhistoryPolicy):
		if self.exists() and not self.hasChanged('password'):
			return ml
		if self['overridePWHistory'] == '1':
			return ml

		pwhistory = self.oldattr.get('pwhistory', [''])[0]

		if univention.admin.password.password_already_used(self['password'], pwhistory):
			raise univention.admin.uexceptions.pwalreadyused()

		if pwhistoryPolicy.pwhistoryLength is not None:
			newPWHistory = univention.admin.password.get_password_history(univention.admin.password.crypt(self['password']), pwhistory, pwhistoryPolicy.pwhistoryLength)
			ml.append(('pwhistory', self.oldattr.get('pwhistory', [''])[0], newPWHistory))

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
				pwdCheck.check(self['password'])
			except ValueError as e:
				raise univention.admin.uexceptions.pwQuality(str(e).replace('W?rterbucheintrag', 'Wörterbucheintrag').replace('enth?lt', 'enthält'))

	def _modlist_samba_password(self, ml, pwhistoryPolicy):
		if self.exists() and not self.hasChanged('password'):
			return ml

		password_nt, password_lm = univention.admin.password.ntlm(self['password'])
		ml.append(('sambaNTPassword', self.oldattr.get('sambaNTPassword', [''])[0], password_nt))
		ml.append(('sambaLMPassword', self.oldattr.get('sambaLMPassword', [''])[0], password_lm))

		if pwhistoryPolicy.pwhistoryLength is not None:
			smbpwhistory = self.oldattr.get('sambaPasswordHistory', [''])[0]
			newsmbPWHistory = self.__getsmbPWHistory(password_nt, smbpwhistory, pwhistoryPolicy.pwhistoryLength)
			ml.append(('sambaPasswordHistory', self.oldattr.get('sambaPasswordHistory', [''])[0], newsmbPWHistory))
		return ml

	def _modlist_kerberos_password(self, ml):
		if self.exists() and not self.hasChanged('password'):
			return ml

		krb_keys = univention.admin.password.krb5_asn1(self.krb5_principal(), self['password'])
		krb_key_version = str(int(self.oldattr.get('krb5KeyVersionNumber', ['0'])[0]) + 1)
		ml.append(('krb5Key', self.oldattr.get('krb5Key', []), krb_keys))
		ml.append(('krb5KeyVersionNumber', self.oldattr.get('krb5KeyVersionNumber', []), krb_key_version))
		return ml

	def _modlist_password_expiry(self, ml, pwhistoryPolicy):
		pwd_change_next_login = self.hasChanged('pwdChangeNextLogin') and self['pwdChangeNextLogin'] == '1'
		unset_pwd_change_next_login = self.hasChanged('pwdChangeNextLogin') and self['pwdChangeNextLogin'] == '0'

		now = (long(time.time()) / 3600 / 24)
		shadowLastChange = str(int(now))
		shadowMax = str(pwhistoryPolicy.expiryInterval or '')
		if pwd_change_next_login:
			# force user to change password on next login
			shadowMax = shadowMax or '1'
			shadowLastChange = str(int(now) - int(shadowMax) - 1)
		elif unset_pwd_change_next_login:
			shadowMax = ''

		if not pwhistoryPolicy.expiryInterval and not self.hasChanged('pwdChangeNextLogin'):
			# An empty field means that password aging features are disabled.
			shadowLastChange = ''

		old_shadowMax = self.oldattr.get('shadowMax', [''])[0]
		if old_shadowMax != shadowMax:
			ml.append(('shadowMax', old_shadowMax, shadowMax))

		if shadowLastChange:  # FIXME: this check causes, that the value is not unset. Is this correct?
			ml.append(('shadowLastChange', self.oldattr.get('shadowLastChange', [''])[0], shadowLastChange))

		# if pwdChangeNextLogin has been set, set sambaPwdLastSet to 0 (see UCS Bug #17890)
		# OLD behavior was: set sambaPwdLastSet to 1 (see UCS Bug #8292 and Samba Bug #4313)
		sambaPwdLastSetValue = '0' if pwd_change_next_login else str(long(time.time()))
		ud.debug(ud.ADMIN, ud.INFO, 'sambaPwdLastSetValue: %s' % sambaPwdLastSetValue)
		ml.append(('sambaPwdLastSet', self.oldattr.get('sambaPwdLastSet', [''])[0], sambaPwdLastSetValue))

		krb5PasswordEnd = ''
		if pwhistoryPolicy.expiryInterval or pwd_change_next_login:
			expiry = long(time.time())
			if not pwd_change_next_login:
				expiry = expiry + (pwhistoryPolicy.expiryInterval * 3600 * 24)
			krb5PasswordEnd = time.strftime("%Y%m%d000000Z", time.gmtime(expiry))

		ud.debug(ud.ADMIN, ud.INFO, 'krb5PasswordEnd: %s' % krb5PasswordEnd)
		old_krb5PasswordEnd = self.oldattr.get('krb5PasswordEnd', [''])[0]
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
				old_kdcflags = int(self.oldattr.get('krb5KDCFlags', ['0'])[0])
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

			ml.append(('krb5KDCFlags', str(old_kdcflags), str(krb_kdcflags)))
		return ml

	# If you change anything here, please also check users/ldap.py
	def _modlist_posix_password(self, ml):
		if not self.exists() or self.hasChanged(['disabled', 'password']):
			old_password = self.oldattr.get('userPassword', [''])[0]
			password = self['password']

			if self.hasChanged('password') and univention.admin.password.RE_PASSWORD_SCHEME.match(password):
				# hacking attempt. user tries to change the password to e.g. {KINIT} or {crypt}$6$...
				raise univention.admin.uexceptions.valueError(_('Invalid password.'), property='password')

			if univention.admin.password.password_is_auth_saslpassthrough(old_password):
				# do not change {SASL} password, but lock it if necessary
				password = old_password

			password_crypt = univention.admin.password.lock_password(password)
			if self['disabled'] != '1':
				password_crypt = univention.admin.password.unlock_password(password_crypt)
			ml.append(('userPassword', old_password, password_crypt))
		return ml

	def _modlist_pwd_account_locked_time(self, ml):
		# remove pwdAccountLockedTime during unlocking
		if self.hasChanged('locked') and self['locked'] == '0':
			pwdAccountLockedTime = self.oldattr.get('pwdAccountLockedTime', [''])[0]
			if pwdAccountLockedTime:
				ml.append(('pwdAccountLockedTime', pwdAccountLockedTime, ''))
		return ml

	def _modlist_samba_bad_pw_count(self, ml):
		if self.hasChanged('locked') and self['locked'] == '0':
			# reset bad pw count
			ml.append(('sambaBadPasswordCount', self.oldattr.get('sambaBadPasswordCount', [''])[0], "0"))
			ml.append(('sambaBadPasswordTime', self.oldattr.get('sambaBadPasswordTime', [''])[0], '0'))
		return ml

	def _modlist_samba_kickoff_time(self, ml):
		if self.hasChanged('userexpiry'):
			sambaKickoffTime = ''
			if self['userexpiry']:
				sambaKickoffTime = "%d" % long(time.mktime(time.strptime(self['userexpiry'], "%Y-%m-%d")))
				ud.debug(ud.ADMIN, ud.INFO, 'sambaKickoffTime: %s' % sambaKickoffTime)
			old_sambaKickoffTime = self.oldattr.get('sambaKickoffTime', '')
			if old_sambaKickoffTime != sambaKickoffTime:
				ml.append(('sambaKickoffTime', self.oldattr.get('sambaKickoffTime', [''])[0], sambaKickoffTime))
		return ml

	def _modlist_krb5_valid_end(self, ml):
		if self.hasChanged('userexpiry'):
			krb5ValidEnd = ''
			if self['userexpiry']:
				krb5ValidEnd = "%s%s%s000000Z" % (self['userexpiry'][0:4], self['userexpiry'][5:7], self['userexpiry'][8:10])
				ud.debug(ud.ADMIN, ud.INFO, 'krb5ValidEnd: %s' % krb5ValidEnd)
			old_krb5ValidEnd = self.oldattr.get('krb5ValidEnd', '')
			if old_krb5ValidEnd != krb5ValidEnd:
				if not self['userexpiry']:
					ml.append(('krb5ValidEnd', old_krb5ValidEnd, '0'))
				else:
					ml.append(('krb5ValidEnd', self.oldattr.get('krb5ValidEnd', [''])[0], krb5ValidEnd))
		return ml

	def _modlist_shadow_expire(self, ml):
		if self.hasChanged('disabled') or self.hasChanged('userexpiry'):
			if self['disabled'] == '1' and self.hasChanged('disabled') and not self.hasChanged('userexpiry'):
				shadowExpire = '1'
			elif self['userexpiry']:
				shadowExpire = "%d" % long(time.mktime(time.strptime(self['userexpiry'], "%Y-%m-%d")) / 3600 / 24 + 1)
			elif self['disabled'] == '1':
				shadowExpire = '1'
			else:
				shadowExpire = ''

			old_shadowExpire = self.oldattr.get('shadowExpire', '')
			if old_shadowExpire != shadowExpire:
				ml.append(('shadowExpire', old_shadowExpire, shadowExpire))
		return ml

	def _modlist_mail_forward(self, ml):
		if self['mailForwardAddress'] and not self['mailPrimaryAddress']:
			raise univention.admin.uexceptions.missingInformation(_('Primary e-mail address must be set, if messages should be forwarded for it.'))
		if self.__forward_copy_to_self and not self['mailPrimaryAddress']:
			raise univention.admin.uexceptions.missingInformation(_('Primary e-mail address must be set, if a copy of forwarded messages should be stored in its mailbox.'))

		# remove virtual property mailForwardCopyToSelf from modlist
		ml = [(key_, old_, new_) for (key_, old_, new_) in ml if key_ != 'mailForwardCopyToSelf']

		# add mailPrimaryAddress to mailForwardAddress if "mailForwardCopyToSelf" is True
		for num_, (key_, old_, new_) in enumerate(ml[:]):
			if key_ == 'mailForwardAddress':
				# old in ml may be missing the mPA removed in open()
				if old_:
					ml[num_][1][:] = self.oldattr.get('mailForwardAddress')
				if new_:
					self.__remove_old_mpa(new_)
					self.__set_mpa_for_forward_copy_to_self(new_)
				break
		else:
			mod_ = (
				'mailForwardAddress',
				self.oldattr.get('mailForwardAddress', []),
				self['mailForwardAddress'][:]
			)
			if self['mailForwardAddress']:
				self.__remove_old_mpa(mod_[2])
				self.__set_mpa_for_forward_copy_to_self(mod_[2])
			if mod_[1] != mod_[2]:
				ml.append(mod_)
		return ml

	def _modlist_univention_person(self, ml):
		# make sure that univentionPerson is set as objectClass when needed
		if any(self.hasChanged(ikey) and self[ikey] for ikey in ('umcProperty', 'birthday')) and 'univentionPerson' not in self.oldattr.get('objectClass', []):
			ml.append(('objectClass', '', 'univentionPerson'))  # TODO: check if exists already
		return ml

	def _modlist_home_share(self, ml):
		if self.hasChanged('homeShare') or self.hasChanged('homeSharePath'):
			if self['homeShare']:
				share_mod = univention.admin.modules.get('shares/share')
				try:
					share = share_mod.object(None, self.lo, self.position, self['homeShare'])
					share.open()
				except:
					raise univention.admin.uexceptions.noObject(_('DN given as share is not valid.'))

				if share['host'] and share['path']:
					if 'automount' not in self.oldattr.get('objectClass', []):
						ml.append(('objectClass', '', 'automount'))

					am_host = share['host']
					if not self['homeSharePath'] or not isinstance(self['homeSharePath'], six.string_types):
						raise univention.admin.uexceptions.missingInformation(_('%(homeSharePath)s must be given if %(homeShare)s is given.') % {'homeSharePath': _('Home share path'), 'homeShare': _('Home share')})
					else:
						am_path = os.path.abspath(os.path.join(share['path'], self['homeSharePath']))
						if not am_path.startswith(share['path']):
							raise univention.admin.uexceptions.valueError(_('%s: Invalid path') % _('Home share path'), property='homeShare')

					am_old = self.oldattr.get('automountInformation', [''])[0]
					am_new = '-rw %s:%s' % (am_host, am_path)
					ml.append(('automountInformation', am_old, am_new))
				else:
					raise univention.admin.uexceptions.noObject(_('Given DN is no share.'))

			if not self['homeShare'] or not share['host'] or not share['path']:
				if 'automount' not in self.oldattr.get('objectClass', []):
					ml.append(('objectClass', '', 'automount'))
				am_old = self.oldattr.get('automountInformation', [''])[0]
				if am_old:
					ml.append(('automountInformation', am_old, ''))
		return ml

	def _modlist_samba_sid(self, ml):
		if not self.exists() or self.hasChanged('sambaRID'):
			sid = self.__generate_user_sid(self['uidNumber'])
			ml.append(('sambaSID', self.oldattr.get('sambaSID', ['']), [sid]))
		return ml

	def _modlist_primary_group(self, ml):
		if not self.exists() or self.hasChanged('primaryGroup'):
			# Posix
			ml.append(('gidNumber', self.oldattr.get('gidNumber', ['']), [self.get_gid_for_primary_group()]))
			# Samba
			ml.append(('sambaPrimaryGroupSID', self.oldattr.get('sambaPrimaryGroupSID', ['']), [self.get_sid_for_primary_group()]))
		return ml

	def _modlist_sambaAcctFlags(self, ml):
		if self.exists() and not self.hasChanged(['disabled', 'locked']):
			return ml

		old_flags = self.oldattr.get("sambaAcctFlags", [''])[0]
		acctFlags = univention.admin.samba.acctFlags(old_flags)
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

		if str(old_flags) != str(acctFlags.decode()):
			ml.append(('sambaAcctFlags', old_flags, acctFlags.decode()))
		return ml

	def _ldap_post_remove(self):
		self.alloc.append(('sid', self.oldattr['sambaSID'][0]))
		self.alloc.append(('uid', self.oldattr['uid'][0]))
		self.alloc.append(('uidNumber', self.oldattr['uidNumber'][0]))
		if self['mailPrimaryAddress']:
			self.alloc.append(('mailPrimaryAddress', self['mailPrimaryAddress']))
		self._release_locks()

		groupObjects = univention.admin.handlers.groups.group.lookup(self.co, self.lo, filter_s=filter_format('uniqueMember=%s', [self.dn]))
		if groupObjects:
			uid = univention.admin.uldap.explodeDn(self.dn, 1)[0]
			for groupObject in groupObjects:
				groupObject.fast_member_remove([self.dn], [uid], ignore_license=1)

		admin_settings_dn = 'uid=%s,cn=admin-settings,cn=univention,%s' % (ldap.dn.escape_dn_chars(self['username']), self.lo.base)
		# delete admin-settings object of user if it exists
		try:
			self.lo.delete(admin_settings_dn)
		except univention.admin.uexceptions.noObject:
			pass

	def _move(self, newdn, modify_childs=True, ignore_license=False):
		olddn = self.dn
		tmpdn = 'cn=%s-subtree,cn=temporary,cn=univention,%s' % (ldap.dn.escape_dn_chars(self['username']), self.lo.base)
		al = [('objectClass', ['top', 'organizationalRole']), ('cn', ['%s-subtree' % self['username']])]
		subelements = self.lo.search(base=self.dn, scope='one', attr=['objectClass'])  # FIXME: identify may fail, but users will raise decode-exception
		if subelements:
			try:
				self.lo.add(tmpdn, al)
			except:
				# real errors will be caught later
				pass
			try:
				moved = dict(self.move_subelements(olddn, tmpdn, subelements, ignore_license))
				subelements = [(moved[subdn], subattrs) for (subdn, subattrs) in subelements]
			except:
				# subelements couldn't be moved to temporary position
				# subelements were already moved back to self
				# stop moving and reraise
				raise

		try:
			dn = super(object, self)._move(newdn, modify_childs, ignore_license)
		except:
			# self couldn't be moved
			# move back subelements and reraise
			self.move_subelements(tmpdn, olddn, subelements, ignore_license)
			raise

		if subelements:
			try:
				moved = dict(self.move_subelements(tmpdn, newdn, subelements, ignore_license))
				subelements = [(moved[subdn], subattrs) for (subdn, subattrs) in subelements]
			except:
				# subelements couldn't be moved to self
				# subelements were already moved back to temporary position
				# move back self, move back subelements to self and reraise
				super(object, self)._move(olddn, modify_childs, ignore_license)
				self.move_subelements(tmpdn, olddn, subelements, ignore_license)
				raise

		return dn

	def __getsmbPWHistory(self, newpassword, smbpwhistory, smbpwhlen):
		# split the history
		if len(string.strip(smbpwhistory)):
			pwlist = string.split(smbpwhistory, ' ')
		else:
			pwlist = []

		# calculate the password hash & salt
		salt = ''
		urandom = open('/dev/urandom', 'r')
		# get 16 bytes from urandom for salting our hash
		rand = urandom.read(16)
		for i in range(0, len(rand)):
			salt = salt + '%.2X' % ord(rand[i])
		# we have to have that in hex
		hexsalt = salt
		# and binary for calculating the md5
		salt = self.getbytes(salt)
		# we need the ntpwd binary data to
		pwd = self.getbytes(newpassword)
		# calculating hash. sored as a 32byte hex in sambePasswordHistory,
		# syntax like that: [Salt][MD5(Salt+Hash)]
		#	First 16bytes ^		^ last 16bytes.
		pwdhash = hashlib.md5(salt + pwd).hexdigest().upper()
		smbpwhash = hexsalt + pwdhash

		if len(pwlist) < smbpwhlen:
			# just append
			pwlist.append(smbpwhash)
		else:
			# calc entries to cut out
			cut = 1 + len(pwlist) - smbpwhlen
			pwlist[0:cut] = []
			if smbpwhlen > 1:
				# and append to shortened history
				pwlist.append(smbpwhash)
			else:
				# or replace the history completely
				if len(pwlist) > 0:
					pwlist[0] = smbpwhash
					# just to be sure...
					pwlist[1:] = []
				else:
					pwlist.append(smbpwhash)

		# and build the new history
		res = string.join(pwlist, '')
		return res

	def __allocate_rid(self, rid):
		searchResult = self.lo.search(filter='objectClass=sambaDomain', attr=['sambaSID'])
		domainsid = searchResult[0][1]['sambaSID'][0]
		sid = domainsid + '-' + rid
		try:
			userSid = univention.admin.allocators.request(self.lo, self.position, 'sid', sid)
			self.alloc.append(('sid', userSid))
		except univention.admin.uexceptions.noLock:
			raise univention.admin.uexceptions.sidAlreadyUsed(': %s' % rid)
		return userSid

	def __generate_user_sid(self, uidNum):
		# TODO: cleanup function
		userSid = None

		if self['sambaRID']:
			userSid = self.__allocate_rid(self['sambaRID'])
		else:
			if self.s4connector_present:
				# In this case Samba 4 must create the SID, the s4 connector will sync the
				# new sambaSID back from Samba 4.
				userSid = 'S-1-4-%s' % uidNum
			else:
				rid = rids_for_well_known_security_identifiers.get(self['username'].lower())
				if rid:
					userSid = self.__allocate_rid(rid)
				else:
					try:
						userSid = univention.admin.allocators.requestUserSid(self.lo, self.position, uidNum)
					except:
						pass
			if not userSid or userSid == 'None':
				num = uidNum
				while not userSid or userSid == 'None':
					num = str(int(num) + 1)
					try:
						userSid = univention.admin.allocators.requestUserSid(self.lo, self.position, num)
					except univention.admin.uexceptions.noLock:
						num = str(int(num) + 1)
				self.alloc.append(('sid', userSid))

		return userSid

	def getbytes(self, string):
		# return byte values of a string (for smbPWHistory)
		bytes = [int(string[i:i + 2], 16) for i in xrange(0, len(string), 2)]
		return struct.pack("%iB" % len(bytes), *bytes)

	@classmethod
	def unmapped_lookup_filter(cls):
		filter_p = super(object, cls).unmapped_lookup_filter()
		filter_p.expressions.extend([
			univention.admin.filter.conjunction('!', [univention.admin.filter.expression('uidNumber', '0')]),
			univention.admin.filter.conjunction('!', [univention.admin.filter.expression('univentionObjectFlag', 'functional')]),
		])
		return filter_p

	@classmethod
	def _ldap_attributes(cls):
		return ['*', 'pwdAccountLockedTime']

	@classmethod
	def rewrite_filter(cls, filter, mapping):
		if filter.variable == 'primaryGroup':
			filter.variable = 'gidNumber'
		elif filter.variable == 'groups':
			filter.variable = 'memberOf'
		elif filter.variable == 'disabled':
			# substring match for userPassword is not possible
			if filter.value == '1':
				filter.transform_to_conjunction(univention.admin.filter.parse('(&(shadowExpire=1)(krb5KDCFlags:1.2.840.113556.1.4.803:=128)(|(sambaAcctFlags=[UD       ])(sambaAcctFlags=[ULD       ])))'))
			elif filter.value == '0':
				filter.transform_to_conjunction(univention.admin.filter.parse('(&(!(shadowExpire=1))(!(krb5KDCFlags:1.2.840.113556.1.4.803:=128))(!(|(sambaAcctFlags=[UD       ])(sambaAcctFlags=[ULD       ]))))'))
			elif filter.value == 'none':
				filter.transform_to_conjunction(univention.admin.filter.parse('(&(!(shadowExpire=1))(!(krb5KDCFlags:1.2.840.113556.1.4.803:=128))(!(|(sambaAcctFlags=[UD       ])(sambaAcctFlags=[ULD       ]))))'))
			elif filter.value == 'all':
				filter.transform_to_conjunction(univention.admin.filter.parse('(&(shadowExpire=1)(krb5KDCFlags:1.2.840.113556.1.4.803:=128)(|(sambaAcctFlags=[UD       ])(sambaAcctFlags=[ULD       ])))'))
			elif filter.value == 'posix':
				filter.variable = 'shadowExpire'
				filter.value = '1'
			elif filter.value == 'kerberos':
				filter.transform_to_conjunction(univention.admin.filter.parse('(&(krb5KDCFlags:1.2.840.113556.1.4.803:=128))'))
			elif filter.value == 'windows':
				filter.transform_to_conjunction(univention.admin.filter.parse('(|(sambaAcctFlags=[UD       ])(sambaAcctFlags==[ULD       ]))'))
			elif filter.value == 'windows_kerberos':
				filter.transform_to_conjunction(univention.admin.filter.parse('(&(krb5KDCFlags:1.2.840.113556.1.4.803:=128)(|(sambaAcctFlags=[UD       ])(sambaAcctFlags==[ULD       ])))'))
			elif filter.value == 'windows_posix':
				filter.transform_to_conjunction(univention.admin.filter.parse('(&(shadowExpire=1)(|(sambaAcctFlags=[UD       ])(sambaAcctFlags==[ULD       ])))'))
			elif filter.value == 'posix_kerberos':
				filter.transform_to_conjunction(univention.admin.filter.parse('(&(shadowExpire=1)(krb5KDCFlags=254))'))
			elif filter.value == '*':
				filter.variable = 'uid'
		elif filter.variable == 'locked':
			if filter.value == '1':
				filter.transform_to_conjunction(univention.admin.filter.parse('(|(krb5KDCFlags:1.2.840.113556.1.4.803:=131072)(sambaAcctFlags=[UL       ])(sambaAcctFlags=[ULD       ]))'))
			elif filter.value == '0':
				filter.transform_to_conjunction(univention.admin.filter.parse('(&(!(krb5KDCFlags:1.2.840.113556.1.4.803:=131072))(!(sambaAcctFlags=[UL       ]))(!(sambaAcctFlags=[ULD       ])))'))
			elif filter.value in ['posix', 'windows', 'all', 'none']:
				if filter.value == 'all':
					filter.transform_to_conjunction(univention.admin.filter.parse('(|(sambaAcctFlags=[UL       ])(sambaAcctFlags=[ULD       ]))'))
					# filter.transform_to_conjunction(univention.admin.filter.parse('(|(sambaAcctFlags=[UL       ])(sambaAcctFlags=[ULD       ])(userPassword={crypt}!*))'))
				elif filter.value == 'windows':
					filter.transform_to_conjunction(univention.admin.filter.parse('(|(sambaAcctFlags=[UL       ])(sambaAcctFlags=[ULD       ]))'))
				# elif filter.value == 'posix':
				#	filter.variable='userPassword'
				#	filter.value = '{crypt}!*'
				elif filter.value == 'none':
					# filter.transform_to_conjunction(univention.admin.filter.parse('(&(!(sambaAcctFlags=[UL       ]))(!(sambaAcctFlags=[ULD       ]))(!(userPassword={crypt}!*)))'))
					filter.transform_to_conjunction(univention.admin.filter.parse('(&(!(sambaAcctFlags=[UL       ]))(!(sambaAcctFlags=[ULD       ])))'))
			elif filter.value == '*':
				filter.variable = 'uid'
		else:
			super(object, cls).rewrite_filter(filter, mapping)

	@classmethod
	def identify(cls, dn, attr, canonical=False):
		if '0' in attr.get('uidNumber', []) or '$' in attr.get('uid', [''])[0] or 'univentionHost' in attr.get('objectClass', []) or 'functional' in attr.get('univentionObjectFlag', []):
			return False
		required_ocs = {'posixAccount', 'shadowAccount', 'sambaSamAccount', 'person', 'krb5KDCEntry', 'krb5Principal'}
		ocs = set(attr.get('objectClass', []))
		return ocs & required_ocs == required_ocs


lookup = object.lookup
lookup_filter = object.lookup_filter
identify = object.identify
