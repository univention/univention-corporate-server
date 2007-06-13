# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin module for the dns host records
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

module='dns/host_record'
operations=['add','edit','remove','search']
superordinate='dns/forward_zone'
usewizard=1
childs=0
short_description='DNS: Host Record'
long_description=''

property_descriptions={
	'name': univention.admin.property(
			short_description=_('Hostname'),
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
	'a': univention.admin.property(
			short_description=_('IP Address'),
			long_description='',
			syntax=univention.admin.syntax.ipAddress,
			multivalue=1,
			options=[],
			required=0,
			may_change=1
		),
	'mx': univention.admin.property(
			short_description=_('Mail Exchanger'),
			long_description='',
			syntax=univention.admin.syntax.dnsMX,
			multivalue=1,
			options=[],
			required=0,
			may_change=1
		),
	'txt': univention.admin.property(
			short_description=_('Text Record'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=1,
			options=[],
			required=0,
			may_change=1
		)
}
layout=[
	univention.admin.tab(_('General'), _('Basic Values'), fields=[
		[univention.admin.field('name')],
		[univention.admin.field('a', first_only=1, short_description=_('Primary IP-Address'))],
		[univention.admin.field('zonettl')]
	]),
	univention.admin.tab(_('IP-Addresses'), _('IP Addresses of the Host'), fields=[
		[univention.admin.field('a')],
	]),
	univention.admin.tab(_('Mail'), _('Mail Exchangers for this Host'), fields=[
		[univention.admin.field('mx')],
	]),
	univention.admin.tab(_('Text'), _('Optional Text'), fields=[
		[univention.admin.field('txt')],
	])
]


def unmapMX(old):
	univention.debug.function('admin.handlers.dns.host_record.unmapMX old=%s' % str(old))
	new=[]
	for i in old:
		new.append(i.split(' '))
	return new

def mapMX(old):
	univention.debug.function('admin.handlers.dns.host_record.mapMX old=%s' % str(old))
	new=[]
	for i in old:
		new.append(string.join(i, ' '))
	return new

mapping=univention.admin.mapping.mapping()
mapping.register('name', 'relativeDomainName', None, univention.admin.mapping.ListToString)
mapping.register('a', 'aRecord')
mapping.register('mx', 'mXRecord', mapMX, unmapMX)
mapping.register('txt', 'tXTRecord')
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
			raise univention.admin.uexceptions.insufficientInformation, _( 'superordinate object not present' )
		if not dn and not position:
			raise univention.admin.uexceptions.insufficientInformation, _( 'neither DN nor position present' )

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

def lookup(co, lo, filter_s, base='', superordinate=None,scope="sub", unique=0, required=0, timeout=-1, sizelimit=0):

	filter=univention.admin.filter.conjunction('&', [
		univention.admin.filter.expression('objectClass', 'dNSZone'),
		univention.admin.filter.conjunction('!', [univention.admin.filter.expression('relativeDomainName', '@')]),
		univention.admin.filter.conjunction('!', [univention.admin.filter.expression('zoneName', '*.in-addr.arpa')]),
		univention.admin.filter.conjunction('!', [univention.admin.filter.expression('CNAMERecord', '*')]),
		univention.admin.filter.conjunction('!', [univention.admin.filter.expression('SRVRecord', '*')])
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

	univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'ALIAS(host_record) identify DN=%s'% dn)
	return 'dNSZone' in attr.get('objectClass', []) and\
		'@' not in attr.get('relativeDomainName', []) and\
		not attr['zoneName'][0].endswith('.in-addr.arpa') and\
		'*' not in attr.get('CNAMERecord', []) and\
		'*' not in attr.get('SRVRecord', []) and\
		('*' in attr.get('ARecord', []) or '*' in attr.get('MXRecord', []) )
