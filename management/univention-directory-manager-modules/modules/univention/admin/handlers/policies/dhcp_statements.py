# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin policy for the DHCP statements
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

import sys, string
import univention.admin.syntax
import univention.admin.filter
import univention.admin.handlers
import univention.admin.localization

translation=univention.admin.localization.translation('univention.admin.handlers.policies')
_=translation.translate

class dhcp_statementsFixedAttributes(univention.admin.syntax.select):
	name='dhcp_statementsFixedAttributes'
	choices=[
		('univentionDhcpAuthoritative',_('Authoritative')),
		('univentionDhcpBootUnknownClients',_('Boot unknown clients')),
		('univentionDhcpPingCheck',_('Ping check')),
		('univentionDhcpGetLeaseHostnames',_('Add hostnames to leases')),
		('univentionDhcpServerIdentifier',_('Server identifier')),
		('univentionDhcpServerName',_('Server name')),
		]

module='policies/dhcp_statements'
operations=['add','edit','remove','search']

policy_oc="univentionPolicyDhcpStatements"
policy_apply_to=["dhcp/host", "dhcp/pool", "dhcp/service", "dhcp/subnet", "dhcp/sharedsubnet", "dhcp/shared"]
policy_position_dn_prefix="cn=statements,cn=dhcp"
policies_group="dhcp"
usewizard=1
childs=0
short_description=_('Policy: DHCP statements')
policy_short_description=_('DHCP statement')
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
			identifies=1,
		),
	'authoritative': univention.admin.property(
			short_description=_('Authoritative'),
			long_description=_('Send DHCPNAK messages to misconfigured clients. Disabled by default.'),
			syntax=univention.admin.syntax.booleanNone,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
			),
	'boot-unknown-clients': univention.admin.property(
			short_description=_('Boot unknown clients'),
			long_description=_('Enable clients for which there is no host declaration to obtain IP addresses. Allow and deny statements within pool declarations will still be respected.'),
			syntax=univention.admin.syntax.TrueFalse,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
			),
	'pingCheck': univention.admin.property(
			short_description=_('Ping check'),
			long_description=_('First send an ICMP Echo request (a ping) when considering dynamically allocating an IP address. Should only be disabled if the delay of one second introduced by this is a problem for a client.'),
			syntax=univention.admin.syntax.TrueFalse,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
			),
	'getLeaseHostnames': univention.admin.property(
			short_description=_('Add hostnames to leases'),
			long_description=_('Look up the domain name corresponding to the IP address of each address in the lease pool and use that address for the DHCP hostname option. Disabled by default.'),
			syntax=univention.admin.syntax.TrueFalse,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
			),
	'serverIdentifier': univention.admin.property(
			short_description=_('Server identifier'),
			long_description=_('An IP address identifing the server that should be used by the clients for further requests. Using this is not recommended.'),
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
			),
	'serverName': univention.admin.property(
			short_description=_('Server name'),
			long_description=_('Define the IP address of the boot server'),
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
			),
	'requiredObjectClasses': univention.admin.property(
			short_description=_('Required object classes'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
			),
	'prohibitedObjectClasses': univention.admin.property(
			short_description=_('Excluded object classes'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
			),
	'fixedAttributes': univention.admin.property(
			short_description=_('Fixed attributes'),
			long_description='',
			syntax=dhcp_statementsFixedAttributes,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
			),
	'emptyAttributes': univention.admin.property(
			short_description=_('Empty attributes'),
			long_description='',
			syntax=dhcp_statementsFixedAttributes,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
			),
	'filler': univention.admin.property(
			short_description='',
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
	univention.admin.tab(_('DHCP statements'), _('Miscellaneous DHCP statements'), [
		[univention.admin.field('name', hide_in_resultmode=1), univention.admin.field('filler', hide_in_resultmode=1)],
		[univention.admin.field('authoritative'),univention.admin.field('boot-unknown-clients')],
		[univention.admin.field('pingCheck'), univention.admin.field('getLeaseHostnames')],
		[univention.admin.field('serverIdentifier'), univention.admin.field('serverName')]
	]),
	univention.admin.tab(_('Object'),_('Object'), [
		[univention.admin.field('requiredObjectClasses') , univention.admin.field('prohibitedObjectClasses') ],
		[univention.admin.field('fixedAttributes'), univention.admin.field('emptyAttributes')]
	], advanced = True),
]

mapping=univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('authoritative', 'univentionDhcpAuthoritative', None, univention.admin.mapping.ListToString)
mapping.register('boot-unknown-clients', 'univentionDhcpBootUnknownClients', None, univention.admin.mapping.ListToString)
mapping.register('pingCheck', 'univentionDhcpPingCheck', None, univention.admin.mapping.ListToString)
mapping.register('getLeaseHostnames', 'univentionDhcpGetLeaseHostnames', None, univention.admin.mapping.ListToString)
mapping.register('serverIdentifier', 'univentionDhcpServerIdentifier', None, univention.admin.mapping.ListToString)
mapping.register('serverName', 'univentionDhcpServerName', None, univention.admin.mapping.ListToString)

mapping.register('requiredObjectClasses', 'requiredObjectClasses')
mapping.register('prohibitedObjectClasses', 'prohibitedObjectClasses')
mapping.register('fixedAttributes', 'fixedAttributes')
mapping.register('emptyAttributes', 'emptyAttributes')

class object(univention.admin.handlers.simplePolicy):
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

		univention.admin.handlers.simplePolicy.__init__(self, co, lo, position, dn, superordinate)

	def exists(self):
		return self._exists

	def _ldap_pre_create(self):
		self.dn='%s=%s,%s' % (mapping.mapName('name'), mapping.mapValue('name', self.info['name']), self.position.getDn())

	def _ldap_addlist(self):
		return [
			('objectClass', ['top', 'univentionPolicy', 'univentionPolicyDhcpStatements'])
		]

def lookup(co, lo, filter_s, base='', superordinate=None, scope='sub', unique=0, required=0, timeout=-1, sizelimit=0):

	filter=univention.admin.filter.conjunction('&', [
		univention.admin.filter.expression('objectClass', 'univentionPolicyDhcpStatements'),
		])

	if filter_s:
		filter_p=univention.admin.filter.parse(filter_s)
		univention.admin.filter.walk(filter_p, univention.admin.mapping.mapRewrite, arg=mapping)
		filter.expressions.append(filter_p)

	res=[]
	try:
		for dn in lo.searchDn(unicode(filter), base, scope, unique, required, timeout, sizelimit):
			res.append(object(co, lo, None, dn))
	except:
		pass
	return res

def identify(dn, attr, canonical=0):

	return 'univentionPolicyDhcpStatements' in attr.get('objectClass', [])
