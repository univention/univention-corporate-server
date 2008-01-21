# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin module for the dns reverse zones
#
# Copyright (C) 2004, 2005, 2006 Univention GmbH
#
# http://www.univention.de/
#
# All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# Binary versions of this file provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import sys, string, types
import univention.admin.filter
import univention.admin.handlers
import univention.admin.localization

translation=univention.admin.localization.translation('univention.admin.handlers.dns')
_=translation.translate

def makeContactPerson(object, arg):
	domain=object.position.getDomain()
	return 'root@%s.' %(domain.replace(',dc=','.').replace('dc=',''))

module='dns/reverse_zone'
operations=['add','edit','remove','search']
usewizard=1
childs=1
short_description=_('DNS: Reverse Lookup Zone')
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
	        short_description=_('Zone Time-to-Live'),
	        long_description='',
			syntax=univention.admin.syntax.unixTimeInterval,
			multivalue=0,
			options=[],
			required=1,
			may_change=1,
			identifies=0,
			default=('10800', [])
		),
	'contact': univention.admin.property(
			short_description=_('Responsible Person'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=[],
			required=1,
			may_change=1,
			identifies=0,
			default=(makeContactPerson, [], ''),
		),
	'serial': univention.admin.property(
			short_description=_('Serial Number'),
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
			short_description=_('Refresh Interval'),
			long_description='',
			syntax=univention.admin.syntax.unixTimeInterval,
			multivalue=0,
			options=[],
			required=1,
			may_change=1,
			identifies=0,
			default=('28800', [])
		),
	'retry': univention.admin.property(
			short_description=_('Retry Interval'),
			long_description='',
			syntax=univention.admin.syntax.unixTimeInterval,
			multivalue=0,
			options=[],
			required=1,
			may_change=1,
			identifies=0,
			default=('7200', [])
		),
	'expire': univention.admin.property(
			short_description=_('Expire Interval'),
			long_description='',
			syntax=univention.admin.syntax.unixTimeInterval,
			multivalue=0,
			options=[],
			required=1,
			may_change=1,
			identifies=0,
			default=('604800', [])
		),
	'ttl': univention.admin.property(
			short_description=_('Minimum Time-to-Live'),
			long_description='',
			syntax=univention.admin.syntax.unixTimeInterval,
			multivalue=0,
			options=[],
			required=1,
			may_change=1,
			identifies=0,
			default=('86400', [])
		),
	'nameserver': univention.admin.property(
			short_description=_('Name Servers'),
			long_description='',
			syntax=univention.admin.syntax.dnsName,
			multivalue=1,
			options=[],
			required=1,
			may_change=1,
			identifies=0
		),
	'filler': univention.admin.property(
			short_description=(''),
			long_description='',
			syntax=univention.admin.syntax.none,
			multivalue=0,
			required=0,
			may_change=1,
			identifies=0,
			dontsearch=1
		)
}
layout=[
	univention.admin.tab(_('General'), _('Basic Values'), [
		[univention.admin.field('subnet')],
		[univention.admin.field('zonettl')]
	]),
	univention.admin.tab(_('Start of Authority'), _('Primary Name Server Information'), [
		[univention.admin.field('contact'), univention.admin.field('filler')],
		[univention.admin.field('nameserver', first_only=1, short_description=_('Primary Name Server')), univention.admin.field('serial')],
		[univention.admin.field('refresh'), univention.admin.field('retry')],
		[univention.admin.field('expire'), univention.admin.field('ttl')]
	]),
	univention.admin.tab(_('Name Servers'), _('Additional Name Servers'), [
		[univention.admin.field('nameserver')]
	])
]

def mapSubnet(subnet):
	q=subnet.split('.')
	q.reverse()
	return string.join(q, '.')+'.in-addr.arpa'

def unmapSubnet(zone):
	if type(zone) == types.ListType:
		zone=zone[0]
	zone=zone.replace('.in-addr.arpa', '')
	q=zone.split('.')
	q.reverse()
	return string.join(q, '.')

mapping=univention.admin.mapping.mapping()
mapping.register('subnet', 'zoneName', mapSubnet, unmapSubnet)
mapping.register('zonettl','dNSTTL', None, univention.admin.mapping.ListToString)
mapping.register('nameserver', 'nSRecord')

class object(univention.admin.handlers.simpleLdap):
	module=module

	def __init__(self, co, lo, position, dn='', superordinate=None, arg=None):
		global mapping
		global property_descriptions

		self.co=co
		self.lo=lo
		self.dn=dn
		self.position=position
		self._exists=0
		self.mapping=mapping
		self.descriptions=property_descriptions

		if not dn and not position:
			raise univention.admin.uexceptions.insufficientInformation, _( 'neither DN nor position present' )

		univention.admin.handlers.simpleLdap.__init__(self, co, lo, position, dn, superordinate)

	def open(self):
		univention.admin.handlers.simpleLdap.open(self)

		soa=self.oldattr.get('sOARecord',[''])[0].split(' ')
		if len(soa) > 6:
			self['contact']=soa[1].replace('.','@',1)
			self['serial']=soa[2]
			self['refresh']=soa[3]
			self['retry']=soa[4]
			self['expire']=soa[5]
			self['ttl']=soa[6]

		self.save()

	def exists(self):
		return self._exists

	def _ldap_pre_create(self):
		self.dn='%s=%s,%s' % (mapping.mapName('subnet'), mapping.mapValue('subnet', self.info['subnet']), self.position.getDn())

	def _ldap_modlist(self):
		ml=univention.admin.handlers.simpleLdap._ldap_modlist(self)
		if self.hasChanged(['nameserver', 'contact', 'serial', 'refresh', 'retry', 'expire', 'ttl']):

			soa='%s %s %s %s %s %s %s' % (self['nameserver'][0], self['contact'].replace('@','.',1), self['serial'], self['refresh'], self['retry'], self['expire'], self['ttl'])
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
		univention.admin.filter.expression('zoneName', '*.in-addr.arpa')
		])

	if filter_s:
		filter_p=univention.admin.filter.parse(filter_s)
		univention.admin.filter.walk(filter_p, univention.admin.mapping.mapRewrite, arg=mapping)
		filter.expressions.append(filter_p)

	res=[]
	for dn in lo.searchDn(unicode(filter), base, scope, unique, required, timeout, sizelimit):
		res.append(object(co, lo, None, dn, superordinate=superordinate))
	return res

def identify(dn, attr):

	return 'dNSZone' in attr.get('objectClass', []) and\
		['@'] == attr.get('relativeDomainName', []) and\
		attr['zoneName'][0].endswith('.in-addr.arpa')

def quickDescription(rdn):

	return unmapSubnet(rdn)
