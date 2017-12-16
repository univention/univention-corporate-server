# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin module for user template objects
#
# Copyright 2002-2017 Univention GmbH
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

import copy

from univention.admin.layout import Tab, Group
import univention.admin.filter
import univention.admin.handlers
import univention.admin.localization
import univention.admin.mungeddial as mungeddial

translation = univention.admin.localization.translation('univention.admin.handlers.settings')
_ = translation.translate

module = 'settings/usertemplate'
operations = ['add', 'edit', 'remove', 'search', 'move']
superordinate = 'settings/cn'
childs = 0
short_description = _('Settings: User Template')
long_description = ''
options = {
	'default': univention.admin.option(
		default=True,
		objectClasses=['top', 'univentionUserTemplate'],
	),
}
property_descriptions = {
	'name': univention.admin.property(
		short_description=_('Template name'),
		long_description='',
		syntax=univention.admin.syntax.string,
		multivalue=False,
		include_in_default_search=True,
		required=True,
		may_change=True,
		identifies=True
	),
	'title': univention.admin.property(
		short_description=_('Title'),
		long_description='',
		syntax=univention.admin.syntax.string,
		multivalue=False,
		required=False,
		may_change=True,
		identifies=False
	),
	'description': univention.admin.property(
		short_description=_('Description'),
		long_description='',
		syntax=univention.admin.syntax.string,
		multivalue=False,
		include_in_default_search=True,
		required=False,
		may_change=True,
		identifies=False
	),
	'displayName': univention.admin.property(
		short_description=_('Display name'),
		long_description='',
		syntax=univention.admin.syntax.string,
		multivalue=False,
		required=False,
		may_change=True,
		default='<firstname> <lastname><:strip>',
		identifies=False
	),
	'organisation': univention.admin.property(
		short_description=_('Organisation'),
		long_description='',
		syntax=univention.admin.syntax.string,
		multivalue=False,
		required=False,
		may_change=True,
		identifies=False
	),
	'pwdChangeNextLogin': univention.admin.property(
		short_description=_('Change password on next login'),
		long_description=_('Change password on next login'),
		syntax=univention.admin.syntax.boolean,
		multivalue=False,
		required=False,
		may_change=True,
		dontsearch=True,
		identifies=False
	),
	'disabled': univention.admin.property(
		short_description=_('Account deactivation'),
		long_description='',
		syntax=univention.admin.syntax.boolean,
		multivalue=False,
		required=False,
		may_change=True,
		identifies=False,
		show_in_lists=True
	),
	'e-mail': univention.admin.property(
		short_description=_('E-mail address'),
		long_description='',
		syntax=univention.admin.syntax.string,
		multivalue=True,
		required=False,
		may_change=True,
		identifies=False,
	),
	'unixhome': univention.admin.property(
		short_description=_('Unix home directory'),
		long_description='',
		syntax=univention.admin.syntax.absolutePath,
		multivalue=False,
		required=False,
		may_change=True,
		identifies=False,
		default='/home/<username>',
	),
	'homeShare': univention.admin.property(
		short_description=_('Home share'),
		long_description=_('Share, the user\'s home directory resides on'),
		syntax=univention.admin.syntax.WritableShare,
		multivalue=False,
		required=False,
		dontsearch=True,
		may_change=True,
		identifies=False,
	),
	'homeSharePath': univention.admin.property(
		short_description=_('Home share path'),
		long_description=_('Path to the home directory on the home share'),
		syntax=univention.admin.syntax.string,
		multivalue=False,
		required=False,
		dontsearch=True,
		may_change=True,
		identifies=False,
	),
	'shell': univention.admin.property(
		short_description=_('Login shell'),
		long_description='',
		syntax=univention.admin.syntax.string,
		multivalue=False,
		required=False,
		may_change=True,
		identifies=False,
		default='/bin/bash'
	),
	'sambahome': univention.admin.property(
		short_description=_('Windows home path'),
		long_description='',
		syntax=univention.admin.syntax.string,
		multivalue=False,
		required=False,
		may_change=True,
		identifies=False
	),
	'scriptpath': univention.admin.property(
		short_description=_('Windows logon path'),
		long_description='',
		syntax=univention.admin.syntax.string,
		multivalue=False,
		required=False,
		may_change=True,
		identifies=False
	),
	'profilepath': univention.admin.property(
		short_description=_('Windows profile directory'),
		long_description='',
		syntax=univention.admin.syntax.string,
		multivalue=False,
		required=False,
		may_change=True,
		identifies=False
	),
	'homedrive': univention.admin.property(
		short_description=_('Windows home drive'),
		long_description='',
		syntax=univention.admin.syntax.string,
		multivalue=False,
		required=False,
		may_change=True,
		identifies=False
	),
	'street': univention.admin.property(
		short_description=_('Street'),
		long_description='',
		syntax=univention.admin.syntax.string,
		multivalue=False,
		required=False,
		may_change=True,
		identifies=False
	),
	'postcode': univention.admin.property(
		short_description=_('Postal code'),
		long_description='',
		syntax=univention.admin.syntax.OneThirdString,
		multivalue=False,
		required=False,
		may_change=True,
		identifies=False
	),
	'city': univention.admin.property(
		short_description=_('City'),
		long_description='',
		syntax=univention.admin.syntax.TwoThirdsString,
		multivalue=False,
		required=False,
		may_change=True,
		identifies=False
	),
	'country': univention.admin.property(
		short_description=_('Country'),
		long_description='',
		syntax=univention.admin.syntax.Country,
		multivalue=False,
		required=False,
		may_change=True,
		identifies=False,
	),
	'phone': univention.admin.property(
		short_description=_('Telephone number'),
		long_description='',
		syntax=univention.admin.syntax.phone,
		multivalue=True,
		required=False,
		may_change=True,
		identifies=False
	),
	'employeeNumber': univention.admin.property(
		short_description=_('Employee number'),
		long_description='',
		syntax=univention.admin.syntax.string,
		multivalue=False,
		required=False,
		may_change=True,
		identifies=False,
	),
	'roomNumber': univention.admin.property(
		short_description=_('Room number'),
		long_description='',
		syntax=univention.admin.syntax.OneThirdString,
		multivalue=False,
		required=False,
		may_change=True,
		identifies=False,
	),
	'secretary': univention.admin.property(
		short_description=_('Superior'),
		long_description='',
		syntax=univention.admin.syntax.UserDN,
		multivalue=True,
		required=False,
		may_change=True,
		identifies=False
	),
	'departmentNumber': univention.admin.property(
		short_description=_('Department number'),
		long_description='',
		syntax=univention.admin.syntax.OneThirdString,
		multivalue=False,
		required=False,
		may_change=True,
		identifies=False
	),
	'employeeType': univention.admin.property(
		short_description=_('Employee type'),
		long_description='',
		syntax=univention.admin.syntax.string,
		multivalue=False,
		required=False,
		may_change=True,
		identifies=False
	),
	'groups': univention.admin.property(
		short_description=_('Groups'),
		long_description='',
		syntax=univention.admin.syntax.GroupDN,
		multivalue=True,
		required=False,
		may_change=True,
		identifies=False
	),
	'primaryGroup': univention.admin.property(
		short_description=_('Primary group'),
		long_description='',
		syntax=univention.admin.syntax.GroupDN,
		one_only=True,
		parent='groups',
		multivalue=False,
		required=False,
		dontsearch=True,
		may_change=True,
		identifies=False
	),
	'mailPrimaryAddress': univention.admin.property(
		short_description=_('Primary e-mail address'),
		long_description='',
		syntax=univention.admin.syntax.emailAddressTemplate,
		multivalue=False,
		required=False,
		dontsearch=False,
		may_change=True,
		identifies=False,
	),
	'mailAlternativeAddress': univention.admin.property(
		short_description=_('Alternative e-mail address'),
		long_description='',
		syntax=univention.admin.syntax.emailAddressTemplate,
		multivalue=True,
		required=False,
		dontsearch=False,
		may_change=True,
		identifies=False,
	),
	'_options': univention.admin.property(
		short_description=_('Options'),
		long_description='',
		syntax=univention.admin.syntax.optionsUsersUser,
		multivalue=True,
		required=False,
		dontsearch=True,
		may_change=True,
		identifies=False,
	),
}

