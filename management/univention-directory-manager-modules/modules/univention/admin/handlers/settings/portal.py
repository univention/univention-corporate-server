# -*- coding: utf-8 -*-
#
# Univention Directory Manager Modules
#  direcory manager module for Univention Portal
#
# Copyright 2017-2018 Univention GmbH
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

from ldap.filter import filter_format

from univention.admin.layout import Tab, Group
import univention.admin.filter
import univention.admin.localization

translation = univention.admin.localization.translation('univention.admin.handlers.settings')
_ = translation.translate

OC = "univentionPortal"

module = 'settings/portal'
superordinate = 'settings/cn'
default_containers = ['cn=portal,cn=univention']
childs = False
operations = ['add', 'edit', 'remove', 'search', 'move']
short_description = _('Portal: Portal')
long_description = _('Object that feeds everything in https://fqdn/univention/portal')
options = {
	'default': univention.admin.option(
		default=True,
		objectClasses=['top', OC],
	),
}
property_descriptions = {
	'name': univention.admin.property(
		short_description=_('Internal name'),
		long_description='',
		syntax=univention.admin.syntax.string_numbers_letters_dots,
		multivalue=False,
		include_in_default_search=True,
		options=[],
		required=True,
		may_change=False,
		identifies=True
	),
	'displayName': univention.admin.property(
		short_description=_('Display Name'),
		long_description=_('Headline of the portal. At least one entry; strongly encouraged to have one for en_US'),
		syntax=univention.admin.syntax.LocalizedDisplayName,
		multivalue=True,
		options=[],
		required=True,
		may_change=True,
		identifies=False
	),
	'showMenu': univention.admin.property(
		short_description=_('Show menu'),
		long_description='',
		syntax=univention.admin.syntax.TrueFalseUp,
		default='TRUE',
		multivalue=False,
		options=[],
		required=False,
		may_change=True,
		identifies=False
	),
	'showSearch': univention.admin.property(
		short_description=_('Show search'),
		long_description='',
		syntax=univention.admin.syntax.TrueFalseUp,
		default='TRUE',
		multivalue=False,
		options=[],
		required=False,
		may_change=True,
		identifies=False
	),
	'showLogin': univention.admin.property(
		short_description=_('Show login'),
		long_description='',
		syntax=univention.admin.syntax.TrueFalseUp,
		default='TRUE',
		multivalue=False,
		options=[],
		required=False,
		may_change=True,
		identifies=False
	),
	'showApps': univention.admin.property(
		short_description=_('Show apps'),
		long_description=_('Shows links to locally installed Apps'),
		syntax=univention.admin.syntax.TrueFalseUp,
		default='TRUE',
		multivalue=False,
		options=[],
		required=False,
		may_change=True,
		identifies=False
	),
	'showServers': univention.admin.property(
		short_description=_('Show servers'),
		long_description=_('Shows links to all UCS servers'),
		syntax=univention.admin.syntax.TrueFalseUp,
		default='TRUE',
		multivalue=False,
		options=[],
		required=False,
		may_change=True,
		identifies=False
	),
	'background': univention.admin.property(
		short_description=_('Background'),
		long_description=_('Background image of the Portal'),
		syntax=univention.admin.syntax.Base64BaseUpload,
		multivalue=False,
		dontsearch=True,
		options=[],
		required=False,
		may_change=True,
		identifies=False
	),
	'logo': univention.admin.property(
		short_description=_('Portal logo'),
		long_description=_('Logo image for the portal.'),
		syntax=univention.admin.syntax.Base64BaseUpload,
		multivalue=False,
		dontsearch=True,
		options=[],
		required=False,
		may_change=True,
		identifies=False
	),
	'cssBackground': univention.admin.property(
		short_description=_('CSS background'),
		long_description=_("Style definition for the CSS 'background' property which will be applied to the portal page, e.g. linear-gradient(black, white)"),
		syntax=univention.admin.syntax.TwoString,
		multivalue=False,
		dontsearch=True,
		options=[],
		required=False,
		may_change=True,
		identifies=False
	),
	'fontColor': univention.admin.property(
		short_description=_('Font color'),
		long_description=_('Defines the color which is used for the fonts on the portal page as well as the icons in the header.'),
		syntax=univention.admin.syntax.PortalFontColor,
		default='black',
		multivalue=False,
		dontsearch=True,
		options=[],
		required=False,
		may_change=True,
		identifies=False
	),
	'portalComputers': univention.admin.property(
		short_description=_('Show on server'),
		long_description=_('This portal will be used as start site for the given server'),
		syntax=univention.admin.syntax.PortalComputer,
		multivalue=True,
		dontsearch=True,
		options=[],
		required=False,
		may_change=True,
		identifies=False
	),
	'portalEntriesOrder': univention.admin.property(
		short_description=_('Portal entries order'),
		long_description=_('The order in which the portal entries are shown on this portal'),
		syntax=univention.admin.syntax.PortalEntries,
		multivalue=True,
		options=[],
		required=False,
		may_change=True,
		identifies=False
	),
}

