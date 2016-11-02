# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin module for the DHCP shared subnets
#
# Copyright 2004-2016 Univention GmbH
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
import univention.admin.ipaddress
import univention.admin.localization

from .__common import add_dhcp_options, add_dhcp_objectclass, rangeUnmap, rangeMap

translation = univention.admin.localization.translation('univention.admin.handlers.dhcp')
_ = translation.translate

module = 'dhcp/sharedsubnet'
operations = ['add', 'edit', 'remove', 'search']
superordinate = 'dhcp/shared'
childs = True
childmodules = ['dhcp/pool']
short_description = _('DHCP: Shared subnet')
long_description = ''
options = {
}
property_descriptions = {
	'subnet': univention.admin.property(
		short_description=_('Subnet address'),
		long_description='',
		syntax=univention.admin.syntax.ipv4Address,
		multivalue=False,
		include_in_default_search=True,
		options=[],
		required=True,
		may_change=False,
		identifies=True
	),
	'subnetmask': univention.admin.property(
		short_description=_('Address prefix length (or Netmask)'),
		long_description='',
		syntax=univention.admin.syntax.v4netmask,
		multivalue=False,
		options=[],
		required=True,
		may_change=True,
		identifies=False
	),
	'broadcastaddress': univention.admin.property(
		short_description=_('Broadcast address'),
		long_description='',
		syntax=univention.admin.syntax.ipv4Address,
		multivalue=False,
		options=[],
		required=False,
		may_change=True,
		identifies=False
	),
	'range': univention.admin.property(
		short_description=_('Dynamic address assignment'),
		long_description=_('Define a pool of addresses available for dynamic address assignment.'),
		syntax=univention.admin.syntax.IPv4_AddressRange,
		multivalue=True,
		options=[],
		required=False,
		may_change=True,
		identifies=False
	),
}

layout = [
	Tab(_('General'), _('Basic settings'), layout=[
		Group(_('General DHCP shared subnet settings'), layout=[
			['subnet', 'subnetmask'],
			'broadcastaddress',
			'range'
		]),
	]),
]


mapping = univention.admin.mapping.mapping()
mapping.register('subnet', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('range', 'dhcpRange', rangeMap, rangeUnmap)
mapping.register('subnetmask', 'dhcpNetMask', None, univention.admin.mapping.ListToString)
mapping.register('broadcastaddress', 'univentionDhcpBroadcastAddress', None, univention.admin.mapping.ListToString)

add_dhcp_options(property_descriptions, mapping, layout)


class object(univention.admin.handlers.simpleLdap):
	module = module

	def _ldap_addlist(self):
		return [
			('objectClass', ['top', 'univentionDhcpSubnet', 'univentionDhcpSharedSubnet', 'dhcpOptions']),
		]

	def _ldap_modlist(self):
		ml = univention.admin.handlers.simpleLdap._ldap_modlist(self)

		return add_dhcp_objectclass(self, ml)


def lookup(co, lo, filter_s, base='', superordinate=None, scope='sub', unique=False, required=False, timeout=-1, sizelimit=0):

	filter = univention.admin.filter.conjunction('&', [
		univention.admin.filter.expression('objectClass', 'univentionDhcpSubnet'),
		univention.admin.filter.expression('objectClass', 'univentionDhcpSharedSubnet')
	])

	if filter_s:
		filter_p = univention.admin.filter.parse(filter_s)
		univention.admin.filter.walk(filter_p, univention.admin.mapping.mapRewrite, arg=mapping)
		filter.expressions.append(filter_p)

	res = []
	for dn, attrs in lo.search(unicode(filter), base, scope, [], unique, required, timeout, sizelimit):
		res.append((object(co, lo, None, dn=dn, superordinate=superordinate, attributes=attrs)))
	return res


def identify(dn, attr):
	return 'univentionDhcpSubnet' in attr.get('objectClass', []) and 'univentionDhcpSharedSubnet' in attr.get('objectClass', [])
