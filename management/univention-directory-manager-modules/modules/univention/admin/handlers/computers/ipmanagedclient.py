# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin module for the ip managed clients
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
import univention.admin.uldap
import univention.admin.nagios as nagios
import univention.admin.handlers.dns.forward_zone
import univention.admin.handlers.dns.reverse_zone
import univention.admin.handlers.networks.network

import univention.debug as ud

translation = univention.admin.localization.translation('univention.admin.handlers.computers')
_ = translation.translate

module = 'computers/ipmanagedclient'
operations = ['add', 'edit', 'remove', 'search', 'move']
docleanup = 1
childs = 0
short_description = _('Computer: IP managed client')
object_name = _('IP managed client')
object_name_plural = _('IP managed clients')
long_description = ''
options = {
}
property_descriptions = {
	'name': univention.admin.property(
		short_description=_('IP managed client name'),
		long_description='',
		syntax=univention.admin.syntax.hostName,
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
	'mac': univention.admin.property(
		short_description=_('MAC address'),
		long_description='',
		syntax=univention.admin.syntax.MAC_Address,
		multivalue=True,
		include_in_default_search=True,
	),
	'network': univention.admin.property(
		short_description=_('Network'),
		long_description='',
		syntax=univention.admin.syntax.network,
	),
	'ip': univention.admin.property(
		short_description=_('IP address'),
		long_description='',
		syntax=univention.admin.syntax.ipAddress,
		multivalue=True,
		include_in_default_search=True,
	),
	'dnsEntryZoneForward': univention.admin.property(
		short_description=_('Forward zone for DNS entry'),
		long_description='',
		syntax=univention.admin.syntax.dnsEntry,
		multivalue=True,
		dontsearch=True,
	),
	'dnsEntryZoneReverse': univention.admin.property(
		short_description=_('Reverse zone for DNS entry'),
		long_description='',
		syntax=univention.admin.syntax.dnsEntryReverse,
		multivalue=True,
		dontsearch=True,
	),
	'dnsEntryZoneAlias': univention.admin.property(
		short_description=_('Zone for DNS alias'),
		long_description='',
		syntax=univention.admin.syntax.dnsEntryAlias,
		multivalue=True,
		dontsearch=True,
	),
	'dnsAlias': univention.admin.property(
		short_description=_('DNS alias'),
		long_description='',
		syntax=univention.admin.syntax.string,
		multivalue=True,
	),
	'dhcpEntryZone': univention.admin.property(
		short_description=_('DHCP service'),
		long_description='',
		syntax=univention.admin.syntax.dhcpEntry,
		multivalue=True,
		dontsearch=True,
	),
	'inventoryNumber': univention.admin.property(
		short_description=_('Inventory number'),
		long_description='',
		syntax=univention.admin.syntax.string,
		multivalue=True,
		include_in_default_search=True,
	),
	'groups': univention.admin.property(
		short_description=_('Groups'),
		long_description='',
		syntax=univention.admin.syntax.GroupDN,
		multivalue=True,
		dontsearch=True,
	),
	'domain': univention.admin.property(
		short_description=_('Domain'),
		long_description='',
		syntax=univention.admin.syntax.string,
		include_in_default_search=True,
	),
}

layout = [
	Tab(_('General'), _('Basic settings'), layout=[
		Group(_('Computer account'), layout=[
			['name', 'description'],
			'inventoryNumber',
		]),
		Group(_('Network settings '), layout=[
			'network',
			'mac',
			'ip',
		]),
		Group(_('DNS Forward and Reverse Lookup Zone'), layout=[
			'dnsEntryZoneForward',
			'dnsEntryZoneReverse',
		]),
		Group(_('DHCP'), layout=[
			'dhcpEntryZone'
		]),
	]),
	Tab(_('Groups'), _('Group memberships'), advanced=True, layout=[
		"groups",
	]),
	Tab(_('DNS alias'), _('Alias DNS entry'), advanced=True, layout=[
		'dnsEntryZoneAlias'
	]),
]

mapping = univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('description', 'description', None, univention.admin.mapping.ListToString)
mapping.register('inventoryNumber', 'univentionInventoryNumber')
mapping.register('mac', 'macAddress')
mapping.register('network', 'univentionNetworkLink', None, univention.admin.mapping.ListToString)
mapping.register('domain', 'associatedDomain', None, univention.admin.mapping.ListToString)

# add Nagios extension
nagios.addPropertiesMappingOptionsAndLayout(property_descriptions, mapping, options, layout)


class object(univention.admin.handlers.simpleComputer, nagios.Support):
	module = module

	def __init__(self, co, lo, position, dn='', superordinate=None, attributes=[]):
		univention.admin.handlers.simpleComputer.__init__(self, co, lo, position, dn, superordinate, attributes)
		nagios.Support.__init__(self)

	def open(self):

		univention.admin.handlers.simpleComputer.open(self)
		self.nagios_open()

		if not self.exists():
			return

		self.save()

	def _ldap_pre_create(self):
		super(object, self)._ldap_pre_create()
		self.nagios_ldap_pre_create()

	def _ldap_addlist(self):
		return [('objectClass', ['top', 'univentionHost', 'univentionClient', 'person'])]

	def _ldap_post_create(self):
		univention.admin.handlers.simpleComputer._ldap_post_create(self)
		self.nagios_ldap_post_create()

	def _ldap_post_remove(self):
		self.nagios_ldap_post_remove()
		univention.admin.handlers.simpleComputer._ldap_post_remove(self)

	def _ldap_post_modify(self):
		univention.admin.handlers.simpleComputer._ldap_post_modify(self)
		self.nagios_ldap_post_modify()

	def _ldap_pre_modify(self):
		univention.admin.handlers.simpleComputer._ldap_pre_modify(self)
		self.nagios_ldap_pre_modify()

	def _ldap_modlist(self):
		ml = univention.admin.handlers.simpleComputer._ldap_modlist(self)
		self.nagios_ldap_modlist(ml)
		return ml

	def cleanup(self):
		self.open()
		self.nagios_cleanup()
		univention.admin.handlers.simpleComputer.cleanup(self)

	def cancel(self):
		for key, value in self.alloc:
			ud.debug(ud.ADMIN, ud.WARN, 'cancel: release (%s): %s' % (key, value))
			univention.admin.allocators.release(self.lo, self.position, key, value)


def rewrite(filter, mapping):
	if filter.variable == 'ip':
		filter.variable = 'aRecord'
	else:
		univention.admin.mapping.mapRewrite(filter, mapping)


def lookup(co, lo, filter_s, base='', superordinate=None, scope='sub', unique=False, required=False, timeout=-1, sizelimit=0, serverctrls=None, response=None):
	res = []
	filter_s = univention.admin.filter.replace_fqdn_filter(filter_s)
	filter_s = univention.admin.handlers.dns.alias.lookup_alias_filter(lo, filter_s)
	filter = univention.admin.filter.conjunction('&', [
		univention.admin.filter.expression('objectClass', 'univentionHost'),
		univention.admin.filter.expression('objectClass', 'univentionClient'),
		univention.admin.filter.conjunction('!', [univention.admin.filter.expression('objectClass', 'posixAccount')]),
		univention.admin.filter.conjunction('!', [univention.admin.filter.expression('univentionObjectType', 'computers/managedclient')]),
	])

	if filter_s:
		filter_p = univention.admin.filter.parse(filter_s)
		univention.admin.filter.walk(filter_p, rewrite, arg=mapping)
		filter.expressions.append(filter_p)

	for dn, attrs in lo.search(unicode(filter), base, scope, [], unique, required, timeout, sizelimit, serverctrls, response):
		res.append(object(co, lo, None, dn, attributes=attrs))
	return res


def identify(dn, attr, canonical=0):
	return 'univentionHost' in attr.get('objectClass', []) and 'univentionClient' in attr.get('objectClass', []) and 'posixAccount' not in attr.get('objectClass', [])
