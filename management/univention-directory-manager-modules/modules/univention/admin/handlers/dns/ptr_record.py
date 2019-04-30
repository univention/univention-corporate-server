# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin module for dns reverse records
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
import univention.admin
import univention.admin.handlers
import univention.admin.localization
from univention.admin.filter import (expression, conjunction)
import univention.debug as ud
import ipaddr

translation = univention.admin.localization.translation('univention.admin.handlers.dns')
_ = translation.translate


module = 'dns/ptr_record'
operations = ['add', 'edit', 'remove', 'search']
columns = ['ptr_record']
superordinate = 'dns/reverse_zone'
childs = 0
short_description = _('DNS: Pointer record')
object_name = _('Pointer record')
object_name_plural = _('Pointer records')
long_description = _('Map IP addresses back to hostnames.')
options = {
	'default': univention.admin.option(
		default=True,
		objectClasses=['top', 'dNSZone'],
	),
}
property_descriptions = {
	'address': univention.admin.property(
		short_description=_('Reverse address'),
		long_description=_('The host part of the IP address in reverse notation (e.g. \"172.16.1.2/16\" -> \"2.1\" or \"2001:0db8:0100::0007:0008/96\" -> \"8.0.0.0.7.0.0.0\").'),
		syntax=univention.admin.syntax.dnsPTR,
		required=True,
		identifies=True,
	),
	'ip': univention.admin.property(
		short_description=_('IP Address'),
		long_description='',
		syntax=univention.admin.syntax.ipAddress,
		include_in_default_search=True,
	),
	'ptr_record': univention.admin.property(
		short_description=_('Pointer record'),
		long_description=_("FQDNs must end with a dot."),
		syntax=univention.admin.syntax.dnsName,
		multivalue=True,
		include_in_default_search=True,
		required=True,
	),
}

layout = [
	Tab(_('General'), _('Basic settings'), layout=[
		Group(_('General pointer record settings'), layout=[
			['ip', 'ptr_record'],
		]),
	]),
]

mapping = univention.admin.mapping.mapping()
mapping.register('address', 'relativeDomainName', None, univention.admin.mapping.ListToString)
mapping.register('ptr_record', 'pTRRecord')


def ipv6(string):
	"""
	>>> ipv6('0123456789abcdef0123456789abcdef')
	'0123:4567:89ab:cdef:0123:4567:89ab:cdef'
	"""
	assert len(string) == 32, string
	return ':'.join(string[i:i + 4] for i in range(0, 32, 4))


def calc_ip(rev, subnet):
	"""
	>>> calc_ip(rev='8.0.0.0.7.0.0.0.6.0.0.0.5.0.0.0.4.0.0', subnet='0001:0002:0003:0').exploded
	'0001:0002:0003:0004:0005:0006:0007:0008'
	>>> calc_ip(rev='4.3', subnet='1.2').exploded
	'1.2.3.4'
	"""
	parts = rev.split('.')
	parts.reverse()
	if ':' in subnet:
		string = ''.join(subnet.split(':') + parts)
		ip = ipaddr.IPv6Address(ipv6(string))
	else:
		octets = subnet.split('.') + parts
		assert len(octets) == 4, octets
		addr = '.'.join(octets)
		ip = ipaddr.IPv4Address(addr)
	return ip


