# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin module for the DNS forward objects
#
# Copyright 2004-2012 Univention GmbH
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

import ipaddr

from univention.admin.layout import Tab, Group
from univention.admin import configRegistry

import univention.admin.filter
import univention.admin.handlers
import univention.admin.localization
from univention.admin.handlers.dns import ARPA_IP4, ARPA_IP6, escapeSOAemail, unescapeSOAemail

translation=univention.admin.localization.translation('univention.admin.handlers.dns')
_=translation.translate

module='dns/forward_zone'
operations=['add','edit','remove','search']
usewizard=1
childs=1
short_description=_('DNS: Forward lookup zone')
long_description=''
options={
}
property_descriptions={
	'zone': univention.admin.property(
			short_description=_('Zone name'),
			long_description='',
			syntax=univention.admin.syntax.dnsZone,
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
			default=( ( '3', 'hours' ), [])
		),
	'contact': univention.admin.property(
			short_description=_('Contact person'),
			long_description='',
			syntax=univention.admin.syntax.emailAddress,
			multivalue=0,
			options=[],
			required=1,
			may_change=1,
			identifies=0,
			default = ( 'root@%s' % configRegistry.get( 'domainname' ), [] ),
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
			default=( ( '8', 'hours' ), [])
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
			default=( ( '2', 'hours' ), [] )
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
			default = ( ( '3', 'hours' ), [] )
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
	'mx': univention.admin.property(
			short_description=_('Mail exchanger host'),
			long_description='',
			syntax=univention.admin.syntax.dnsMX,
			multivalue=1,
			options=[],
			required=0,
			may_change=1
		),
	'txt': univention.admin.property(
			short_description=_('TXT record'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=1,
			options=[],
			required=0,
			may_change=1
		),
	'a': univention.admin.property(
			short_description=_('IP addresses'),
			long_description='',
			syntax=univention.admin.syntax.ipAddress,
			multivalue=1,
			options=[],
			required=0,
			may_change=1
		),
}

layout = [
	Tab( _( 'General' ), _( 'Basic settings' ), layout = [
		Group( _( 'General' ), layout = [
			'zone',
			'nameserver',
			'zonettl'
		] ),
	] ),
	Tab( _( 'Start of authority' ), _( 'Primary name server information' ), layout = [
		Group( _( 'Start of authority' ), layout = [
			'contact',
			'serial',
			[ 'refresh', 'retry' ],
			[ 'expire', 'ttl' ]
		] ),
	] ),
	Tab(_('IP addresses'), _('IP addresses of the zone'), layout = [
		Group( _( 'IP addresses of the zone' ), layout = [
			'a'
		] ),
	] ),
	Tab( _( 'MX records' ), _( 'Mail exchanger records' ), layout = [
		Group( _( 'MX records' ), layout = [
			'mx'
		] ),
	] ),
	Tab(_('TXT records'), _('Text records'), layout = [
		Group( _( 'TXT records' ), layout = [
			'txt'
		] ),
	] ),
]

def mapMX(old):
	lst = []
	if old == '*':
		return str('*')
	if type(old) is list and len(old) == 2 and type(old[0]) is unicode and type(old[1]) is unicode:
		return str('%s %s' % (old[0], old[1], ))
	for entry in old:
		lst.append( '%s %s' % (entry[0], entry[1]) )
	return lst

def unmapMX(old):
	lst = []
	for entry in old:
		lst.append( entry.split(' ', 1) )
	return lst

mapping=univention.admin.mapping.mapping()
mapping.register('zone', 'zoneName', None, univention.admin.mapping.ListToString)
mapping.register('nameserver', 'nSRecord')
mapping.register('zonettl', 'dNSTTL', univention.admin.mapping.mapUNIX_TimeInterval, univention.admin.mapping.unmapUNIX_TimeInterval )
mapping.register('mx', 'mXRecord', mapMX, unmapMX)
mapping.register('txt', 'tXTRecord', None, univention.admin.mapping.ListToString)

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
		self.oldinfo['a'] = []
		self.info['a'] = []
		if 'aRecord' in self.oldattr:
			self.oldinfo['a'].extend(self.oldattr['aRecord'])
			self.info['a'].extend(   self.oldattr['aRecord'])
		if 'aAAARecord' in self.oldattr:
			self.oldinfo['a'].extend(map(lambda x: ipaddr.IPv6Address(x).exploded, self.oldattr['aAAARecord']))
			self.info['a'].extend(   map(lambda x: ipaddr.IPv6Address(x).exploded, self.oldattr['aAAARecord']))

		soa=self.oldattr.get('sOARecord',[''])[0].split(' ')
		if len(soa) > 6:
			self['contact'] = unescapeSOAemail(soa[1])
			self['serial']=soa[2]
			self['refresh'] = univention.admin.mapping.unmapUNIX_TimeInterval( soa[3] )
			self['retry'] = univention.admin.mapping.unmapUNIX_TimeInterval( soa[4] )
			self['expire'] = univention.admin.mapping.unmapUNIX_TimeInterval( soa[5] )
			self['ttl'] = univention.admin.mapping.unmapUNIX_TimeInterval( soa[6] )

		self.save()

	def _ldap_pre_create(self):
		self.dn='%s=%s,%s' % (mapping.mapName('zone'), mapping.mapValue('zone', self.info['zone']), self.position.getDn())

	def _ldap_addlist(self):
		return [
			('objectClass', ['top', 'dNSZone']),
			('relativeDomainName', ['@'])
		]

	def _ldap_modlist(self):
		ml=univention.admin.handlers.simpleLdap._ldap_modlist(self)
		if self.hasChanged(['nameserver', 'contact', 'serial', 'refresh', 'retry', 'expire', 'ttl']):
			if self['contact'] and not self['contact'].endswith('.'):
				self['contact'] += '.'
			if len (self['nameserver'][0]) > 0 \
				and ':' not in self['nameserver'][0] \
				and '.' in self['nameserver'][0] \
				and not self['nameserver'][0].endswith('.'):
				self['nameserver'][0] += '.'
			refresh = univention.admin.mapping.mapUNIX_TimeInterval( self[ 'refresh' ] )
			retry = univention.admin.mapping.mapUNIX_TimeInterval( self[ 'retry' ] )
			expire = univention.admin.mapping.mapUNIX_TimeInterval( self[ 'expire' ] )
			ttl = univention.admin.mapping.mapUNIX_TimeInterval( self[ 'ttl' ] )
			soa='%s %s %s %s %s %s %s' % (self['nameserver'][0], escapeSOAemail(self['contact']), self['serial'], refresh, retry, expire, ttl )
			ml.append(('sOARecord', self.oldattr.get('sOARecord', []), [soa]))

		oldAddresses = self.oldinfo.get('a')
		newAddresses = self.info.get('a')
		oldARecord = []
		newARecord = []
		oldAaaaRecord = []
		newAaaaRecord = []
		if oldAddresses != newAddresses:
			if oldAddresses:
			    for address in oldAddresses:
					if ':' in address: # IPv6
						oldAaaaRecord.append(address)
					else:
						oldARecord.append(address)
			if newAddresses:
			    for address in newAddresses:
					if ':' in address: # IPv6
						newAaaaRecord.append(ipaddr.IPv6Address(address).exploded)
					else:
						newARecord.append(address)
			ml.append(('aRecord',    oldARecord,    newARecord, ))
			ml.append(('aAAARecord', oldAaaaRecord, newAaaaRecord, ))
		return ml

	def _ldap_pre_modify(self, modify_childs=1):
		# update SOA record
		if not self.hasChanged('serial'):
			self['serial']=str(int(self['serial'])+1)

def lookup(co, lo, filter_s, base='', superordinate=None, scope='sub', unique=0, required=0, timeout=-1, sizelimit=0):

	filter=univention.admin.filter.conjunction('&', [
		univention.admin.filter.expression('objectClass', 'dNSZone'),
		univention.admin.filter.expression('relativeDomainName', '@'),
		univention.admin.filter.conjunction('!', [univention.admin.filter.expression('zoneName', '*%s' % ARPA_IP4)]),
		univention.admin.filter.conjunction('!', [univention.admin.filter.expression('zoneName', '*%s' % ARPA_IP6)]),
		])

	if filter_s:
		filter_p=univention.admin.filter.parse(filter_s)
		univention.admin.filter.walk(filter_p, univention.admin.mapping.mapRewrite, arg=mapping)
		filter.expressions.append(filter_p)

	res=[]
	for dn, attrs in lo.search(unicode(filter), base, scope, [], unique, required, timeout, sizelimit):
		res.append((object(co, lo, None, dn=dn, superordinate=superordinate, attributes = attrs )))
	return res


def identify(dn, attr, canonical=0):
	return 'dNSZone' in attr.get('objectClass', []) and ['@'] == attr.get('relativeDomainName', []) and not attr['zoneName'][0].endswith(ARPA_IP4) and not attr['zoneName'][0].endswith(ARPA_IP6)
