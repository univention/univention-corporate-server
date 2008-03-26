# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin module for the user objects
#
# Copyright (C) 2004, 2005, 2006 Univention GmbH
#
# http://www.univention.de/
#
# All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# Binary versions of this file provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import os, sys, string, re, copy, time, sha, types, struct, md5
import tempfile
from M2Crypto import X509
import ldap, heimdal
import univention.admin
import univention.admin.filter
import univention.admin.handlers
import univention.admin.handlers.groups.group
import univention.admin.handlers.settings.user
import univention.admin.password
import univention.admin.samba
import univention.admin.allocators
import univention.admin.localization
import univention.admin.uexceptions
import univention.admin.uldap
import univention.admin.mungeddial as mungeddial
import univention.admin.handlers.settings.prohibited_username
import base64

import univention.debug

translation=univention.admin.localization.translation('univention.admin.handlers.users')
_=translation.translate

class vacationResendDays(univention.admin.syntax.select):
	name = 'vacationresendDays'
	choices = [('1','1 %s' % _('day'))]
	for i in range(2,60):
		choices.append(("%s" % i,"%s %s" % (i, _('days'))))

class _default_gecos:
	def __init__( self ):
		pass

	def __call__( self, object, old_data = False ):
		if not old_data:
			if object[ 'firstname' ]:
				gecos = "%s %s" % ( object.info.get( 'firstname', '' ), object.info.get( 'lastname', '' ) )
			else:
				gecos = "%s" % object.info.get( 'lastname', '' )
		else:
			if object[ 'firstname' ]:
				gecos = "%s %s" % ( object.oldinfo.get( 'firstname', '' ), object.oldinfo.get( 'lastname', '' ) )
			else:
				gecos = "%s" % object.oldinfo.get( 'lastname', '' )

		# replace umlauts
		_umlauts = { 'ä' :'ae', 'Ä' : 'Ae', 'ö' : 'oe', 'Ö' : 'Oe', 'ü' : 'ue', 'Ü' : 'Ue', 'ß' : u'ss' }
		for umlaut, code in _umlauts.items():
			gecos = gecos.replace( umlaut, code )

		return gecos

module='users/user'
operations=['add','edit','remove','search','move']
template='settings/usertemplate'
usewizard=1
wizardmenustring=_("Users")
wizarddescription=_("Add, edit and delete users")
wizardoperations={"add":[_("Add"), _("Add User")],"find":[_("Find"), _("Find User(s)")]}
uid_umlauts = 0

childs=0
short_description=_('User')
long_description=''

