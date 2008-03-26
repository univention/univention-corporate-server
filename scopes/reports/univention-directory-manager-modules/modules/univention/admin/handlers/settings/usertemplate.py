# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin module for user template objects
#
# Copyright (C) 2002, 2003, 2004, 2005, 2006 Univention GmbH
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

import sys, string, time
import univention.admin.filter
import univention.admin.handlers
import univention.admin.localization
import univention.admin.mungeddial as mungeddial

translation=univention.admin.localization.translation('univention.admin.handlers.settings')
_=translation.translate

module='settings/usertemplate'
operations=['add','edit','remove','search','move']
superordinate='settings/cn'
childs=0
short_description=_('Settings: User Template')
long_description=''
options={
}
property_descriptions={
	'name': univention.admin.property(
			short_description=_('Name'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=[],
			required=1,
			may_change=1,
			identifies=1
		),
	'title': univention.admin.property(
			short_description=_('Title'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'description': univention.admin.property(
			short_description=_('Description'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'organisation': univention.admin.property(
			short_description=_('Organization'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'pwdChangeNextLogin': univention.admin.property(
			short_description=_('Change password on Next Login'),
			long_description=_('Change password on next login'),
			syntax=univention.admin.syntax.boolean,
			multivalue=0,
			options=[],
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
 			options=[],
 			required=0,
 			may_change=1,
 			identifies=0,
 			show_in_lists=1
 		),
	'e-mail': univention.admin.property(
			short_description=_('E-Mail Address'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0,
		),
	'unixhome': univention.admin.property(
			short_description=_('Unix Home Directory'),
			long_description='',
			syntax=univention.admin.syntax.absolutePath,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0,
			default=('/home/<username>', [])
		),
 	'homeShare': univention.admin.property(
 			short_description=_('Home Share'),
 			long_description=_('Share, the user\'s home directory resides on'),
 			syntax=univention.admin.syntax.module('shares/share'),
 			multivalue=0,
 			required=0,
 			dontsearch=1,
 			may_change=1,
 			identifies=0,
 		),
 	'homeSharePath': univention.admin.property(
 			short_description=_('Home Share Path'),
 			long_description=_('Path on the home share'),
 			syntax=univention.admin.syntax.string,
 			multivalue=0,
 			options=[],
 			required=0,
 			dontsearch=1,
 			may_change=1,
 			identifies=0,
 		),
	'shell': univention.admin.property(
			short_description=_('Login Shell'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=[],
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
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'scriptpath': univention.admin.property(
			short_description=_('Windows Script Path'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'profilepath': univention.admin.property(
			short_description=_('Windows Profile Path'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'homedrive': univention.admin.property(
			short_description=_('Windows Home Drive'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'street': univention.admin.property(
			short_description=_('Street'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'postcode': univention.admin.property(
			short_description=_('Postal Code'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'city': univention.admin.property(
			short_description=_('City'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'phone': univention.admin.property(
			short_description=_('Telephone Number'),
			long_description='',
			syntax=univention.admin.syntax.phone,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'secretary': univention.admin.property(
			short_description=_('Secretary'),
			long_description='',
			syntax=univention.admin.syntax.userDn,
			multivalue=1,
			options=[],
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
 	'groups': univention.admin.property(
 			short_description=_('Groups'),
 			long_description='',
 			syntax=univention.admin.syntax.groupDn,
 			multivalue=1,
 			options=[],
 			required=0,
 			may_change=1,
 			identifies=0
 		),
 	'primaryGroup': univention.admin.property(
 			short_description=_('Primary Group'),
 			long_description='',
 			syntax=univention.admin.syntax.primaryGroup,
 			one_only=1,
 			parent='groups',
 			multivalue=0,
 			options=[],
 			required=0,
 			dontsearch=1,
 			may_change=1,
 			identifies=0
 		),
	'mailPrimaryAddress': univention.admin.property(
			short_description=_('Primary E-Mail Address'),
			long_description='',
			syntax=univention.admin.syntax.emailAddressTemplate,
			multivalue=0,
			options=[],
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
			options=[],
			required=0,
			may_change=1,
			dontsearch=1,
			identifies=0
		),
	'mailAlternativeAddress': univention.admin.property(
			short_description=_('Alternative E-Mail Addresses'),
			long_description='',
			syntax=univention.admin.syntax.emailAddressTemplate,
			multivalue=1,
			options=[],
			required=0,
			dontsearch=0,
			may_change=1,
			identifies=0,
		),
	# Groupware settings
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
			required=0,
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
			short_description=_("Activate folderdelivery"),
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
			short_description=_("Deliver to Folder"),
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
			short_description=_("Delegates"),
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
			short_description=_("Vacation Address"),
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
			short_description=_("Activate Vacation"),
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
			short_description=_("Vacation Resend Interval"),
			long_description='',
			syntax=univention.admin.syntax.integer,
			multivalue=0,
			required=0,
			dontsearch=1,
			may_change=1,
			options=['groupware'],
			identifies=0
		),
	'kolabVacationReplyToUCE': univention.admin.property(
			short_description=_("Vacation Spam Reply"),
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
			short_description=_("React Domain"),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=1,
			required=0,
			dontsearch=1,
			may_change=1,
			options=['groupware'],
			identifies=0
		),
	'kolabVacationNoReactDomain': univention.admin.property(
			short_description=_("No React Domain"),
			long_description='',
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
	'_options': univention.admin.property(
			short_description=_('Options'),
			long_description='',
			syntax=univention.admin.syntax.optionsUsersUser,
			multivalue=1,
			required=0,
			dontsearch=1,
			may_change=1,
			identifies=0,
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

layout=[
	univention.admin.tab(_('General'),_('Basic Values'),[
		[univention.admin.field("name"),univention.admin.field("description")],
		[[univention.admin.field("title"),
		  univention.admin.field("organisation")],
		 univention.admin.field("_options")],
	]),
 	univention.admin.tab(_('User Account'),_('Account Settings'),[
	[univention.admin.field("disabled"),univention.admin.field("pwdChangeNextLogin")]
 	]),
	univention.admin.tab(_('Mail'),_('Mail Settings'),[
		[univention.admin.field("mailPrimaryAddress")],
		[univention.admin.field("mailAlternativeAddress")],
		[univention.admin.field("mailGlobalSpamFolder")],
	]),
	univention.admin.tab(_('User Contact'),_('Contact Information'),[
		[univention.admin.field("e-mail"), univention.admin.field("phone")],
		[univention.admin.field("street"),univention.admin.field("filler")],
		[univention.admin.field("postcode"),univention.admin.field("city")]
	]),
	univention.admin.tab(_('Employee'),_('Employee Information'),[
		[univention.admin.field("employeeType")],
		[univention.admin.field("departmentNumber")],
		[univention.admin.field("secretary")]
	]),
	univention.admin.tab(_('Linux'),_('Unix Account Settings'), [
		[univention.admin.field("unixhome"), univention.admin.field("shell")],
		[univention.admin.field("homeShare"), univention.admin.field("homeSharePath")]
	]),
	univention.admin.tab(_('Windows'),_('Windows Account Settings'),[
		[univention.admin.field("sambahome"), univention.admin.field("homedrive")],
		[univention.admin.field("scriptpath"), univention.admin.field("profilepath")]
	]),
	univention.admin.tab(_('Groups'),_('Group Memberships'), [
		[univention.admin.field("primaryGroup")],
		[univention.admin.field("groups")]
	]),
	univention.admin.tab(_('Vacation'),_('Vacation'), [
		[univention.admin.field('kolabVacationText'),
		 [univention.admin.field('kolabVacationActive'),
		  univention.admin.field('kolabVacationReplyToUCE'),
		  univention.admin.field('kolabVacationResendInterval'),]],
		[univention.admin.field('kolabVacationAddress')],
		[univention.admin.field('kolabVacationReactDomain'), univention.admin.field('kolabVacationNoReactDomain')]
	]),
	univention.admin.tab(_('Groupware'),_('Groupware Settings'), [
		[univention.admin.field('kolabHomeServer')],
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
]

# append tab with CTX flags
layout.append( mungeddial.tab )

mapping=univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('title', 'title', None, univention.admin.mapping.ListToString)
mapping.register('description', 'description', None, univention.admin.mapping.ListToString)
mapping.register('organisation', 'o', None, univention.admin.mapping.ListToString)
mapping.register('postcode', 'postalCode', None, univention.admin.mapping.ListToString)
mapping.register('userexpiry', 'shadowMax', None, univention.admin.mapping.ListToString)
mapping.register('passwordexpiry', 'shadowExpire', None, univention.admin.mapping.ListToString)
mapping.register('e-mail', 'mail')
mapping.register('unixhome', 'homeDirectory', None, univention.admin.mapping.ListToString)
mapping.register('shell', 'loginShell', None, univention.admin.mapping.ListToString)
mapping.register('sambahome', 'sambaHomePath', None, univention.admin.mapping.ListToString)
mapping.register('scriptpath', 'sambaLogonScript', None, univention.admin.mapping.ListToString)
mapping.register('profilepath', 'sambaProfilePath', None, univention.admin.mapping.ListToString)
mapping.register('homedrive', 'sambaHomeDrive', None, univention.admin.mapping.ListToString)
mapping.register('phone', 'telephoneNumber')
mapping.register('employeeType', 'employeeType', None, univention.admin.mapping.ListToString)
mapping.register('secretary', 'secretary')
mapping.register('street', 'street', None, univention.admin.mapping.ListToString)
mapping.register('postcode', 'postalCode', None, univention.admin.mapping.ListToString)
mapping.register('city', 'l', None, univention.admin.mapping.ListToString)
mapping.register('disabled','userDisabledPreset',None,univention.admin.mapping.ListToString)
mapping.register('pwdChangeNextLogin','userPwdMustChangePreset',None,univention.admin.mapping.ListToString)
mapping.register('homeShare','userHomeSharePreset',None,univention.admin.mapping.ListToString)
mapping.register('homeSharePath','userHomeSharePathPreset',None,univention.admin.mapping.ListToString)
mapping.register('primaryGroup','userPrimaryGroupPreset',None,univention.admin.mapping.ListToString)
mapping.register('groups','userGroupsPreset')
mapping.register('mailPrimaryAddress', 'mailPrimaryAddress', None, univention.admin.mapping.ListToString)
mapping.register('mailAlternativeAddress', 'mailAlternativeAddress')
mapping.register('mailGlobalSpamFolder', 'mailGlobalSpamFolder', None, univention.admin.mapping.ListToString)

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
mapping.register('kolabInvitationPolicy', 'kolabInvitationPolicy')

mapping.register('_options', 'userOptionsPreset')

class object( univention.admin.handlers.simpleLdap, mungeddial.Support ):
	module=module

	def __init__(self, co, lo, position, dn='', superordinate=None, arg=None):
		global mapping
		global property_descriptions

		self.co=co
		self.lo=lo
		self.dn=dn
		self.position=position
		self._exists=0
		self.mapping=mapping
		self.descriptions=property_descriptions

		univention.admin.handlers.simpleLdap.__init__(self, co, lo, position, dn, superordinate)
		mungeddial.Support.__init__( self )

	def exists(self):
		return self._exists

	def _ldap_pre_create(self):
		self.dn='%s=%s,%s' % (mapping.mapName('name'), mapping.mapValue('name', self.info['name']), self.position.getDn())

	def _ldap_addlist(self):
		return [ ('objectClass', ['top', 'univentionUserTemplate'] ) ]

	def _ldap_modlist(self):
		ml=univention.admin.handlers.simpleLdap._ldap_modlist(self)
		sambaMunged=self.sambaMungedDialMap()
		if sambaMunged:
			ml.append( ( 'sambaMungedDial', self.oldattr.get( 'sambaMungedDial', [ '' ] ), [ sambaMunged ] ) )

		return ml


	def open(self):
		univention.admin.handlers.simpleLdap.open(self)
		self.sambaMungedDialUnmap()
		self.sambaMungedDialParse()


def lookup(co, lo, filter_s, base='', superordinate=superordinate, scope='sub', unique=0, required=0, timeout=-1, sizelimit=0):

	filter=univention.admin.filter.conjunction('&', [
		univention.admin.filter.expression('objectClass', 'univentionUserTemplate' ) ] )

	if filter_s:
		filter_p=univention.admin.filter.parse(filter_s)
		univention.admin.filter.walk(filter_p, univention.admin.mapping.mapRewrite, arg=mapping)
		filter.expressions.append(filter_p)

	res=[]
	for dn in lo.searchDn(unicode(filter), base, scope, unique, required, timeout, sizelimit):
		res.append(object(co, lo, None, dn))
	return res

def identify(dn, attr, canonical=0):

	return 'univentionUserTemplate' in attr.get('objectClass', [])