def calc_rev(ip, subnet):
	"""
	>>> calc_rev(ip='1.2.3.4', subnet='1.2')
	'4.3'
	>>> calc_rev(ip='0001:0002:0003:0004:0005:0006:0007:0008', subnet='0001:0002:0003:0')
	'8.0.0.0.7.0.0.0.6.0.0.0.5.0.0.0.4.0.0'
	>>> calc_rev(ip='1:2:3:4:5:6:7:8', subnet='0001:0002:0003:0')
	'8.0.0.0.7.0.0.0.6.0.0.0.5.0.0.0.4.0.0'
	"""
	if ':' in subnet:
		string = ''.join(subnet.split(':'))
		prefix = len(string)
		assert 1 <= prefix < 32
		string += '0' * (32 - prefix)
		net = ipaddr.IPv6Network('%s/%d' % (ipv6(string), 4 * prefix))
		addr = ipaddr.IPv6Address(ip)
		host = ''.join(addr.exploded.split(':'))
	else:
		octets = subnet.split('.')
		prefix = len(octets)
		assert 1 <= prefix < 4
		octets += ['0'] * (4 - prefix)
		net = ipaddr.IPv4Network('%s/%d' % ('.'.join(octets), 8 * prefix))
		addr = ipaddr.IPv4Address(ip)
		host = addr.exploded.split('.')
	if addr not in net:
		raise ValueError()
	return '.'.join(reversed(host[prefix:]))


class object(univention.admin.handlers.simpleLdap):
	module = module

	def description(self):
		try:
			return calc_ip(self.info['address'], self.superordinate.info['subnet']).compressed
		except (LookupError, ValueError, AssertionError) as ex:
			ud.debug(ud.ADMIN, ud.WARN, 'Failed to parse dn=%s: (%s)' % (self.dn, ex))
			return super(object, self).description()

	def open(self):
		super(object, self).open()
		try:
			self.info['ip'] = calc_ip(self.info['address'], self.superordinate.info['subnet']).compressed
			self.save()
		except (LookupError, ValueError, AssertionError) as ex:
			ud.debug(ud.ADMIN, ud.WARN, 'Failed to parse dn=%s: (%s)' % (self.dn, ex))

	def ready(self):
		old_ip = self.oldinfo.get('ip')
		new_ip = self.info.get('ip')
		if old_ip != new_ip:
			try:
				self.info['address'] = calc_rev(new_ip, self.superordinate.info['subnet'])
			except (LookupError, ValueError, AssertionError) as ex:
				ud.debug(ud.ADMIN, ud.WARN, 'Failed to handle address: dn=%s addr=%r (%s)' % (self.dn, new_ip, ex))
				raise univention.admin.uexceptions.InvalidDNS_Information(_('Reverse zone and IP address are incompatible.'))
		super(object, self).ready()

	def _updateZone(self):
		if self.update_zone:
			self.superordinate.open()
			self.superordinate.modify()

	def __init__(self, co, lo, position, dn='', superordinate=None, attributes=[], update_zone=True):
		self.update_zone = update_zone
		univention.admin.handlers.simpleLdap.__init__(self, co, lo, position, dn, superordinate, attributes=attributes)

	def _ldap_addlist(self):
		return [
			(self.superordinate.mapping.mapName('subnet'), self.superordinate.mapping.mapValue('subnet', self.superordinate['subnet'])),
		]

	def _ldap_post_modify(self):
		if self.hasChanged(self.descriptions.keys()):
			self._updateZone()

	def _ldap_post_create(self):
		self._updateZone()

	def _ldap_post_remove(self):
		self._updateZone()

	@classmethod
	def lookup_filter_superordinate(cls, filter, superordinate):
		filter.expressions.append(univention.admin.filter.expression('zoneName', superordinate.mapping.mapValue('subnet', superordinate['subnet']), escape=True))
		filter = rewrite_rev(filter, superordinate.info['subnet'])
		return filter

	@classmethod
	def unmapped_lookup_filter(cls):
		return univention.admin.filter.conjunction('&', [
			univention.admin.filter.expression('objectClass', 'dNSZone'),
			univention.admin.filter.conjunction('!', [univention.admin.filter.expression('relativeDomainName', '@')]),
			univention.admin.filter.conjunction('|', [
				univention.admin.filter.expression('zoneName', '*.in-addr.arpa', escape=False),
				univention.admin.filter.expression('zoneName', '*.ip6.arpa', escape=False),
			]),
		])