options={
	'posix': univention.admin.option(
			short_description=_('Posix Account'),
			default=1,
			objectClasses = ['posixAccount', 'shadowAccount'],
		),
	'samba': univention.admin.option(
			short_description=_('Samba Account'),
			default=1,
			objectClasses = ['sambaSamAccount'],
		),
	'kerberos': univention.admin.option(
			short_description=_('Kerberos Principal'),
			default=1,
			objectClasses = ['krb5Principal', 'krb5KDCEntry'],
		),
	'mail': univention.admin.option(
			short_description=_('Mail Account'),
			default=1,
			objectClasses = ['univentionMail'],
		),
	'groupware': univention.admin.option(
			short_description=_('Groupware Account'),
			default=0,
			editable=1,
			objectClasses = ['univentionKolabInetOrgPerson'],
		),
	'pki': univention.admin.option(
			short_description=_('Public Key Infrastructure Account'),
			default=0,
			editable=1,
			objectClasses = ['pkiUser'],
		),
	'person': univention.admin.option(
			short_description=_('Personal Information'),
			default=1,
			objectClasses = ['person', 'organizationalPerson', 'inetOrgPerson'],
		)
}
property_descriptions={
	'username': univention.admin.property(
			short_description=_('Username'),
			long_description='',
			syntax=univention.admin.syntax.uid,
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
			short_description=_('First Name'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=['person'],
			required=0,
			may_change=1,
			identifies=0
		),
	'lastname': univention.admin.property(
			short_description=_('Last Name'),
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
			syntax=univention.admin.syntax.string,
			options=['posix'],
			multivalue=0,
			required=0,
			may_change=1,
			default = ( _default_gecos(), [], False ),
			identifies=0
		),
	'title': univention.admin.property(
			short_description=_('Title'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=['person'],
			required=0,
			may_change=1,
			identifies=0
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
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=['person'],
			required=0,
			may_change=1,
			identifies=0
		),
	'userexpiry': univention.admin.property(
			short_description=_('Account Expiration Date'),
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
			short_description=_('Password Expiration Date'),
			long_description=_('Enter date as day.month.year.'),
			syntax=univention.admin.syntax.date,
			multivalue=0,
			options=['posix', 'samba', 'kerberos', 'mail'],
			editable=0,
			required=0,
			may_change=0,
			dontsearch=1,
			identifies=0
		),
	'pwdChangeNextLogin': univention.admin.property(
			short_description=_('Change Password on Next Login'),
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
			short_description=_('Disabled'),
			long_description='',
			syntax=univention.admin.syntax.boolean,
			multivalue=0,
			options=['posix', 'samba', 'kerberos', 'mail'],
			required=0,
			may_change=1,
			identifies=0,
			show_in_lists=1
		),
	'locked': univention.admin.property(
			short_description=_('Locked'),
			long_description='',
			syntax=univention.admin.syntax.boolean,
			multivalue=0,
			options=['samba'],
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
			options=['posix', 'samba', 'kerberos', 'mail'],
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
			short_description=_('E-Mail Address'),
			long_description='',
			syntax=univention.admin.syntax.emailAddress,
			multivalue=1,
			options=['person'],
			required=0,
			may_change=1,
			identifies=0,
			default=(['<mailPrimaryAddress>'])
		),
	'postcode': univention.admin.property(
			short_description=_('Postal Code'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=['person'],
			required=0,
			may_change=1,
			identifies=0
		),
	'city': univention.admin.property(
			short_description=_('City'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=['person'],
			required=0,
			may_change=1,
			identifies=0
		),
	'phone': univention.admin.property(
			short_description=_('Telephone Number'),
			long_description='',
			syntax=univention.admin.syntax.phone,
			multivalue=1,
			options=['person'],
			required=0,
			may_change=1,
			identifies=0
		),
	'employeeNumber': univention.admin.property(
			short_description=_('Employee Number'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=['person'],
			required=0,
			may_change=1,
			identifies=0
		),
	'roomNumber': univention.admin.property(
			short_description=_('Room Number'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=['person'],
			required=0,
			may_change=1,
			identifies=0
		),
	'secretary': univention.admin.property(
			short_description=_('Secretary'),
			long_description='',
			syntax=univention.admin.syntax.userDn,
			multivalue=1,
			options=['person'],
			required=0,
			may_change=1,
			identifies=0
		),
	'departmentNumber': univention.admin.property(
			short_description=_('Department Number'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=['person'],
			required=0,
			may_change=1,
			identifies=0
		),
	'employeeType': univention.admin.property(
			short_description=_('Employee Type'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=['person'],
			required=0,
			may_change=1,
			identifies=0
		),
	'homePostalAddress': univention.admin.property(
			short_description=_('Home Postal Address'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=1,
			options=['person'],
			required=0,
			may_change=1,
			identifies=0
		),
	'homeTelephoneNumber': univention.admin.property(
			short_description=_('Home Telephone Number'),
			long_description='',
			syntax=univention.admin.syntax.phone,
			multivalue=1,
			options=['person'],
			required=0,
			may_change=1,
			identifies=0
		),
	'mobileTelephoneNumber': univention.admin.property(
			short_description=_('Mobile Telephone Number'),
			long_description='',
			syntax=univention.admin.syntax.phone,
			multivalue=1,
			options=['person'],
			required=0,
			may_change=1,
			identifies=0
		),
	'pagerTelephoneNumber': univention.admin.property(
			short_description=_('Pager Telephone Number'),
			long_description='',
			syntax=univention.admin.syntax.phone,
			multivalue=1,
			options=['person'],
			required=0,
			may_change=1,
			identifies=0
		),
	'unixhome': univention.admin.property(
			short_description=_('Unix Home Directory'),
			long_description='',
			syntax=univention.admin.syntax.absolutePath,
			multivalue=0,
			options=['posix'],
			required=1,
			may_change=1,
			identifies=0,
			default=('/home/<username>', ['username']) # FIXME: should escape umlauts
		),

	'shell': univention.admin.property(
			short_description=_('Login Shell'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=['posix'],
			required=0,
			may_change=1,
			identifies=0,
			default=('/bin/bash', [])
		),
	'sambahome': univention.admin.property(
			short_description=_('Windows Home Path'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=['samba'],
			required=0,
			may_change=1,
			identifies=0
		),
	'scriptpath': univention.admin.property(
			short_description=_('Windows Script Path'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=['samba'],
			required=0,
			may_change=1,
			identifies=0
		),
	'profilepath': univention.admin.property(
			short_description=_('Windows Profile Path'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=['samba'],
			required=0,
			may_change=1,
			identifies=0
		),
	'homedrive': univention.admin.property(
			short_description=_('Windows Home Drive'),
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
			may_change=0,
			dontsearch=1,
			identifies=0,
			options=['samba']
		),
	'groups': univention.admin.property(
			short_description=_('Groups'),
			long_description='',
			syntax=univention.admin.syntax.groupDn,
			multivalue=1,
			options=['posix'],
			required=0,
			dontsearch=1,
			may_change=1,
			identifies=0
		),
	'primaryGroup': univention.admin.property(
			short_description=_('Primary Group'),
			long_description='',
			syntax=univention.admin.syntax.primaryGroup,
			multivalue=0,
			options=['posix'],
			required=1,
			dontsearch=1,
			may_change=1,
			identifies=0
		),
	'mailPrimaryAddress': univention.admin.property(
			short_description=_('Primary E-Mail Address'),
			long_description='',
			syntax=univention.admin.syntax.emailAddress,
			multivalue=0,
			options=['mail', 'groupware'],
			required=0,
			dontsearch=0,
			may_change=1,
			identifies=0,
		),
	'mailGlobalSpamFolder': univention.admin.property(
			short_description=_('Use Global Spam Folder'),
			long_description=_('Move Spam to a global spam folder instead of a local folder'),
			syntax=univention.admin.syntax.boolean,
			multivalue=0,
			options=['mail', 'groupware'],
			required=0,
			may_change=1,
			dontsearch=1,
			identifies=0
		),
	'mailAlternativeAddress': univention.admin.property(
			short_description=_('Alternative E-Mail Addresses'),
			long_description='',
			syntax=univention.admin.syntax.emailAddress,
			multivalue=1,
			options=['mail', 'groupware'],
			required=0,
			dontsearch=0,
			may_change=1,
			identifies=0,
		),
	'overridePWHistory': univention.admin.property(
			short_description=_('Override Password History'),
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
			short_description=_('Override Password Length'),
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
			short_description=_('Home Share'),
			long_description=_('Share, the user\'s home directory resides on'),
			syntax=univention.admin.syntax.module('shares/share'),
			multivalue=0,
			options=['samba', 'posix', 'kerberos' ],
			required=0,
			dontsearch=1,
			may_change=1,
			identifies=0,
		),
	'homeSharePath': univention.admin.property(
			short_description=_('Home Share Path'),
			long_description=_('Path on the Home Share'),
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=['samba', 'posix', 'kerberos' ],
			required=0,
			dontsearch=1,
			may_change=1,
			identifies=0,
			default=('<username>', ['username']) # FIXME: should escape umlauts
		),
	'sambaUserWorkstations': univention.admin.property(
			short_description=_('Samba User Workstations'),
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
			syntax=univention.admin.syntax.sambaLogonHours,
			multivalue=0,
			options=['samba'],
			required=0,
			dontsearch=0,
			may_change=1,
			identifies=0,
		),
	'kolabForwardActive': univention.admin.property(
			short_description=_("Forward Mail"),
			long_description='',
			syntax=univention.admin.syntax.TrueFalseUp,
			multivalue=0,
			required=0,
			dontsearch=1,
			may_change=1,
			options=['groupware'],
			identifies=0
		),
	'kolabForwardAddress': univention.admin.property(
			short_description=_("Forward Address"),
			long_description='',
			syntax=univention.admin.syntax.emailAddress,
			multivalue=0,
			required=0,
			dontsearch=1,
			may_change=1,
			options=['groupware'],
			identifies=0
		),
	'kolabForwardKeepCopy': univention.admin.property(
			short_description=_("Forward Keep Copy"),
			long_description='',
			syntax=univention.admin.syntax.TrueFalseUp,
			multivalue=0,
			required=0,
			dontsearch=1,
			may_change=1,
			options=['groupware'],
			identifies=0
		),
	'kolabHomeServer': univention.admin.property(
			short_description=_("Kolab Home Server"),
			long_description='',
			syntax=univention.admin.syntax.kolabHomeServer,
			multivalue=0,
			required=1,
			dontsearch=1,
			may_change=1,
			options=['groupware'],
			identifies=0
		),
	'kolabForwardUCE': univention.admin.property(
			short_description=_("Forward Spam"),
			long_description='',
			syntax=univention.admin.syntax.TrueFalseUp,
			multivalue=0,
			required=0,
			dontsearch=1,
			may_change=1,
			options=['groupware'],
			identifies=0
		),
	'kolabDeliveryToFolderActive': univention.admin.property(
			short_description=_("Move incoming mails into a chosen folder"),
			long_description='',
			syntax=univention.admin.syntax.TrueFalseUp,
			multivalue=0,
			required=0,
			dontsearch=1,
			may_change=1,
			options=['groupware'],
			identifies=0
		),
	'kolabDeliveryToFolderName': univention.admin.property(
			short_description=_("Folder for incoming mail"),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			required=0,
			dontsearch=1,
			may_change=1,
			options=['groupware'],
			identifies=0
		),
	'kolabDelegate': univention.admin.property(
			short_description=_("E-mail addresses of delegate users"),
			long_description='',
			syntax=univention.admin.syntax.emailAddress,
			multivalue=1,
			required=0,
			dontsearch=1,
			may_change=1,
			options=['groupware'],
			identifies=0
		),
	'kolabVacationAddress': univention.admin.property(
			short_description=_("E-mail adresses for vacation notice"),
			long_description='',
			syntax=univention.admin.syntax.emailAddress,
			multivalue=1,
			required=0,
			dontsearch=1,
			may_change=1,
			options=['groupware'],
			identifies=0
		),
	'kolabVacationActive': univention.admin.property(
			short_description=_("Activate Vacation Notice"),
			long_description='',
			syntax=univention.admin.syntax.TrueFalseUp,
			multivalue=0,
			required=0,
			dontsearch=1,
			may_change=1,
			options=['groupware'],
			identifies=0
		),
	'kolabVacationText': univention.admin.property(
			short_description=_("Vacation Text"),
			long_description='',
			syntax=univention.admin.syntax.long_string,
			multivalue=0,
			required=0,
			dontsearch=1,
			may_change=1,
			options=['groupware'],
			identifies=0
		),
	'kolabVacationResendInterval':univention.admin.property(
			short_description=_("Vacation Notice Resend Interval"),
			long_description='',
			syntax=vacationResendDays,
			multivalue=0,
			required=0,
			dontsearch=1,
			may_change=1,
			options=['groupware'],
			identifies=0,
			default='7'
		),
	'kolabVacationReplyToUCE': univention.admin.property(
			short_description=_("Vacation Notice Spam Reply"),
			long_description='',
			syntax=univention.admin.syntax.TrueFalseUp,
			multivalue=0,
			required=0,
			dontsearch=1,
			may_change=1,
			options=['groupware'],
			identifies=0
		),
	'kolabVacationReactDomain': univention.admin.property(
			short_description=_("Vacation Notice To"),
			long_description=_( 'Contains a list of sender domains the vacation notice is send to.' ),
			syntax=univention.admin.syntax.string,
			multivalue=1,
			required=0,
			dontsearch=1,
			may_change=1,
			options=['groupware'],
			identifies=0
		),
	'kolabVacationNoReactDomain': univention.admin.property(
			short_description=_("No Vacation Notice To"),
			long_description=_('Contains a list of sender domains the vacation notice is not send to.'),
			syntax=univention.admin.syntax.string,
			multivalue=1,
			required=0,
			dontsearch=1,
			may_change=1,
			options=['groupware'],
			identifies=0
		),
	'kolabInvitationPolicy': univention.admin.property(
			short_description=_("Invitation Policy"),
			long_description='',
			syntax=univention.admin.syntax.kolabInvitationPolicy,
			multivalue=1,
			required=0,
			dontsearch=1,
			may_change=1,
			options=['groupware'],
			identifies=0
		),
	'kolabDisableSieve': univention.admin.property(
			short_description=_("Disable Kolab Sieve Scripts"),
			long_description='',
			syntax=univention.admin.syntax.TrueFalseUp,
			multivalue=0,
			required=0,
			dontsearch=1,
			may_change=1,
			options=['groupware'],
			identifies=0
		),
	'userCertificate': univention.admin.property(
			short_description=_("PKI User Certificate"),
			long_description=_( 'Public Key Infrastructure - User Certificate ' ),
			syntax=univention.admin.syntax.binaryfile,
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
	'filler': univention.admin.property(
			short_description='',
			long_description='',
			syntax=univention.admin.syntax.none,
			multivalue=0,
			required=0,
			may_change=1,
			identifies=0,
			dontsearch=1
		)
}

# append CTX properties
for key, value in mungeddial.properties.items():
	property_descriptions[ key ] = value

default_property_descriptions=copy.deepcopy(property_descriptions) # for later reset of descriptions

layout=[
	univention.admin.tab(_('General'),_('Basic Values'),[
		[univention.admin.field("username"), univention.admin.field("description",width=300)],
		[univention.admin.field("password"),
		 [univention.admin.field("overridePWHistory"), univention.admin.field("overridePWLength")]],
		[univention.admin.field("firstname"), univention.admin.field("lastname")],
		[univention.admin.field("title"), univention.admin.field("organisation")],
	]),
	univention.admin.tab(_('User Account'),_('Account Settings'),[
		[univention.admin.field("userexpiry"), univention.admin.field("passwordexpiry")],
		[univention.admin.field("disabled"), univention.admin.field("pwdChangeNextLogin")],
		[univention.admin.field("locked")],
	]),
	univention.admin.tab(_('Mail'),_('Mail Preferences'),[
		[univention.admin.field("mailPrimaryAddress")],
		[univention.admin.field("mailAlternativeAddress")],
		[univention.admin.field("mailGlobalSpamFolder")],
	]),
	univention.admin.tab(_('Contact'),_('Contact Information'),[
		[univention.admin.field("e-mail"), univention.admin.field("phone")],
		[univention.admin.field("street"), univention.admin.field("filler")],
		[univention.admin.field("postcode"), univention.admin.field("city")],
	]),
	univention.admin.tab(_('Organisation'),_('Organisational Information'),[
		[univention.admin.field("employeeNumber")],
		[univention.admin.field("employeeType")],
		[univention.admin.field("roomNumber")],
		[univention.admin.field("departmentNumber")],
		[univention.admin.field("secretary")]
	]),
	univention.admin.tab(_('Private Contact'),_('Private Contact Information'),[
		[univention.admin.field("mobileTelephoneNumber"), univention.admin.field("homeTelephoneNumber")],
		[univention.admin.field("pagerTelephoneNumber"),univention.admin.field("homePostalAddress")]
	]),
	univention.admin.tab(_('Linux/UNIX'),_('Unix Account Settings'), [
		[univention.admin.field("unixhome"), univention.admin.field("shell")],
		[univention.admin.field("uidNumber"), univention.admin.field("gidNumber")],
		[univention.admin.field("homeShare"), univention.admin.field("homeSharePath")],
		[univention.admin.field("gecos"),]
	]),
	univention.admin.tab(_('Windows'),_('Windows Account Settings'),[
		[univention.admin.field("sambahome"), univention.admin.field("homedrive")],
		[univention.admin.field("scriptpath"), univention.admin.field("profilepath")],
		[univention.admin.field("sambaRID")],
		[univention.admin.field("sambaLogonHours"), univention.admin.field("sambaUserWorkstations")]
	]),
	univention.admin.tab(_('Groups'),_('Group Memberships'), [
		[univention.admin.field("primaryGroup")],
		[univention.admin.field("groups")]
	]),
	univention.admin.tab(_('Vacation Notice'),_('Vacation Notice'), [
		[univention.admin.field('kolabVacationText'),
		 [univention.admin.field('kolabVacationActive'),
		  univention.admin.field('kolabVacationReplyToUCE'),
		  univention.admin.field('kolabVacationResendInterval'),]],
		[univention.admin.field('kolabVacationAddress')],
		[univention.admin.field('kolabVacationReactDomain'), univention.admin.field('kolabVacationNoReactDomain')]
	]),
	univention.admin.tab(_('Groupware'),_('Groupware Settings'), [
		[univention.admin.field('kolabHomeServer'), univention.admin.field('kolabDisableSieve')],
		[univention.admin.field('kolabForwardAddress'),
		 [univention.admin.field('kolabForwardActive'),
		  univention.admin.field('kolabForwardKeepCopy'),
		  univention.admin.field('kolabForwardUCE')],],
		[univention.admin.field("filler"), univention.admin.field("filler")],
		[univention.admin.field('kolabDeliveryToFolderName'), univention.admin.field('kolabDeliveryToFolderActive')],
		[univention.admin.field("filler"), univention.admin.field("filler")],
		[univention.admin.field('kolabDelegate')]
	]),
	univention.admin.tab(_('Invitation'),_('Invitation'), [
		[univention.admin.field('kolabInvitationPolicy')],
	]),
	univention.admin.tab(_('User Certificate'),_('User Certificate'), [
		[univention.admin.field("userCertificate")],
		[univention.admin.field('certificateSubjectCommonName'), univention.admin.field('certificateSubjectOrganisationalUnit')],
		[univention.admin.field('certificateSubjectOrganisation'), univention.admin.field('certificateSubjectLocation')],
		[univention.admin.field('certificateSubjectState'), univention.admin.field('certificateSubjectCountry')],
		[univention.admin.field('certificateSubjectMail'), ],
		[univention.admin.field('certificateIssuerCommonName'), univention.admin.field('certificateIssuerOrganisationalUnit')],
		[univention.admin.field('certificateIssuerOrganisation'), univention.admin.field('certificateIssuerLocation')],
		[univention.admin.field('certificateIssuerState'), univention.admin.field('certificateIssuerCountry')],
		[univention.admin.field('certificateIssuerMail'), ],
		[univention.admin.field('certificateDateNotBefore'), univention.admin.field('certificateDateNotAfter') ],
		[univention.admin.field('certificateVersion'), univention.admin.field('certificateSerial') ],
	]),
]

# append tab with CTX flags
layout.append( mungeddial.tab )

def posixDaysToDate(days):
	return time.strftime("%d.%m.%y",time.gmtime(long(days)*3600*24))

def sambaWorkstationsMap(workstations):
	univention.debug.debug(univention.debug.ADMIN, univention.debug.ALL, 'samba: sambaWorkstationMap: in=%s; out=%s' % (workstations,string.join(workstations, ',')))
	return string.join(workstations, ',')

def sambaWorkstationsUnmap(workstations):
	univention.debug.debug(univention.debug.ADMIN, univention.debug.ALL, 'samba: sambaWorkstationUnmap: in=%s; out=%s' % (workstations[0],string.split(workstations[0],',')))
	return string.split(workstations[0],',')

def logonHoursMap(logontimes):
	"converts the bitfield 001110010110...100 to the respective string"

	logontimes=logontimes[0:168]

	while len(logontimes)<168:
		logontimes=logontimes.join("1")

	# shift numbers to correspond to GMT
	logontimes=shift(logontimes, -GMTOffset()-1) # -1 needed for internal reasons

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

        return shift(newtime, GMTOffset()+1)	# +1 needed for internal reasons

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
	certificate=base64.encodestring(string.join(user_certificate))

	tempf=tempfile.mktemp()
	fh=open(tempf,'w')
	c='-----BEGIN CERTIFICATE-----\n%s-----END CERTIFICATE-----\n' % certificate
	fh.write(c)
	fh.close()

	x509 = X509.load_cert(tempf)
	os.unlink(tempf)
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
		return "%s.%s.%s" % (dl[1], dl[0], dl[3][-2:])

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

mapping=univention.admin.mapping.mapping()
mapping.register('title', 'title', None, univention.admin.mapping.ListToString)
mapping.register('description', 'description', None, univention.admin.mapping.ListToString)
mapping.register('organisation', 'o', None, univention.admin.mapping.ListToString)

mapping.register('mailPrimaryAddress', 'mailPrimaryAddress', None, univention.admin.mapping.ListToLowerString)
mapping.register('mailAlternativeAddress', 'mailAlternativeAddress', univention.admin.mapping.ListToLowerListUniq)
mapping.register('mailGlobalSpamFolder', 'mailGlobalSpamFolder', None, univention.admin.mapping.ListToString)

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
mapping.register('scriptpath', 'sambaLogonScript', None, univention.admin.mapping.ListToString)
mapping.register('profilepath', 'sambaProfilePath', None, univention.admin.mapping.ListToString)
mapping.register('homedrive', 'sambaHomeDrive', None, univention.admin.mapping.ListToString)
mapping.register('gecos', 'gecos', None, univention.admin.mapping.ListToString)

mapping.register('kolabHomeServer', 'kolabHomeServer', None, univention.admin.mapping.ListToString)
mapping.register('kolabForwardActive', 'univentionKolabForwardActive',  None, univention.admin.mapping.ListToString)
mapping.register('kolabForwardAddress', 'kolabForwardAddress', None, univention.admin.mapping.ListToString)
mapping.register('kolabForwardKeepCopy', 'kolabForwardKeepCopy', None, univention.admin.mapping.ListToString)
mapping.register('kolabForwardUCE', 'kolabForwardUCE', None, univention.admin.mapping.ListToString)
mapping.register('kolabDeliveryToFolderActive', 'univentionKolabDeliveryToFolderActive',  None, univention.admin.mapping.ListToString)
mapping.register('kolabDeliveryToFolderName', 'univentionKolabDeliveryToFolderName', None, univention.admin.mapping.ListToString)
mapping.register('kolabDelegate', 'kolabDelegate')
mapping.register('kolabVacationActive', 'univentionKolabVacationActive', None, univention.admin.mapping.ListToString)
mapping.register('kolabVacationText', 'univentionKolabVacationText', None, univention.admin.mapping.ListToString)
mapping.register('kolabVacationResendInterval', 'kolabVacationResendInterval', None, univention.admin.mapping.ListToString)
mapping.register('kolabVacationReplyToUCE', 'kolabVacationReplyToUCE', None, univention.admin.mapping.ListToString)
mapping.register('kolabVacationAddress', 'kolabVacationAddress')
mapping.register('kolabVacationReactDomain', 'kolabVacationReactDomain')
mapping.register('kolabVacationNoReactDomain', 'univentionKolabVacationNoReactDomain')
mapping.register('kolabDisableSieve', 'univentionKolabDisableSieve', None, univention.admin.mapping.ListToString)
mapping.register('kolabInvitationPolicy', 'kolabInvitationPolicy')
mapping.register('userCertificate', 'userCertificate;binary')

class object( univention.admin.handlers.simpleLdap, mungeddial.Support ):
	module=module

	def __pwd_is_disabled(self, password):
		if password.startswith('{crypt}!') or password.startswith('{LANMAN}!'):
			return True
		return False

	def __pwd_enable(self, password):
		if self.__pwd_is_disabled(password):
			if password.startswith("{crypt}!"):
				return password.replace("{crypt}!","{crypt}")
			elif password.startswith('{LANMAN}!'):
				return password.replace("{LANMAN}!","{LANMAN}")
		return password

	def __pwd_disable(self, password):
		if not self.__pwd_is_disabled(password):
			if password.startswith("{crypt}"):
				return password.replace("{crypt}","{crypt}!")
			elif password.startswith("{LANMAN}"):
				return password.replace("{LANMAN}","{LANMAN}!")
		return password

	def __init__(self, co, lo, position, dn='', superordinate=None, arg=None):
		global options
		global mapping
		global property_descriptions
		global default_property_descriptions

		self.co=co
		self.lo=lo
		self.dn=dn
		self.position=position
		self._exists=0
		self.mapping=mapping
		self.descriptions=property_descriptions
		self.kerberos_active=0
		self.pwhistory_active=0
		self.mail_active=0
		self.groupsLoaded=1

		self.password_length=8

		self.alloc=[]

		self.locked=0

		univention.admin.handlers.simpleLdap.__init__(self, co, lo, position, dn, superordinate)
		mungeddial.Support.__init__( self )

		searchResult = self.lo.search('(&(|(objectClass=univentionDomainController)(objectClass=univentionMemberServer))(univentionService=kolab2))', attr = ['aRecord'])
		if not [ dn for (dn, attr) in searchResult if attr.has_key('aRecord') ]:
			options['groupware'].default = False

		self.options=[]
		if self.oldattr.has_key('objectClass'):
			ocs = set(self.oldattr['objectClass'])
			for opt in ('posix', 'samba', 'person', 'kerberos', 'mail', 'groupware', 'pki'):
				if options[opt].matches(ocs):
					self.options.append(opt)
		else:
			univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'users/user.py: reset options to default by _define_options' )
			self._define_options( options )

		if 'posix' in self.options:

			# The shadowLastChange attribute is the amount of days between 1/1/1970 upto the day that password was modified,
			# shadowMax is the number of days a password is valid. So the password expires on 1/1/1970+shadowLastChange+shadowMax.
			# shadowExpire contains the absolute date to expire the account.

			if self.oldattr.has_key('shadowExpire') and len(self.oldattr['shadowExpire']) > 0 :
				self.info['userexpiry'] = posixDaysToDate(self.oldattr['shadowExpire'][0])
			if self.oldattr.has_key( 'shadowLastChange' ) and self.oldattr.has_key( 'shadowMax' ) and len(self.oldattr['shadowLastChange']) > 0 and len(self.oldattr['shadowMax']) > 0:
				try:
					self.info['passwordexpiry'] = posixDaysToDate(int(self.oldattr['shadowLastChange'][0]) +  int(self.oldattr['shadowMax'][0]))
				except:
					univention.debug.debug(univention.debug.ADMIN, univention.debug.WARN, 'users/user: failed to calculate password expiration correctly, use only shadowMax instead')
					self.info['passwordexpiry'] = posixDaysToDate(int(self.oldattr['shadowMax'][0]))

		elif 'kerberos' in self.options:
			if self.oldattr.has_key('krb5ValidEnd'):
				krb5validend=self.oldattr['krb5ValidEnd'][0]
				univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'krb5validend is: %s' %
						       krb5validend)
				self.info['userexpiry']="%s.%s.%s"%(krb5validend[6:8],krb5validend[4:6],krb5validend[2:4])
		elif 'samba' in self.options:
			if self.oldattr.has_key('sambaKickoffTime'):
				univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'sambaKickoffTime is: %s' %
						       self.oldattr['sambaKickoffTime'][0])
				self.info['userexpiry']=time.strftime("%d.%m.%y",time.gmtime(long(self.oldattr['sambaKickoffTime'][0])+(3600*24)))

		uid=self.oldattr.get('uid',[''])[0]
		if uid:
			try:
				s=self.descriptions['username'].syntax
				try:
					username_match=s.parse(uid)
				except univention.admin.uexceptions.valueError,e: # uid contains already umlauts, so we switch
					self.set_uid_umlauts()
				self['username']=uid
			# FIXME: we should NEVER catch all exceptions
			except Exception, e:
				self.dn=None
				return

		try:
			self['firstname']=self.oldattr.get('givenName',[''])[0]
			self['lastname']=self.oldattr.get('sn',[''])[0]
		except Exception, e:
			self.dn=None
			return

		self.save()

	def open(self, loadGroups=1):
		univention.admin.handlers.simpleLdap.open(self)

		self.newPrimaryGroupDn=0
		self.oldPrimaryGroupDn=0

		self.modifypassword=1

		self.save()

		if self.dn:
			is_disabled = 0
			self.modifypassword=0
			self['password']='********'
			if 'posix' in self.options or 'mail' in self.options:
				userPassword=self.oldattr.get('userPassword',[''])[0]
				if userPassword:
					self.info['password']=userPassword
					self.modifypassword=0
					if self.__pwd_is_disabled(userPassword):
						is_disabled += 1

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
							self['primaryGroup']=None
							self.save()
							raise univention.admin.uexceptions.primaryGroup
					else:
						self['primaryGroup']=None
						self.save()
						raise univention.admin.uexceptions.primaryGroup

					self.info['uidNumber'] = self.oldattr.get('uidNumber', [''])[0]
					self.info['gidNumber'] = self.oldattr.get('gidNumber', [''])[0]

			if self['passwordexpiry']:
				today=time.strftime('%d.%m.%y').split('.')
				expiry=self['passwordexpiry'].split('.')
				expiry.reverse()
				today.reverse()
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
							is_disabled += 1
					except KeyError:
						pass
					try:
						if acctFlags['L']  == 1:
							self['locked']="1"
					except KeyError:
						pass


			if 'kerberos' in self.options:
				kdcflags = self.oldattr.get('krb5KDCFlags', ['0'])[0]
				if kdcflags == '254':
					is_disabled += 1

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

			if is_disabled > 0:
				self['disabled'] = '1'
			else:
				self['disabled'] = '0'

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
		if 'groupware' in self.options and not self[ 'kolabHomeServer' ]:
			searchResult=self.lo.search( filter = '(objectClass=univentionDefault)', base = 'cn=univention,' + self.position.getDomain(),
					attr = [ 'univentionDefaultKolabHomeServer' ] )
			univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'DEFAULT KOLAB SERVER: %s' % str( searchResult ) )
			if searchResult and searchResult[ 0 ][ 1 ]:
				self[ 'kolabHomeServer' ] = searchResult[ 0 ][ 1 ][ 'univentionDefaultKolabHomeServer' ][ 0 ]

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

		if self.info.has_key('userCertificate') and len(self.info['userCertificate'][0]) > 0:
			values=load_certificate(self.info['userCertificate'])
			if not values:
				self.__certificate_clean()
			else:
				for i in values.keys():
					self.info[i]=values[i]
		else:
			self.__certificate_clean()

	def exists(self):
		return self._exists

	def hasChanged(self, key):
		if key == 'disabled':
			password  = self['password']
			acctFlags = univention.admin.samba.acctFlags(self.oldattr.get("sambaAcctFlags", [''])[0]).decode()
			krb5Flags = self.oldattr.get('krb5KDCFlags', [])
			if not password and not acctFlags and not krb5Flags:
				return False
			if self['disabled'] == '1':
				return not self.__pwd_is_disabled(password) or \
				       not 'D' in acctFlags or \
				       '126' in krb5Flags
			else:
				return self.__pwd_is_disabled(password) or \
				       'D' in acctFlags or \
				       '254' in krb5Flags
		return super(object, self).hasChanged(key)

	def __update_groups(self):
		if not self.groupsLoaded:
			return

		if self.exists():
			old_groups = self.oldinfo.get('groups', [])
		else:
			old_groups = []

		add_to_group=[]
		remove_from_group=[]

		def case_insensitive_in_list(dn, list):
			for element in list:
				if dn.lower() == element.lower():
					return True
			return False

		def case_insensitive_remove_from_list(dn, list):
			for element in list:
				if dn.lower() == element.lower():
					remove_element = element
			list.remove(remove_element)
			return list

		univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'users/user: check groups in old_groups')
		for group in old_groups:
			if group and not case_insensitive_in_list(group, self.info.get('groups', [])) and group.lower() != self['primaryGroup'].lower():
				remove_from_group.append(group)

		univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'users/user: check groups in info[groups]')
		for group in self.info.get('groups', []):
			if group and not case_insensitive_in_list(group, old_groups):
				add_to_group.append(group)

		univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'users/user: check primaryGroup')
		if self.newPrimaryGroupDn and not case_insensitive_in_list(self.newPrimaryGroupDn,add_to_group):
			add_to_group.append(self.newPrimaryGroupDn)

		for group in add_to_group:
			if type(group) == type([]):
				group=group[0]
			members=self.lo.getAttr(group, 'uniqueMember')
			if case_insensitive_in_list(self.dn, members):
				continue
			newmembers=copy.deepcopy(members)
			newmembers.append(self.dn)
			univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'users/user: add to group %s'%group)
			self.lo.modify(group, [('uniqueMember', members, newmembers)])
			self.__rewrite_member_uid( group, newmembers )

		for group in remove_from_group:
			if type(group) == type([]):
				group=group[0]
			members=self.lo.getAttr(group, 'uniqueMember')
			if not case_insensitive_in_list(self.dn, members):
				continue
			newmembers=copy.deepcopy(members)
			newmembers=case_insensitive_remove_from_list(self.dn, newmembers)
			univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'users/user: remove from group %s'%group)
			self.lo.modify(group, [('uniqueMember', members, newmembers)])
			self.__rewrite_member_uid( group, newmembers )

	def __rewrite_member_uid( self, group, members = [] ):
		uids = self.lo.getAttr( group, 'memberUid' )
		if not members:
			members = self.lo.getAttr( group, 'uniqueMember' )
		new = map( lambda x: x[ x.find( '=' ) + 1 : x.find( ',' ) ], members )
		self.lo.modify(group, [ ( 'memberUid', uids, new ) ] )
		
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

		def case_insensitive_in_list(dn, list):
			for element in list:
				if dn.lower() == element.lower():
					return True
			return False

		members=self.lo.getAttr(self.newPrimaryGroupDn, 'uniqueMember')
		if not  case_insensitive_in_list(self.dn, members):
			newmembers=copy.deepcopy(members)
			newmembers.append(self.dn)
			self.lo.modify(self.newPrimaryGroupDn, [('uniqueMember', members, newmembers)])
		self.save()

	def krb5_principal(self):
		if hasattr(self, '__krb5_principal'):
			return self.__krb5_principal
		elif self.oldattr.has_key('krb5PrincipalName'):
			self.__krb5_principal=self.oldattr['krb5PrincipalName'][0]
		else:
			domain=univention.admin.uldap.domain(self.lo, self.position)
			realm=domain.getKerberosRealm()
			self.__krb5_principal=self['username']+'@'+realm
		return self.__krb5_principal

	def set_uid_umlauts(self, umlauts=1):
		self.uid_umlauts=umlauts
		if umlauts:
			self.descriptions['username'] = univention.admin.property(
				short_description=_('Username'),
				long_description='',
				syntax=univention.admin.syntax.uid_umlauts,
				multivalue=0,
				required=1,
				may_change=1,
				identifies=1
				)
		else:
			self.descriptions['username'] = univention.admin.property(
				short_description=_('Username'),
				long_description='',
				syntax=univention.admin.syntax.uid,
				multivalue=0,
				required=1,
				may_change=1,
				identifies=1
				)


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

			if not ( 'posix' in self.options or 'samba' in self.options or 'person' in self.options):
				#no objectClass which provides uid...
				raise univention.admin.uexceptions.invalidOptions, _('Need one of %s, %s or %s in options to create user.')%(
					'posix',
					'samba',
					'person')

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
			except univention.admin.uexceptions.noLock, e:
				username=self['username']
				del(self.info['username'])
				self.oldinfo={}
				self.dn=None
				self._exists=0
				univention.admin.allocators.release(self.lo, self.position, 'uid', username)
				raise univention.admin.uexceptions.uidAlreadyUsed, ': %s' % username

			self.alloc.append(('uid', uid))

			if self['uidNumber']:
				self.alloc.append(('uidNumber', self['uidNumber']))
				self.uidNum = univention.admin.allocators.acquireUnique(self.lo, self.position, 'uidNumber', self['uidNumber'], 'uidNumber', scope='base')
			else:
				self.uidNum=univention.admin.allocators.request(self.lo, self.position, 'uidNumber')
				self.alloc.append(('uidNumber', self.uidNum))

			self.userSid=None
			if self.uidNum and 'samba' in self.options:

				if self['sambaRID']:
					searchResult=self.lo.search(filter='objectClass=sambaDomain', attr=['sambaSID'])
					domainsid=searchResult[0][1]['sambaSID'][0]
					sid = domainsid+'-'+self['sambaRID']
					self.userSid = univention.admin.allocators.request(self.lo, self.position, 'sid', sid)
					self.alloc.append(('sid', self.userSid))

				else:

					try:
						self.userSid=univention.admin.allocators.requestUserSid(self.lo, self.position, self.uidNum)
					except:
						pass
					if not self.userSid or self.userSid == 'None':
						num=self.uidNum
						while not self.userSid or self.userSid == 'None':
							num = str(int(num)+1)
							try:
								self.userSid=univention.admin.allocators.requestUserSid(self.lo, self.position, num)
							except univention.admin.uexceptions.noLock, e:
								num = str(int(num)+1)
						self.alloc.append(('sid', self.userSid))

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
			if 'groupware' in self.options:
				ocs.extend(['univentionKolabInetOrgPerson', 'kolabInetOrgPerson'])
			if 'samba' in self.options:
				ocs.extend(['sambaSamAccount'])
				al.append(('sambaSID', [self.userSid]))
				#('sambaAcctFlags', [acctFlags.decode()])
			if 'person' in self.options:
				ocs.extend(['organizationalPerson','inetOrgPerson'])
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
				univention.admin.allocators.release( self.lo, self.position, 'mailPrimaryAddress', self[ 'mailPrimaryAddress' ] )

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

		shadowLastChangeValue = ''	# if is filled, it will be added to ml in the end
		sambaPwdLastSetValue = ''	# if is filled, it will be added to ml in the end

		if self.options != self.old_options:
			univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'options: %s' % self.options)
			univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'old_options: %s' % self.old_options)
			if 'groupware' in self.options and not 'groupware' in self.old_options:
				univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'added groupware option')
				ocs=self.oldattr.get('objectClass', [])
				if not 'kolabInetOrgPerson' in ocs:
					ml.insert(0, ('objectClass', '', 'kolabInetOrgPerson'))
				if not 'univentionKolabInetOrgPerson' in ocs:
					ml.insert(0, ('objectClass', '', 'univentionKolabInetOrgPerson'))
			if not 'groupware' in self.options and 'groupware' in self.old_options:
				univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'remove groupware option')
				ocs=self.oldattr.get('objectClass', [])
				if 'kolabInetOrgPerson' in ocs:
					ml.insert(0, ('objectClass', 'kolabInetOrgPerson', ''))
				if 'univentionKolabInetOrgPerson' in ocs:
					ml.insert(0, ('objectClass', 'univentionKolabInetOrgPerson', ''))

				for key in [ 'kolabHomeServer', 'univentionKolabForwardActive', 'kolabForwardAddress', 'kolabForwardKeepCopy', 'kolabForwardUCE',\
							'univentionKolabDeliveryToFolderActive', 'univentionKolabDeliveryToFolderName', 'kolabDelegate', 'univentionKolabVacationActive', \
							'univentionKolabVacationText', 'kolabVacationResendInterval', 'kolabVacationReplyToUCE', 'kolabVacationAddress', \
							'kolabVacationReactDomain', 'univentionKolabVacationNoReactDomain', 'kolabInvitationPolicy', 'univentionKolabDisableSieve']:
					ml=self._remove_attr(ml,key)
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



		if  self.hasChanged(['firstname', 'lastname']):
			if self['firstname']:
				cn = "%s %s" % (self.info.get('firstname', ''), self.info.get('lastname', ''))
			else:
				cn = "%s" % self.info.get('lastname', '')
			ml.append(('cn', self.oldattr.get('cn', [''])[0], cn))
			ml.append(('sn', self.oldattr.get('cn', [''])[0], self['lastname']))
			if 'person' in self.options:
				ml.append(('displayName', self.oldattr.get('displayName', [''])[0], cn))
				ml.append(('givenName', self.oldattr.get('givenName', [''])[0], self['firstname']))

			if 'posix' in self.options:
				gecos = _default_gecos()
				if self.oldinfo.get( 'gecos', '' ):
					old_gecos = gecos( self, old_data = True )
					if old_gecos == self.oldinfo.get( 'gecos', '' ):
						ml.append( ( 'gecos', self.oldinfo.get( 'gecos', [ '' ] )[ 0 ], gecos( self ) ) )

		# shadowlastchange=self.oldattr.get('shadowLastChange',[str(long(time.time())/3600/24)])[0]

		pwd_change_next_login=0
		if self.hasChanged('pwdChangeNextLogin') and self['pwdChangeNextLogin'] == '1':
			pwd_change_next_login=1

		if self.modifypassword:
			# if the password is going to be changed in ldap and account is not disabled
			# check password-history
			ocs=self.oldattr.get('objectClass', [])
			if not 'univentionPWHistory' in ocs and not self.pwhistory_active:
				ml.insert(0, ('objectClass', '', 'univentionPWHistory'))

			pwhistory=self.oldattr.get('pwhistory',[''])[0]
			#read policy
			pwhistoryPolicy = self.loadPolicyObject('policies/pwhistory')
			if self["disabled"] != "1":
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
						raise univention.admin.uexceptions.pwToShort, _('The password is too short, at least %d characters!')% int(pwhistoryPolicy['pwLength'])
			else:
				if self['overridePWLength'] != '1':
					if len(self['password']) < self.password_length:
						for i,j in self.alloc:
							univention.admin.allocators.release(self.lo, self.position, i, j)
						raise univention.admin.uexceptions.pwToShort, _('The password is too short, at least %d character!') %self.password_length
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
				if 'samba' in self.options:
					if pwd_change_next_login == 1:
						sambaPwdMustChange="%d" % long(time.time())
						ml.append(("sambaPwdMustChange", "-1", sambaPwdMustChange))
					else:
						if expiryInterval==-1 or expiryInterval == 0:
							sambaPwdMustChange=''
						else:
							sambaPwdMustChange="%d" % long(time.time()+(expiryInterval*3600*24))
					univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'sambaPwdMustChange: %s' % sambaPwdMustChange)
					old_sambaPwdMustChange=self.oldattr.get('sambaPwdMustChange', '')
					if old_sambaPwdMustChange != sambaPwdMustChange:
						ml.append(('sambaPwdMustChange',self.oldattr.get('sambaPwdMustChange', [''])[0], sambaPwdMustChange))
				if 'kerberos' in self.options:
					if pwd_change_next_login == 1:
						expiry=time.strftime("%d.%m.%y",time.gmtime((long(time.time()))))
					else:
						if expiryInterval==-1 or expiryInterval == 0:
							expiry='0'
						else:
							expiry=time.strftime("%d.%m.%y",time.gmtime((long(time.time()) + (expiryInterval*3600*24))))
					if expiry == '0':
						krb5PasswordEnd='0'
					else:
						krb5PasswordEnd="%s" % "20"+expiry[6:8]+expiry[3:5]+expiry[0:2]+"000000Z"
					univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'krb5PasswordEnd: %s' % krb5PasswordEnd)
					old_krb5PasswordEnd=self.oldattr.get('krb5PasswordEnd', '')
					if old_krb5PasswordEnd != krb5PasswordEnd:
						ml.append(('krb5PasswordEnd',self.oldattr.get('krb5PasswordEnd', [''])[0], krb5PasswordEnd))
				if pwd_change_next_login == 1:
					pwd_change_next_login=0
			else:
				if 'posix' in self.options or 'mail' in self.options:
					ml.append(('shadowMax',self.oldattr.get('shadowMax', [''])[0], ''))
					shadowLastChangeValue = ''
				if 'samba' in self.options:
					old_sambaPwdMustChange=self.oldattr.get('sambaPwdMustChange', '')
					if old_sambaPwdMustChange:
						ml.append(('sambaPwdMustChange',self.oldattr.get('sambaPwdMustChange', [''])[0], ''))
				if 'kerberos' in self.options:
					old_krb5PasswordEnd=self.oldattr.get('krb5PasswordEnd', '')
					if old_krb5PasswordEnd:
						ml.append(('krb5PasswordEnd',old_krb5PasswordEnd, '0'))


			disabled=""
			acctFlags=univention.admin.samba.acctFlags(self.oldattr.get("sambaAcctFlags", [''])[0])
			krb_kdcflags='126'
			if self["disabled"] == "1":
				acctFlags.set('D')
				krb_kdcflags='254'
				disabled="!"

			#                             FIXME: required for join user root
			if 'posix' in self.options or ('samba' in self.options and self['username'] == 'root') or 'mail' in self.options:
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

		elif self.hasChanged('disabled') and self['disabled'] == "1":
			# disable password:
			#                             FIXME: required for join user root
			if 'posix' in self.options or ('samba' in self.options and self['username'] == 'root') or 'mail' in self.options:
				password_disabled = self.__pwd_disable(self['password'])
				ml.append(('userPassword', self.oldattr.get('userPassword', [''])[0], password_disabled))
			# disable samba account
			if 'samba' in self.options:
				acctFlags=univention.admin.samba.acctFlags(self.oldattr.get("sambaAcctFlags", [''])[0])
				acctFlags.set('D')
				ml.append(('sambaAcctFlags', self.oldattr.get('sambaAcctFlags', [''])[0], acctFlags.decode()))
			# disable kerberos account
			if 'kerberos' in self.options:
				krb_kdcflags='254'
				ml.append(('krb5KDCFlags', self.oldattr.get('krb5KDCFlags', ['']), krb_kdcflags))

		elif self.hasChanged('disabled') and self['disabled'] == "0":
			# enable password:
			#                             FIXME: required for join user root
			if 'posix' in self.options or ('samba' in self.options and self['username'] == 'root') or 'mail' in self.options:
				password_enabled = self.__pwd_enable(self['password'])
				ml.append(('userPassword', self.oldattr.get('userPassword', [''])[0], password_enabled))
			# enable samba account
			if 'samba' in self.options:
				acctFlags=univention.admin.samba.acctFlags(self.oldattr.get("sambaAcctFlags", [''])[0])
				acctFlags.unset('D')
				# lock account, if necessary (this is unset by removing flag D)
				if self['locked'] == "1":
					acctFlags.set("L")
				if str(self.oldattr.get('sambaAcctFlags', [''])[0]) != str(acctFlags.decode()):
					ml.append(('sambaAcctFlags', self.oldattr.get('sambaAcctFlags', [''])[0], acctFlags.decode()))
			# enable kerberos account
			if 'kerberos' in self.options:
				krb_kdcflags='126'
				ml.append(('krb5KDCFlags', self.oldattr.get('krb5KDCFlags', ['']), krb_kdcflags))
		elif self.hasChanged(['locked']) and self['locked'] == "1":
			# lock samba account
			acctFlags=univention.admin.samba.acctFlags(self.oldattr.get("sambaAcctFlags", [''])[0])
			acctFlags.set("L")
			ml.append(('sambaAcctFlags', self.oldattr.get('sambaAcctFlags', [''])[0], acctFlags.decode()))
		elif self.hasChanged(['locked']) and self['locked'] == "0":
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



		if pwd_change_next_login == 1:
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
				sambaPwdMustChange="%d" % long(time.time())
				ml.append(('sambaPwdCanChange', '-1', sambaPwdMustChange))
				univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'sambaPwdMustChange: %s' % sambaPwdMustChange)
				old_sambaPwdMustChange=self.oldattr.get('sambaPwdMustChange', '')
				if old_sambaPwdMustChange != sambaPwdMustChange:
					ml.append(('sambaPwdMustChange',self.oldattr.get('sambaPwdMustChange', [''])[0], sambaPwdMustChange))
				# set sambaPwdLastSet to 1, see UCS Bug #8292 and Samba Bug #4313
				sambaPwdLastSetValue='1'

			if 'kerberos' in self.options:
				expiry=time.strftime("%d.%m.%y",time.gmtime((long(time.time()))))
				krb5PasswordEnd="%s" % "20"+expiry[6:8]+expiry[3:5]+expiry[0:2]+"000000Z"
				univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'krb5PasswordEnd: %s' % krb5PasswordEnd)
				old_krb5PasswordEnd=self.oldattr.get('krb5PasswordEnd', '')
				if old_krb5PasswordEnd != krb5PasswordEnd:
					ml.append(('krb5PasswordEnd',self.oldattr.get('krb5PasswordEnd', [''])[0], krb5PasswordEnd))

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
			pass

		if sambaPwdLastSetValue:
			ml.append(('sambaPwdLastSet', self.oldattr.get('sambaPwdLastSet', [''])[0], sambaPwdLastSetValue))

		if shadowLastChangeValue:
			ml.append(('shadowLastChange',self.oldattr.get('shadowLastChange', [''])[0], shadowLastChangeValue))

		return ml

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
		_umlauts = { 'ä' :'ae', 'Ä' : 'Ae', 'ö' : 'oe', 'Ö' : 'Oe', 'ü' : 'ue', 'Ü' : 'Ue', 'ß' : 'ss' }
		for umlaut, code in _umlauts.items():
			gecos = gecos.replace( umlaut, code )

		return gecos

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
			for i in range(0, len(groupObjects)):
				groupObjects[i].open()
				if self.dn in groupObjects[i]['users']:
					groupObjects[i]['users'].remove(self.dn)
					groupObjects[i].modify(ignore_license=1)

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
		s = sha.new( newpassword.encode( 'utf-8' ) )
		newpwhash = string.upper(s.hexdigest())
		if not string.find(pwhistory, newpwhash) < 0:
			# password has already been used.
			return 1
		return 0

	def __getPWHistory(self, newpassword, pwhistory, pwhlen):
		# first calc hash for the new pw
		s = sha.new( newpassword.encode( 'utf-8' ) )
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
		pwdhash = md5.md5(salt + pwd).hexdigest().upper()
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
		filter.variable='krb5KDCFlags'
		if filter.value == '1':
			filter.value='254'
		else:
			filter.value='126'
	elif filter.variable == 'locked':
		filter.variable='sambaAcctFlags'
		if filter.value != '1':
			filter.operator='!='
		filter.value = '*L*'
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
	for dn in lo.searchDn(unicode(filter), base, scope, unique, required, timeout, sizelimit):
		res.append(object(co, lo, None, dn))
	return res

def identify(dn, attr, canonical=0):

	if type(attr.get('uid',[])) == type([]) and len(attr.get('uid',[]))>0 and ('$' in attr.get('uid',[])[0]):
		return False

	return ((('posixAccount' in attr.get('objectClass', [])
			  and 'shadowAccount' in attr.get('objectClass', []))
			 or 'univentionMail' in attr.get('objectClass', [])
			 or 'sambaSamAccount' in attr.get('objectClass', [])
			 or
			 ('person' in attr.get('objectClass', [])
			  and	'organizationalPerson' in attr.get('objectClass', [])
			  and 'inetOrgPerson' in attr.get('objectClass', [])))
			and not '0' in attr.get('uidNumber', [])
			and not '$' in attr.get('uid',[])
		        and not 'univentionHost' in attr.get('objectClass', [])
			)
