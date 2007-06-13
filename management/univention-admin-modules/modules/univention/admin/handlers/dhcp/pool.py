# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin module for the DHCP pool
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

import sys, string, re, copy
import univention.admin.filter
import univention.admin.handlers
import univention.admin.localization
import univention.admin.uexceptions

translation=univention.admin.localization.translation('univention.admin.handlers.dhcp')
_=translation.translate

module='dhcp/pool'
operations=['add','edit','remove','search','move']
superordinate='dhcp/subnet'
childs=0
usewizard=1
short_description=_('DHCP: Pool')
long_description=''
options={
}
property_descriptions={
	'name': univention.admin.property(
			short_description=_('Name'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=[],
			required=1,
			may_change=0,
			identifies=1
		),
	'range': univention.admin.property(
			short_description=_('Dynamic Range'),
			long_description='',
			syntax=univention.admin.syntax.ipRange,
			multivalue=1,
			options=[],
			required=1,
			may_change=1,
			identifies=0
		),
	'failover_peer': univention.admin.property(
			short_description=_('Failover Peer'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0,
		),
	'known_clients': univention.admin.property(
			short_description=_('Allow Known Clients'),
			long_description='',
			syntax=univention.admin.syntax.AllowDeny,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'unknown_clients': univention.admin.property(
			short_description=_('Allow Unknown Clients'),
			long_description='',
			syntax=univention.admin.syntax.AllowDeny,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'dynamic_bootp_clients': univention.admin.property(
			short_description=_('Allow Dynamic BOOTP Clients'),
			long_description='',
			syntax=univention.admin.syntax.AllowDeny,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'all_clients': univention.admin.property(
			short_description=_('All Clients'),
			long_description='',
			syntax=univention.admin.syntax.AllowDeny,
			multivalue=0,
			options=[],
			required=0,
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
options={
}
layout=[
	univention.admin.tab(_('General'), _('Basic Values'), [
		[univention.admin.field('name'), univention.admin.field('range')]
	]),
	univention.admin.tab(_('Advanced'), _('Advanced DHCP Pool Options'), [
		[univention.admin.field('failover_peer'), univention.admin.field('filler')],
		[univention.admin.field('known_clients'),univention.admin.field('unknown_clients')],
		[univention.admin.field('dynamic_bootp_clients'),univention.admin.field('all_clients') ]
	])
]

def rangeMap(old):
	new=[]
	for i in old:
		new.append(string.join(i, ' '))
	return new

def rangeUnmap(old):
	new=[]
	for i in old:
		new.append(i.split(' '))
	return new

mapping=univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('range', 'dhcpRange', rangeMap, rangeUnmap)
mapping.register('failover_peer', 'univentionDhcpFailoverPeer', None, univention.admin.mapping.ListToString)

class object(univention.admin.handlers.simpleLdap):
	module=module

	def __init__(self, co, lo, position, dn='', superordinate=None, arg=None):
		global mapping
		global property_descriptions

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
	
	def open(self):

		univention.admin.handlers.simpleLdap.open(self)
	
		for i in self.oldattr.get('dhcpPermitList', []):
			pos=i.find(' ')
			permit=i[:pos]
			name=i[pos+1:]
			if name == 'known clients':
				self['known_clients']=permit
			elif name == 'unknown clients':
				self['unknown_clients']=permit
			elif name == 'dynamic bootp clients':
				self['dynamic_bootp_clients']=permit
			elif name == 'all clients':
				self['all_clients']=permit

		self.save()


	def exists(self):
		return self._exists
	
	def _ldap_pre_create(self):
		self.dn='%s=%s,%s' % (mapping.mapName('name'), mapping.mapValue('name', self.info['name']), self.position.getDn())

	def _ldap_addlist(self):
		return [
			('objectClass', ['top', 'univentionDhcpPool']),
		]
	
	def _ldap_modlist(self):
		ml=univention.admin.handlers.simpleLdap._ldap_modlist(self)
		if self.hasChanged(['known_clients', 'unknown_clients', 'dynamic_bootp_clients', 'all_clients']):
			old=self.oldattr.get('dhcpPermitList', [])
			new=copy.deepcopy(old)

			if self.oldinfo.has_key('known_clients') and self.oldinfo['known_clients']:
				new.remove(self.oldinfo['known_clients']+' known clients')
			if self.info.has_key('known_clients') and self.info['known_clients']:
				new.append(self.info['known_clients']+' known clients')
				
			if self.oldinfo.has_key('unknown_clients') and self.oldinfo['unknown_clients']:
				new.remove(self.oldinfo['unknown_clients']+' unknown clients')
			if self.info.has_key('unknown_clients') and self.info['unknown_clients']:
				new.append(self.info['unknown_clients']+' unknown clients')

			if self.oldinfo.has_key('dynamic_bootp_clients') and self.oldinfo['dynamic_bootp_clients']:
				new.remove(self.oldinfo['dynamic_bootp_clients']+' dynamic bootp clients')
			if self.info.has_key('dynamic_bootp_clients') and self.info['dynamic_bootp_clients']:
				new.append(self.info['dynamic_bootp_clients']+' dynamic bootp clients')
			
			if self.oldinfo.has_key('all_clients') and self.oldinfo['all_clients']:
				new.remove(self.oldinfo['all_clients']+' all clients')
			if self.info.has_key('all_clients') and self.info['all_clients']:
				new.append(self.info['all_clients']+' all clients')
				
			ml.append(('dhcpPermitList', old, new))
		if self.info.get('failover_peer', None) and not self.info.get('dynamic_bootp_clients', None) == 'deny':
			raise univention.admin.uexceptions.bootpXORFailover
		return ml
		
def lookup(co, lo, filter_s, base='', superordinate=None, scope='sub', unique=0, required=0, timeout=-1, sizelimit=0):

	filter=univention.admin.filter.conjunction('&', [
	univention.admin.filter.expression('objectClass', 'univentionDhcpPool')
	])
	
	if filter_s:
		filter_p=univention.admin.filter.parse(filter_s)
		univention.admin.filter.walk(filter_p, univention.admin.mapping.mapRewrite, arg=mapping)
		filter.expressions.append(filter_p)

	res=[]
	for dn in lo.searchDn(unicode(filter), base, scope, unique, required, timeout, sizelimit):
		res.append((object(co, lo, None, dn, superordinate=superordinate)))
	return res

def identify(dn, attr):
	
	return 'univentionDhcpPool' in attr.get('objectClass', [])
