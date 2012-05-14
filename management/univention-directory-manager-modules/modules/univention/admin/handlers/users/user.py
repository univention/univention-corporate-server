# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin module for the user objects
#
# Copyright 2004-2011 Univention GmbH
#
# http://www.univention.de/
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
# <http://www.gnu.org/licenses/>.

import hashlib
import os
import string
import re
import copy
import time
import types
import struct
import tempfile
from M2Crypto import X509
import ldap
import base64

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
import univention.admin.mungeddial as mungeddial
import univention.admin.handlers.settings.prohibited_username

import univention.debug
import univention.password
from univention.admin import configRegistry

translation=univention.admin.localization.translation('univention.admin.handlers.users')
_=translation.translate

class vacationResendDays(univention.admin.syntax.select):
	name = 'vacationresendDays'
	choices = [('1','1 %s' % _('day'))]
	for i in range(2,60):
		choices.append(("%s" % i,"%s %s" % (i, _('days'))))

module='users/user'
operations=['add','edit','remove','search','move']
template='settings/usertemplate'
usewizard=1
wizardmenustring=_("Users")
wizarddescription=_("Add, edit and delete users")
wizardoperations={"add":[_("Add"), _("Add User")],"find":[_("Search"), _("Search for user(s)")]}
uid_umlauts_mixedcase = 0

childs=0
short_description=_('User')
long_description=''

ldap_search_mailhomeserver = univention.admin.syntax.LDAP_Search(
	filter = '(&(objectClass=univentionHost)(univentionService=SMTP))',
	attribute = [ 'computers/computer: fqdn' ],
	value='computers/computer: fqdn' )


