# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin module for the DNS aliases
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

import sys, string
import univention.admin.filter
import univention.admin.handlers
import univention.admin.handlers.dns.forward_zone
import univention.admin.localization

translation=univention.admin.localization.translation('univention.admin.handlers.dns')
_=translation.translate

module='dns/alias'
operations=['add','edit','remove','search']
superordinate='dns/forward_zone'
usewizard=1
childs=0
short_description=_('DNS: Alias Record')
long_description=''
options={
}
property_descriptions={
	'name': univention.admin.property(
			short_description=_('Alias'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=[],
			required=1,
			may_change=1,
			identifies=1
		),
	'zonettl': univention.admin.property(
			short_description=_('Zone Time-to-Live'),
			long_description='',
			syntax=univention.admin.syntax.unixTimeInterval,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0,
			default=('10800', [])
		),
	'cname': univention.admin.property(
			short_description=_('Canonical Name'),
			long_description=_("FQDNs must end with '.'"),
			syntax=univention.admin.syntax.dnsName,
			multivalue=0,
			options=[],
			required=1,
			may_change=1
		)
}
layout=[
	univention.admin.tab(_('General'), _('Basic Values'), fields=[
		[univention.admin.field('name')],
		[univention.admin.field('zonettl')],
	]),	
	univention.admin.tab(_('Alias'), _('Alias for this Host'), fields=[
		[univention.admin.field('cname')],
	])
]


mapping=univention.admin.mapping.mapping()
mapping.register('name', 'relativeDomainName', None, univention.admin.mapping.ListToString)
mapping.register('cname', 'cNAMERecord', None, univention.admin.mapping.ListToString)
mapping.register('zonettl', 'dNSTTL', None, univention.admin.mapping.ListToString)

class object(univention.admin.handlers.simpleLdap):
	module=module

	def _updateZone(self):
		self.superordinate.open()
		self.superordinate.modify()

	def __init__(self, co, lo, position, dn='', superordinate=None, arg=None):
		self.co=co
		self.lo=lo
		self.dn=dn
		self.position=position
		self.superordinate=superordinate
		self._exists=0
		self.mapping=mapping
		self.descriptions=property_descriptions

		if not superordinate:
			raise univention.admin.uexceptions.insufficientInformation, 'superordinate object not present'
		if not dn and not position:
			raise univention.admin.uexceptions.insufficientInformation, 'neither dn nor position present'

		univention.admin.handlers.simpleLdap.__init__(self, co, lo, position, dn, superordinate)

	def exists(self):
		return self._exists
		
	def _ldap_pre_create(self):
		self.dn='%s=%s,%s' % (mapping.mapName('name'), mapping.mapValue('name', self['name']), self.position.getDn())

	def _ldap_addlist(self):
		return [
			('objectClass', ['top', 'dNSZone']),
			(self.superordinate.mapping.mapName('zone'), self.superordinate.mapping.mapValue('zone', self.superordinate['zone'])),
		]
		
	def _ldap_post_create(self):	
		self._updateZone()
		
	def _ldap_post_modify(self):
		if self.hasChanged(self.descriptions.keys()):
			self._updateZone()

	def _ldap_post_remove(self):
		self._updateZone()
	
def lookup(co, lo, filter_s, base='', superordinate=None, scope="sub", unique=0, required=0, timeout=-1, sizelimit=0):

	filter=univention.admin.filter.conjunction('&', [
		univention.admin.filter.expression('objectClass', 'dNSZone'),
		univention.admin.filter.conjunction('!', [univention.admin.filter.expression('relativeDomainName', '@')]),
		univention.admin.filter.conjunction('!', [univention.admin.filter.expression('zoneName', '*.in-addr.arpa')]),
		univention.admin.filter.conjunction('!', [univention.admin.filter.expression('ARecord', '*')]),
		univention.admin.filter.expression('CNAMERecord', '*')
		])

	if superordinate:
		filter.expressions.append(univention.admin.filter.expression('zoneName', superordinate.mapping.mapValue('zone', superordinate['zone'])))

	if filter_s:
		filter_p=univention.admin.filter.parse(filter_s)
		univention.admin.filter.walk(filter_p, univention.admin.mapping.mapRewrite, arg=mapping)
		filter.expressions.append(filter_p)

	res=[]
	for dn in lo.searchDn(unicode(filter), base, scope, unique, required, timeout, sizelimit):
		res.append(object(co, lo, None, dn, superordinate=superordinate))
	return res

def identify(dn, attr, canonical=0):
	
	return 'dNSZone' in attr.get('objectClass', []) and\
		'@' not in attr.get('relativeDomainName', []) and\
		not attr['zoneName'][0].endswith('.in-addr.arpa') and\
		'*' in attr.get('CNAMERecord', []) and\
		not '*' in attr.get('ARecord', [])

