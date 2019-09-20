# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin module for syntax objects
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

from univention.admin.layout import Tab, Group
import univention.admin.filter
import univention.admin.handlers
import univention.admin.password
import univention.admin.allocators
import univention.admin.localization

translation = univention.admin.localization.translation('univention.admin.handlers.settings')
_ = translation.translate

module = 'settings/syntax'
superordinate = 'settings/cn'
childs = 0
operations = ['add', 'edit', 'remove', 'search', 'move']
short_description = _('Settings: Syntax Definition')
object_name = _('Syntax Definition')
object_name_plural = _('Syntax Definitions')
long_description = ''
options = {
	'default': univention.admin.option(
		default=True,
		objectClasses=['top', 'univentionSyntax'],
	),
}
property_descriptions = {
	'name': univention.admin.property(
		short_description=_('Syntax Name'),
		long_description='',
		syntax=univention.admin.syntax.string,
		include_in_default_search=True,
		required=True,
		identifies=True
	),
	'description': univention.admin.property(
		short_description=_('Syntax Description'),
		long_description='',
		syntax=univention.admin.syntax.string,
		include_in_default_search=True,
	),
	'filter': univention.admin.property(
		short_description=_('LDAP Search Filter'),
		long_description='',
		syntax=univention.admin.syntax.string,
		required=True,
	),
	'base': univention.admin.property(
		short_description=_('LDAP Base'),
		long_description='',
		syntax=univention.admin.syntax.ldapDn,
	),
	'attribute': univention.admin.property(
		short_description=_('Displayed Attributes'),
		long_description='',
		# syntax = univention.admin.syntax.UDM_PropertySelect,
		syntax=univention.admin.syntax.listAttributes,
		multivalue=True,
		include_in_default_search=True,
	),
	'ldapattribute': univention.admin.property(
		short_description=_('Displayed LDAP Attributes'),
		long_description='',
		syntax=univention.admin.syntax.string,
		multivalue=True,
	),
	'viewonly': univention.admin.property(
		short_description=_('Show Only'),
		long_description='',
		syntax=univention.admin.syntax.TrueFalseUp,
	),
	'addEmptyValue': univention.admin.property(
		short_description=_('Add an empty value to choice list'),
		long_description='',
		syntax=univention.admin.syntax.TrueFalseUp,
	),
	'value': univention.admin.property(
		short_description=_('Stored Attribute'),
		long_description='',
		# syntax = univention.admin.syntax.UDM_PropertySelect,
		syntax=univention.admin.syntax.listAttributes,
		include_in_default_search=True,
	),
	'ldapvalue': univention.admin.property(
		short_description=_('Stored LDAP Attribute'),
		long_description='',
		syntax=univention.admin.syntax.string,
	),
}

layout = [
	Tab(_('General'), _('Basic values'), layout=[
		Group(_('General syntax definition settings'), layout=[
			["name", "description"],
			["filter", "base"]]),
		Group(_('Display'), layout=[
			"attribute",
			"ldapattribute"]),
		Group(_('Storage'), layout=[
			"value",
			"ldapvalue"]),
		Group(_('Options'), layout=[
			"viewonly",
			"addEmptyValue"])
	]),
]


mapping = univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('filter', 'univentionSyntaxLDAPFilter', None, univention.admin.mapping.ListToString)
mapping.register('base', 'univentionSyntaxLDAPBase', None, univention.admin.mapping.ListToString)
mapping.register('viewonly', 'univentionSyntaxViewOnly', None, univention.admin.mapping.ListToString)
mapping.register('description', 'univentionSyntaxDescription', None, univention.admin.mapping.ListToString)
mapping.register('addEmptyValue', 'univentionSyntaxAddEmptyValue', None, univention.admin.mapping.ListToString)


class object(univention.admin.handlers.simpleLdap):
	module = module

	def __check(self):
		if self.info.get('viewonly', 'FALSE') == 'FALSE' and not (self['value'] or self['ldapvalue']):
			raise univention.admin.uexceptions.insufficientInformation(_('An LDAP attribute is required of which the information will be stored.'))

	def open(self):
		univention.admin.handlers.simpleLdap.open(self)
		if self.exists():
			# initialize items
			self['attribute'] = []
			self['ldapattribute'] = []
			self['value'] = ''
			self['ldapvalue'] = ''

			# split ldap attribute value into two parts and add them to separate dir manager widgets
			for item in self.oldattr.get('univentionSyntaxLDAPAttribute', []):
				if ':' in item:
					self['attribute'].append(item)
				else:
					self['ldapattribute'].append(item)

			# set attribute name of value that shall be written to LDAP
			# WARNING: drop down box is only used if string is not set
			val = self.oldattr.get('univentionSyntaxLDAPValue', '')
			if isinstance(val, (list, tuple)):
				val = val[0]
			if val and ':' in val:
				self['value'] = val
			else:
				self['ldapvalue'] = val

	def _ldap_pre_create(self):
		self.__check()
		super(object, self)._ldap_pre_create()

	def _ldap_pre_modify(self):
		self.__check()

	def _ldap_modlist(self):
		ml = univention.admin.handlers.simpleLdap._ldap_modlist(self)

		attr = self['attribute']
		attr.extend(self['ldapattribute'])
		ml.append(('univentionSyntaxLDAPAttribute', self.oldattr.get('univentionSyntaxLDAPAttribute', []), attr))

		vallist = [self['value']]
		if self['ldapvalue']:
			vallist = [self['ldapvalue']]
		ml.append(('univentionSyntaxLDAPValue', self.oldattr.get('univentionSyntaxLDAPValue', []), vallist))

		return ml


lookup = object.lookup
identify = object.identify