options={
	'posix': univention.admin.option(
			short_description=_('POSIX account'),
			default=1,
			objectClasses = ['posixAccount', 'shadowAccount'],
		),
	'samba': univention.admin.option(
			short_description=_('Samba account'),
			default=1,
			objectClasses = ['sambaSamAccount'],
		),
	'kerberos': univention.admin.option(
			short_description=_('Kerberos principal'),
			default=1,
			objectClasses = ['krb5Principal', 'krb5KDCEntry'],
		),
	'mail': univention.admin.option(
			short_description=_('Mail account'),
			default=1,
			objectClasses = ['univentionMail'],
		),
	'pki': univention.admin.option(
			short_description=_('Public key infrastructure account'),
			default=0,
			editable=1,
			objectClasses = ['pkiUser'],
		),
	'person': univention.admin.option(
			short_description=_('Personal information'),
			default=1,
			objectClasses = ['person', 'organizationalPerson', 'inetOrgPerson'],
		),
	'ldap_pwd' : univention.admin.option(
			short_description=_( 'Simple authentication account' ),
			default=0,
			editable=1,
			objectClasses = [ 'simpleSecurityObject', 'uidObject' ],
		)
}
property_descriptions={
	'username': univention.admin.property(
			short_description=_('User name'),
			long_description='',
			syntax=univention.admin.syntax.uid_umlauts_lower_except_first_letter,
			multivalue=0,
			required=1,
			may_change=1,
			identifies=1
		),
	'uidNumber': univention.admin.property(
			short_description=_('User ID'),
			long_description='',
			syntax=univention.admin.syntax.integer,
			multivalue=0,
			required=0,
			may_change=0,
			identifies=0,
			options=['posix','samba']
		),
	'gidNumber': univention.admin.property(
			short_description=_('Group ID'),
			long_description='',
			syntax=univention.admin.syntax.integer,
			multivalue=0,
			required=0,
			may_change=0,
			identifies=0,
			editable=0,
			options=['posix','samba']
		),
	'firstname': univention.admin.property(
			short_description=_('First name'),
			long_description='',
			syntax=univention.admin.syntax.TwoThirdsString,
			multivalue=0,
			options=['person'],
			required=0,
			may_change=1,
			identifies=0
		),
	'lastname': univention.admin.property(
			short_description=_('Last name'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			required=1,
			may_change=1,
			identifies=0
		),
	'gecos': univention.admin.property(
			short_description=_('GECOS'),
			long_description='',
			syntax=univention.admin.syntax.IA5string,
			options=['posix'],
			multivalue=0,
			required=0,
			may_change=1,
			default = '<firstname> <lastname><:umlauts,strip>',
			identifies=0
		),
	'displayName': univention.admin.property(
			short_description=_('Display name'),
			long_description='',
			syntax=univention.admin.syntax.string,
			options=['posix'],
			multivalue=0,
			required=0,
			may_change=1,
			default = '<firstname> <lastname><:strip>',
			identifies=0
		),
	'title': univention.admin.property(
			short_description=_('Title'),
			long_description='',
			syntax=univention.admin.syntax.OneThirdString,
			multivalue=0,
			options=['person'],
			required=0,
			may_change=1,
			identifies=0
		),
	'sambaPrivileges': univention.admin.property(
			short_description = _( 'Samba privileges' ),
			long_description = _( 'Manage samba privileges' ),
			syntax = univention.admin.syntax.SambaPrivileges,
			multivalue = True,
			options = [ 'samba' ],
			required = False,
			dontsearch = False,
			may_change = True,
			identifies = False,
	),
	'description': univention.admin.property(
			short_description=_('Description'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			required=0,
			may_change=1,
			identifies=0
		),
	'organisation': univention.admin.property(
			short_description=_('Organisation'),
			long_description='',
			syntax=univention.admin.syntax.string64,
			multivalue=0,
			options=['person'],
			required=0,
			may_change=1,
			identifies=0
		),
	'userexpiry': univention.admin.property(
			short_description=_('Account expiry date'),
			long_description=_('Enter date as day.month.year.'),
			syntax=univention.admin.syntax.date,
			multivalue=0,
			options=['posix', 'samba', 'kerberos', 'mail'],
			required=0,
			may_change=1,
			dontsearch=1,
			identifies=0
		),
	'passwordexpiry': univention.admin.property(
			short_description=_('Password expiry date'),
			long_description=_('Enter date as day.month.year.'),
			syntax=univention.admin.syntax.date,
			multivalue=0,
			options=['posix', 'samba', 'kerberos', 'mail'],
			editable=0,
			required=0,
			may_change=1,
			dontsearch=1,
			identifies=0
		),
	'pwdChangeNextLogin': univention.admin.property(
			short_description=_('Change password on next login'),
			long_description=_('Change password on next login'),
			syntax=univention.admin.syntax.boolean,
			multivalue=0,
			options=['posix', 'samba', 'kerberos', 'mail'],
			required=0,
			may_change=1,
			dontsearch=1,
			identifies=0
		),
	'disabled': univention.admin.property(
			short_description=_('Account deactivation'),
			long_description='',
			syntax=univention.admin.syntax.disabled,
			multivalue=0,
			options=['posix', 'samba', 'kerberos'],
			required=0,
			may_change=1,
			identifies=0,
			show_in_lists=1
		),
	'locked': univention.admin.property(
			short_description=_('Locked login methods'),
			long_description='',
			syntax=univention.admin.syntax.locked,
			multivalue=0,
			options=['samba', 'posix', 'mail'],
			required=0,
			may_change=1,
			identifies=0,
			show_in_lists=1
		),
	'password': univention.admin.property(
			short_description=_('Password'),
			long_description='',
			syntax=univention.admin.syntax.userPasswd,
			multivalue=0,
			options=['posix', 'samba', 'kerberos', 'mail', 'ldap_pwd' ],
			required=1,
			may_change=1,
			identifies=0,
			dontsearch=1
		),
	'street': univention.admin.property(
			short_description=_('Street'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=['person'],
			required=0,
			may_change=1,
			identifies=0
		),
	'e-mail': univention.admin.property(
			short_description=_('E-mail address(es)'),
			long_description='',
			syntax=univention.admin.syntax.emailAddress,
			multivalue=1,
			options=['person'],
			required=0,
			may_change=1,
			identifies=0,
			default = [ '<mailPrimaryAddress>' ]
		),
	'postcode': univention.admin.property(
			short_description=_('Postal code'),
			long_description='',
			syntax=univention.admin.syntax.OneThirdString,
			multivalue=0,
			options=['person'],
			required=0,
			may_change=1,
			identifies=0
		),
	'city': univention.admin.property(
			short_description=_('City'),
			long_description='',
			syntax=univention.admin.syntax.TwoThirdsString,
			multivalue=0,
			options=['person'],
			required=0,
			may_change=1,
			identifies=0
		),
	'phone': univention.admin.property(
			short_description=_('Telephone number(s)'),
			long_description='',
			syntax=univention.admin.syntax.phone,
			multivalue=1,
			options=['person'],
			required=0,
			may_change=1,
			identifies=0
		),
	'employeeNumber': univention.admin.property(
			short_description=_('Employee number'),
			long_description='',
			syntax=univention.admin.syntax.TwoThirdsString,
			multivalue=0,
			options=['person'],
			required=0,
			may_change=1,
			identifies=0
		),
	'roomNumber': univention.admin.property(
			short_description=_('Room number'),
			long_description='',
			syntax=univention.admin.syntax.OneThirdString,
			multivalue=0,
			options=['person'],
			required=0,
			may_change=1,
			identifies=0
		),
	'secretary': univention.admin.property(
			short_description=_('Superior'),
			long_description='',
			syntax=univention.admin.syntax.UserDN,
			multivalue=1,
			options=['person'],
			required=0,
			may_change=1,
			identifies=0
		),
	'departmentNumber': univention.admin.property(
			short_description=_('Department number'),
			long_description='',
			syntax=univention.admin.syntax.OneThirdString,
			multivalue=0,
			options=['person'],
			required=0,
			may_change=1,
			identifies=0
		),
	'employeeType': univention.admin.property(
			short_description=_('Employee type'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=['person'],
			required=0,
			may_change=1,
			identifies=0
		),
	'homePostalAddress': univention.admin.property(
			short_description=_('Private postal address'),
			long_description='',
			syntax=univention.admin.syntax.postalAddress,
			multivalue=1,
			options=['person'],
			required=0,
			may_change=1,
			identifies=0
		),
	'homeTelephoneNumber': univention.admin.property(
			short_description=_('Private telephone number'),
			long_description='',
			syntax=univention.admin.syntax.phone,
			multivalue=1,
			options=['person'],
			required=0,
			may_change=1,
			identifies=0
		),
	'mobileTelephoneNumber': univention.admin.property(
			short_description=_('Mobile phone number'),
			long_description='',
			syntax=univention.admin.syntax.phone,
			multivalue=1,
			options=['person'],
			required=0,
			may_change=1,
			identifies=0
		),
	'pagerTelephoneNumber': univention.admin.property(
			short_description=_('Pager telephone number'),
			long_description='',
			syntax=univention.admin.syntax.phone,
			multivalue=1,
			options=['person'],
			required=0,
			may_change=1,
			identifies=0
		),
	'birthday' : univention.admin.property(
			short_description=_('Birthday'),
			long_description=_('Date of birth'),
			syntax=univention.admin.syntax.iso8601Date,
			multivalue=0,
			options=['person'],
			required=0,
			may_change=1,
			identifies=0
	),
	'unixhome': univention.admin.property(
			short_description=_('Unix home directory'),
			long_description='',
			syntax=univention.admin.syntax.absolutePath,
			multivalue=0,
			options=['posix'],
			required=1,
			may_change=1,
			identifies=0,
			default= '/home/<username>'
		),

	'shell': univention.admin.property(
			short_description=_('Login shell'),
			long_description='',
			syntax=univention.admin.syntax.OneThirdString,
			multivalue=0,
			options=['posix'],
			required=0,
			may_change=1,
			identifies=0,
			default = '/bin/bash'
		),
	'sambahome': univention.admin.property(
			short_description=_('Windows home path'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=['samba'],
			required=0,
			may_change=1,
			identifies=0
		),
	'scriptpath': univention.admin.property(
			short_description=_('Windows logon script'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=['samba'],
			required=0,
			may_change=1,
			identifies=0
		),
	'profilepath': univention.admin.property(
			short_description=_('Windows profile directory'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=['samba'],
			required=0,
			may_change=1,
			identifies=0
		),
	'homedrive': univention.admin.property(
			short_description=_('Windows home drive'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=['samba'],
			required=0,
			may_change=1,
			identifies=0
		),
	'sambaRID': univention.admin.property(
			short_description=_('Relative ID'),
			long_description='',
			syntax=univention.admin.syntax.integer,
			multivalue=0,
			required=0,
			may_change=1,
			dontsearch=1,
			identifies=0,
			options=['samba']
		),
	'groups': univention.admin.property(
			short_description=_('Groups'),
			long_description='',
			syntax=univention.admin.syntax.GroupDN,
			multivalue=1,
			options=['posix'],
			required=0,
			dontsearch=1,
			may_change=1,
			identifies=0
		),
	'primaryGroup': univention.admin.property(
			short_description=_('Primary group'),
			long_description='',
			syntax=univention.admin.syntax.GroupDN,
			multivalue=0,
			options=['posix'],
			required=1,
			dontsearch=1,
			may_change=1,
			identifies=0
		),
	'mailHomeServer': univention.admin.property(
			short_description=_('Mail home server'),
			long_description='',
			syntax=ldap_search_mailhomeserver,
			multivalue=0,
			options=['mail'],
			required=0,
			dontsearch=0,
			may_change=1,
			identifies=0,
		),
	'mailPrimaryAddress': univention.admin.property(
			short_description=_('Primary e-mail address'),
			long_description='',
			syntax=univention.admin.syntax.emailAddress,
			multivalue=0,
			options=['mail'],
			required=0,
			dontsearch=0,
			may_change=1,
			identifies=0,
		),
	'mailAlternativeAddress': univention.admin.property(
			short_description=_('Alternative e-mail addresses'),
			long_description='',
			syntax=univention.admin.syntax.emailAddress,
			multivalue=1,
			options=['mail'],
			required=0,
			dontsearch=0,
			may_change=1,
			identifies=0,
		),
	'overridePWHistory': univention.admin.property(
			short_description=_('Override password history'),
			long_description='',
			syntax=univention.admin.syntax.boolean,
			multivalue=0,
			options=['samba', 'posix', 'mail'],
			required=0,
			dontsearch=1,
			may_change=1,
			identifies=0,
		),
	'overridePWLength': univention.admin.property(
			short_description=_('Override password check'),
			long_description='',
			syntax=univention.admin.syntax.boolean,
			multivalue=0,
			options=['samba', 'posix', 'mail'],
			required=0,
			dontsearch=1,
			may_change=1,
			identifies=0,
		),
	'homeShare': univention.admin.property(
			short_description=_('Home share'),
			long_description=_('Share, the user\'s home directory resides on'),
			syntax = univention.admin.syntax.WritableShare,
			multivalue=0,
			options=['samba', 'posix', 'kerberos' ],
			required=0,
			dontsearch=1,
			may_change=1,
			identifies=0,
		),
	'homeSharePath': univention.admin.property(
			short_description=_('Home share path'),
			long_description=_('Path to the home directory on the home share'),
			syntax=univention.admin.syntax.HalfString,
			multivalue=0,
			options=['samba', 'posix', 'kerberos' ],
			required=0,
			dontsearch=1,
			may_change=1,
			identifies=0,
			default = '<username>'
		),
	'sambaUserWorkstations': univention.admin.property(
			short_description=_('Allow the authentication only on these Microsoft Windows hosts'),
			long_description=(''),
			syntax=univention.admin.syntax.string,
			multivalue=1,
			options=['samba'],
			required=0,
			dontsearch=0,
			may_change=1,
			identifies=0,
		),
	'sambaLogonHours': univention.admin.property(
			short_description=_('Samba User Login Times'),
			long_description=(""),
			syntax=univention.admin.syntax.SambaLogonHours,
			multivalue = False,
			options=['samba'],
			required=0,
			dontsearch=0,
			may_change=1,
			identifies=0,
		),
	'jpegPhoto': univention.admin.property(
			short_description=_("jpeg photo"),
			long_description=_( 'Picture for user account in JPEG format' ),
			syntax=univention.admin.syntax.jpegPhoto,
			multivalue=0,
			required=0,
			dontsearch=1,
			may_change=1,
			options=['person'],
			identifies=0
	),
	'userCertificate': univention.admin.property(
			short_description=_("PKI user certificate (DER format)"),
			long_description=_( 'Public key infrastructure - user certificate ' ),
			syntax=univention.admin.syntax.Base64Upload,
			multivalue=0,
			required=0,
			dontsearch=1,
			may_change=1,
			options=['pki'],
			identifies=0
		),
	'certificateIssuerCountry': univention.admin.property(
			short_description=_('Issuer Country'),
			long_description=_( 'Certificate Issuer Country' ),
			syntax=univention.admin.syntax.string,
			multivalue=0,
			required=0,
			dontsearch=1,
			may_change=0,
			options=['pki'],
			identifies=0
		),
	'certificateIssuerState': univention.admin.property(
			short_description=_('Issuer State'),
			long_description=_( 'Certificate Issuer State' ),
			syntax=univention.admin.syntax.string,
			multivalue=0,
			required=0,
			dontsearch=1,
			may_change=0,
			options=['pki'],
			identifies=0
		),
	'certificateIssuerLocation': univention.admin.property(
			short_description=_('Issuer Location'),
			long_description=_( 'Certificate Issuer Location' ),
			syntax=univention.admin.syntax.string,
			multivalue=0,
			required=0,
			dontsearch=1,
			may_change=0,
			options=['pki'],
			identifies=0
		),
	'certificateIssuerOrganisation': univention.admin.property(
			short_description=_('Issuer Organisation'),
			long_description=_( 'Certificate Issuer Organisation' ),
			syntax=univention.admin.syntax.string,
			multivalue=0,
			required=0,
			dontsearch=1,
			may_change=0,
			options=['pki'],
			identifies=0
		),
	'certificateIssuerOrganisationalUnit': univention.admin.property(
			short_description=_('Issuer Organisational Unit'),
			long_description=_( 'Certificate Issuer Organisational Unit' ),
			syntax=univention.admin.syntax.string,
			multivalue=0,
			required=0,
			dontsearch=1,
			may_change=0,
			options=['pki'],
			identifies=0
		),
	'certificateIssuerCommonName': univention.admin.property(
			short_description=_('Issuer Common Name'),
			long_description=_( 'Certificate Issuer Common Name' ),
			syntax=univention.admin.syntax.string,
			multivalue=0,
			required=0,
			dontsearch=1,
			may_change=0,
			options=['pki'],
			identifies=0
		),
	'certificateIssuerMail': univention.admin.property(
			short_description=_('Issuer Mail'),
			long_description=_( 'Certificate Issuer Mail' ),
			syntax=univention.admin.syntax.string,
			multivalue=0,
			required=0,
			dontsearch=1,
			may_change=0,
			options=['pki'],
			identifies=0
		),
	'certificateSubjectCountry': univention.admin.property(
			short_description=_('Subject Country'),
			long_description=_( 'Certificate Subject Country' ),
			syntax=univention.admin.syntax.string,
			multivalue=0,
			required=0,
			dontsearch=1,
			may_change=0,
			options=['pki'],
			identifies=0
		),
	'certificateSubjectState': univention.admin.property(
			short_description=_('Subject State'),
			long_description=_( 'Certificate Subject State' ),
			syntax=univention.admin.syntax.string,
			multivalue=0,
			required=0,
			dontsearch=1,
			may_change=0,
			options=['pki'],
			identifies=0
		),
	'certificateSubjectLocation': univention.admin.property(
			short_description=_('Subject Location'),
			long_description=_( 'Certificate Subject Location' ),
			syntax=univention.admin.syntax.string,
			multivalue=0,
			required=0,
			dontsearch=1,
			may_change=0,
			options=['pki'],
			identifies=0
		),
	'certificateSubjectOrganisation': univention.admin.property(
			short_description=_('Subject Organisation'),
			long_description=_( 'Certificate Subject Organisation' ),
			syntax=univention.admin.syntax.string,
			multivalue=0,
			required=0,
			dontsearch=1,
			may_change=0,
			options=['pki'],
			identifies=0
		),
	'certificateSubjectOrganisationalUnit': univention.admin.property(
			short_description=_('Subject Organisational Unit'),
			long_description=_( 'Certificate Subject Organisational Unit' ),
			syntax=univention.admin.syntax.string,
			multivalue=0,
			required=0,
			dontsearch=1,
			may_change=0,
			options=['pki'],
			identifies=0
		),
	'certificateSubjectCommonName': univention.admin.property(
			short_description=_('Subject Common Name'),
			long_description=_( 'Certificate Subject Common Name' ),
			syntax=univention.admin.syntax.string,
			multivalue=0,
			required=0,
			dontsearch=1,
			may_change=0,
			options=['pki'],
			identifies=0
		),
	'certificateSubjectMail': univention.admin.property(
			short_description=_('Issuer Mail'),
			long_description=_( 'Certificate Issuer Mail' ),
			syntax=univention.admin.syntax.string,
			multivalue=0,
			required=0,
			dontsearch=1,
			may_change=0,
			options=['pki'],
			identifies=0
		),
	'certificateDateNotBefore': univention.admin.property(
			short_description=_('Valid from'),
			long_description=_( 'Certificate valid from' ),
			syntax=univention.admin.syntax.date,
			multivalue=0,
			required=0,
			dontsearch=1,
			may_change=0,
			options=['pki'],
			identifies=0
		),
	'certificateDateNotAfter': univention.admin.property(
			short_description=_('Valid until'),
			long_description=_( 'Certificate valid until' ),
			syntax=univention.admin.syntax.date,
			multivalue=0,
			required=0,
			dontsearch=1,
			may_change=0,
			options=['pki'],
			identifies=0
		),
	'certificateVersion': univention.admin.property(
			short_description=_('Version'),
			long_description=_( 'Certificate Version' ),
			syntax=univention.admin.syntax.string,
			multivalue=0,
			required=0,
			dontsearch=1,
			may_change=0,
			options=['pki'],
			identifies=0
		),
	'certificateSerial': univention.admin.property(
			short_description=_('Serial'),
			long_description=_( 'Certificate Serial' ),
			syntax=univention.admin.syntax.string,
			multivalue=0,
			required=0,
			dontsearch=1,
			may_change=0,
			options=['pki'],
			identifies=0
		),
}

# append CTX properties
for key, value in mungeddial.properties.items():
	property_descriptions[ key ] = value

default_property_descriptions=copy.deepcopy(property_descriptions) # for later reset of descriptions

layout = [
	Tab( _( 'General' ), _( 'Basic settings' ),	layout = [
		Group( _( 'User account' ), layout = [
			[ 'title', 'firstname', 'lastname'],
			[ 'username', 'description' ],
			'password',
 			[ 'overridePWHistory', 'overridePWLength' ] ,
			'mailPrimaryAddress',
			] ),
		Group( _( 'Personal information' ), layout = [
			'displayName',
			'organisation',
			'birthday',
			'jpegPhoto',
			] ),
		Group( _( 'Organisation' ), layout = [
			[ 'employeeNumber', 'employeeType' ],
			'secretary',
			] ),
		] ),
	Tab( _( 'Groups' ), _( 'Groups' ), layout = [
		Group( _( 'Primary group' ), layout = [
			'primaryGroup',
		] ),
		Group( _( 'Additional groups' ), layout = [
			'groups',
			] ),
		] ),
	Tab( _( 'Account' ),  _( 'Account settings' ), layout = [
		Group( _( 'Locking and deactivation' ), layout = [
			[ 'disabled', 'locked'],
			[ 'userexpiry', 'passwordexpiry' ],
			'pwdChangeNextLogin', 
			] ),
		Group( _( 'Windows' ), _( 'Windows account settings' ), layout = [
			[ 'homedrive', 'sambahome' ],
			[ 'scriptpath', 'profilepath' ],
			'sambaRID',
			'sambaPrivileges',
			'sambaLogonHours',
			'sambaUserWorkstations'
			] ),
		Group( _( 'POSIX (Linux/UNIX)' ), _( 'POSIX (Linux/UNIX) account settings' ), layout = [
			[ 'unixhome', 'shell' ],
			[ 'uidNumber', 'gidNumber' ],
			[ 'homeShare', 'homeSharePath' ],
			] ),
		] ),
	Tab( _( 'Contact' ), _( 'Contact information' ), layout = [
		Group( _( 'Business' ), layout = [
			'e-mail',
			'phone',
			[ 'roomNumber', 'departmentNumber' ],
			[ 'street', 'postcode', 'city' ],
			] ),
		Group( _( 'Privat' ), layout = [
			'homeTelephoneNumber',
			'mobileTelephoneNumber',
			'pagerTelephoneNumber',
			'homePostalAddress'
			] ),
		] ),
	Tab(_( 'Mail' ), _( 'Mail preferences' ), advanced = True, layout = [
		Group( _( 'Advanced settings' ), layout = [
			'mailAlternativeAddress',
			'mailHomeServer',
			], ),
		] ),
	Tab( _( 'Certificate' ), _( 'Certificate' ), advanced = True, layout = [
		Group( _( 'General' ), '', [
			'userCertificate',
			'certificateSubjectCommonName',
			'certificateSubjectOrganisationalUnit',
			'certificateSubjectOrganisation',
			'certificateSubjectLocation',
			'certificateSubjectState',
			'certificateSubjectCountry',
			'certificateSubjectMail',
			] ),
		Group( _( 'Issuer' ), '', [
			'certificateIssuerCommonName',
			'certificateIssuerOrganisationalUnit',
			'certificateIssuerOrganisation',
			'certificateIssuerLocation',
			'certificateIssuerState',
			'certificateIssuerCountry',
			'certificateIssuerMail',
			] ),
		Group( _( 'Dates' ), '', [
			'certificateDateNotBefore',
			'certificateDateNotAfter',
			] ),
		Group( _( 'Misc' ), '', [
			'certificateVersion',
			'certificateSerial'
			] )
		] )
	]

# append tab with CTX flags
layout.append( mungeddial.tab )

def case_insensitive_in_list(dn, list):
	for element in list:
		if dn.decode('utf8').lower() == element.decode('utf8').lower():
			return True
	return False

def posixDaysToDate(days):
	return time.strftime("%Y-%m-%d",time.gmtime(long(days)*3600*24))

def sambaWorkstationsMap(workstations):
	univention.debug.debug(univention.debug.ADMIN, univention.debug.ALL, 'samba: sambaWorkstationMap: in=%s; out=%s' % (workstations,string.join(workstations, ',')))
	return string.join(workstations, ',')

def sambaWorkstationsUnmap(workstations):
	univention.debug.debug(univention.debug.ADMIN, univention.debug.ALL, 'samba: sambaWorkstationUnmap: in=%s; out=%s' % (workstations[0],string.split(workstations[0],',')))
	return string.split(workstations[0],',')

def logonHoursMap(logontimes):
	"converts the bitfield 001110010110...100 to the respective string"

	# convert list of bit numbers to bit-string
	# bitstring = '0' * 168
	bitstring = ''.join( map( lambda x: x in logontimes and '1' or '0', range( 168 ) ) )

	# for idx in logontimes:
	# 	bitstring[ idx ] = '1'

	logontimes = bitstring

	# the order of the bits of each byte has to be reversed. The reason for this is that
	# consecutive bytes mean consecutive 8-hrs-intervals, but the leftmost bit stands for
	# the last hour in that interval, the 2nd but leftmost bit for the second-but-last
	# hour and so on. We want to hide this from anybody using this feature.
	# See http://ma.ph-freiburg.de/tng/tng-technical/2003-04/msg00015.html for details.

	newtimes = ""
	for i in range(0,21):
		bitlist=list(logontimes[(i*8):(i*8)+8])
		bitlist.reverse()
		newtimes+="".join(bitlist)
	logontimes = newtimes

	# create a hexnumber from each 8-bit-segment
	ret=""
	for i in range(0,21):
	        val=0
	        exp=7
	        for j in range((i*8), (i*8)+8):
	                if not (logontimes[j]=="0"):
	                        val+=2**exp
	                exp-=1
		# we now have: 0<=val<=255
	        hx=hex(val)[2:4]
	        if len(hx)==1: hx="0"+hx
	        ret+=hx

	return ret

def logonHoursUnmap(logontimes):
	"converts the string to a bit array"

	times=logontimes[0][:42]
	while len(times)<42:
		times=times
        ret=""
        for i in range(0,42,2):
                val=int(times[i:i+2],16)
                ret+=intToBinary(val)

	# reverse order of the bits in each byte. See above for details
	newtime = ""
	for i in range(0, 21):
		bitlist=list(ret[(i*8):(i*8)+8])
		bitlist.reverse()
		newtime+="".join(bitlist)

	# convert bit-string to list
	return filter( lambda i: newtime[ i ] == '1', range( 168 ) )

def intToBinary(val):
        ret=""
        while val>0:
                ret=str(val&1)+ret
                val=val>>1
        # pad with leading 0s until length is n*8
        if ret=="": ret="0"
        while not (len(ret)%8==0):
                ret="0"+ret
        return ret

def GMTOffset():
	# returns the difference in hours between local time and GMT (is -1 for CET and CEST)
	return time.timezone/3600

def shift(string, offset):
	# shifts the string #offset chars to the left
	if offset<0:
		for i in range(0, abs(offset)):
			string=string[-1:]+string[:-1]
	else:
		for i in range(0, offset):
			string=string[1:]+string[:1]
	return string

def load_certificate(user_certificate):
	"""Import a certificate in DER format"""
	certificate = base64.decodestring( user_certificate )

	tempf=tempfile.mktemp()
	fh=open(tempf,'w')
	fh.write( certificate )
	fh.close()

	x509 = X509.load_cert( tempf, format = X509.FORMAT_DER )
	os.unlink( tempf )
	if not x509:
		return {}

	not_after=x509.get_not_after()
	not_before=x509.get_not_before()

	if not not_after or not not_before:
		return {}

	def convert_certdate (certdate):
		datestring=str(certdate)
		dl=string.split(datestring)
		month=[None, 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec' ]
		try:
			dl[0]=month.index(dl[0])
		except:
			return ''
		return "%s-%02d-%02d" % ( dl[ 3 ], int( dl[ 0 ] ), int( dl[ 1 ] ) )

	issuer=str(x509.get_issuer())
	if not issuer:
		return {}

	subject=str(x509.get_subject())
	if not subject:
		return {}

	version=x509.get_version()
	if not version:
		return {}

	serial=x509.get_serial_number()
	if not serial:
		return {}


	value={}

	value['certificateDateNotBefore']=convert_certdate(not_before)
	value['certificateDateNotAfter']=convert_certdate(not_after)
	value['certificateVersion']=str(version)
	value['certificateSerial']=str(serial)

	for i in issuer.split('/'):
		if re.match('^C=', i):
			value['certificateIssuerCountry']=string.split(i, '=')[1]
		elif re.match('^ST=', i):
			value['certificateIssuerState']=string.split(i, '=')[1]
		elif re.match('^L=', i):
			value['certificateIssuerLocation']=string.split(i, '=')[1]
		elif re.match('^O=', i):
			value['certificateIssuerOrganisation']=string.split(i, '=')[1]
		elif re.match('^OU=', i):
			value['certificateIssuerOrganisationalUnit']=string.split(i, '=')[1]
		elif re.match('^CN=', i):
			value['certificateIssuerCommonName']=string.split(i, '=')[1]
		elif re.match('^emailAddress=', i):
			value['certificateIssuerMail']=string.split(i, '=')[1]
	for i in subject.split('/'):
		if re.match('^C=', i):
			value['certificateSubjectCountry']=string.split(i, '=')[1]
		elif re.match('^ST=', i):
			value['certificateSubjectState']=string.split(i, '=')[1]
		elif re.match('^L=', i):
			value['certificateSubjectLocation']=string.split(i, '=')[1]
		elif re.match('^O=', i):
			value['certificateSubjectOrganisation']=string.split(i, '=')[1]
		elif re.match('^OU=', i):
			value['certificateSubjectOrganisationalUnit']=string.split(i, '=')[1]
		elif re.match('^CN=', i):
			value['certificateSubjectCommonName']=string.split(i, '=')[1]
		elif re.match('^emailAddress=', i):
			value['certificateSubjectMail']=string.split(i, '=')[1]

	univention.debug.debug(univention.debug.ADMIN, univention.debug.ERROR, 'value=%s' % value)
	return value

def mapHomePostalAddress(old):
	new=[]
	for i in old:
		new.append(string.join(i, '$' ))
	return new

def unmapHomePostalAddress(old):
	new=[]
	for i in old:
		if '$' in i:
			new.append(i.split('$'))
		else:
			new.append([i, " ", " "])

	return new

mapping=univention.admin.mapping.mapping()
mapping.register('title', 'title', None, univention.admin.mapping.ListToString)
mapping.register('description', 'description', None, univention.admin.mapping.ListToString)
mapping.register('organisation', 'o', None, univention.admin.mapping.ListToString)

mapping.register('mailPrimaryAddress', 'mailPrimaryAddress', None, univention.admin.mapping.ListToLowerString)
mapping.register('mailAlternativeAddress', 'mailAlternativeAddress')
mapping.register('mailHomeServer', 'univentionMailHomeServer', None, univention.admin.mapping.ListToString)

mapping.register('street', 'street', None, univention.admin.mapping.ListToString)
mapping.register('e-mail', 'mail')
mapping.register('postcode', 'postalCode', None, univention.admin.mapping.ListToString)
mapping.register('city', 'l', None, univention.admin.mapping.ListToString)
mapping.register('phone', 'telephoneNumber')
mapping.register('roomNumber', 'roomNumber', None, univention.admin.mapping.ListToString)
mapping.register('employeeNumber', 'employeeNumber', None, univention.admin.mapping.ListToString)
mapping.register('employeeType', 'employeeType', None, univention.admin.mapping.ListToString)
mapping.register('secretary', 'secretary')
mapping.register('departmentNumber', 'departmentNumber', None, univention.admin.mapping.ListToString)
mapping.register('mobileTelephoneNumber', 'mobile')
mapping.register('pagerTelephoneNumber', 'pager')
mapping.register('homeTelephoneNumber', 'homePhone')
mapping.register('homePostalAddress', 'homePostalAddress')
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

def unmapCertificate( value ):
	return base64.encodestring( value[ 0 ] )

def mapCertificate( value ):
	return base64.decodestring( value )

mapping.register('userCertificate', 'userCertificate;binary', mapCertificate, unmapCertificate )
mapping.register('jpegPhoto', 'jpegPhoto', None, univention.admin.mapping.ListToString)

class object( univention.admin.handlers.simpleLdap, mungeddial.Support ):
	module=module

	def __pwd_is_locked(self, password):
		if password.startswith('{crypt}!') or password.startswith('{LANMAN}!'):
			return True
		return False

	def __pwd_unlocked(self, password):
		if self.__pwd_is_locked(password):
			if password.startswith("{crypt}!"):
				return password.replace("{crypt}!","{crypt}")
			elif password.startswith('{LANMAN}!'):
				return password.replace("{LANMAN}!","{LANMAN}")
		return password

	def __pwd_locked(self, password):
		# cleartext password?
		if not password.startswith('{crypt}') and not password.startswith('{LANMAN}'):
			return "{crypt}!%s" % (univention.admin.password.crypt('password'))

		if not self.__pwd_is_locked(password):
			if password.startswith("{crypt}"):
				return password.replace("{crypt}","{crypt}!")
			elif password.startswith("{LANMAN}"):
				return password.replace("{LANMAN}","{LANMAN}!")
		return password

	def __add_disabled(self, new):
		if self['disabled'] == 'none' or not self['disabled']:
			self['disabled']=new
		elif (self['disabled'] == 'windows' and new == 'posix') or (new == 'windows' and self['disabled'] == 'posix'):
			self['disabled']='windows_posix'
		elif (self['disabled'] == 'windows' and new == 'kerberos') or (new == 'windows' and self['disabled'] == 'kerberos'):
			self['disabled']='windows_kerberos'
		elif (self['disabled'] == 'kerberos' and new == 'posix') or (new == 'kerberos' and self['disabled'] == 'posix'):
			self['disabled']='posix_kerberos'
		elif self['disabled'] == 'posix_kerberos' and new == 'windows':
			self['disabled']='all'
		elif self['disabled'] == 'windows_kerberos' and new == 'posix':
			self['disabled']='all'
		elif self['disabled'] == 'windows_posix' and new == 'kerberos':
			self['disabled']='all'

	def __is_kerberos_disabled(self):
		if self['disabled'] in ['all', 'kerberos', 'posix_kerberos', 'windows_kerberos']:
			return True
		return False
	def __is_windows_disabled(self):
		if self['disabled'] in ['all', 'windows', 'windows_posix', 'windows_kerberos']:
			return True
		return False
	def __is_posix_disabled(self):
		if self['disabled'] in ( 'all', 'posix', 'posix_kerberos', 'windows_posix' ):
			return True
		return False

	def __pwd_is_auth_saslpassthrough(self, password):
		if password.startswith('{SASL}') and univention.admin.baseConfig.get('directory/manager/web/modules/users/user/auth/saslpassthrough','no').lower() == 'keep':
			return 'keep'
		return 'no'

	def __init__(self, co, lo, position, dn='', superordinate=None, attributes = []):
		global options
		global mapping
		global property_descriptions
		global default_property_descriptions

		# homePostalAddress backward compatibility
		# change mapping only if new syntax is used (via ucr)
		if property_descriptions.get("homePostalAddress", False):
			if hasattr(property_descriptions['homePostalAddress'], "syntax"):
				if hasattr(property_descriptions['homePostalAddress'].syntax, "name"):
					if property_descriptions['homePostalAddress'].syntax.name == "postalAddress":
						mapping.register('homePostalAddress', 'homePostalAddress', mapHomePostalAddress, unmapHomePostalAddress)

		self.mapping=mapping
		self.descriptions=property_descriptions
		self.kerberos_active=0
		self.pwhistory_active=0
		self.mail_active=0
		self.groupsLoaded=1

		self.password_length=8

		self.alloc=[]

		self.old_username = None

		univention.admin.handlers.simpleLdap.__init__(self, co, lo, position, dn, superordinate, attributes = attributes )
		mungeddial.Support.__init__( self )

		self.options=[]
		if 'objectClass' in self.oldattr:
			ocs = set(self.oldattr['objectClass'])
			for opt in ('posix', 'samba', 'person', 'kerberos', 'mail', 'pki', 'ldap_pwd'):
				if options[opt].matches(ocs):
					self.options.append(opt)
		else:
			univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'users/user.py: reset options to default by _define_options' )
			self._define_options( options )

		if 'posix' in self.options:

			# The shadowLastChange attribute is the amount of days between 1/1/1970 upto the day that password was modified,
			# shadowMax is the number of days a password is valid. So the password expires on 1/1/1970+shadowLastChange+shadowMax.
			# shadowExpire contains the absolute date to expire the account.

			if 'shadowExpire' in self.oldattr and len(self.oldattr['shadowExpire']) > 0 :
				univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'userexpiry: %s' % posixDaysToDate(self.oldattr['shadowExpire'][0]))
				if self.oldattr['shadowExpire'][0] != '1':
					self.info['userexpiry'] = posixDaysToDate(self.oldattr['shadowExpire'][0])
			if 'shadowLastChange' in self.oldattr and 'shadowMax' in self.oldattr and len(self.oldattr['shadowLastChange']) > 0 and len(self.oldattr['shadowMax']) > 0:
				try:
					self.info['passwordexpiry'] = posixDaysToDate(int(self.oldattr['shadowLastChange'][0]) +  int(self.oldattr['shadowMax'][0]))
				except:
					univention.debug.debug(univention.debug.ADMIN, univention.debug.WARN, 'users/user: failed to calculate password expiration correctly, use only shadowMax instead')
					self.info['passwordexpiry'] = posixDaysToDate(int(self.oldattr['shadowMax'][0]))

		if 'kerberos' in self.options:
			if self.oldattr.has_key('krb5ValidEnd'):
				krb5validend=self.oldattr['krb5ValidEnd'][0]
				univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'krb5validend is: %s' %
						       krb5validend)
				self.info['userexpiry']="%s-%s-%s"%(krb5validend[0:4],krb5validend[4:6],krb5validend[6:8])
		elif 'samba' in self.options:
			if self.oldattr.has_key('sambaKickoffTime'):
				univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'sambaKickoffTime is: %s' %
						       self.oldattr['sambaKickoffTime'][0])
				self.info['userexpiry']=time.strftime("%Y-%m-%d",time.gmtime(long(self.oldattr['sambaKickoffTime'][0])+(3600*24)))

		uid=self.oldattr.get('uid',[''])[0]
		if uid:
			try:
				s=self.descriptions['username'].syntax
				try:
					username_match=s.parse(uid)
				except univention.admin.uexceptions.valueError,e: # uid contains already mixed case umlauts, so we switch
					self.set_uid_umlauts()
				self['username']=uid
			# FIXME: we should NEVER catch all exceptions
			except Exception, e:
				# at least write some debuging output..
				univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'Cought exception: %s' % e )
				univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'Continuing without dn..')
				self.dn=None
				return

		try:
			givenName=self.oldattr.get('givenName',[''])[0]
			if givenName:
				self['firstname']=givenName
			sn=self.oldattr.get('sn',[''])[0]
			if sn:
				self['lastname']=sn
		except Exception, e:					# FIXME: we should NEVER catch all exceptions
			# at least write some debuging output..
			univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'Cought exception: %s' % e )
			univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'Continuing without dn..')
			self.dn=None
			return

		self.save()

	def open(self, loadGroups=1):
		univention.admin.handlers.simpleLdap.open(self)

		self.newPrimaryGroupDn=0
		self.oldPrimaryGroupDn=0

		self.modifypassword=1
		self.is_auth_saslpassthrough='no'

		self['locked']='none'
		self['disabled']='none'

		self.save()

		if self.dn:
			self.modifypassword=0
			self['password']='********'
			if 'posix' in self.options or 'mail' in self.options or 'ldap_pwd' in self.options:
				#if 'username' not in self.oldattr and 'username' in self.info and len(self.info['username'][0]) > 0:
				#	self.info['username'][0] = self.info['username'][0].lower()

				userPassword=self.oldattr.get('userPassword',[''])[0]
				if userPassword:
					self.info['password']=userPassword
					self.modifypassword=0
					if self.__pwd_is_locked(userPassword):
						self['locked']='posix'
					self.is_auth_saslpassthrough=self.__pwd_is_auth_saslpassthrough(userPassword)

				if 'posix' in self.options:

					if loadGroups: # this is optional because it can take much time on larger installations, default is true
						self.groupsLoaded=1
						self['groups']=self.lo.searchDn(filter='(&(cn=*)(|(objectClass=univentionGroup)(objectClass=sambaGroupMapping))(uniqueMember=%s))' % univention.admin.filter.escapeForLdapFilter(self.dn))
					else:
						self.groupsLoaded=0
						univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'user: open with loadGroups=false for user %s'%self['username'])
					primaryGroupNumber=self.oldattr.get('gidNumber',[''])[0]
					if primaryGroupNumber:
						primaryGroupResult=self.lo.searchDn('(&(cn=*)(|(objectClass=posixGroup)(objectClass=sambaGroupMapping))(gidNumber='+primaryGroupNumber+'))')
						if primaryGroupResult:
							self['primaryGroup']=primaryGroupResult[0]
						else:
							try:
								primaryGroup = self.lo.search( filter='(objectClass=univentionDefault)', base='cn=univention,'+self.position.getDomain(), attr=['univentionDefaultGroup'])
								try:
									primaryGroup = primaryGroup[0][1]["univentionDefaultGroup"][0]
								except:
									primaryGroup = None
							except:
								primaryGroup = None

							univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'user: could not find primaryGroup, setting primaryGroup to %s' % primaryGroup)

							self['primaryGroup']=primaryGroup
							self.newPrimaryGroupDn=primaryGroup
							self.__primary_group()
							self.save()
					else:
						self['primaryGroup']=None
						self.save()
						raise univention.admin.uexceptions.primaryGroup

					self.info['uidNumber'] = self.oldattr.get('uidNumber', [''])[0]
					self.info['gidNumber'] = self.oldattr.get('gidNumber', [''])[0]

			if self['passwordexpiry']:
				today=time.strftime('%Y-%m-%d').split('-')
				expiry=self['passwordexpiry'].split('-')
				# expiry.reverse()
				# today.reverse()
				if int(string.join(today,''))>=int(string.join(expiry,'')):
					self['pwdChangeNextLogin']='1'

			if 'samba' in self.options:
				sid = self.oldattr.get('sambaSID', [''])[0]
				pos = sid.rfind('-')
				self.info['sambaRID'] = sid[pos+1:]
				self.sambaMungedDialUnmap()
				self.sambaMungedDialParse()

				flags=self.oldattr.get('sambaAcctFlags', None)
				if flags:
					acctFlags=univention.admin.samba.acctFlags(flags[0])
					try:
						if acctFlags['D']  == 1:
							self.__add_disabled('windows')
					except KeyError:
						pass
					try:
						if acctFlags['L']  == 1:
							if self['locked'] == 'posix':
								self['locked']='all'
							else:
								self['locked']='windows'
					except KeyError:
						pass


			if 'kerberos' in self.options:
				kdcflags = self.oldattr.get('krb5KDCFlags', ['0'])[0]
				if kdcflags == '254':
					self.__add_disabled('kerberos')

			if 'posix' in self.options:
				shadowExpire = self.oldattr.get('shadowExpire', ['0'])[0]
				if shadowExpire == '1' or (shadowExpire < int(time.time()/3600/24) and (self._is_kerberos_disabled() or self._is_windows_disabled())):
					self.__add_disabled('posix')

			if self.oldattr.has_key('automountInformation'):
				unc = ''
				try:
					flags, unc = re.split(' *', self.oldattr['automountInformation'][0])
				except ValueError:
					pass
				if unc.find(':') > 1:
					host, path = unc.split(':')
					sharepath=path
					while len(sharepath) > 1:
						res = univention.admin.modules.lookup(univention.admin.modules.get('shares/share'), None, self.lo, filter='(&(host=%s)(path=%s))' % (host, sharepath), scope='domain')
						if len(res) == 1:
							self['homeShare']=res[0].dn
							relpath=path.replace(sharepath, '')
							if len(relpath)>0 and relpath[0] == '/':
								relpath = relpath[1:]
							self['homeSharePath']=relpath
							break
						elif len(res) > 1:
							break
						elif len(res) < 1:
							sharepath=os.path.split(sharepath)[0]


			if 'pki' in self.options:
				self.reload_certificate()

			self.save()
		else:
			if 'posix' in self.options:
				primary_group_from_template = self['primaryGroup']
				if not primary_group_from_template:
					searchResult=self.lo.search( filter='(objectClass=univentionDefault)', base='cn=univention,'+self.position.getDomain(), attr=['univentionDefaultGroup'])
					if not searchResult or not searchResult[0][1]:
						self['primaryGroup']=None
						self.save()
						raise univention.admin.uexceptions.primaryGroup

					for tmp,number in searchResult:
						primaryGroupResult=self.lo.searchDn('(&(objectClass=posixGroup)(cn=%s))' % (univention.admin.uldap.explodeDn(number['univentionDefaultGroup'][0], 1)[0]), base=self.position.getDomain(), scope='domain')
						if primaryGroupResult:
							self['primaryGroup']=primaryGroupResult[0]
							self.newPrimaryGroupDn=primaryGroupResult[0]

		self.old_options= copy.deepcopy( self.options )


	def __certificate_clean(self):
		self.info['certificateSubjectCountry']=''
		self.info['certificateSubjectState']=''
		self.info['certificateSubjectLocation']=''
		self.info['certificateSubjectOrganisation']=''
		self.info['certificateSubjectOrganisationalUnit']=''
		self.info['certificateSubjectCommonName']=''
		self.info['certificateSubjectMail']=''
		self.info['certificateIssuerCountry']=''
		self.info['certificateIssuerState']=''
		self.info['certificateIssuerLocation']=''
		self.info['certificateIssuerOrganisation']=''
		self.info['certificateIssuerOrganisationalUnit']=''
		self.info['certificateIssuerCommonName']=''
		self.info['certificateIssuerMail']=''
		self.info['certificateDateNotBefore']=''
		self.info['certificateDateNotAfter']=''
		self.info['certificateVersion']=''
		self.info['certificateSerial']=''
		self.info['userCertificate']=''

	def reload_certificate(self):

		if self.info.get( 'userCertificate' ):
			values=load_certificate(self.info['userCertificate'])
			if not values:
				self.__certificate_clean()
			else:
				for i in values.keys():
					self.info[i]=values[i]
		else:
			self.__certificate_clean()

	def hasChanged(self, key):
		if key == 'disabled':
			acctFlags = univention.admin.samba.acctFlags(self.oldattr.get("sambaAcctFlags", [''])[0]).decode()
			krb5Flags = self.oldattr.get('krb5KDCFlags', [])
			shadowExpire = self.oldattr.get('shadowExpire', [])

			if not acctFlags and not krb5Flags and not shadowExpire:
				return False
			if self['disabled'] == 'all':
				return not 'D' in acctFlags or \
						'126' in krb5Flags or \
						not '1' in shadowExpire
			elif self['disabled'] == 'windows':
				return not 'D' in acctFlags or \
						'254' in krb5Flags or \
						'1' in shadowExpire
			elif self['disabled'] == 'kerberos':
				return 'D' in acctFlags or \
						'126' in krb5Flags or \
						'1' in shadowExpire
			elif self['disabled'] == 'posix':
				return 'D' in acctFlags or \
				       '254' in krb5Flags or \
						not '1' in shadowExpire
			elif self['disabled'] == 'windows_kerberos':
				return not 'D' in acctFlags or \
				       '126' in krb5Flags or \
						'1' in shadowExpire
			elif self['disabled'] == 'windows_posix':
				return not 'D' in acctFlags or \
						'254' in krb5Flags or \
						not '1' in shadowExpire
			elif self['disabled'] == 'posix_kerberos':
				return 'D' in acctFlags or \
						'126' in krb5Flags or \
						not '1' in shadowExpire
			else: #enabled
				return 'D' in acctFlags or \
				       '254' in krb5Flags or \
						'1' in shadowExpire
		elif key == 'locked':
			password  = self['password']
			acctFlags = univention.admin.samba.acctFlags(self.oldattr.get("sambaAcctFlags", [''])[0]).decode()
			if not password and not acctFlags:
				return False
			if self['locked'] == 'all':
				return not self.__pwd_is_locked(password) or \
				       not 'L' in acctFlags
			elif self['locked'] == 'windows':
				return self.__pwd_is_locked(password) or \
				       not 'L' in acctFlags
			elif self['locked'] == 'posix':
				return not self.__pwd_is_locked(password) or \
				       'L' in acctFlags
			else:
				return self.__pwd_is_locked(password) or \
				       'L' in acctFlags

		return super(object, self).hasChanged(key)

	def __update_groups(self):
		if not self.groupsLoaded:
			return

		if self.exists():
			old_groups = self.oldinfo.get('groups', [])
			old_uid = self.oldinfo.get( 'username', '' )
		else:
			old_groups = []
			old_uid = ""
		new_uid = self.info.get('username','')
		new_groups = self.info.get('groups', [])

		# change memberUid if we have a new username
		if not old_uid == new_uid and self.exists():
			univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'users/user: rewrite memberuid after rename')
			for group in new_groups:
				self.__rewrite_member_uid( group )

		group_mod = univention.admin.modules.get('groups/group')

		univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'users/user: check groups in old_groups')
		for group in old_groups:
			if group and not case_insensitive_in_list(group, self.info.get('groups', [])) and group.lower() != self['primaryGroup'].lower():
				grpobj = group_mod.object(None, self.lo, self.position, group)
				grpobj.fast_member_remove( [ self.dn ], [ old_uid ] )

		univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'users/user: check groups in info[groups]')
		for group in self.info.get('groups', []):
			if group and not case_insensitive_in_list(group, old_groups):
				grpobj = group_mod.object(None, self.lo, self.position, group)
				grpobj.fast_member_add( [ self.dn ], [ new_uid ] )

		univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'users/user: check primaryGroup')
		if not self.exists() and self.info.get('primaryGroup'):
			grpobj = group_mod.object(None, self.lo, self.position, self.info.get('primaryGroup'))
			grpobj.fast_member_add( [ self.dn ], [ new_uid ] )

	def __rewrite_member_uid( self, group, members = [] ):
		uids = self.lo.getAttr( group, 'memberUid' )
		if not members:
			members = self.lo.getAttr( group, 'uniqueMember' )
		new_uids = []
		for memberDNstr in members:
			memberDN = ldap.dn.str2dn(memberDNstr)
			if memberDN[0][0][0] == 'uid': # UID is stored in DN --> use UID directly
				new_uids.append(memberDN[0][0][1])
			else:
				UIDs = self.lo.getAttr(memberDNstr, 'uid')
				if UIDs:
					new_uids.append(UIDs[0])
					if len(UIDs) > 1:
						univention.debug.debug(univention.debug.ADMIN, univention.debug.WARN, 'users/user: A groupmember has multiple UIDs (%s %s)' % (memberDNstr, repr(uid_list)))
		self.lo.modify(group, [ ( 'memberUid', uids, new_uids ) ] )

	def __primary_group(self):
		self.newPrimaryGroupDn=0
		self.oldPrimaryGroupDn=0
		if not self.hasChanged('primaryGroup'):
			return

		searchResult=self.lo.search(base=self['primaryGroup'], attr=['gidNumber'])
		for tmp,number in searchResult:
			primaryGroupNumber = number['gidNumber']
		self.newPrimaryGroupDn=self['primaryGroup']

		if 'samba' in self.options:
			searchResult=self.lo.search(base=self['primaryGroup'], attr=['sambaSID'])
			for tmp,number in searchResult:
				primaryGroupSambaNumber = number['sambaSID']

		if self.oldinfo.has_key('primaryGroup'):
			self.oldPrimaryGroupDn=self.oldinfo['primaryGroup']
			searchResult=self.lo.search(base=self.oldinfo['primaryGroup'], attr=['gidNumber'])
			for tmp,number in searchResult:
				oldPrimaryGroup = number['gidNumber']
			univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'users/user: set gidNumber by oldinfo')
			self.lo.modify(self.dn, [('gidNumber',oldPrimaryGroup[0], primaryGroupNumber[0])])
			if 'samba' in self.options:
				univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'users/user: set sambaPrimaryGroupSID by oldinfo')
				self.lo.modify(self.dn, [('sambaPrimaryGroupSID',oldPrimaryGroup[0], primaryGroupSambaNumber[0])])
		else:
			searchResult=self.lo.search(base=self.dn, scope='base', attr=['gidNumber'])
			for tmp,number in searchResult:
				oldNumber = number['gidNumber']
			univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'users/user: set gidNumber')
			self.lo.modify(self.dn, [('gidNumber',oldNumber, primaryGroupNumber[0])])
			if 'samba' in self.options:
				univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'users/user: set sambaPrimaryGroupSID')
				self.lo.modify(self.dn, [('sambaPrimaryGroupSID',oldNumber, primaryGroupSambaNumber[0])])

		new_uid = self.info.get('username')
		group_mod = univention.admin.modules.get('groups/group')
		grpobj = group_mod.object(None, self.lo, self.position, self.newPrimaryGroupDn)
		grpobj.fast_member_add( [ self.dn ], [ new_uid ] )
		univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'users/user: adding to new primaryGroup %s (uid=%s)' % (self.newPrimaryGroupDn, new_uid))

		self.save()

	def krb5_principal(self):
		domain=univention.admin.uldap.domain(self.lo, self.position)
		realm=domain.getKerberosRealm()
		return self['username']+'@'+realm

	def _ldap_pre_create(self):
		_d=univention.debug.function('admin.handlers.users.user.object._ldap_pre_create')

		self.dn='uid=%s,%s' % ( self['username'], self.position.getDn())
		univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'users/user: dn was set to %s'%self.dn)
		if not self['password']:
			self['password']=self.oldattr.get('password',[''])[0]
			self.modifypassword=0
		else:
			self.modifypassword=1

		if self['mailPrimaryAddress']:
			self['mailPrimaryAddress']=self['mailPrimaryAddress'].lower()

	def _ldap_addlist(self):

		try:
			error=0
			uid=None

			if not ( 'posix' in self.options or 'samba' in self.options or 'person' in self.options or 'ldap_pwd' in self.options):
				#no objectClass which provides uid...
				raise univention.admin.uexceptions.invalidOptions, _('Need one of %s, %s, %s or %s in options to create user.')%(
					'posix',
					'samba',
					'person',
					'ldap_pwd')

			if 'posix' in self.options or 'samba' in self.options:
				if self['primaryGroup']:
					searchResult=self.lo.search(base=self['primaryGroup'], attr=['gidNumber'])
					for tmp,number in searchResult:
						gidNum = number['gidNumber'][0]
					self.newPrimaryGroupDn=self['primaryGroup']
				else:
					gidNum='99999'

			prohibited_objects=univention.admin.handlers.settings.prohibited_username.lookup(self.co, self.lo, '')
			if prohibited_objects and len(prohibited_objects) > 0:
				for i in range(0,len(prohibited_objects)):
					if self['username'] in prohibited_objects[i]['usernames']:
						raise univention.admin.uexceptions.prohibitedUsername, ': %s' % self['username']
						return []
			try:
				uid=univention.admin.allocators.request(self.lo, self.position, 'uid', value=self['username'])
				if 'posix' in self.options:
					if self['unixhome'] == '/home/%s' % self.old_username:
						self['unixhome'] = '/home/%s' % self['username']
			except univention.admin.uexceptions.noLock, e:
				username=self['username']
				del(self.info['username'])
				self.oldinfo={}
				self.dn=None
				self._exists=0
				self.old_username = username
				univention.admin.allocators.release(self.lo, self.position, 'uid', username)
				raise univention.admin.uexceptions.uidAlreadyUsed, ': %s' % username

			self.alloc.append(('uid', uid))

			if self['uidNumber']:
				self.alloc.append(('uidNumber', self['uidNumber']))
				self.uidNum = univention.admin.allocators.acquireUnique(self.lo, self.position, 'uidNumber', self['uidNumber'], 'uidNumber', scope='base')
			else:
				self.uidNum=univention.admin.allocators.request(self.lo, self.position, 'uidNumber')
				self.alloc.append(('uidNumber', self.uidNum))

			if 'samba' in self.options:
				self.userSid = self.__generate_user_sid(self.uidNum)

			# due to the fact that the modlist is appended to the addlist this would be added twice
			# leave commented out for now!
			#acctFlags=univention.admin.samba.acctFlags(flags={'U':1})
			#if self['disabled']:
			#	acctFlags.set('D')

			ocs=['top', 'person', 'univentionPWHistory']
			self.pwhistory_active=1
			al=[('uid', [uid])]
			if 'posix' in self.options:
				ocs.extend(['posixAccount', 'shadowAccount'])
				self.mail_active=1
				al.append(('uidNumber', [self.uidNum]))
				al.append(('gidNumber', [gidNum]))
			if 'mail' in self.options:
				if not 'posix' in self.options:
					ocs.extend(['shadowAccount','univentionMail'])
				else:
					ocs.extend(['univentionMail'])
				self.mail_active=1
				if self[ 'mailPrimaryAddress' ]:
					try:
						self.alloc.append( ( 'mailPrimaryAddress', self[ 'mailPrimaryAddress' ] ) )
						univention.admin.allocators.request( self.lo, self.position, 'mailPrimaryAddress', value = self[ 'mailPrimaryAddress' ] )
					except univention.admin.uexceptions.noLock:
						self.cancel()
						raise univention.admin.uexceptions.mailAddressUsed
			if 'samba' in self.options:
				ocs.extend(['sambaSamAccount'])
				al.append(('sambaSID', [self.userSid]))
				#('sambaAcctFlags', [acctFlags.decode()])
			if 'person' in self.options:
				ocs.extend(['organizationalPerson','inetOrgPerson'])
			if 'ldap_pwd' in self.options:
				ocs.extend(['simpleSecurityObject','uidObject'])
 			if 'kerberos' in self.options:
				domain=univention.admin.uldap.domain(self.lo, self.position)
				realm=domain.getKerberosRealm()
				if realm:
					ocs.extend(['krb5Principal', 'krb5KDCEntry'])
					al.append(('krb5PrincipalName', [uid+'@'+realm]))
					al.append(('krb5MaxLife', '86400'))
					al.append(('krb5MaxRenew', '604800'))
					self.kerberos_active=1
				else:
					# can't do kerberos
					self.options.remove('kerberos')
			if 'pki' in self.options:
				ocs.extend(['pkiUser'])

			al.insert(0, ('objectClass', ocs))
			return al

		except:
			self.cancel()
			raise

	def _ldap_post_create(self):
		univention.admin.allocators.confirm(self.lo, self.position, 'uid', self['username'])
		if 'samba' in self.options:
			univention.admin.allocators.confirm(self.lo, self.position, 'sid', self.userSid)
		if 'mail' in self.options and self[ 'mailPrimaryAddress' ]:
			univention.admin.allocators.confirm( self.lo, self.position, 'mailPrimaryAddress', self[ 'mailPrimaryAddress' ] )
		if 'posix' in self.options:
			univention.admin.allocators.confirm(self.lo, self.position, 'uidNumber', self.uidNum)
			self.__update_groups()
			self.__primary_group()

	def _ldap_post_modify(self):
		if 'posix' in self.options:
			self.__update_groups()
			self.__primary_group()
		if 'mail' in self.options and self.hasChanged( 'mailPrimaryAddress' ):
			if self[ 'mailPrimaryAddress' ]:
				univention.admin.allocators.confirm( self.lo, self.position, 'mailPrimaryAddress', self[ 'mailPrimaryAddress' ] )
			else:
				univention.admin.allocators.release( self.lo, self.position, 'mailPrimaryAddress', self.oldinfo[ 'mailPrimaryAddress' ] )
		if 'samba' in self.options and self.hasChanged('sambaRID'):
			univention.admin.allocators.confirm(self.lo, self.position, 'sid', self.userSid)

	def _ldap_pre_modify(self):
		if self.hasChanged('mailPrimaryAddress'):
			if self['mailPrimaryAddress']:
				self['mailPrimaryAddress']=self['mailPrimaryAddress'].lower()

		if self.hasChanged('username'):
			try:
				uid=univention.admin.allocators.request(self.lo, self.position, 'uid', value=self['username'])
			except univention.admin.uexceptions.noLock, e:
				username=self['username']
				del(self.info['username'])
				self.oldinfo={}
				self.dn=None
				self._exists=0
				self.old_username = username
				univention.admin.allocators.release(self.lo, self.position, 'uid', username)
				raise univention.admin.uexceptions.uidAlreadyUsed, ': %s' % username

			newdn = 'uid=%s%s' % (self['username'],self.dn[self.dn.find(','):])
			self._move(newdn)
			univention.admin.allocators.release(self.lo, self.position, 'uid', self['username'])

		if self.hasChanged('password'):
			if not self['password']:
				self['password']=self.oldattr.get('password',['********'])[0]
				self.modifypassword=0
			elif not self.info['password']:
				self['password']=self.oldattr.get('password',['********'])[0]
				self.modifypassword=0
			else:
				self.modifypassword=1

	def _remove_attr(self, ml, attr):
		for m in ml:
			if m[0] == attr:
				ml.remove(m)
		if self.oldattr.get(attr, []):
			ml.insert(0, (attr, self.oldattr.get(attr, []), ''))
		return ml

	def _ldap_modlist(self):
		ml=univention.admin.handlers.simpleLdap._ldap_modlist(self)


		# samba privileges
		if self.hasChanged( 'sambaPrivileges' ) and 'samba' in self.options:
			o = self.oldattr.get( 'objectClass', [] )
			# add univentionSambaPrivileges objectclass
			if self[ 'sambaPrivileges'] and not "univentionSambaPrivileges" in o:
				ml.insert( 0, ( 'objectClass', '', 'univentionSambaPrivileges' ) )


		shadowLastChangeValue = ''	# if is filled, it will be added to ml in the end
		sambaPwdLastSetValue = ''	# if is filled, it will be added to ml in the end

		if self.options != self.old_options:
			univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'options: %s' % self.options)
			univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'old_options: %s' % self.old_options)
			# pki option add / remove
			if 'pki' in self.options and not 'pki' in self.old_options:
				univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'added pki option')
				ocs=self.oldattr.get('objectClass', [])
				if not 'pkiUser' in ocs:
					ml.insert(0, ('objectClass', '', 'pkiUser'))
			if not 'pki' in self.options and 'pki' in self.old_options:
				univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'remove pki option')
				ocs=self.oldattr.get('objectClass', [])
				if 'pkiUser' in ocs:
					ml.insert(0, ('objectClass', 'pkiUser', ''))
					for attr in ['userCertificate;binary']:
						ml=self._remove_attr(ml,attr)
			# ldap_pwd option add / remove
			if 'ldap_pwd' in self.options and not 'ldap_pwd' in self.old_options:
				univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'added ldap_pwd option')
				ocs=self.oldattr.get('objectClass', [])
				if not 'simpleSecurityObject' in ocs:
					ml.insert(0, ('objectClass', '', 'simpleSecurityObject'))
					ml.insert(0, ('objectClass', '', 'uidObject'))
			if not 'ldap_pwd' in self.options and 'ldap_pwd' in self.old_options:
				univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'remove ldap_pwd option')
				ocs=self.oldattr.get('objectClass', [])
				if 'simpleSecurityObject' in ocs:
					ml.insert(0, ('objectClass', 'simpleSecurityObject', ''))
					ml.insert(0, ('objectClass', 'uidObject', ''))

		# set cn
		cnAtts = univention.admin.baseConfig.get('directory/manager/usercn/attributes', "<firstname> <lastname>")
		prop = univention.admin.property()
		cn = prop._replace(cnAtts, self)
		cn = cn.strip()
		ml.append(('cn', self.oldattr.get('cn', [''])[0], cn))

		if  self.hasChanged(['firstname', 'lastname']):
			ml.append(('sn', self.oldattr.get('cn', [''])[0], self['lastname']))
			if 'person' in self.options:
				ml.append(('givenName', self.oldattr.get('givenName', [''])[0], self['firstname']))

			if 'posix' in self.options:
				prop = self.descriptions[ 'gecos' ]
				gecos = prop._replace( prop.base_default, self )
				if self.oldinfo.get( 'gecos', '' ):
					old_gecos = prop._replace( prop.base_default, self.oldinfo )
					if old_gecos == self.oldinfo.get( 'gecos', '' ):
						ml.append( ( 'gecos', self.oldinfo.get( 'gecos', [ '' ] )[ 0 ], gecos ) )

		# shadowlastchange=self.oldattr.get('shadowLastChange',[str(long(time.time())/3600/24)])[0]

		pwd_change_next_login=0
		if self.hasChanged('pwdChangeNextLogin') and self['pwdChangeNextLogin'] == '1':
			pwd_change_next_login=1
		elif self.hasChanged('pwdChangeNextLogin') and self['pwdChangeNextLogin'] == '0':
			pwd_change_next_login=2

		if self.hasChanged('username'):
 			if 'kerberos' in self.options:
				ml.append(('krb5PrincipalName', self.oldattr.get('krb5PrincipalName', []), [self.krb5_principal()]))

		if self.modifypassword:
			# if the password is going to be changed in ldap check password-history
			ocs=self.oldattr.get('objectClass', [])
			if not 'univentionPWHistory' in ocs and not self.pwhistory_active:
				ml.insert(0, ('objectClass', '', 'univentionPWHistory'))

			pwhistory=self.oldattr.get('pwhistory',[''])[0]
			#read policy
			pwhistoryPolicy = self.loadPolicyObject('policies/pwhistory')
			if self['overridePWHistory'] != '1':
				#TODO: if checkbox "override pwhistory" is not set
				if self.__passwordInHistory(self['password'], pwhistory):
					raise univention.admin.uexceptions.pwalreadyused
					return []
				if pwhistoryPolicy and pwhistoryPolicy.has_key('length') and pwhistoryPolicy['length']:
					pwhlen = int(pwhistoryPolicy['length'])
					newPWHistory = self.__getPWHistory(self['password'], pwhistory, pwhlen)
					ml.append(('pwhistory', self.oldattr.get('pwhistory', [''])[0], newPWHistory))
			if pwhistoryPolicy != None and pwhistoryPolicy['pwLength'] != None and pwhistoryPolicy['pwLength'] != 0 and self['overridePWLength'] != '1':
					if len(self['password']) < int(pwhistoryPolicy['pwLength']):
						for i,j in self.alloc:
							univention.admin.allocators.release(self.lo, self.position, i, j)
						raise univention.admin.uexceptions.pwToShort, _('The password is too short, at least %d characters needed!')% int(pwhistoryPolicy['pwLength'])
			else:
				if self['overridePWLength'] != '1':
					if len(self['password']) < self.password_length:
						for i,j in self.alloc:
							univention.admin.allocators.release(self.lo, self.position, i, j)
						raise univention.admin.uexceptions.pwToShort, _('The password is too short, at least %d characters needed!') %self.password_length
			if pwhistoryPolicy != None and pwhistoryPolicy['pwQualityCheck'] != None and pwhistoryPolicy['pwQualityCheck'].lower() in ['true', '1']:
				if self['overridePWLength'] != '1':
					pwdCheck = univention.password.Check(self.lo)
					pwdCheck.enableQualityCheck = True
					try:
						pwdCheck.check(self['password'])
					except ValueError, e:
						raise univention.admin.uexceptions.pwQuality, str(e).replace('W?rterbucheintrag','Wörterbucheintrag').replace('enth?lt', 'enthält')
						
					
			if pwhistoryPolicy != None and pwhistoryPolicy['expiryInterval'] != None and len(pwhistoryPolicy['expiryInterval']) > 0:
				try:
					expiryInterval=int(pwhistoryPolicy['expiryInterval'])
				except:
					# expiryInterval is empty or no legal int-string
					pwhistoryPolicy['expiryInterval']=''
					expiryInterval=-1
				if 'posix' in self.options or 'mail' in self.options:
					now=(long(time.time())/3600/24)
					if pwd_change_next_login == 1:
						if expiryInterval == -1:
							shadowMax = "1"
						else:
							shadowMax="%d" % expiryInterval

						shadowLastChangeValue = str(int(now) - int(shadowMax) - 1)
					else:
						if expiryInterval==-1:
							shadowMax=''
						else:
							shadowMax="%d" % expiryInterval

						shadowLastChangeValue = str(int(now))

					univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'shadowMax: %s' % shadowMax)
					old_shadowMax=self.oldattr.get('shadowMax', '')
					if old_shadowMax != shadowMax:
						ml.append(('shadowMax',self.oldattr.get('shadowMax', [''])[0], shadowMax))
				if 'kerberos' in self.options:
					if pwd_change_next_login == 1:
						expiry=time.strftime("%d.%m.%y",time.gmtime((long(time.time()))))
					else:
						if expiryInterval==-1 or expiryInterval == 0:
							expiry='0'
						else:
							expiry=time.strftime("%d.%m.%y",time.gmtime((long(time.time()) + (expiryInterval*3600*24))))
					if expiry == '0':
						krb5PasswordEnd=''
					else:
						krb5PasswordEnd="%s" % "20"+expiry[6:8]+expiry[3:5]+expiry[0:2]+"000000Z"
					univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'krb5PasswordEnd: %s' % krb5PasswordEnd)
					old_krb5PasswordEnd=self.oldattr.get('krb5PasswordEnd', '')
					if old_krb5PasswordEnd != krb5PasswordEnd:
						ml.append(('krb5PasswordEnd',self.oldattr.get('krb5PasswordEnd', [''])[0], krb5PasswordEnd))
				if pwd_change_next_login == 1:
					pwd_change_next_login=0
			else: # no pwhistoryPolicy['expiryInterval']
				if 'posix' in self.options or 'mail' in self.options:
					ml.append(('shadowMax',self.oldattr.get('shadowMax', [''])[0], ''))
					shadowLastChangeValue = ''
				if 'kerberos' in self.options:
					old_krb5PasswordEnd=self.oldattr.get('krb5PasswordEnd', '')
					if old_krb5PasswordEnd:
						ml.append(('krb5PasswordEnd',old_krb5PasswordEnd, '0'))


			disabled=""
			acctFlags=univention.admin.samba.acctFlags(self.oldattr.get("sambaAcctFlags", [''])[0])
			krb_kdcflags='126'
			if self.__is_windows_disabled():
				acctFlags.set('D')
			if self.__is_kerberos_disabled():
				krb_kdcflags='254'
			if self.__is_posix_disabled():
				shadowExpire='1'

			if self["locked"] in ['all', 'windows']:
				acctFlags.set('L')
			if self["locked"] in ['all', 'posix']:
				disabled="!"

			#                             FIXME: required for join user root
			if 'posix' in self.options or ('samba' in self.options and self['username'] == 'root') or 'mail' in self.options or 'ldap_pwd' in self.options:
				if self.is_auth_saslpassthrough == 'no':
					password_crypt = "{crypt}%s%s" % (disabled, univention.admin.password.crypt(self['password']))
					#shadowlastchange=str(long(time.time())/3600/24)
					ml.append(('userPassword', self.oldattr.get('userPassword', [''])[0], password_crypt))
					#if 'posix' in self.options:
					#	if pwd_change_next_login != 1:
					#		shadowLastChangeValue = shadowlastchange
			if 'samba' in self.options:
				password_nt, password_lm = univention.admin.password.ntlm(self['password'])
				if str(self.oldattr.get('sambaAcctFlags', [''])[0]) != str(acctFlags.decode()):
					ml.append(('sambaAcctFlags', self.oldattr.get('sambaAcctFlags', [''])[0], acctFlags.decode()))
				ml.append(('sambaNTPassword', self.oldattr.get('sambaNTPassword', [''])[0], password_nt))
				ml.append(('sambaLMPassword', self.oldattr.get('sambaLMPassword', [''])[0], password_lm))
				sambaPwdLastSetValue = str(long(time.time()))

				smbpwhistoryPolicy = self.loadPolicyObject('policies/pwhistory')
				if smbpwhistoryPolicy != None and smbpwhistoryPolicy['length'] != None:
					smbpwhlen = int(pwhistoryPolicy['length'])
					smbpwhistory=self.oldattr.get('sambaPasswordHistory',[''])[0]
					newsmbPWHistory = self.__getsmbPWHistory(password_nt, smbpwhistory, smbpwhlen)
					ml.append(('sambaPasswordHistory', self.oldattr.get('sambaPasswordHistory', [''])[0], newsmbPWHistory))

			if 'kerberos' in self.options:
				krb_keys=univention.admin.password.krb5_asn1(self.krb5_principal(), self['password'])
				krb_key_version=str(int(self.oldattr.get('krb5KeyVersionNumber', ['0'])[0])+1)
				ml.append(('krb5Key', self.oldattr.get('krb5Key', []), krb_keys))
				ml.append(('krb5KDCFlags', self.oldattr.get('krb5KDCFlags', []), krb_kdcflags))
				ml.append(('krb5KeyVersionNumber', self.oldattr.get('krb5KeyVersionNumber', []), krb_key_version))

				if not 'krb5KDCEntry' in ocs and not self.kerberos_active:
					domain=univention.admin.uldap.domain(self.lo, self.position)
					realm=domain.getKerberosRealm()
					if realm:
						ml.append(('krb5PrincipalName', '', [self['username']+'@'+realm]))
						ml.append(('krb5MaxLife', '', '86400'))
						ml.append(('krb5MaxRenew', '', '604800'))
						ml.insert(0, ('objectClass', '', ['krb5Principal', 'krb5KDCEntry']))

		if self.hasChanged('disabled'):
			if 'kerberos' in self.options:
				if self.__is_kerberos_disabled():
					# disable kerberos account
					krb_kdcflags='254'
					ml.append(('krb5KDCFlags', self.oldattr.get('krb5KDCFlags', ['']), krb_kdcflags))
				else:
					# enable kerberos account
					krb_kdcflags='126'
					ml.append(('krb5KDCFlags', self.oldattr.get('krb5KDCFlags', ['']), krb_kdcflags))

			if 'samba' in self.options:
				if self.__is_windows_disabled():
					# disable samba account
					acctFlags=univention.admin.samba.acctFlags(self.oldattr.get("sambaAcctFlags", [''])[0])
					acctFlags.set('D')
					ml.append(('sambaAcctFlags', self.oldattr.get('sambaAcctFlags', [''])[0], acctFlags.decode()))
				else:
					# enable samba account
					acctFlags=univention.admin.samba.acctFlags(self.oldattr.get("sambaAcctFlags", [''])[0])
					acctFlags.unset('D')
					# lock account, if necessary (this is unset by removing flag D)
					if self['locked'] in ['all', 'windows']:
						acctFlags.set("L")
					if str(self.oldattr.get('sambaAcctFlags', [''])[0]) != str(acctFlags.decode()):
						ml.append(('sambaAcctFlags', self.oldattr.get('sambaAcctFlags', [''])[0], acctFlags.decode()))
			if 'posix' in self.options:
				if self.__is_posix_disabled():
					# disable posix account
					shadowExpire=self.oldattr.get("shadowExpire", [''])[0]
					ml.append(('shadowExpire', self.oldattr.get('shadowExpire', [''])[0], '1'))
				else:
					# enable posix account
					shadowExpire=self.oldattr.get("shadowExpire", [''])[0]
					if shadowExpire == '1':
						if self['userexpiry']:
							shadowExpire="%d" % long(time.mktime(time.strptime(self['userexpiry'],"%Y-%m-%d"))/3600/24+1)
						else:
							shadowExpire=''
						ml.append(('shadowExpire', self.oldattr.get('shadowExpire', [''])[0], shadowExpire))
		if self.hasChanged('locked'):
			if 'posix' in self.options or ('samba' in self.options and self['username'] == 'root') or 'mail' in self.options:
				# if self.modifypassword is set the password was already locked
				if not self.modifypassword: 
					if self['locked'] in ['all', 'posix']:
						password_disabled = self.__pwd_locked(self['password'])
						ml.append(('userPassword', self.oldattr.get('userPassword', [''])[0], password_disabled))
					else:
						password_enabled = self.__pwd_unlocked(self['password'])
						ml.append(('userPassword', self.oldattr.get('userPassword', [''])[0], password_enabled))
			if 'samba' in self.options:
				if self['locked'] in ['all', 'windows']:
					# lock samba account
					acctFlags=univention.admin.samba.acctFlags(self.oldattr.get("sambaAcctFlags", [''])[0])
					acctFlags.set("L")
					ml.append(('sambaAcctFlags', self.oldattr.get('sambaAcctFlags', [''])[0], acctFlags.decode()))
				else:
					# unlock samba account
					acctFlags=univention.admin.samba.acctFlags(self.oldattr.get("sambaAcctFlags", [''])[0])
					acctFlags.unset("L")
					if str(self.oldattr.get('sambaAcctFlags', [''])[0]) != str(acctFlags.decode()):
						ml.append(('sambaAcctFlags', self.oldattr.get('sambaAcctFlags', [''])[0], acctFlags.decode()))
					# reset bad pw count
					ml.append(('sambaBadPasswordCount', self.oldattr.get('sambaBadPasswordCount', [''])[0], "0"))

		if self.hasChanged(['userexpiry']):
			if 'posix' in self.options or 'mail' in self.options:
				shadowExpire=''
				if self['userexpiry']:
					shadowExpire="%d" % long(time.mktime(time.strptime(self['userexpiry'],"%d.%m.%y"))/3600/24+1)
					univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'shadowExpire: %s' % shadowExpire)
				old_shadowExpire=self.oldattr.get('shadowExpire', '')
				if old_shadowExpire != shadowExpire:
					ml.append(('shadowExpire',self.oldattr.get('shadowExpire', [''])[0], shadowExpire))
			if 'samba' in self.options:
				sambaKickoffTime=''
				if self['userexpiry']:
					sambaKickoffTime="%d" % long(time.mktime(time.strptime(self['userexpiry'],"%d.%m.%y")))
					univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'sambaKickoffTime: %s' % sambaKickoffTime)
				old_sambaKickoffTime=self.oldattr.get('sambaKickoffTime', '')
				if old_sambaKickoffTime != sambaKickoffTime:
					ml.append(('sambaKickoffTime',self.oldattr.get('sambaKickoffTime', [''])[0], sambaKickoffTime))
			if 'kerberos' in self.options:
				krb5ValidEnd=''
				if self['userexpiry']:
					krb5ValidEnd="%s" % "20"+self['userexpiry'][6:8]+self['userexpiry'][3:5]+self['userexpiry'][0:2]+"000000Z"
					univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'krb5ValidEnd: %s' % krb5ValidEnd)
				old_krb5ValidEnd=self.oldattr.get('krb5ValidEnd', '')
				if old_krb5ValidEnd != krb5ValidEnd:
					if not self['userexpiry']:
						ml.append(('krb5ValidEnd',old_krb5ValidEnd, '0'))
					else:
						ml.append(('krb5ValidEnd',self.oldattr.get('krb5ValidEnd', [''])[0], krb5ValidEnd))



		if pwd_change_next_login == 1:	# ! self.modifypassword or no pwhistoryPolicy['expiryInterval']
			if 'posix' in self.options or 'mail' in self.options:
				pwhistoryPolicy = self.loadPolicyObject('policies/pwhistory')
				if pwhistoryPolicy != None and pwhistoryPolicy['expiryInterval'] != None and len(pwhistoryPolicy['expiryInterval']) > 0:
					try:
						expiryInterval=int(pwhistoryPolicy['expiryInterval'])
					except:
						# expiryInterval is empty or no legal int-string
						pwhistoryPolicy['expiryInterval']=''
						expiryInterval=-1
				else:
					# expiryInterval is empty or no legal int-string
					pwhistoryPolicy['expiryInterval']=''
					expiryInterval=-1

				if expiryInterval == -1:
					shadowMax = "1"
				else:
					shadowMax="%d" % expiryInterval

				now=(long(time.time())/3600/24)
				shadowLastChangeValue = str(int(now) - int(shadowMax) - 1)

				old_shadowMax=self.oldattr.get('shadowMax', '')
				if old_shadowMax != shadowMax:
					ml.append(('shadowMax',self.oldattr.get('shadowMax', [''])[0], shadowMax))

			if 'samba' in self.options:
				# set sambaPwdLastSet to 1, see UCS Bug #8292 and Samba Bug #4313
				sambaPwdLastSetValue='1'

			if 'kerberos' in self.options:
				expiry=time.strftime("%d.%m.%y",time.gmtime((long(time.time()))))
				krb5PasswordEnd="%s" % "20"+expiry[6:8]+expiry[3:5]+expiry[0:2]+"000000Z"
				univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'krb5PasswordEnd: %s' % krb5PasswordEnd)
				old_krb5PasswordEnd=self.oldattr.get('krb5PasswordEnd', '')
				if old_krb5PasswordEnd != krb5PasswordEnd:
					ml.append(('krb5PasswordEnd',self.oldattr.get('krb5PasswordEnd', [''])[0], krb5PasswordEnd))
		elif pwd_change_next_login == 2:	# pwdChangeNextLogin changed from 1 to 0
			# 1. determine expiryInterval (could be done once before "if self.modifypassword" above)
			pwhistoryPolicy = self.loadPolicyObject('policies/pwhistory')
			if pwhistoryPolicy != None and pwhistoryPolicy['expiryInterval'] != None and len(pwhistoryPolicy['expiryInterval']) > 0:
				try:
					expiryInterval=int(pwhistoryPolicy['expiryInterval'])
				except:
					# expiryInterval is empty or no legal int-string
					pwhistoryPolicy['expiryInterval']=''
					expiryInterval=-1
			else: # no pwhistoryPolicy['expiryInterval']
				expiryInterval=-1

			# 2. set posix attributes
			if 'posix' in self.options or 'mail' in self.options:
				if expiryInterval==-1:
					shadowMax=''
				else:
					shadowMax="%d" % expiryInterval

				now=(long(time.time())/3600/24)
				shadowLastChangeValue = str(int(now))

				univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'shadowMax: %s' % shadowMax)
				old_shadowMax=self.oldattr.get('shadowMax', [''])[0]
				if old_shadowMax != shadowMax:
					ml.append(('shadowMax', old_shadowMax, shadowMax))

			# 3. set samba attributes
			if 'samba' in self.options:
				sambaPwdLastSetValue = str(long(time.time()))
				# transfered into ml below
				univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'sambaPwdLastSetValue: %s' % sambaPwdLastSetValue)

			# 4. set kerberos attribute
			if 'kerberos' in self.options:
				if expiryInterval==-1 or expiryInterval == 0:
					krb5PasswordEnd=''
				else:
					expiry=time.strftime("%d.%m.%y",time.gmtime((long(time.time()) + (expiryInterval*3600*24))))
					krb5PasswordEnd="%s" % "20"+expiry[6:8]+expiry[3:5]+expiry[0:2]+"000000Z"
				univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'krb5PasswordEnd: %s' % krb5PasswordEnd)
				old_krb5PasswordEnd=self.oldattr.get('krb5PasswordEnd', [''])[0]
				if old_krb5PasswordEnd != krb5PasswordEnd:
					ml.append(('krb5PasswordEnd',old_krb5PasswordEnd, krb5PasswordEnd))


		if (self.hasChanged('mailPrimaryAddress') and self['mailPrimaryAddress']) or (self.hasChanged('mailAlternativeAddress') and self['mailAlternativeAddress']):
			if 'mail' in self.options and not self.mail_active:
				ocs=self.oldattr.get('objectClass', [])
				if not 'univentionMail' in ocs:
					ml.insert(0, ('objectClass', '', 'univentionMail'))
		if self.hasChanged('mailPrimaryAddress') and self['mailPrimaryAddress']:
			for i, j in self.alloc:
				if i == 'mailPrimaryAddress': break
			else:
				try:
					self.alloc.append( ( 'mailPrimaryAddress', self[ 'mailPrimaryAddress' ] ) )
					univention.debug.debug( univention.debug.ADMIN, univention.debug.INFO, "LOCKING: %s" % self[ 'mailPrimaryAddress' ] )
					univention.admin.allocators.request( self.lo, self.position, 'mailPrimaryAddress', value = self[ 'mailPrimaryAddress' ] )
					univention.debug.debug( univention.debug.ADMIN, univention.debug.INFO, "LOCKING DONE: %s" % self[ 'mailPrimaryAddress' ] )
				except univention.admin.uexceptions.noLock:
					self.cancel()
					raise univention.admin.uexceptions.mailAddressUsed

		if self.hasChanged('birthday'):
			if self['birthday']:
				if not 'univentionPerson' in self.oldattr.get('objectClass', []):
					ml.insert(0, ('objectClass', self.oldattr.get('objectClass', []), self.oldattr.get('objectClass', []) + ['univentionPerson']))
		if self.hasChanged('homeShare') or self.hasChanged('homeSharePath'):
			if self['homeShare']:
				share_mod = univention.admin.modules.get('shares/share')
				try:
					share=share_mod.object(None, self.lo, self.position, self['homeShare'])
					share.open()
				except:
					raise univention.admin.uexceptions.noObject, _('DN given as share is not valid.')

				if share['host'] and share['path']:
					if not 'automount' in self.oldattr.get('objectClass', []):
						ml.insert(0, ('objectClass', '', 'automount'))

					am_host=share['host']
					if not self['homeSharePath'] or type(self['homeSharePath']) not in [types.StringType, types.UnicodeType]:
						am_path=os.path.join(share['path'])
					else:
						am_path=os.path.join(share['path'], self['homeSharePath'])

					am_old = self.oldattr.get('automountInformation', [''])[0]
					am_new = '-rw %s:%s' % (am_host, am_path)
					ml.append(('automountInformation', am_old, am_new))
				else:
					raise univention.admin.uexceptions.noObject, _('Given DN is no share.')

			if not self['homeShare'] or not share['host'] or not share['path']:
					if 'automount' in self.oldattr.get('objectClass', []):
						ml.insert(0, ('objectClass', 'automount', ''))
					am_old = self.oldattr.get('automountInformation', [''])[0]
					if am_old:
						ml.append(('automountInformation', am_old, ''))
		if 'samba' in self.options:
			sambaMunged=self.sambaMungedDialMap()
			if sambaMunged:
				ml.append(('sambaMungedDial', self.oldattr.get('sambaMungedDial', ['']), [sambaMunged]))

			if self.hasChanged('sambaRID') and not hasattr(self, 'userSid'):
				self.userSid = self.__generate_user_sid(self.oldattr['uidNumber'][0])
				ml.append(('sambaSID', self.oldattr.get('sambaSID', ['']), [self.userSid]))
			pass

		if sambaPwdLastSetValue:
			ml.append(('sambaPwdLastSet', self.oldattr.get('sambaPwdLastSet', [''])[0], sambaPwdLastSetValue))

		if shadowLastChangeValue:
			ml.append(('shadowLastChange',self.oldattr.get('shadowLastChange', [''])[0], shadowLastChangeValue))

		return ml

	#FIXME: this functions seems deprecated, there is no call to it in any UCS package below dev/trunk/ucs
	def __create_gecos( self, old_data = False ):
		if not old_data:
			if self[ 'firstname' ]:
				gecos = "%s %s" % ( self.info.get( 'firstname', '' ), self.info.get( 'lastname', '' ) )
			else:
				gecos = "%s" % self.info.get( 'lastname', '' )
		else:
			if self.oldinfo[ 'firstname' ]:
				gecos = "%s %s" % ( self.oldinfo.get( 'firstname', '' ), self.oldinfo.get( 'lastname', '' ) )
			else:
				gecos = "%s" % self.oldinfo.get( 'lastname', '' )

		# replace umlauts
		_umlauts = { 'ä' :'ae', 'Ä' : 'Ae', 'ö' : 'oe', 'Ö' : 'Oe', 'ü' : 'ue', 'Ü' : 'Ue', 'ß' : 'ss', 'Á' : 'A', 'Â' : 'A', 'Ã' : 'A', 'Ä' : 'A', 'Å' : 'A', 'Æ' : 'AE', 'Ç' : 'C', 'È' : 'E', 'É' : 'E', 'Ê' : 'E', 'Ë' : 'E', 'Ì' : 'I', 'Í' : 'I', 'Î' : 'I', 'Ï' : 'I', 'Ð' : 'D', 'Ñ' : 'N', 'Ò' : 'O', 'Ó' : 'O', 'Ô' : 'O', 'Õ' : 'O', 'Ö' : 'O', 'Ù' : 'U', 'Ú' : 'U', 'Û' : 'U', 'à' : 'a', 'â' : 'a', 'á' : 'a', 'ã' : 'a', 'æ' : 'ae', 'ç' : 'c', 'è' : 'e', 'é' : 'e', 'ê' : 'e', 'ë' : 'e', 'ì' : 'i', 'í' : 'i', 'î' : 'i', 'ï' : 'i', 'ñ' : 'n', 'ò' : 'o', 'ó' : 'o', 'ô' : 'o', 'ù' : 'u', 'ú' : 'u', 'û' : 'u', 'ý' : 'y', 'ÿ' : 'y', 'Ĉ' : 'C', 'ĉ' : 'c' }
		for umlaut, code in _umlauts.items():
			gecos = gecos.replace( umlaut, code )

		return gecos.encode('ascii', 'replace')

	def _ldap_pre_remove(self):
		if 'samba' in self.options:
			self.sid=self.oldattr['sambaSID'][0]
		if 'posix' in self.options:
			self.uidNum=self.oldattr['uidNumber'][0]
		self.uid=self.oldattr['uid'][0]

	def _ldap_post_remove(self):
		if 'samba' in self.options:
			univention.admin.allocators.release(self.lo, self.position, 'sid', self.sid)
		if 'posix' in self.options:
			univention.admin.allocators.release(self.lo, self.position, 'uidNumber', self.uidNum)
		if 'mail' in self.options and  self['mailPrimaryAddress']:
			univention.admin.allocators.release(self.lo, self.position, 'mailPrimaryAddress', self[ 'mailPrimaryAddress' ] )
		univention.admin.allocators.release(self.lo, self.position, 'uid', self.uid)

		f=univention.admin.filter.expression('uniqueMember', self.dn)
		groupObjects=univention.admin.handlers.groups.group.lookup(self.co, self.lo, filter_s=f)
		if groupObjects:
			uid = univention.admin.uldap.explodeDn(self.dn, 1)[0]
			for groupObject in groupObjects:
				groupObject.fast_member_remove( [ self.dn ], [ uid ], ignore_license=1 )

		admin_settings_dn='uid=%s,cn=admin-settings,cn=univention,%s' % (self['username'], self.lo.base)
		# delete admin-settings object of user if it exists
		try:
			self.lo.delete(admin_settings_dn)
		except univention.admin.uexceptions.noObject:
			pass

	def _move(self, newdn, modify_childs = True, ignore_license = False):
		olddn = self.dn
		tmpdn = 'cn=%s-subtree,cn=temporary,cn=univention,%s' % (self['username'], self.lo.base)
		al = [('objectClass', ['top', 'organizationalRole']), ('cn', ['%s-subtree' % self['username']])]
		subelements = self.lo.search(base=self.dn, scope='one', attr=['objectClass']) # FIXME: identify may fail, but users will raise decode-exception
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
			super(object, self)._move(newdn, modify_childs, ignore_license)
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

	def __passwordInHistory(self, newpassword, pwhistory):
		# first calc hash for the new pw
		s = hashlib.sha1( newpassword.encode( 'utf-8' ) )
		newpwhash = string.upper(s.hexdigest())
		if not string.find(pwhistory, newpwhash) < 0:
			# password has already been used.
			return 1
		return 0

	def __getPWHistory(self, newpassword, pwhistory, pwhlen):
		# first calc hash for the new pw
		s = hashlib.sha1( newpassword.encode( 'utf-8' ) )
		newpwhash = string.upper(s.hexdigest())

		# split the history
		if len(string.strip(pwhistory)):
			pwlist = string.split(pwhistory, ' ')
		else:
			pwlist = []

		#this preserves a temporary disabled history
		if pwhlen > 0:
			if len(pwlist) < pwhlen:
				pwlist.append(newpwhash)
			else:
				# calc entries to cut out
				cut = 1 + len(pwlist) - pwhlen
				pwlist[0:cut] = []
				if pwhlen > 1:
					# and append to shortened history
					pwlist.append(newpwhash)
				else:
					# or replace the history completely
					if len(pwlist) > 0:
						pwlist[0] = newpwhash
						# just to be sure...
						pwlist[1:] = []
					else:
						pwlist.append(newpwhash)
		# and build the new history
		res = string.join(pwlist)
		return res

	def __getsmbPWHistory(self, newpassword, smbpwhistory, smbpwhlen):
		# split the history
		if len(string.strip(smbpwhistory)):
			pwlist = string.split(smbpwhistory, ' ')
		else:
			pwlist = []

		#calculate the password hash & salt
		salt=''
		urandom = open('/dev/urandom', 'r')
		#get 16 bytes from urandom for salting our hash
		rand = urandom.read(16)
		for i in range(0, len(rand)):
			salt = salt + '%.2X' % ord(rand[i])
		#we have to have that in hex
		hexsalt = salt
		#and binary for calculating the md5
		salt = self.getbytes(salt)
		#we need the ntpwd binary data to
		pwd = self.getbytes(newpassword)
		#calculating hash. sored as a 32byte hex in sambePasswordHistory,
		#syntax like that: [Salt][MD5(Salt+Hash)]
		#	First 16bytes ^		^ last 16bytes.
		pwdhash = hashlib.md5(salt + pwd).hexdigest().upper()
		smbpwhash = hexsalt+pwdhash

		if len(pwlist) < smbpwhlen:
			#just append
			pwlist.append(smbpwhash)
		else:
			#calc entries to cut out
			cut = 1 + len(pwlist) - smbpwhlen
			pwlist[0:cut] = []
			if smbpwhlen > 1:
				#and append to shortened history
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

	def __generate_user_sid(self, uidNum):
		# TODO: cleanup function
		userSid = None

		if self['sambaRID']:
			searchResult=self.lo.search(filter='objectClass=sambaDomain', attr=['sambaSID'])
			domainsid=searchResult[0][1]['sambaSID'][0]
			sid = domainsid+'-'+self['sambaRID']
			try:
				userSid = univention.admin.allocators.request(self.lo, self.position, 'sid', sid)
				self.alloc.append(('sid', userSid))
			except univention.admin.uexceptions.noLock, e:
				raise univention.admin.uexceptions.sidAlreadyUsed, ': %s' % self['sambaRID']
		
		else:
			if self.s4connector_present:
				# In this case Samba 4 must create the SID, the s4 connector will sync the
				# new sambaSID back from Samba 4.
				userSid='S-1-4-%s' % uidNum
			else:
				try:
					userSid=univention.admin.allocators.requestUserSid(self.lo, self.position, uidNum)
				except:
					pass
			if not userSid or userSid == 'None':
				num=uidNum
				while not userSid or userSid == 'None':
					num = str(int(num)+1)
					try:
						userSid=univention.admin.allocators.requestUserSid(self.lo, self.position, num)
					except univention.admin.uexceptions.noLock, e:
						num = str(int(num)+1)
				self.alloc.append(('sid', userSid))

		return userSid

	def getbytes(self, string):
		#return byte values of a string (for smbPWHistory)
		bytes = [int(string[i:i+2], 16) for i in xrange(0, len(string), 2)]
		return struct.pack("%iB" % len(bytes), *bytes)

	def cancel(self):
		for i,j in self.alloc:
			univention.admin.allocators.release(self.lo, self.position, i, j)


	def setPassword(newPassword):
		self.open(loadGroups=0)
		self['password']=newPassword

