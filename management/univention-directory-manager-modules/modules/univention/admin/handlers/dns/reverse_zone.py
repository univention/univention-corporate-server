# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin module for the dns reverse zones
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
from univention.admin import configRegistry

import univention.admin.filter
import univention.admin.handlers
import univention.admin.localization
from univention.admin.handlers.dns import ARPA_IP4, ARPA_IP6, escapeSOAemail, unescapeSOAemail

translation = univention.admin.localization.translation('univention.admin.handlers.dns')
_ = translation.translate

module = 'dns/reverse_zone'
operations = ['add', 'edit', 'remove', 'search']
columns = ['nameserver']
childs = 1
childmodules = ['dns/ptr_record']
short_description = _('DNS: Reverse lookup zone')
object_name = _('Reverse lookup zone')
object_name_plural = _('Reverse lookup zones')
long_description = _('Map IP addresses back to hostnames.')
options = {
	'default': univention.admin.option(
		default=True,
		objectClasses=['top', 'dNSZone'],
	),
}
property_descriptions = {
	'subnet': univention.admin.property(
		short_description=_('Subnet'),
		long_description=_('The networks address in forward notation.'),
		syntax=univention.admin.syntax.reverseLookupSubnet,
		include_in_default_search=True,
		required=True,
		may_change=False,
		identifies=True
	),
	'zonettl': univention.admin.property(
		short_description=_('Zone time to live'),
		long_description=_('The time this entry may be cached.'),
		syntax=univention.admin.syntax.UNIX_TimeInterval,
		required=True,
		default=(('3', 'hours'), []),
		dontsearch=True,
	),
	'contact': univention.admin.property(
		short_description=_('Contact person'),
		long_description=_('The email address of the person responsible for this zone.'),
		syntax=univention.admin.syntax.string,
		required=True,
		default=('root@%s.' % configRegistry.get('domainname', ''), []),
	),
	'serial': univention.admin.property(
		short_description=_('Serial number'),
		long_description=_('The sequence number for this zone. Updates automatically.'),
		syntax=univention.admin.syntax.integer,
		required=True,
		default=('1', [])
	),
	'refresh': univention.admin.property(
		short_description=_('Refresh interval'),
		long_description=_('The time interval secondary DNS servers use to check the zone for updates.'),
		syntax=univention.admin.syntax.UNIX_TimeInterval,
		required=True,
		default=(('8', 'hours'), [])
	),
	'retry': univention.admin.property(
		short_description=_('Retry interval'),
		long_description=_('The time interval secondary DNS servers use to retry failed refresh updates.'),
		syntax=univention.admin.syntax.UNIX_TimeInterval,
		required=True,
		default=(('2', 'hours'), [])
	),
	'expire': univention.admin.property(
		short_description=_('Expiry interval'),
		long_description=_('The time interval after which secondary DNS servers will expire failed zones.'),
		syntax=univention.admin.syntax.UNIX_TimeInterval,
		required=True,
		default=(('7', 'days'), [])
	),
	'ttl': univention.admin.property(
		short_description=_('Negative time to live'),
		long_description=_('The time interval "not found" answers are cached.'),
		syntax=univention.admin.syntax.UNIX_TimeInterval,
		required=True,
		default=(('1', 'days'), [])
	),
	'nameserver': univention.admin.property(
		short_description=_('Name server'),
		long_description=_('The FQDNs of the servers serving this zone.'),
		syntax=univention.admin.syntax.dnsHostname,
		multivalue=True,
		required=True,
	),
}

layout = [
	Tab(_('General'), _('Basic settings'), layout=[
		Group(_('General reverse lookup zone settings'), layout=[
			'subnet',
			'zonettl',
			'nameserver'
		]),
	]),
	Tab(_('Start of authority'), _('Primary name server information'), layout=[
		Group(_('Start of authority'), layout=[
			'contact',
			'serial',
			['refresh', 'retry'],
			['expire', 'ttl']
		]),
	])
]


def mapSubnet(subnet):
	"""
	Map subnet to reverse zone.
	>>> mapSubnet('0123:4567:89ab:cdef')
	'f.e.d.c.b.a.9.8.7.6.5.4.3.2.1.0.ip6.arpa'
	>>> mapSubnet('0123:4567:89ab:cd')
	'd.c.b.a.9.8.7.6.5.4.3.2.1.0.ip6.arpa'
	>>> mapSubnet('1.2.3')
	'3.2.1.in-addr.arpa'
	"""
	if ':' in subnet:  # IPv6
		return '%s%s' % ('.'.join(reversed(subnet.replace(':', ''))), ARPA_IP6)
	else:
		q = subnet.split('.')
		q.reverse()
		return '%s%s' % ('.'.join(q), ARPA_IP4)


