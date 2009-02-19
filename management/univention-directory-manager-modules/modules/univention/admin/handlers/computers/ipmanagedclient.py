# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin module for the ip managed clients
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

import sys, string, ldap, copy
import univention.admin.filter
import univention.admin.handlers
import univention.admin.password
import univention.admin.allocators
import univention.admin.localization
import univention.admin.uldap
import univention.admin.nagios as nagios
import univention.admin.handlers.dns.forward_zone
import univention.admin.handlers.dns.reverse_zone
import univention.admin.handlers.networks.network

translation=univention.admin.localization.translation('univention.admin.handlers.computers')
_=translation.translate

module='computers/ipmanagedclient'
operations=['add','edit','remove','search','move']
usewizard=1
docleanup=1
childs=0
short_description=_('Computer: IP managed client')
long_description=''
options={
}
property_descriptions={
	'name': univention.admin.property(
			short_description=_('IP managed client name'),
			long_description='',
			syntax=univention.admin.syntax.hostName,
			multivalue=0,
			options=[],
			required=1,
			may_change=0,
			identifies=1
		),
	'description': univention.admin.property(
			short_description=_('Description'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			required=0,
			may_change=1,
			identifies=0
		),	
	'mac': univention.admin.property(
			short_description=_('MAC address'),
			long_description='',
			syntax=univention.admin.syntax.macAddress,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'network': univention.admin.property(
			short_description=_('Network'),
			long_description='',
			syntax=univention.admin.syntax.network,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'ip': univention.admin.property(
			short_description=_('IP address'),
			long_description='',
			syntax=univention.admin.syntax.ipAddress,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'dnsEntryZoneForward': univention.admin.property(
			short_description=_('Forward zone for DNS entry'),
			long_description='',
			syntax=univention.admin.syntax.dnsEntry,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			dontsearch=1,
			identifies=0
		),
	'dnsEntryZoneReverse': univention.admin.property(
			short_description=_('Reverse zone for DNS entry'),
			long_description='',
			syntax=univention.admin.syntax.dnsEntryReverse,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			dontsearch=1,
			identifies=0
		),
	'dhcpEntryZone': univention.admin.property(
			short_description=_('Service for DHCP entry'),
			long_description='',
			syntax=univention.admin.syntax.dhcpEntry,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			dontsearch=1,
			identifies=0
		),
	'inventoryNumber': univention.admin.property(
			short_description=_('Inventory number'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'groups': univention.admin.property(
			short_description=_('Groups'),
			long_description='',
			syntax=univention.admin.syntax.groupDn,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			dontsearch=1,
			identifies=0
		),
	'domain': univention.admin.property(
			short_description=_('Domain'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			required=0,
			may_change=1,
			identifies=0
		),
}
layout=[
	univention.admin.tab(_('General'),_('Basic settings'),[
			[univention.admin.field("name"), univention.admin.field('description')],
			[univention.admin.field("mac"), univention.admin.field('network')],
			[univention.admin.field("inventoryNumber")],
		]),
	univention.admin.tab(_('IP'),_('IP'),[
			[univention.admin.field("ip")],
		]),
	univention.admin.tab(_('DNS'),_('DNS Forward and Reverse Lookup Zone'),[
			[univention.admin.field("dnsEntryZoneForward")],
			[univention.admin.field("dnsEntryZoneReverse")]
		]),
	univention.admin.tab(_('DHCP'),_('DHCP'),[
			[univention.admin.field("dhcpEntryZone")]
		]),
	univention.admin.tab(_('Groups'),_('Group memberships'),[
			[univention.admin.field("groups")],
		], advanced = True)
]

mapping=univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('description', 'description', None, univention.admin.mapping.ListToString)
mapping.register('inventoryNumber', 'univentionInventoryNumber')
mapping.register('mac', 'macAddress' )
mapping.register('ip', 'aRecord' )
mapping.register('network', 'univentionNetworkLink', None, univention.admin.mapping.ListToString)
mapping.register('domain', 'associatedDomain', None, univention.admin.mapping.ListToString)

# add Nagios extension
nagios.addPropertiesMappingOptionsAndLayout(property_descriptions, mapping, options, layout)


class object(univention.admin.handlers.simpleComputer, nagios.Support):
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

		self.alloc=[]
		self.options = []

		self.ipRequest=0

		univention.admin.handlers.simpleComputer.__init__(self, co, lo, position, dn, superordinate)

		nagios.Support.__init__(self)

		self.save( )

	def open(self):

		univention.admin.handlers.simpleComputer.open( self )
		self.nagios_open()

		if not self.dn:
			return

		self.save()

	def exists(self):
		return self._exists
	
	def _ldap_pre_create(self):
		self.dn='%s=%s,%s' % (mapping.mapName('name'), mapping.mapValue('name', self.info['name']), self.position.getDn())
		self.nagios_ldap_pre_create()
		univention.admin.handlers.simpleComputer._ldap_pre_create( self )

	def _ldap_addlist(self):
		return [ ('objectClass', ['top', 'univentionHost','univentionClient', 'person']) ]

	def _ldap_post_create(self):
		univention.admin.handlers.simpleComputer._ldap_post_create( self )
		self.nagios_ldap_post_create()

	def _ldap_post_remove(self):
		self.nagios_ldap_post_remove()
		univention.admin.handlers.simpleComputer._ldap_post_remove( self )

	def _ldap_post_modify(self):
		univention.admin.handlers.simpleComputer._ldap_post_modify( self )
		self.nagios_ldap_post_modify()

	def _ldap_pre_modify(self):
		univention.admin.handlers.simpleComputer._ldap_pre_modify( self )
		self.nagios_ldap_pre_modify()

	def _ldap_modlist(self):
		ml=univention.admin.handlers.simpleComputer._ldap_modlist( self )
		self.nagios_ldap_modlist(ml)
		return ml

	def cleanup(self):
		self.open()
		self.nagios_cleanup()
		univention.admin.handlers.simpleComputer.cleanup( self )

	def cancel(self):
		for key, value in self.alloc:
			univention.debug.debug(univention.debug.ADMIN, univention.debug.WARN, 'cancel: release (%s): %s' % (key, value) )
			univention.admin.allocators.release(self.lo, self.position, key, value)

def rewrite(filter, mapping):
	if filter.variable == 'ip':
		filter.variable='aRecord'
	else:
		univention.admin.mapping.mapRewrite(filter, mapping)

def lookup(co, lo, filter_s, base='', superordinate=None, scope='sub', unique=0, required=0, timeout=-1, sizelimit=0):
	filter=univention.admin.filter.conjunction('&', [
		univention.admin.filter.expression('objectClass', 'univentionHost'),
		univention.admin.filter.expression('objectClass', 'univentionClient'),
		univention.admin.filter.conjunction('!', [univention.admin.filter.expression('objectClass', 'posixAccount')]),
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
	return 'univentionHost' in attr.get('objectClass', []) and 'univentionClient' in attr.get('objectClass', []) and not 'posixAccount' in attr.get('objectClass', [])