def rewrite(filter, mapping):
	if filter.variable == 'username':
		filter.variable='uid'
	elif filter.variable == 'firstname':
		filter.variable='givenName'
	elif filter.variable == 'lastname':
		filter.variable='sn'
	elif filter.variable == 'primaryGroup':
		filter.variable='gidNumber'

	elif filter.variable == 'disabled':
		if filter.value == 'none':
			filter.variable='&(!(shadowExpire=1))(!(krb5KDCFlags=254))(!(|(sambaAcctFlags=[UD       ])(sambaAcctFlags'
			filter.value='[ULD       ])))'
		elif filter.value == 'all':
			filter.variable='&(shadowExpire=1)(krb5KDCFlags=254)(|(sambaAcctFlags=[UD       ])(sambaAcctFlags'
			filter.value='[ULD       ]))'
		elif filter.value == 'posix':
			filter.variable='shadowExpire'
			filter.value='1'
		elif filter.value == 'kerberos':
			filter.variable='krb5KDCFlags'
			filter.value='254'
		elif filter.value == 'windows':
			filter.variable='|(sambaAcctFlags=[UD       ])(sambaAcctFlags'
			filter.value='=[ULD       ])'
		elif filter.value == 'windows_kerberos':
			filter.variable='&(krb5KDCFlags=254)(|(sambaAcctFlags=[UD       ])(sambaAcctFlags'
			filter.value='=[ULD       ]))'
		elif filter.value == 'windows_posix':
			filter.variable='&(shadowExpire=1)(|(sambaAcctFlags=[UD       ])(sambaAcctFlags'
			filter.value='=[ULD       ]))'
		elif filter.value == 'posix_kerberos':
			filter.variable='&(shadowExpire=1)(krb5KDCFlags'
			filter.value='254)'
		elif filter.value == '*':
			filter.variable='uid'

	elif filter.variable == 'locked':
		# substring match for userPassword is not possible
		if filter.value in ['posix', 'windows', 'all', 'none']:
			if filter.value == 'all':
				filter.variable='|(sambaAcctFlags=[UL       ])(sambaAcctFlags'
				filter.value='[ULD       ])'
				#filter.variable='|(sambaAcctFlags=[UL       ])(sambaAcctFlags=[ULD       ])(userPassword'
				#filter.value = '{crypt}!*)'
			if filter.value == 'windows':
				filter.variable='|(sambaAcctFlags=[UL       ])(sambaAcctFlags'
				filter.value = '[ULD       ])'
			#if filter.value == 'posix':
			#	filter.variable='userPassword'
			#	filter.value = '{crypt}!*'
			if filter.value == 'none':
				#filter.variable='&(!(sambaAcctFlags=[UL       ]))(!(sambaAcctFlags=[ULD       ]))(!(userPassword'
				#filter.value = '{crypt}!*))'
				filter.variable='&(!(sambaAcctFlags=[UL       ]))(!(sambaAcctFlags'
				filter.value='[ULD       ]))'
		elif filter.value == '*':
			filter.variable='uid'
	else:
		univention.admin.mapping.mapRewrite(filter, mapping)

