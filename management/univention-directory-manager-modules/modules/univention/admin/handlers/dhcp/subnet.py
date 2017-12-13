# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin module for the DHCP subnet
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
import univention.admin.ipaddress
import univention.admin.localization

from .__common import DHCPBase, add_dhcp_options, rangeUnmap

translation = univention.admin.localization.translation('univention.admin.handlers.dhcp')
_ = translation.translate

module = 'dhcp/subnet'
operations = ['add', 'edit', 'remove', 'search']
superordinate = 'dhcp/service'
childs = 1
childmodules = ['dhcp/pool']
short_description = _('DHCP: Subnet')
long_description = _('The IP address range used in a dedicated (non-shared) physical network.')
options = {
}
property_descriptions = {
	'subnet': univention.admin.property(
		short_description=_('Subnet address'),
		long_description=_('The network address.'),
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
		long_description=_('The number of leading bits of the IP address used to identify the network.'),
		syntax=univention.admin.syntax.v4netmask,
		multivalue=False,
		options=[],
		required=True,
		may_change=True,
		identifies=False
	),
	'broadcastaddress': univention.admin.property(
		short_description=_('Broadcast address'),
		long_description=_('The IP addresses used to send data to all hosts inside the network.'),
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
mapping.register('broadcastaddress', 'univentionDhcpBroadcastAddress', None, univention.admin.mapping.ListToString)

add_dhcp_options(__name__)


class object(DHCPBase):
	module = module

	def open(self):
		univention.admin.handlers.simpleLdap.open(self)
		self.info['range'] = rangeUnmap(self.oldattr.get('dhcpRange', []))
		self.oldinfo['range'] = rangeUnmap(self.oldattr.get('dhcpRange', []))

	def _ldap_addlist(self):
		return [
			('objectClass', ['top', 'univentionDhcpSubnet']),
		]

	def _ldap_modlist(self):
		ml = super(object, self)._ldap_modlist()

		if self.hasChanged('range'):
			dhcpRange = []
			for i in self['range']:
				for j in self['range']:
					if i != j and univention.admin.ipaddress.is_range_overlapping(i, j):
						raise univention.admin.uexceptions.rangesOverlapping('%s-%s; %s-%s' % (i[0], i[1], j[0], j[1]))

				ip_in_network = True
				for j in i:
					if not univention.admin.ipaddress.ip_is_in_network(self['subnet'], self['subnetmask'], j):
						ip_in_network = False

					if univention.admin.ipaddress.ip_is_network_address(self['subnet'], self['subnetmask'], j):
						raise univention.admin.uexceptions.rangeInNetworkAddress('%s-%s' % (i[0], i[1]))

					if univention.admin.ipaddress.ip_is_broadcast_address(self['subnet'], self['subnetmask'], j):
						raise univention.admin.uexceptions.rangeInBroadcastAddress('%s-%s' % (i[0], i[1]))

				if ip_in_network:
					dhcpRange.append(' '.join(i))
				else:
					raise univention.admin.uexceptions.rangeNotInNetwork('%s-%s' % (i[0], i[1]))
			# univention.debug.debug(univention.debug.ADMIN, univention.debug.ERROR, 'old Range: %s' % self.oldinfo['range'])
			if '' in dhcpRange:
				dhcpRange.remove('')
			ml.append(('dhcpRange', self.oldattr.get('dhcpRange', []), dhcpRange))
		return ml

	@staticmethod
	def unmapped_lookup_filter():
		return univention.admin.filter.conjunction('&', [
			univention.admin.filter.expression('objectClass', 'univentionDhcpSubnet'),
			univention.admin.filter.conjunction('!', [univention.admin.filter.expression('objectClass', 'univentionDhcpSharedSubnet')])
		])


def identify(dn, attr):
	return 'univentionDhcpSubnet' in attr.get('objectClass', []) and 'univentionDhcpSharedSubnet' not in attr.get('objectClass', [])


lookup_filter = object.lookup_filter
lookup = object.lookup