# append CTX properties
for key, value in mungeddial.properties.items():
	property_descriptions[key] = copy.deepcopy(value)
	property_descriptions[key].options = []

layout = [
	Tab(_('General'), _('Basic values'), layout=[
		Group(_('General user template settings'), layout=[
			"name",
			["_options"],
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
			"secretary"
		]),
	]),
	Tab(_('Groups'), _('Group Memberships'), layout=[
		Group(_('Groups'), layout=[
			["primaryGroup"],
			["groups"]
		]),
	]),
	Tab(_('Account'), _('Account settings'), layout=[
		Group(_('Locking and deactivation'), layout=[
			["disabled", "pwdChangeNextLogin"]
		]),
		Group(_('Windows'), _('Windows Account Settings'), layout=[
			['homedrive', 'sambahome'],
			["scriptpath", "profilepath"]
		]),
		Group(_('POSIX (Linux/UNIX)'), _('POSIX (Linux/UNIX) account settings'), layout=[
			["unixhome", "shell"],
			["homeShare", "homeSharePath"]
		]),
	]),
	Tab(_('Contact'), _('Contact Information'), layout=[
		Group(_('Business'), layout=[
			"e-mail",
			"phone",
			['roomNumber', 'departmentNumber'],
			['street', 'postcode', 'city', 'country'],
		]),
	]),
]