def lookup(co, lo, filter_s, base='', superordinate=None, scope='sub', unique=0, required=0, timeout=-1, sizelimit=0):

	filter=univention.admin.filter.conjunction('&', [
		univention.admin.filter.conjunction('|', [
			univention.admin.filter.conjunction('&', [
				univention.admin.filter.expression('objectClass', 'posixAccount'),
				univention.admin.filter.expression('objectClass', 'shadowAccount'),
			]),
			univention.admin.filter.expression('objectClass', 'univentionMail'),
			univention.admin.filter.expression('objectClass', 'sambaSamAccount'),
			univention.admin.filter.expression('objectClass', 'simpleSecurityObject'),
			univention.admin.filter.conjunction('&', [
				univention.admin.filter.expression('objectClass', 'person'),
				univention.admin.filter.expression('objectClass', 'organizationalPerson'),
				univention.admin.filter.expression('objectClass', 'inetOrgPerson'),
			]),
		]),
		univention.admin.filter.conjunction('!', [univention.admin.filter.expression('uidNumber', '0')]),
		univention.admin.filter.conjunction('!', [univention.admin.filter.expression('uid', '*$')]),
	])

	if filter_s:
		filter_p=univention.admin.filter.parse(filter_s)
		univention.admin.filter.walk(filter_p, rewrite, arg=mapping)
		filter.expressions.append(filter_p)

	res=[]
	for dn, attrs in lo.search(unicode(filter), base, scope, [], unique, required, timeout, sizelimit):
		res.append( object( co, lo, None, dn, attributes = attrs ) )
	return res

def identify(dn, attr, canonical=0):

	if type(attr.get('uid',[])) == type([]) and len(attr.get('uid',[]))>0 and ('$' in attr.get('uid',[])[0]):
		return False

	return ((('posixAccount' in attr.get('objectClass', [])
			  and 'shadowAccount' in attr.get('objectClass', []))
			 or 'univentionMail' in attr.get('objectClass', [])
			 or 'sambaSamAccount' in attr.get('objectClass', [])
			 or 'simpleSecurityObject' in attr.get('objectClass', [])
			 or
			 ('person' in attr.get('objectClass', [])
			  and	'organizationalPerson' in attr.get('objectClass', [])
			  and 'inetOrgPerson' in attr.get('objectClass', [])))
			and not '0' in attr.get('uidNumber', [])
			and not '$' in attr.get('uid',[])
		        and not 'univentionHost' in attr.get('objectClass', [])
			)
