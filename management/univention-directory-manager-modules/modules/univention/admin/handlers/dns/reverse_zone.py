# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin module for the dns reverse zones
#
# Copyright 2004-2011 Univention GmbH
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

import string
import types

from univention.admin.layout import Tab, Group
from univention.admin import configRegistry

import univention.admin.filter
import univention.admin.handlers
import univention.admin.localization

translation=univention.admin.localization.translation('univention.admin.handlers.dns')
_=translation.translate

module='dns/reverse_zone'
operations=['add','edit','remove','search']
usewizard=1
childs=1
short_description=_('DNS: Reverse lookup zone')
long_description=''
options={
}
property_descriptions={
	'subnet': univention.admin.property(
			short_description=_('Subnet'),
			long_description='',
			syntax=univention.admin.syntax.reverseLookupSubnet,
			multivalue=0,
			options=[],
			required=1,
			may_change=0,
			identifies=1
		),
	'zonettl': univention.admin.property(
	        short_description=_('Zone time to live'),
	        long_description='',
			syntax=univention.admin.syntax.UNIX_TimeInterval,
			multivalue=0,
			options=[],
			required=1,
			may_change=1,
			identifies=0,
			default = ( ( '3', 'hours' ), [] )
		),
	'contact': univention.admin.property(
			short_description=_('Contact person'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=[],
			required=1,
			may_change=1,
			identifies=0,
			default = ( 'root@%s.' % configRegistry.get( 'domainname', '' ), [] ),
		),
	'serial': univention.admin.property(
			short_description=_('Serial number'),
			long_description='',
			syntax=univention.admin.syntax.integer,
			multivalue=0,
			options=[],
			required=1,
			may_change=1,
			identifies=0,
			default=('1', [])
		),
	'refresh': univention.admin.property(
			short_description=_('Refresh interval'),
			long_description='',
			syntax=univention.admin.syntax.UNIX_TimeInterval,
			multivalue=0,
			options=[],
			required=1,
			may_change=1,
			identifies=0,
			default = ( ( '8', 'hours' ), [] )
		),
	'retry': univention.admin.property(
			short_description=_('Retry interval'),
			long_description='',
			syntax=univention.admin.syntax.UNIX_TimeInterval,
			multivalue=0,
			options=[],
			required=1,
			may_change=1,
			identifies=0,
			default = ( ( '2', 'hours' ), [] )
		),
	'expire': univention.admin.property(
			short_description=_('Expiry interval'),
			long_description='',
			syntax=univention.admin.syntax.UNIX_TimeInterval,
			multivalue=0,
			options=[],
			required=1,
			may_change=1,
			identifies=0,
			default = ( ( '7', 'days' ), [] )
		),
	'ttl': univention.admin.property(
			short_description=_('Minimum time to live'),
			long_description='',
			syntax=univention.admin.syntax.UNIX_TimeInterval,
			multivalue=0,
			options=[],
			required=1,
			may_change=1,
			identifies=0,
			default = ( ( '1', 'days' ), [] )
		),
	'nameserver': univention.admin.property(
			short_description=_('Name servers'),
			long_description='',
			syntax=univention.admin.syntax.dnsName,
			multivalue=1,
			options=[],
			required=1,
			may_change=1,
			identifies=0
		),
}

layout = [
	Tab( _( 'General' ), _( 'Basic settings' ), layout = [
		Group( _( 'General' ), layout = [
			'subnet',
			'zonettl',
			'nameserver'
		] ),
	] ),
	Tab(_('Start of authority'), _('Primary name server information'), layout = [
		Group( _( 'General' ), layout = [
			'contact',
			'serial',
			['refresh', 'retry'],
			['expire', 'ttl']
		] ),
	] )
]

def mapSubnet(subnet):
	if ':' in subnet: # IPv6
		return '.'.join(reversed(subnet.replace(':', ''))) + '.ip6.arpa'
	else:
		q=subnet.split('.')
		q.reverse()
		return string.join(q, '.')+'.in-addr.arpa'

def unmapSubnet(zone):
	if type(zone) == types.ListType:
		zone=zone[0]
	if '.ip6.arpa' in zone: # IPv6
		zone = list(reversed(zone.replace('.ip6.arpa', '').split('.')))
		return ':'.join([''.join(zone[i:i+4]) for i in xrange(0, len(zone), 4)])
	else:
		zone=zone.replace('.in-addr.arpa', '')
		q=zone.split('.')
		q.reverse()
		return string.join(q, '.')

mapping=univention.admin.mapping.mapping()
mapping.register('subnet', 'zoneName', mapSubnet, unmapSubnet)
mapping.register('zonettl','dNSTTL', univention.admin.mapping.mapUNIX_TimeInterval, univention.admin.mapping.unmapUNIX_TimeInterval )
mapping.register('nameserver', 'nSRecord')

class object(univention.admin.handlers.simpleLdap):
	module=module

	def __init__(self, co, lo, position, dn='', superordinate=None, attributes = [] ):
		global mapping
		global property_descriptions

		self.mapping=mapping
		self.descriptions=property_descriptions

		if not dn and not position:
			raise univention.admin.uexceptions.insufficientInformation, _( 'neither DN nor position present' )

		univention.admin.handlers.simpleLdap.__init__(self, co, lo, position, dn, superordinate, attributes = attributes )

	def open(self):
		univention.admin.handlers.simpleLdap.open(self)

		soa=self.oldattr.get('sOARecord',[''])[0].split(' ')
		if len(soa) > 6:
			self['contact']=soa[1].replace('.','@',1)
			self['serial'] = soa[2]
			self['refresh'] = univention.admin.mapping.unmapUNIX_TimeInterval( soa[3] )
			self['retry'] = univention.admin.mapping.unmapUNIX_TimeInterval( soa[4] )
			self['expire'] = univention.admin.mapping.unmapUNIX_TimeInterval( soa[5] )
			self['ttl'] = univention.admin.mapping.unmapUNIX_TimeInterval( soa[6] )

		self.save()

	def _ldap_pre_create(self):
		self.dn='%s=%s,%s' % (mapping.mapName('subnet'), mapping.mapValue('subnet', self.info['subnet']), self.position.getDn())

	def _ldap_modlist(self):
		ml=univention.admin.handlers.simpleLdap._ldap_modlist(self)
		if self.hasChanged(['nameserver', 'contact', 'serial', 'refresh', 'retry', 'expire', 'ttl']):

			refresh = univention.admin.mapping.mapUNIX_TimeInterval( self[ 'refresh' ] )
			retry = univention.admin.mapping.mapUNIX_TimeInterval( self[ 'retry' ] )
			expire = univention.admin.mapping.mapUNIX_TimeInterval( self[ 'expire' ] )
			ttl = univention.admin.mapping.mapUNIX_TimeInterval( self[ 'ttl' ] )
			soa = '%s %s %s %s %s %s %s' % ( self[ 'nameserver' ][ 0 ], self[ 'contact' ].replace( '@', '.', 1 ), self[ 'serial' ], refresh, retry, expire, ttl )
			ml.append(('sOARecord', self.oldattr.get('sOARecord', []), soa))
		return ml

	def _ldap_pre_modify(self, modify_childs=1):
		# update SOA record
		if not self.hasChanged('serial'):
			self['serial']=str(int(self['serial'])+1)

	def _ldap_addlist(self):
		return [
			('objectClass', ['top', 'dNSZone']),
			('relativeDomainName', ['@'])
		]

	# FIXME: there should be general solution; subnet is just a naming
	# attribute (though calculated from rdn)
	def description(self):
		if 0: # open?
			return self['subnet']
		else:
			rdn = self.lo.explodeDn(self.dn)[0]
			rdn_value = rdn[rdn.find('=')+1:]
			return unmapSubnet(rdn_value)


def lookup(co, lo, filter_s, base='', superordinate=None, scope='sub', unique=0, required=0, timeout=-1, sizelimit=0):

	filter=univention.admin.filter.conjunction('&', [
		univention.admin.filter.expression('objectClass', 'dNSZone'),
		univention.admin.filter.expression('relativeDomainName', '@'),
		univention.admin.filter.conjunction('|', [
			univention.admin.filter.expression('zoneName', '*.in-addr.arpa'),
			univention.admin.filter.expression('zoneName', '*.ip6.arpa')
			]),
		])

	if filter_s:
		filter_p=univention.admin.filter.parse(filter_s)
		univention.admin.filter.walk(filter_p, univention.admin.mapping.mapRewrite, arg=mapping)
		filter.expressions.append(filter_p)

	res=[]
	for dn, attrs in lo.search(unicode(filter), base, scope, [], unique, required, timeout, sizelimit):
		res.append((object(co, lo, None, dn=dn, superordinate=superordinate, attributes = attrs )))
	return res

def identify(dn, attr):

	return 'dNSZone' in attr.get('objectClass', []) and\
		['@'] == attr.get('relativeDomainName', []) and\
		(attr['zoneName'][0].endswith('.in-addr.arpa') or attr['zoneName'][0].endswith('.ip6.arpa'))

def quickDescription(rdn):

	return unmapSubnet(rdn)