def unmapSubnet(zone):
	"""
	Map reverse zone to subnet.
	>>> unmapSubnet('f.e.d.c.b.a.9.8.7.6.5.4.3.2.1.0.ip6.arpa')
	'0123:4567:89ab:cdef'
	>>> unmapSubnet('d.c.b.a.9.8.7.6.5.4.3.2.1.0.ip6.arpa')
	'0123:4567:89ab:cd'
	>>> unmapSubnet('3.2.1.in-addr.arpa')
	'1.2.3'
	"""
	if isinstance(zone, list):
		zone = zone[0]
	if zone.endswith(ARPA_IP6):  # IPv6
		zone = zone[:-len(ARPA_IP6)]
		zone = list(reversed(zone.split('.')))
		return ':'.join([''.join(zone[i:i + 4]) for i in xrange(0, len(zone), 4)])
	elif zone.endswith(ARPA_IP4):  # IPv4
		zone = zone[:-len(ARPA_IP4)]
		q = zone.split('.')
		q.reverse()
		return '.'.join(q)
	else:
		raise ValueError('Neither an IPv4 nor an IPv6 reverse address')


mapping = univention.admin.mapping.mapping()
mapping.register('subnet', 'zoneName', mapSubnet, unmapSubnet)
mapping.register('zonettl', 'dNSTTL', univention.admin.mapping.mapUNIX_TimeInterval, univention.admin.mapping.unmapUNIX_TimeInterval)
mapping.register('nameserver', 'nSRecord')


class object(univention.admin.handlers.simpleLdap):
	module = module

	def __init__(self, co, lo, position, dn='', superordinate=None, attributes=[]):
		univention.admin.handlers.simpleLdap.__init__(self, co, lo, position, dn, superordinate, attributes=attributes)
		if not self.dn and not self.position:
			raise univention.admin.uexceptions.insufficientInformation(_('Neither DN nor position given.'))

	def open(self):
		univention.admin.handlers.simpleLdap.open(self)

		soa = self.oldattr.get('sOARecord', [''])[0].split(' ')
		if len(soa) > 6:
			self['contact'] = unescapeSOAemail(soa[1])
			self['serial'] = soa[2]
			self['refresh'] = univention.admin.mapping.unmapUNIX_TimeInterval(soa[3])
			self['retry'] = univention.admin.mapping.unmapUNIX_TimeInterval(soa[4])
			self['expire'] = univention.admin.mapping.unmapUNIX_TimeInterval(soa[5])
			self['ttl'] = univention.admin.mapping.unmapUNIX_TimeInterval(soa[6])

		self.save()

	def _ldap_modlist(self):
		ml = univention.admin.handlers.simpleLdap._ldap_modlist(self)
		if self.hasChanged(['nameserver', 'contact', 'serial', 'refresh', 'retry', 'expire', 'ttl']):
			if self['contact'] and not self['contact'].endswith('.'):
				self['contact'] += '.'
			for i in range(0, len(self['nameserver'])):
				if len(self['nameserver'][i]) > 0 \
					and ':' not in self['nameserver'][i] \
					and '.' in self['nameserver'][i] \
					and not self['nameserver'][i].endswith('.'):
					self['nameserver'][i] += '.'
			refresh = univention.admin.mapping.mapUNIX_TimeInterval(self['refresh'])
			retry = univention.admin.mapping.mapUNIX_TimeInterval(self['retry'])
			expire = univention.admin.mapping.mapUNIX_TimeInterval(self['expire'])
			ttl = univention.admin.mapping.mapUNIX_TimeInterval(self['ttl'])
			soa = '%s %s %s %s %s %s %s' % (self['nameserver'][0], escapeSOAemail(self['contact']), self['serial'], refresh, retry, expire, ttl)
			ml.append(('sOARecord', self.oldattr.get('sOARecord', []), soa))
		return ml

	def _ldap_pre_modify(self, modify_childs=1):
		# update SOA record
		if not self.hasChanged('serial'):
			self['serial'] = str(int(self['serial']) + 1)

	def _ldap_addlist(self):
		return [
			('relativeDomainName', ['@'])
		]

	# FIXME: there should be general solution; subnet is just a naming
	# attribute (though calculated from rdn)
	def description(self):
		if 0:  # open?
			return self['subnet']
		else:
			rdn = self.lo.explodeDn(self.dn)[0]
			rdn_value = rdn[rdn.find('=') + 1:]
			return unmapSubnet(rdn_value)

	@classmethod
	def unmapped_lookup_filter(cls):
		return univention.admin.filter.conjunction('&', [
			univention.admin.filter.expression('objectClass', 'dNSZone'),
			univention.admin.filter.expression('relativeDomainName', '@'),
			univention.admin.filter.conjunction('|', [
				univention.admin.filter.expression('zoneName', '*%s' % ARPA_IP4, escape=False),
				univention.admin.filter.expression('zoneName', '*%s' % ARPA_IP6, escape=False)
			]),
		])


lookup = object.lookup
lookup_filter = object.lookup_filter


def identify(dn, attr):
	return 'dNSZone' in attr.get('objectClass', []) and\
		['@'] == attr.get('relativeDomainName', []) and\
		(attr['zoneName'][0].endswith(ARPA_IP4) or attr['zoneName'][0].endswith(ARPA_IP6))


def quickDescription(rdn):
	return unmapSubnet(rdn)


if __name__ == '__main__':
	import doctest
	doctest.testmod()