layout = [
	Tab(_('General'), _('Portal options'), layout=[
		Group(_('Name'), layout=[
			["name"],
			["displayName"],
		]),
		Group(_('Visibility'), layout=[
			["portalComputers"],
		]),
		Group(_('Appearance'), layout=[
			["logo"],
			["background"],
			["cssBackground"],
			["fontColor"],
		]),
		Group(_('General Content'), layout=[
			# ["showMenu"],
			# ["showSearch"],
			# ["showLogin"],
			["showApps"],
			# ["showServers"],
		]),
	]),
]


def mapTranslationValue(vals):
	ret = []
	for val in vals:
		ret.append('%s %s' % (val[0], val[1]))
	return ret


def unmapTranslationValue(vals):
	ret = []
	for val in vals:
		ret.append(val.split(' ', 1))
	return ret


mapping = univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('displayName', 'univentionPortalDisplayName', mapTranslationValue, unmapTranslationValue)
mapping.register('showMenu', 'univentionPortalShowMenu', None, univention.admin.mapping.ListToString)
mapping.register('showSearch', 'univentionPortalShowSearch', None, univention.admin.mapping.ListToString)
mapping.register('showLogin', 'univentionPortalShowLogin', None, univention.admin.mapping.ListToString)
mapping.register('showApps', 'univentionPortalShowApps', None, univention.admin.mapping.ListToString)
mapping.register('showServers', 'univentionPortalShowServers', None, univention.admin.mapping.ListToString)
mapping.register('background', 'univentionPortalBackground', None, univention.admin.mapping.ListToString)
mapping.register('cssBackground', 'univentionPortalCSSBackground', None, univention.admin.mapping.ListToString)
mapping.register('fontColor', 'univentionPortalFontColor', None, univention.admin.mapping.ListToString)
mapping.register('logo', 'univentionPortalLogo', None, univention.admin.mapping.ListToString)
mapping.register('portalEntriesOrder', 'univentionPortalEntriesOrder')


class object(univention.admin.handlers.simpleLdap):
	module = module

	def open(self):
		super(object, self).open()
		self['portalComputers'] = self.lo.searchDn(filter=filter_format('(&(objectClass=univentionPortalComputer)(univentionComputerPortal=%s))', [self.dn]))
		self.save()

	def _ldap_addlist(self):
		ocs = ['top', OC]

		return [
			('objectClass', ocs),
		]

	def _ldap_post_create(self):
		self.__update_portal_computers()

	def _ldap_post_modify(self):
		self.__update_portal_computers()

	def __update_portal_computers(self):
		if self.exists():
			# case coming from _ldap_post_modify
			old_portal_computers = self.oldinfo.get('portalComputers', [])
		else:
			# case coming from _ldap_post_create
			old_portal_computers = []
		new_portal_computers = self.info.get('portalComputers', [])

		# set portal attribute of old computers to blank
		for computer in old_portal_computers:
			if computer not in new_portal_computers:
				try:
					compobj = univention.admin.modules.lookup('computers/computer', None, self.lo, scope='base', base=computer)[0]
					# initialize module of the computer obj for extended attributes
					compmod = univention.admin.modules.get(compobj.module)
					if not compmod.initialized:
						univention.admin.modules.init(self.lo, self.position, compmod)
				except univention.admin.uexceptions.noObject:
					continue
				compobj.open()
				compobj['portal'] = ''
				compobj.modify()

		# set portal attribute of new computers to this portal
		for computer in new_portal_computers:
			if computer not in old_portal_computers:
				try:
					compobj = univention.admin.modules.lookup('computers/computer', None, self.lo, scope='base', base=computer)[0]
					# initialize module of the computer obj for extended attributes
					compmod = univention.admin.modules.get(compobj.module)
					if not compmod.initialized:
						univention.admin.modules.init(self.lo, self.position, compmod)
				except univention.admin.uexceptions.noObject:
					continue
				compobj.open()
				compobj['portal'] = self.dn
				compobj.modify()

	def _ldap_post_remove(self):
		for obj in univention.admin.modules.lookup('settings/portal_entry', None, self.lo, scope='sub', filter=filter_format('portal=%s', [self.dn])):
			obj.open()
			obj['portal'] = [x for x in obj.info.get('portal', []) if not self.lo.compare_dn(x, self.dn)]
			obj.modify()

	def _ldap_post_move(self, olddn):
		for obj in univention.admin.modules.lookup('settings/portal_entry', None, self.lo, scope='sub', filter=filter_format('portal=%s', [olddn])):
			obj.open()
			obj['portal'] = [x for x in obj.info.get('portal', []) + [self.dn] if not self.lo.compare_dn(x, olddn)]
			obj.modify()

	@classmethod
	def unmapped_lookup_filter(cls):
		return univention.admin.filter.conjunction('&', [
			univention.admin.filter.expression('objectClass', OC),
		])


lookup = object.lookup


def identify(dn, attr, canonical=0):
	return OC in attr.get('objectClass', [])
