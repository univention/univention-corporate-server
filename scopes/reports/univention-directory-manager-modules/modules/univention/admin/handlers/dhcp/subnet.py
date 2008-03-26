# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin module for the DHCP subnet
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
import socket, struct
import univention.admin.filter
import univention.admin.handlers
import univention.admin.ipaddress
import univention.admin.localization

translation=univention.admin.localization.translation('univention.admin.handlers.dhcp')
_=translation.translate

module='dhcp/subnet'
operations=['add','edit','remove','search','move']
superordinate='dhcp/service'
childs=1
usewizard=1
short_description=_('DHCP: Subnet')
long_description=''
options={
}
property_descriptions={
	'subnet': univention.admin.property(
			short_description=_('Subnet Address'),
			long_description='',
			syntax=univention.admin.syntax.ipAddress,
			multivalue=0,
			options=[],
			required=1,
			may_change=0,
			identifies=1
		),
	'subnetmask': univention.admin.property(
			short_description=_('Netmask'),
			long_description='',
			syntax=univention.admin.syntax.netmask,
			multivalue=0,
			options=[],
			required=1,
			may_change=1,
			identifies=0
		),
	'broadcastaddress': univention.admin.property(
			short_description=_('Broadcast Address'),
			long_description='',
			syntax=univention.admin.syntax.ipAddress,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'range': univention.admin.property(
			short_description=_('Dynamic Range'),
			long_description='',
			syntax=univention.admin.syntax.ipRange,
			multivalue=1,
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
		[univention.admin.field('subnet'),univention.admin.field('subnetmask')],
		[univention.admin.field('broadcastaddress'),univention.admin.field('filler')]
	]),
	univention.admin.tab(_('Dynamic Address Assignment'), _('Define a pool of addresses available for dynamic address assignment.'), [
		[univention.admin.field('range')]
	]),
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
mapping.register('subnet', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('subnetmask', 'dhcpNetMask', None, univention.admin.mapping.ListToString)
mapping.register('broadcastaddress', 'univentionDhcpBroadcastAddress', None, univention.admin.mapping.ListToString)

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

		self['range']=[]
		if self.dn:
			dhcpRange=self.oldattr.get('dhcpRange',[])
			if dhcpRange:
				self['range']=[]
			for i in dhcpRange:
				self['range'].append(i.split(' '))

		self.save()

	def exists(self):
		return self._exists
	
	def _ldap_pre_create(self):
		self.dn='%s=%s,%s' % (mapping.mapName('subnet'), mapping.mapValue('subnet', self.info['subnet']), self.position.getDn())

	def _ldap_addlist(self):
		return [
			('objectClass', ['top', 'univentionDhcpSubnet']),
		]

	def _ldap_modlist(self):

		ml=univention.admin.handlers.simpleLdap._ldap_modlist(self)

		if self.hasChanged('range'):
			dhcpRange=[]
			for i in self['range']:
				for j in self['range']:
					if i != j and univention.admin.ipaddress.is_range_overlapping(i, j):
						raise univention.admin.uexceptions.rangesOverlapping, '%s-%s; %s-%s' % (i[0], i[1], j[0], j[1])

				ip_in_network=1
				for j in i:
					if not univention.admin.ipaddress.ip_is_in_network(self['subnet'], self['subnetmask'], j):
						ip_in_network=0

					if univention.admin.ipaddress.ip_is_network_address(self['subnet'], self['subnetmask'], j):
						raise univention.admin.uexceptions.rangeInNetworkAddress, '%s-%s' % (i[0], i[1])

					if univention.admin.ipaddress.ip_is_broadcast_address(self['subnet'], self['subnetmask'], j):
						raise univention.admin.uexceptions.rangeInBroadcastAddress, '%s-%s' % (i[0], i[1])

				if ip_in_network:
					dhcpRange.append(string.join(i, ' '))
				else:
					raise univention.admin.uexceptions.rangeNotInNetwork, '%s-%s' % (i[0], i[1])
			univention.debug.debug(univention.debug.ADMIN, univention.debug.ERROR, 'old Range: %s' % self.oldinfo['range'])
			ml.append(('dhcpRange', self.oldattr.get('dhcpRange', ['']), dhcpRange))

		return ml

def lookup(co, lo, filter_s, base='', superordinate=None, scope='sub', unique=0, required=0, timeout=-1, sizelimit=0):

	filter=univention.admin.filter.conjunction('&', [
	univention.admin.filter.expression('objectClass', 'univentionDhcpSubnet'),
	univention.admin.filter.conjunction('!', [univention.admin.filter.expression('objectClass', 'univentionDhcpSharedSubnet')])
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
	
	return 'univentionDhcpSubnet' in attr.get('objectClass', []) and not 'univentionDhcpSharedSubnet' in attr.get('objectClass', [])
