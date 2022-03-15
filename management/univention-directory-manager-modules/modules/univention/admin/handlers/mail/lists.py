# -*- coding: utf-8 -*-
#
# Copyright 2004-2022 Univention GmbH
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
|UDM| module for mailinglists
"""

from univention.admin.layout import Tab, Group
import univention.admin.filter
import univention.admin.handlers
import univention.admin.allocators
import univention.admin.localization

translation = univention.admin.localization.translation('univention.admin.handlers.mail')
_ = translation.translate

module = 'mail/lists'
operations = ['add', 'edit', 'remove', 'search', 'move']
childs = False
short_description = _('Mailing list')
object_name = _('Mailing list')
object_name_plural = _('Mailing lists')
long_description = ''

module_search_filter = univention.admin.filter.expression('objectClass', 'univentionMailList'),

options = {
	'default': univention.admin.option(
		short_description=short_description,
		default=True,
		objectClasses=['top', 'univentionMailList'],
	),
}
property_descriptions = {
	'name': univention.admin.property(
		short_description=_('Name'),
		long_description='',
		syntax=univention.admin.syntax.mailinglist_name,
		include_in_default_search=True,
		required=True,
		identifies=True
	),
	'description': univention.admin.property(
		short_description=_('Description'),
		long_description='',
		syntax=univention.admin.syntax.string,
		include_in_default_search=True,
	),
	'members': univention.admin.property(
		short_description=_('Members'),
		long_description='',
		syntax=univention.admin.syntax.emailAddress,
		multivalue=True,
		dontsearch=True,
	),
	'mailAddress': univention.admin.property(
		short_description=_('Mail address'),
		long_description='',
		syntax=univention.admin.syntax.emailAddressValidDomain,
		include_in_default_search=True,
	),
	'allowedEmailUsers': univention.admin.property(
		short_description=_('Users that are allowed to send e-mails to the list'),
		long_description='',
		syntax=univention.admin.syntax.UserDN,
		multivalue=True,
		dontsearch=True,
	),
	'allowedEmailGroups': univention.admin.property(
		short_description=_('Groups that are allowed to send e-mails to the list'),
		long_description='',
		syntax=univention.admin.syntax.GroupDN,
		multivalue=True,
		dontsearch=True,
	)
}

layout = [
	Tab(_('General'), _('Basic settings'), layout=[
		Group(_('General mailing list settings'), layout=[
			["name", "description"],
			"mailAddress",
			"members"
		]),
	]),
	Tab(_('Authorized users'), _('Users that are allowed to send e-mails to the list'), advanced=True, layout=[
		"allowedEmailUsers"
	]),
	Tab(_('Authorized groups'), _('Groups that are allowed to send e-mails to the list'), advanced=True, layout=[
		"allowedEmailGroups"
	])
]

mapping = univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('description', 'description', None, univention.admin.mapping.ListToString)
mapping.register('members', 'univentionMailMember')
mapping.register('mailAddress', 'mailPrimaryAddress', None, univention.admin.mapping.ListToString)
mapping.register('allowedEmailUsers', 'univentionAllowedEmailUsers')
mapping.register('allowedEmailGroups', 'univentionAllowedEmailGroups')


class object(univention.admin.handlers.simpleLdap):
	module = module

	def _ldap_pre_ready(self):
		super(object, self)._ldap_pre_ready()
		if not self.exists() or self.hasChanged('mailAddress'):
			try:
				if self['mailAddress'] and self['mailAddress'].lower() != self.oldinfo.get('mailAddress', '').lower():
					self.request_lock('mailPrimaryAddress', self['mailAddress'])
			except univention.admin.uexceptions.noLock:
				raise univention.admin.uexceptions.mailAddressUsed(self['mailAddress'])

	def _ldap_pre_remove(self):
		super(object, self)._ldap_pre_remove()
		if self.oldattr.get('mailPrimaryAddress'):
			self.alloc.append(('mailPrimaryAddress', self.oldattr['mailPrimaryAddress'][0].decode('UTF-8')))


lookup = object.lookup
identify = object.identify
