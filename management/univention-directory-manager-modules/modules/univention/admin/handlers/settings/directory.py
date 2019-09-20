# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin module for default directories
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

import ldap

from univention.admin.layout import Tab, Group
import univention.admin.filter
import univention.admin.handlers
import univention.admin.password
import univention.admin.localization

translation = univention.admin.localization.translation('univention.admin.handlers.settings')
_ = translation.translate


def plusBase(object, arg):
	return [arg + ',' + object.position.getDomain()]


module = 'settings/directory'
superordinate = 'settings/cn'
childs = 0
operations = ['search', 'edit']
short_description = _('Preferences: Default Container')
object_name = _('Default container')
object_name_plural = _('Default containers')
long_description = ''
options = {
	'default': univention.admin.option(
		default=True,
		objectClasses=['top', 'univentionDirectory'],
	),
}
property_descriptions = {
	'name': univention.admin.property(
		short_description=_('Name'),
		long_description='',
		syntax=univention.admin.syntax.string,
		include_in_default_search=True,
		required=True,
		may_change=False,
		identifies=True,
		default=('directory', [])
	),
	'policies': univention.admin.property(
		short_description=_('Policy Link'),
		long_description='',
		syntax=univention.admin.syntax.ldapDn,
		multivalue=True,
	),
	'dns': univention.admin.property(
		short_description=_('DNS Link'),
		long_description='',
		syntax=univention.admin.syntax.ldapDn,
		multivalue=True,
	),
	'dhcp': univention.admin.property(
		short_description=_('DHCP Link'),
		long_description='',
		syntax=univention.admin.syntax.ldapDn,
		multivalue=True,
	),
	'users': univention.admin.property(
		short_description=_('User Link'),
		long_description='',
		syntax=univention.admin.syntax.ldapDn,
		multivalue=True,
	),
	'groups': univention.admin.property(
		short_description=_('Group Link'),
		long_description='',
		syntax=univention.admin.syntax.ldapDn,
		multivalue=True,
	),
	'computers': univention.admin.property(
		short_description=_('Computer Link'),
		long_description='',
		syntax=univention.admin.syntax.ldapDn,
		multivalue=True,
	),
	'domaincontroller': univention.admin.property(
		short_description=_('Domaincontroller Computer Link'),
		long_description='',
		syntax=univention.admin.syntax.ldapDn,
		multivalue=True,
	),
	'networks': univention.admin.property(
		short_description=_('Network Link'),
		long_description='',
		syntax=univention.admin.syntax.ldapDn,
		multivalue=True,
	),
	'shares': univention.admin.property(
		short_description=_('Share Link'),
		long_description='',
		syntax=univention.admin.syntax.ldapDn,
		multivalue=True,
	),
	'printers': univention.admin.property(
		short_description=_('Printer Link'),
		long_description='',
		syntax=univention.admin.syntax.ldapDn,
		multivalue=True,
	),
	'mail': univention.admin.property(
		short_description=_('Mail Link'),
		long_description='',
		syntax=univention.admin.syntax.ldapDn,
		multivalue=True,
	),
	'license': univention.admin.property(
		short_description=_('License Link'),
		long_description='',
		syntax=univention.admin.syntax.ldapDn,
		multivalue=True,
	)
}

layout = [
	Tab(_('General'), _('Basic values'), layout=[
		Group(_('Default container description'), layout=[
			"name"
		]),
		Group(_('User Links'), layout=[
			"users"
		]),
		Group(_('Group Links'), layout=[
			"groups"
		]),
		Group(_('Computer Links'), layout=[
			"computers",
		]),
		Group(_('Domaincontroller Computer Links'), layout=[
			"domaincontroller",
		]),
		Group(_('Policy Links'), layout=[
			"policies",
		]),
		Group(_('DNS Links'), layout=[
			"dns",
		]),
		Group(_('DHCP Links'), layout=[
			"dhcp",
		]),
		Group(_('Network Links'), layout=[
			"networks",
		]),
		Group(_('Shares Links'), layout=[
			"shares",
		]),
		Group(_('Printers Links'), layout=[
			"printers",
		]),
		Group(_('Mail Links'), layout=[
			"mail",
		]),
		Group(_('License Links'), layout=[
			"license",
		]),
	]),
]

mapping = univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('policies', 'univentionPolicyObject')
mapping.register('dns', 'univentionDnsObject')
mapping.register('dhcp', 'univentionDhcpObject')
mapping.register('users', 'univentionUsersObject')
mapping.register('groups', 'univentionGroupsObject')
mapping.register('computers', 'univentionComputersObject')
mapping.register('domaincontroller', 'univentionDomainControllerComputersObject')
mapping.register('networks', 'univentionNetworksObject')
mapping.register('shares', 'univentionSharesObject')
mapping.register('printers', 'univentionPrintersObject')
mapping.register('mail', 'univentionMailObject')
mapping.register('license', 'univentionLicenseObject')


class object(univention.admin.handlers.simpleLdap):
	module = module

	def _ldap_dn(self):
		dn = ldap.dn.str2dn(super(object, self)._ldap_dn())
		return '%s,cn=univention,%s' % (ldap.dn.dn2str(dn[0]), self.position.getDomain())


lookup = object.lookup
identify = object.identify
