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
|UDM| module for |DHCP| subnets
"""

from univention.admin.layout import Tab, Group
import univention.admin.filter
import univention.admin.handlers
import univention.admin.localization

from .__common import DHCPBaseSubnet, add_dhcp_options, rangeUnmap, rangeMap

translation = univention.admin.localization.translation('univention.admin.handlers.dhcp')
_ = translation.translate

module = 'dhcp/subnet'
operations = ['add', 'edit', 'remove', 'search']
superordinate = 'dhcp/service'
childs = True
childmodules = ['dhcp/pool']
short_description = _('DHCP: Subnet')
object_name = _('DHCP subnet')
object_name_plural = _('DHCP subnets')
long_description = _('The IP address range used in a dedicated (non-shared) physical network.')
options = {
	'default': univention.admin.option(
		short_description=short_description,
		default=True,
		objectClasses=['top', 'univentionDhcpSubnet'],
	),
}
property_descriptions = {
	'subnet': univention.admin.property(
		short_description=_('Subnet address'),
		long_description=_('The network address.'),
		syntax=univention.admin.syntax.ipv4Address,
		include_in_default_search=True,
		required=True,
		may_change=False,
		identifies=True
	),
	'subnetmask': univention.admin.property(
		short_description=_('Address prefix length (or Netmask)'),
		long_description=_('The number of leading bits of the IP address used to identify the network.'),
		syntax=univention.admin.syntax.v4netmask,
		required=True,
	),
	'broadcastaddress': univention.admin.property(
		short_description=_('Broadcast address'),
		long_description=_('The IP addresses used to send data to all hosts inside the network.'),
		syntax=univention.admin.syntax.ipv4Address,
	),
	'range': univention.admin.property(
		short_description=_('Dynamic address assignment'),
		long_description=_('Define a pool of addresses available for dynamic address assignment.'),
		syntax=univention.admin.syntax.IPv4_AddressRange,
		multivalue=True,
	),
}

layout = [
	Tab(_('General'), _('Basic settings'), layout=[
		Group(_('General DHCP subnet settings'), layout=[
			['subnet', 'subnetmask'],
			'broadcastaddress',
			'range'
		]),
	]),
]


mapping = univention.admin.mapping.mapping()
mapping.register('subnet', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('subnetmask', 'dhcpNetMask', None, univention.admin.mapping.ListToString)
mapping.register('broadcastaddress', 'univentionDhcpBroadcastAddress', None, univention.admin.mapping.ListToString, encoding='ASCII')
mapping.register('range', 'dhcpRange', rangeMap, rangeUnmap)
add_dhcp_options(__name__)


class object(DHCPBaseSubnet):
	module = module

	@staticmethod
	def unmapped_lookup_filter():
		return univention.admin.filter.conjunction('&', [
			univention.admin.filter.expression('objectClass', 'univentionDhcpSubnet'),
			univention.admin.filter.conjunction('!', [univention.admin.filter.expression('objectClass', 'univentionDhcpSharedSubnet')])
		])


def identify(dn, attr):
	return b'univentionDhcpSubnet' in attr.get('objectClass', []) and b'univentionDhcpSharedSubnet' not in attr.get('objectClass', [])


lookup_filter = object.lookup_filter
lookup = object.lookup
