# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin module for mailinglists
#
# Copyright 2004-2017 Univention GmbH
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
import univention.admin.allocators
import univention.admin.localization

translation = univention.admin.localization.translation('univention.admin.handlers.mail')
_ = translation.translate

module = 'mail/lists'
operations = ['add', 'edit', 'remove', 'search', 'move']
childs = 0
short_description = _('Mailing list')
long_description = ''

module_search_filter = univention.admin.filter.expression('objectClass', 'univentionMailList'),

options = {
	'default': univention.admin.option(
		default=True,
		objectClasses=['top', 'univentionMailList'],
	),
}
property_descriptions = {
	'name': univention.admin.property(
		short_description=_('Name'),
		long_description='',
		syntax=univention.admin.syntax.gid,
		multivalue=False,
		include_in_default_search=True,
		required=True,
		may_change=True,
		identifies=True
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
	'members': univention.admin.property(
		short_description=_('Members'),
		long_description='',
		syntax=univention.admin.syntax.emailAddress,
		multivalue=True,
		required=False,
		may_change=True,
		dontsearch=True,
		identifies=False
	),
	'mailAddress': univention.admin.property(
		short_description=_('Mail address'),
		long_description='',
		syntax=univention.admin.syntax.emailAddressValidDomain,
		multivalue=False,
		include_in_default_search=True,
		required=False,
		may_change=True,
		dontsearch=False,
		identifies=False
	),
	'allowedEmailUsers': univention.admin.property(
		short_description=_('Users that are allowed to send e-mails to the list'),
		long_description='',
		syntax=univention.admin.syntax.UserDN,
		multivalue=True,
		required=False,
		may_change=True,
		dontsearch=True,
		identifies=False
	),
	'allowedEmailGroups': univention.admin.property(
		short_description=_('Groups that are allowed to send e-mails to the list'),
		long_description='',
		syntax=univention.admin.syntax.GroupDN,
		multivalue=True,
		required=False,
		may_change=True,
		dontsearch=True,
		identifies=False
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


class object(univention.admin.handlers.simpleLdap):
	module = module

	def open(self):
		univention.admin.handlers.simpleLdap.open(self)

		self['allowedEmailUsers'] = self.oldattr.get('univentionAllowedEmailUsers', [])
		self['allowedEmailGroups'] = self.oldattr.get('univentionAllowedEmailGroups', [])

		self.save()

	def _ldap_post_create(self):
		if self['mailAddress']:
			univention.admin.allocators.confirm(self.lo, self.position, 'mailPrimaryAddress', self['mailAddress'])

	def _ldap_post_modify(self):
		if self['mailAddress'] and self.hasChanged('mailAddress'):
			univention.admin.allocators.confirm(self.lo, self.position, 'mailPrimaryAddress', self['mailAddress'])

	def _ldap_addlist(self):
		al = []
		# mail address MUST be unique
		if self['mailAddress']:
			try:
				self.alloc.append(('mailPrimaryAddress', self['mailAddress']))
				univention.admin.allocators.request(self.lo, self.position, 'mailPrimaryAddress', value=self['mailAddress'])
			except:
				univention.admin.allocators.release(self.lo, self.position, 'mailPrimaryAddress', value=self['mailAddress'])
				raise univention.admin.uexceptions.mailAddressUsed

		return al

	def _ldap_modlist(self):
		if self.hasChanged('mailAddress') and self['mailAddress']:
			for i, j in self.alloc:
				if i == 'mailPrimaryAddress':
					break
			else:
				try:
					univention.admin.allocators.request(self.lo, self.position, 'mailPrimaryAddress', value=self['mailAddress'])
				except:
					univention.admin.allocators.release(self.lo, self.position, 'mailPrimaryAddress', value=self['mailAddress'])
					raise univention.admin.uexceptions.mailAddressUsed

		ml = univention.admin.handlers.simpleLdap._ldap_modlist(self)

		oldEmailUsers = self.oldinfo.get('allowedEmailUsers', [])
		newEmailUsers = self.info.get('allowedEmailUsers', [])
		if oldEmailUsers != newEmailUsers:
			ml.append(('univentionAllowedEmailUsers', oldEmailUsers, newEmailUsers))

		oldEmailGroups = self.oldinfo.get('allowedEmailGroups', [])
		newEmailGroups = self.info.get('allowedEmailGroups', [])
		if oldEmailGroups != newEmailGroups:
			ml.append(('univentionAllowedEmailGroups', oldEmailGroups, newEmailGroups))

		return ml


def lookup(co, lo, filter_s, base='', superordinate=None, scope='sub', unique=False, required=False, timeout=-1, sizelimit=0):

	filter = univention.admin.filter.conjunction('&', [
		univention.admin.filter.expression('objectClass', 'univentionMailList')
	])

	if filter_s:
		filter_p = univention.admin.filter.parse(filter_s)
		univention.admin.filter.walk(filter_p, univention.admin.mapping.mapRewrite, arg=mapping)
		filter.expressions.append(filter_p)

	res = []
	for dn, attrs in lo.search(unicode(filter), base, scope, [], unique, required, timeout, sizelimit):
		res.append(object(co, lo, None, dn, attributes=attrs))
	return res


def identify(dn, attr, canonical=0):

	return 'univentionMailList' in attr.get('objectClass', [])
