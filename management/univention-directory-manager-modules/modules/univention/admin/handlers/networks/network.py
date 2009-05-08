# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin module for network objects
#
# Copyright (C) 2004-2009 Univention GmbH
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

import sys, string, re , copy, time, sha
import socket, struct
import univention.admin.filter
import univention.admin.handlers
import univention.admin.ipaddress
import univention.admin.localization

import univention.debug

translation=univention.admin.localization.translation('univention.admin.handlers.networks')
_=translation.translate

module='networks/network'
operations=['add','edit','remove','search']
usewizard=1
wizardmenustring=_("Networks")
wizarddescription=_("Add, edit and delete networks")
wizardoperations={"add":[_("Add"), _("Add network object")],"find":[_("Search"), _("Search network object(s)")]}

childs=0
short_description=_('Networks: Network')
long_description=''

property_descriptions={
	'name': univention.admin.property(
			short_description=_('Name'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			required=1,
			may_change=0,
			identifies=1
		),
	'network': univention.admin.property(
			short_description=_('Networks'),
			long_description='',
			syntax=univention.admin.syntax.ipAddress,
			multivalue=0,
			required=1,
			may_change=0,
			identifies=0
		),
	'netmask': univention.admin.property(
			short_description=_('Netmask'),
			long_description='',
			syntax=univention.admin.syntax.netmask,
			multivalue=0,
			required=1,
			may_change=0,
			identifies=0
		),
	'nextIp': univention.admin.property(
			short_description=_('Next IP address'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			required=0,
			may_change=1,
			identifies=0
		),
	'ipRange': univention.admin.property(
			short_description=_('IP Address Range'),
			long_description='',
			syntax=univention.admin.syntax.ipRange,
			multivalue=1,
			dontsearch=1,
			required=0,
			may_change=1,
			identifies=0
		),
	'dnsEntryZoneForward': univention.admin.property(
			short_description=_('DNS forward lookup zone'),
			long_description='',
			syntax=univention.admin.syntax.dnsEntryNetwork,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			dontsearch=1,
			identifies=0
		),
	'dnsEntryZoneReverse': univention.admin.property(
			short_description=_('DNS reverse lookup zone'),
			long_description='',
			syntax=univention.admin.syntax.dnsEntryReverseNetwork,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			dontsearch=1,
			identifies=0
		),
	'dhcpEntryZone': univention.admin.property(
			short_description=_('DHCP service'),
			long_description='',
			syntax=univention.admin.syntax.dhcpEntryNetwork,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			dontsearch=1,
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
	univention.admin.tab(_('General'),_('Basic settings'), [
		[univention.admin.field('name'), univention.admin.field('filler')],
		[univention.admin.field('network'), univention.admin.field('netmask')],
	]),
	univention.admin.tab(_('IP'),_('IP address ranges'), [
		[univention.admin.field('ipRange')],
	]),
	univention.admin.tab(_('DNS'),_('DNS preferences'), [
		[univention.admin.field('dnsEntryZoneForward') ],
		[ univention.admin.field('dnsEntryZoneReverse')],
	]),
	univention.admin.tab(_('DHCP'),_('DHCP'),[
			[univention.admin.field("dhcpEntryZone")]
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
mapping.register('network', 'univentionNetwork', None, univention.admin.mapping.ListToString)
mapping.register('netmask','univentionNetmask', None, univention.admin.mapping.ListToString)
mapping.register('nextIp','univentionNextIp', None, univention.admin.mapping.ListToString)
mapping.register('dnsEntryZoneForward','univentionDnsForwardZone', univention.admin.mapping.IgnoreNone, univention.admin.mapping.ListToString)
mapping.register('dnsEntryZoneReverse','univentionDnsReverseZone', univention.admin.mapping.IgnoreNone, univention.admin.mapping.ListToString)
mapping.register('dhcpEntryZone','univentionDhcpEntry', univention.admin.mapping.IgnoreNone, univention.admin.mapping.ListToString)

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

		univention.admin.handlers.simpleLdap.__init__(self, co, lo, position, dn, superordinate)

	def open(self):
		univention.admin.handlers.simpleLdap.open(self)

		self['ipRange']=[]
		if self.dn:
			ipRange=self.oldattr.get('univentionIpRange',[])
			if ipRange:
				self['ipRange']=[]
			for i in ipRange:
				self['ipRange'].append(i.split(' '))

		self.save()

	def stepIp(self):
		if self['nextIp']:
			# nextIP is already set:
			#	- check range for actual ip
			#	- inc ip
			#	- check for range
			range=''
			for r in self['ipRange']:
				if univention.admin.ipaddress.is_ip_in_range(self['nextIp'], r):
					range=r
			newIp=univention.admin.ipaddress.ip_plus_one(self['nextIp'])
			if range:
				if not univention.admin.ipaddress.is_ip_in_range(newIp, range):
					try:
						position = self['ipRange'].index(range)
					except:
						position = self['nextIp'].index(range)
					position += 1
					if position < len(self['ipRange']):
						self['nextIp']=self['ipRange'][position][0]
					else:
						self['nextIp'] = self['ipRange'][0][0]
				else:
					self['nextIp'] = newIp
			elif self['ipRange']:
				self['nextIp']=self['ipRange'][0][0]
				if self['nextIp'].split('.')[3] == '0':
					self['nextIp']=univention.admin.ipaddress.ip_plus_one(self['ipRange'][0][0])
				
			else:
				if not univention.admin.ipaddress.ip_is_in_network(self['network'], self['netmask'], newIp):
					self['nextIp']=univention.admin.ipaddress.ip_plus_one(self['network'])
				else:
					self['nextIp'] = newIp

		elif self['ipRange']:
			# nextIP is not set
			# 	- use first ip range entry
			self['nextIp']=self['ipRange'][0][0]
			if self['nextIp'].split('.')[3] == '0':
				self['nextIp']=univention.admin.ipaddress.ip_plus_one(self['ipRange'][0][0])

		elif self['network']:
			# nextIP is not set, no IPrange, then we use the first ip of the network
			self['nextIp']=univention.admin.ipaddress.ip_plus_one(self['network'])
			if not univention.admin.ipaddress.ip_is_in_network(self['network'], self['netmask'], self['nextIp']):
				pass


	def _ldap_pre_create(self):
		self.dn='%s=%s,%s' % (mapping.mapName('name'), mapping.mapValue('name', self.info['name']), self.position.getDn())

	def _ldap_addlist(self):
		if not self['nextIp']:
			self.stepIp()

		return [
			('objectClass', ['top', 'univentionNetworkClass']),
		]

	def _ldap_modlist(self):

		ml=univention.admin.handlers.simpleLdap._ldap_modlist(self)

		next_ip_changed=0
		next_ip_in_range=0

		if self.hasChanged('ipRange'):
			ipRange=[]
			for i in self['ipRange']:
				if univention.admin.ipaddress.is_ip_in_range(self['nextIp'], i):
					next_ip_in_range=1
				for j in self['ipRange']:
					if i != j and univention.admin.ipaddress.is_range_overlapping(i, j):
						raise univention.admin.uexceptions.rangesOverlapping, '%s-%s; %s-%s' % (i[0], i[1], j[0], j[1])
				ip_in_network=1
				for j in i:
					if not univention.admin.ipaddress.ip_is_in_network(self['network'], self['netmask'], j):
						ip_in_network=0

					if univention.admin.ipaddress.ip_is_network_address(self['network'], self['netmask'], j):
						raise univention.admin.uexceptions.rangeInNetworkAddress, '%s-%s' % (i[0], i[1])

					if univention.admin.ipaddress.ip_is_broadcast_address(self['network'], self['netmask'], j):
						raise univention.admin.uexceptions.rangeInBroadcastAddress, '%s-%s' % (i[0], i[1])

				if ip_in_network:
					ipRange.append(string.join(i, ' '))
				else:
					raise univention.admin.uexceptions.rangeNotInNetwork, '%s-%s' % (i[0], i[1])
			univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'old Range: %s' % self.oldinfo['ipRange'])
			if self.oldinfo.has_key('ipRange') and self['ipRange'] and not self.oldinfo['ipRange'] or not next_ip_in_range:
				if len(self['ipRange']) > 0 and len(self['ipRange'][0]) > 0:
					self['nextIp'] = self['ipRange'][0][0]
				else:
					self['nextIp'] = ''
				if not self.oldattr.get('univentionNextIp', '') == self['nextIp']:
					next_ip_changed=1
				univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'set nextIP')
				if self['nextIp'] and self['nextIp'].split('.')[3] == '0':
					self['nextIp']=self.ip_plus_one(self['ipRange'][0][0])
					next_ip_changed=1

			ml.append(('univentionIpRange', self.oldattr.get('univentionIpRange', ['']), ipRange))

		if next_ip_changed:
			rmel=''
			for el in ml: # mapping may have set nextIp already, we want our value
				if el[0] == 'univentionNextIp':
					rmel = el
			if rmel:
				ml.remove(rmel)
			ml.append(('univentionNextIp', self.oldattr.get('univentionNextIp', ''), self['nextIp']))

		return ml

	def exists(self):
		return self._exists

def rewrite(filter, mapping):
	univention.admin.mapping.mapRewrite(filter, mapping)

def lookup(co, lo, filter_s, base='', superordinate=None, scope='sub', unique=0, required=0, timeout=-1, sizelimit=0):

	filter=univention.admin.filter.conjunction('&', [
		univention.admin.filter.expression('objectClass', 'univentionNetworkClass'),
	])

	if filter_s:
		filter_p=univention.admin.filter.parse(filter_s)
		univention.admin.filter.walk(filter_p, rewrite, arg=mapping)
		filter.expressions.append(filter_p)

	res=[]
	for dn in lo.searchDn(unicode(filter), base, scope, unique, required, timeout, sizelimit):
		res.append(object(co, lo, None, dn))
	return res

def identify(dn, attr, canonical=0):
	
	return 'univentionNetworkClass' in attr.get('objectClass', [])

