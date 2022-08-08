# -*- coding: utf-8 -*-
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
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
|UDM| module for the |DHCP| subnet
"""

from ipaddress import IPv4Address, IPv4Network
from typing import List, Tuple, Sequence  # noqa: F401
import sys

import univention.admin.localization
import univention.admin.uexceptions as uex
from univention.admin.layout import Tab
from univention.admin.handlers import simpleLdap

Range = Tuple[IPv4Address, IPv4Address]

translation = univention.admin.localization.translation('univention.admin.handlers.dhcp')
_ = translation.translate

_properties = {
	'option': univention.admin.property(
		short_description=_('DHCP options'),
		long_description=_('Additional options for DHCP'),
		syntax=univention.admin.syntax.string,
		multivalue=True,
		options=['options'],
	),
	'statements': univention.admin.property(
		short_description=_('DHCP Statements'),
		long_description=_('Additional statements for DHCP'),
		syntax=univention.admin.syntax.TextArea,
		multivalue=True,
		options=['options'],
	)
}
_options = {
	'options': univention.admin.option(
		short_description=_('Allow custom DHCP options'),
		long_description=_("Allow adding custom DHCP options. Experts only!"),
		default=False,
		editable=True,
		objectClasses=['dhcpOptions'],
	),
}
_mappings = (
	('option', 'dhcpOption', None, None, 'ASCII'),
	('statements', 'dhcpStatements', None, None, 'ASCII'),
)


def rangeMap(value, encoding=()):
	return [u' '.join(x).encode(*encoding) for x in value]


def rangeUnmap(value, encoding=()):
	return [x.decode(*encoding).split() for x in value]


def add_dhcp_options(module_name):
	module = sys.modules[module_name]

	options = getattr(module, "options")
	options.update(_options)

	properties = getattr(module, "property_descriptions")
	properties.update(_properties)

	mapping = getattr(module, "mapping")
	for item in _mappings:
		mapping.register(*item)

	layout = getattr(module, "layout")
	layout.append(Tab(
		_('Low-level DHCP configuration'),
		_('Custom DHCP options'),
		advanced=True,
		layout=['option', 'statements']
	))


def check_range_overlap(ranges):  # type: (Sequence[Range]) -> None
	"""
	Check IPv4 address ranges for overlapping

	:param ranges: List of 2-tuple (first-IP, last-IP) of type :py:class:`IPv4Address`.
	:raises uex.rangesOverlapping: when an overlap exists.

	>>> first = (IPv4Address(u"192.0.2.0"), IPv4Address(u"192.0.2.127"))
	>>> second = (IPv4Address(u"192.0.2.128"), IPv4Address(u"192.0.2.255"))
	>>> both = (IPv4Address(u"192.0.2.0"), IPv4Address(u"192.0.2.255"))
	>>> check_range_overlap([])
	>>> check_range_overlap([first])
	>>> check_range_overlap([first, second])
	>>> check_range_overlap([first, both]) #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	rangesOverlapping: 192.0.2.0-192.0.2.127; 192.0.2.0-192.0.2.255
	"""
	prev = []  # type: List[Range]
	for r1 in ranges:
		(s1, e1) = r1
		assert s1 <= e1  # already checked by syntax.IPv4_AddressRange

		for r2 in prev:
			(s2, e2) = r2
			if e2 < s1:
				# [s2 <= e2] << [s1 <= e1]
				pass
			elif e1 < s2:
				# [s1 <= e1] << [s2 <= e2]
				pass
			else:
				raise uex.rangesOverlapping('%s-%s; %s-%s' % (r1 + r2))

		prev.append(r1)


def check_range_subnet(subnet, ranges):  # type: (IPv4Network, Sequence[Range]) -> None
	"""
	Check IPv4 address ranges are inside the given network.

	:param subnet: IPv4 subnet.
	:param ranges: List of 2-tuple (first-IP, last-IP) of type :py:class:`ipaddress.IPv4Address`.
	:raises uex.rangeInNetworkAddress: when a range includes the reserved network address.
	:raises uex.rangeInBroadcastAddress: when a range includes the reserved broadcast address.
	:raises uex.rangeNotInNetwork: when a range is outside the sub-network.

	>>> subnet = IPv4Network(u'192.0.2.0/24')
	>>> range_ = (subnet[1], subnet[-2])
	>>> check_range_subnet(subnet, [])
	>>> check_range_subnet(subnet, [(subnet[1], subnet[-2])])
	>>> check_range_subnet(subnet, [(subnet[0], subnet[-2])]) # doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	rangeInNetworkAddress: 192.0.2.0-192.0.2.254
	>>> check_range_subnet(subnet, [(subnet[1], subnet[-1])]) # doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	rangeInBroadcastAddress: 192.0.2.1-192.0.2.255
	>>> local = IPv4Address(u"127.0.0.1")
	>>> check_range_subnet(subnet, [(local, local)]) # doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	rangeNotInNetwork: 127.0.0.1
	"""
	for r1 in ranges:
		for ip in r1:
			if ip == subnet.network_address:
				raise uex.rangeInNetworkAddress('%s-%s' % r1)

			if ip == subnet.broadcast_address:
				raise uex.rangeInBroadcastAddress('%s-%s' % r1)

			if ip not in subnet:
				raise uex.rangeNotInNetwork(ip)


class DHCPBase(simpleLdap):
	pass


class DHCPBaseSubnet(DHCPBase):
	def ready(self):
		super(DHCPBaseSubnet, self).ready()

		try:
			subnet = IPv4Network(u'%(subnet)s/%(subnetmask)s' % self.info)
		except ValueError:
			raise uex.valueError(_('The subnet mask does not match the subnet.'), property='subnetmask')

		if self.hasChanged('range') or not self.exists():
			ranges = [tuple(IPv4Address(u'%s' % (ip,)) for ip in range_) for range_ in self['range']]
			check_range_overlap(ranges)
			check_range_subnet(subnet, ranges)
