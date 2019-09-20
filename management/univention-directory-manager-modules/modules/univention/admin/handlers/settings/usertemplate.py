# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin module for user template objects
#
# Copyright 2002-2019 Univention GmbH
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

from univention.admin.layout import Tab, Group
import univention.admin.filter
import univention.admin.handlers
import univention.admin.localization

translation = univention.admin.localization.translation('univention.admin.handlers.settings')
_ = translation.translate

module = 'settings/usertemplate'
operations = ['add', 'edit', 'remove', 'search', 'move']
superordinate = 'settings/cn'
childs = 0
short_description = _('Settings: User Template')
object_name = _('User Template')
object_name_plural = _('User Templates')
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
		include_in_default_search=True,
		required=True,
		identifies=True
	),
	'title': univention.admin.property(
		short_description=_('Title'),
		long_description='',
		syntax=univention.admin.syntax.string,
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
	),
	'displayName': univention.admin.property(
		short_description=_('Display name'),
		long_description='',
		syntax=univention.admin.syntax.string,
		default='<firstname> <lastname><:strip>',
	),
	'organisation': univention.admin.property(
		short_description=_('Organisation'),
		long_description='',
		syntax=univention.admin.syntax.string,
	),
	'pwdChangeNextLogin': univention.admin.property(
		short_description=_('Change password on next login'),
		long_description=_('Change password on next login'),
		syntax=univention.admin.syntax.boolean,
		dontsearch=True,
	),
	'disabled': univention.admin.property(
		short_description=_('Account deactivation'),
		long_description='',
		syntax=univention.admin.syntax.boolean,
		show_in_lists=True
	),
	'e-mail': univention.admin.property(
		short_description=_('E-mail address'),
		long_description='',
		syntax=univention.admin.syntax.string,
		multivalue=True,
	),
	'unixhome': univention.admin.property(
		short_description=_('Unix home directory'),
		long_description='',
		syntax=univention.admin.syntax.absolutePath,
		default='/home/<username>',
	),
	'homeShare': univention.admin.property(
		short_description=_('Home share'),
		long_description=_('Share, the user\'s home directory resides on'),
		syntax=univention.admin.syntax.WritableShare,
		dontsearch=True,
	),
	'homeSharePath': univention.admin.property(
		short_description=_('Home share path'),
		long_description=_('Path to the home directory on the home share'),
		syntax=univention.admin.syntax.string,
		dontsearch=True,
	),
	'shell': univention.admin.property(
		short_description=_('Login shell'),
		long_description='',
		syntax=univention.admin.syntax.string,
		default='/bin/bash'
	),
	'sambahome': univention.admin.property(
		short_description=_('Windows home path'),
		long_description='',
		syntax=univention.admin.syntax.string,
	),
	'scriptpath': univention.admin.property(
		short_description=_('Windows logon path'),
		long_description='',
		syntax=univention.admin.syntax.string,
	),
	'profilepath': univention.admin.property(
		short_description=_('Windows profile directory'),
		long_description='',
		syntax=univention.admin.syntax.string,
	),
	'homedrive': univention.admin.property(
		short_description=_('Windows home drive'),
		long_description='',
		syntax=univention.admin.syntax.string,
	),
	'street': univention.admin.property(
		short_description=_('Street'),
		long_description='',
		syntax=univention.admin.syntax.string,
	),
	'postcode': univention.admin.property(
		short_description=_('Postal code'),
		long_description='',
		syntax=univention.admin.syntax.OneThirdString,
	),
	'city': univention.admin.property(
		short_description=_('City'),
		long_description='',
		syntax=univention.admin.syntax.TwoThirdsString,
	),
	'country': univention.admin.property(
		short_description=_('Country'),
		long_description='',
		syntax=univention.admin.syntax.Country,
	),
	'phone': univention.admin.property(
		short_description=_('Telephone number'),
		long_description='',
		syntax=univention.admin.syntax.phone,
		multivalue=True,
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
	),
	'secretary': univention.admin.property(
		short_description=_('Superior'),
		long_description='',
		syntax=univention.admin.syntax.UserDN,
		multivalue=True,
	),
	'departmentNumber': univention.admin.property(
		short_description=_('Department number'),
		long_description='',
		syntax=univention.admin.syntax.OneThirdString,
		multivalue=True,
	),
	'employeeType': univention.admin.property(
		short_description=_('Employee type'),
		long_description='',
		syntax=univention.admin.syntax.string,
	),
	'groups': univention.admin.property(
		short_description=_('Groups'),
		long_description='',
		syntax=univention.admin.syntax.GroupDN,
		multivalue=True,
	),
	'primaryGroup': univention.admin.property(
		short_description=_('Primary group'),
		long_description='',
		syntax=univention.admin.syntax.GroupDN,
		one_only=True,
		parent='groups',
		dontsearch=True,
	),
	'mailPrimaryAddress': univention.admin.property(
		short_description=_('Primary e-mail address'),
		long_description='',
		syntax=univention.admin.syntax.emailAddressTemplate,
	),
	'mailAlternativeAddress': univention.admin.property(
		short_description=_('Alternative e-mail address'),
		long_description='',
		syntax=univention.admin.syntax.emailAddressTemplate,
		multivalue=True,
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
		Group(_('Windows'), layout=[
			['homedrive', 'sambahome'],
			["scriptpath", "profilepath"]
		]),
		Group(_('POSIX (Linux/UNIX)'), layout=[
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

mapping = univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('title', 'title', None, univention.admin.mapping.ListToString)
#mapping.register('initials', 'initials', None, univention.admin.mapping.ListToString)
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
mapping.register('roomNumber', 'roomNumber')
mapping.register('employeeNumber', 'employeeNumber', None, univention.admin.mapping.ListToString)
mapping.register('employeeType', 'employeeType', None, univention.admin.mapping.ListToString)
mapping.register('secretary', 'secretary')
mapping.register('departmentNumber', 'departmentNumber')
mapping.register('street', 'street', None, univention.admin.mapping.ListToString)
mapping.register('city', 'l', None, univention.admin.mapping.ListToString)
mapping.register('disabled', 'userDisabledPreset', None, univention.admin.mapping.ListToString)
mapping.register('pwdChangeNextLogin', 'userPwdMustChangePreset', None, univention.admin.mapping.ListToString)
mapping.register('homeShare', 'userHomeSharePreset', None, univention.admin.mapping.ListToString)
mapping.register('homeSharePath', 'userHomeSharePathPreset', None, univention.admin.mapping.ListToString)
mapping.register('primaryGroup', 'userPrimaryGroupPreset', None, univention.admin.mapping.ListToString)
mapping.register('groups', 'userGroupsPreset')
mapping.register('mailPrimaryAddress', 'mailPrimaryAddress', None, univention.admin.mapping.ListToLowerString)
#mapping.register('physicalDeliveryOfficeName', 'physicalDeliveryOfficeName', None, univention.admin.mapping.ListToString)
#mapping.register('preferredLanguage', 'preferredLanguage', None, univention.admin.mapping.ListToString)
#mapping.register('postOfficeBox', 'postOfficeBox')
mapping.register('mailAlternativeAddress', 'mailAlternativeAddress')
mapping.register('_options', 'userOptionsPreset')


class object(univention.admin.handlers.simpleLdap):
	module = module

	def __init__(self, co, lo, position, dn='', superordinate=None, attributes=[]):
		super(object, self).__init__(co, lo, position, dn, superordinate, attributes=attributes)
		univention.admin.syntax.optionsUsersUser.update_choices()  # woraround: somehow init() didn't do it
		self.options.extend(self['_options'])

	def _ldap_pre_modify(self):
		super(object, self)._ldap_pre_modify()
		self['_options'].extend(self.options)
		self['_options'] = list(set(self['_options']) - {'default', })

	def _ldap_pre_create(self):
		super(object, self)._ldap_pre_create()
		self['_options'].extend(self.options)
		self['_options'] = list(set(self['_options']) - {'default', })


lookup = object.lookup
identify = object.identify