def rewrite_rev(filter, subnet):
	"""Rewrite LDAP filter expression and convert (ip) -> (zone,reversed)

	>>> rewrite_rev(expression('ip', '1.2.3.4'), subnet='1.2')
	conjunction('&', [expression('zoneName', '2.1.in-addr.arpa', '='), expression('relativeDomainName', '4.3', '=')])
	>>> rewrite_rev(expression('ip', '1.2.3.*', escape=False), subnet='1.2')
	conjunction('&', [expression('zoneName', '2.1.in-addr.arpa', '='), expression('relativeDomainName', '*.3', '=')])
	>>> rewrite_rev(expression('ip', '1.2.*.*', escape=False), subnet='1.2')
	conjunction('&', [expression('zoneName', '2.1.in-addr.arpa', '='), expression('relativeDomainName', '*.*', '=')])
	>>> rewrite_rev(expression('ip', '1.2.*.4', escape=False), subnet='1.2')
	conjunction('&', [expression('zoneName', '2.1.in-addr.arpa', '='), expression('relativeDomainName', '4.*', '=')])
	>>> rewrite_rev(expression('ip', '1.2.*', escape=False), subnet='1.2')
	conjunction('&', [expression('zoneName', '2.1.in-addr.arpa', '='), expression('relativeDomainName', '*', '=')])
	>>> rewrite_rev(expression('ip', '1:2:3:4:5:6:7:8'), subnet='0001:0002')
	conjunction('&', [expression('zoneName', '2.0.0.0.1.0.0.0.ip6.arpa', '='), expression('relativeDomainName', '8.0.0.0.7.0.0.0.6.0.0.0.5.0.0.0.4.0.0.0.3.0.0.0', '=')])
	>>> rewrite_rev(expression('ip', '1:2:3:4:5:6:7:*', escape=False), subnet='0001:0002')
	conjunction('&', [expression('zoneName', '2.0.0.0.1.0.0.0.ip6.arpa', '='), expression('relativeDomainName', '*.7.0.0.0.6.0.0.0.5.0.0.0.4.0.0.0.3.0.0.0', '=')])
	>>> rewrite_rev(expression('ip', '1:2:3:4:5:6:*:8', escape=False), subnet='0001:0002')
	conjunction('&', [expression('zoneName', '2.0.0.0.1.0.0.0.ip6.arpa', '='), expression('relativeDomainName', '8.0.0.0.*.6.0.0.0.5.0.0.0.4.0.0.0.3.0.0.0', '=')])
	>>> rewrite_rev(expression('ip', '1:2:3:*', escape=False), subnet='0001:0002')
	conjunction('&', [expression('zoneName', '2.0.0.0.1.0.0.0.ip6.arpa', '='), expression('relativeDomainName', '*.3.0.0.0', '=')])
	"""
	if isinstance(filter, conjunction):
		filter.expressions = [rewrite_rev(expr, subnet) for expr in filter.expressions]
	if isinstance(filter, expression) and filter.variable == 'ip':
		if ':' in subnet:
			string = ''.join(subnet.split(':'))
			prefix = len(string)
			assert 1 <= prefix < 32
			addr = ''.join(
				part if '*' in part else part.rjust(4, '0')[-4:]
				for part in filter.value.split(':')
			)
			suffix = '.ip6.arpa'
		else:
			octets = subnet.split('.')
			prefix = len(octets)
			assert 1 <= prefix < 4
			addr = filter.value.split('.')
			suffix = '.in-addr.arpa'
		addr_net, addr_host = ['.'.join(reversed(_)) for _ in (addr[:prefix], addr[prefix:])]
		filter = conjunction('&', [
			expression('zoneName', addr_net + suffix),
			expression('relativeDomainName', addr_host or '*', escape=False),
		])
	return filter


lookup = object.lookup


def identify(dn, attr):
	return all([
		'dNSZone' in attr.get('objectClass', []),
		'@' not in attr.get('relativeDomainName', []),
		(attr.get('zoneName', [''])[0].endswith('.in-addr.arpa') or attr.get('zoneName', [''])[0].endswith('.ip6.arpa'))
	])


if __name__ == '__main__':
	import doctest
	doctest.testmod()