# append tab with CTX flags
layout.append(mungeddial.tab)

mapping = univention.admin.mapping.mapping()
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
mapping.register('country', 'st', None, univention.admin.mapping.ListToString)
mapping.register('phone', 'telephoneNumber')
mapping.register('roomNumber', 'roomNumber', None, univention.admin.mapping.ListToString)
mapping.register('employeeNumber', 'employeeNumber', None, univention.admin.mapping.ListToString)
mapping.register('employeeType', 'employeeType', None, univention.admin.mapping.ListToString)
mapping.register('secretary', 'secretary')
mapping.register('departmentNumber', 'departmentNumber', None, univention.admin.mapping.ListToString)
mapping.register('street', 'street', None, univention.admin.mapping.ListToString)
mapping.register('city', 'l', None, univention.admin.mapping.ListToString)
mapping.register('disabled', 'userDisabledPreset', None, univention.admin.mapping.ListToString)
mapping.register('pwdChangeNextLogin', 'userPwdMustChangePreset', None, univention.admin.mapping.ListToString)
mapping.register('homeShare', 'userHomeSharePreset', None, univention.admin.mapping.ListToString)
mapping.register('homeSharePath', 'userHomeSharePathPreset', None, univention.admin.mapping.ListToString)
mapping.register('primaryGroup', 'userPrimaryGroupPreset', None, univention.admin.mapping.ListToString)
mapping.register('groups', 'userGroupsPreset')
mapping.register('mailPrimaryAddress', 'mailPrimaryAddress', None, univention.admin.mapping.ListToLowerString)
mapping.register('mailAlternativeAddress', 'mailAlternativeAddress')


mapping.register('_options', 'userOptionsPreset')


class object(univention.admin.handlers.simpleLdap, mungeddial.Support):
	module = module

	def __init__(self, co, lo, position, dn='', superordinate=None, attributes=[]):
		univention.admin.handlers.simpleLdap.__init__(self, co, lo, position, dn, superordinate, attributes=attributes)
		mungeddial.Support.__init__(self)

	def _ldap_modlist(self):
		ml = univention.admin.handlers.simpleLdap._ldap_modlist(self)
		sambaMunged = self.sambaMungedDialMap()
		if sambaMunged:
			ml.append(('sambaMungedDial', self.oldattr.get('sambaMungedDial', ['']), [sambaMunged]))

		return ml

	def open(self):
		univention.admin.handlers.simpleLdap.open(self)
		self.sambaMungedDialUnmap()
		self.sambaMungedDialParse()


def lookup(co, lo, filter_s, base='', superordinate=superordinate, scope='sub', unique=False, required=False, timeout=-1, sizelimit=0):
	filter = univention.admin.filter.conjunction('&', [
		univention.admin.filter.expression('objectClass', 'univentionUserTemplate')])

	if filter_s:
		filter_p = univention.admin.filter.parse(filter_s)
		univention.admin.filter.walk(filter_p, univention.admin.mapping.mapRewrite, arg=mapping)
		filter.expressions.append(filter_p)

	res = []
	for dn, attrs in lo.search(unicode(filter), base, scope, [], unique, required, timeout, sizelimit):
		res.append(object(co, lo, None, dn, attributes=attrs))
	return res


def identify(dn, attr, canonical=0):
	return 'univentionUserTemplate' in attr.get('objectClass', [])
