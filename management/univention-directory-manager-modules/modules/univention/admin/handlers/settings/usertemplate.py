# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin module for user template objects
#
# Copyright 2002-2011 Univention GmbH
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

from univention.admin.layout import Tab, Group
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
			default = '/home/<username>',
		),
 	'homeShare': univention.admin.property(
 			short_description=_('Home Share'),
 			long_description=_('Share, the user\'s home directory resides on'),
 			syntax = univention.admin.syntax.WritableShare,
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
			default = '/bin/bash'
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
			syntax=univention.admin.syntax.UserDN,
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
 			syntax=univention.admin.syntax.GroupDN,
 			multivalue=1,
 			options=[],
 			required=0,
 			may_change=1,
 			identifies=0
 		),
 	'primaryGroup': univention.admin.property(
 			short_description=_('Primary Group'),
 			long_description='',
 			syntax=univention.admin.syntax.GroupDN,
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
}

# append CTX properties
for key, value in mungeddial.properties.items():
	property_descriptions[ key ] = value

layout = [
	Tab(_('General'),_('Basic Values'), layout = [
		Group( _( 'General' ), layout = [
			[ "name","description" ],
			[  "title", "organisation" ],
			[  "displayName" ],
			[ "_options" ],
		] ),
	] ),
 	Tab(_('User Account'),_('Account Settings'), layout = [
		Group( _( 'User Account' ), layout = [
			[ "disabled", "pwdChangeNextLogin" ]
		] ),
	] ),
	Tab(_('Mail'),_('Mail Settings'), layout = [
		Group( _( 'Mail' ), layout = [
			"mailPrimaryAddress",
			"mailAlternativeAddress",
		] ),
	] ),
	Tab(_('User Contact'),_('Contact Information'), layout = [
		Group( _( 'User Contact' ), layout = [
			[ "e-mail", "phone" ],
			"street",
			[ "postcode","city" ]
		] ),
	] ),
	Tab(_('Employee'),_('Employee Information'), layout = [
		Group( _( 'Employee' ), layout = [
			"employeeType",
			"departmentNumber",
			"secretary"
		] ),
	] ),
	Tab(_('Linux'),_('Unix Account Settings'), layout = [
		Group( _( 'Linux' ), layout = [
			["unixhome", "shell"],
			["homeShare", "homeSharePath"]
		] ),
	] ),
	Tab(_('Windows'),_('Windows Account Settings'), layout = [
		Group( _( 'Windows' ), layout = [
			["sambahome", "homedrive"],
			["scriptpath", "profilepath"]
		] ),
	] ),
	Tab(_('Groups'),_('Group Memberships'), layout = [
		Group( _( 'Groups' ), layout = [
			["primaryGroup"],
			["groups"]
		] ),
	] ),
	]

# append tab with CTX flags
layout.append( mungeddial.tab )

mapping=univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('title', 'title', None, univention.admin.mapping.ListToString)
mapping.register('description', 'description', None, univention.admin.mapping.ListToString)
mapping.register('organisation', 'o', None, univention.admin.mapping.ListToString)
mapping.register('displayName', 'displayName', None, univention.admin.mapping.ListToString)
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


mapping.register('_options', 'userOptionsPreset')

class object( univention.admin.handlers.simpleLdap, mungeddial.Support ):
	module=module

	def __init__(self, co, lo, position, dn='', superordinate=None, attributes = [] ):
		global mapping
		global property_descriptions

		self.mapping=mapping
		self.descriptions=property_descriptions

		univention.admin.handlers.simpleLdap.__init__(self, co, lo, position, dn, superordinate, attributes = attributes )
		mungeddial.Support.__init__( self )

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
	for dn, attrs in lo.search(unicode(filter), base, scope, [], unique, required, timeout, sizelimit):
		res.append( object( co, lo, None, dn, attributes = attrs ) )
	return res

def identify(dn, attr, canonical=0):

	return 'univentionUserTemplate' in attr.get('objectClass', [])
