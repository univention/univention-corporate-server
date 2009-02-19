# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin module for the DHCP hosts
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
import univention.admin.filter
import univention.admin.handlers
import univention.admin.localization

translation=univention.admin.localization.translation('univention.admin.handlers.dhcp')
_=translation.translate

module='dhcp/host'
operations=['add','edit','remove','search','move']
superordinate='dhcp/service'
childs=0
usewizard=1
short_description=_('DHCP: Host')
long_description=''
options={
}
property_descriptions={
	'host':  univention.admin.property(
			short_description=_('Hostname'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=[],
			required=1,
			may_change=1,
			identifies=1
		),
	'hwaddress': univention.admin.property(
			short_description=_('Hardware address'),
			long_description=_('Currently, only the ethernet and token-ring types are recognized. \
The hardware-address should be a set of hexadecimal octets (numbers from 0 through ff) separated by colons.'),
			syntax=univention.admin.syntax.dhcpHWAddress,
			multivalue=0,
			options=[],
			required=1,
			may_change=1,
			identifies=0
		),
	'fixedaddress': univention.admin.property(
			short_description=_('Fixed IP address'),
			long_description=_('Assign one or more fixed IP addresses. \
Each address should be either an IP address or a domain name that resolves to one or more IP addresses'),
			syntax=univention.admin.syntax.string,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
}
layout=[
	univention.admin.tab(_('General'), _('Basic settings'), [
		[univention.admin.field('host')],
		[univention.admin.field('hwaddress')]
	]),
	univention.admin.tab(_('Fixed IP addresses'), _('Fixed IP Addresses of the Host'), [
		[univention.admin.field('fixedaddress')]
	])
]

def unmapHWAddress(old):
	if not old:
		return ['', '']
	return old[0].split(' ')

def mapHWAddress(old):
	if not old[0]:
		return ''
	else:
		return '%s %s' % (old[0], old[1])

mapping=univention.admin.mapping.mapping()
mapping.register('host', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('hwaddress', 'dhcpHWAddress', mapHWAddress, unmapHWAddress)
mapping.register('fixedaddress', 'univentionDhcpFixedAddress')

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

	def exists(self):
		return self._exists

	def _ldap_pre_create(self):
		self.dn='%s=%s,%s' % (mapping.mapName('host'), mapping.mapValue('host', self.info['host']), self.position.getDn())

	def _ldap_addlist(self):
		return [
			('objectClass', ['top', 'univentionDhcpHost']),
		]

def lookup(co, lo, filter_s, base='', superordinate=None, scope='sub', unique=0, required=0, timeout=-1, sizelimit=0):

	filter=univention.admin.filter.conjunction('&', [
	univention.admin.filter.expression('objectClass', 'univentionDhcpHost')
	])

	if filter_s:
		filter_p=univention.admin.filter.parse(filter_s)
		univention.admin.filter.walk(filter_p, univention.admin.mapping.mapRewrite, arg=mapping)
		filter.expressions.append(filter_p)

	res=[]
	for dn in lo.searchDn(unicode(filter), base, scope, unique, required, timeout, sizelimit):
		res.append((object(co, lo, None, dn=dn, superordinate=superordinate)))
	return res

def identify(dn, attr):

	return 'univentionDhcpHost' in attr.get('objectClass', [])
