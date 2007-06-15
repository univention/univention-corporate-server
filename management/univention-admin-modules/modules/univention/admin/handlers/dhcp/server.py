# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin module for the DHCP server
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
import univention.admin.localization

translation=univention.admin.localization.translation('univention.admin.handlers.dhcp')
_=translation.translate

module='dhcp/server'
operations=['add','edit','remove','search','move']
superordinate='dhcp/service'
childs=0
usewizard=1
short_description=_('DHCP: Server')
long_description=''
options={
}

property_descriptions={
	'server': univention.admin.property(
			short_description=_('Server Name'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=[],
			required=1,
			may_change=1,
			identifies=1
		),
}

layout=[
	univention.admin.tab(_('General'), _('General Settings'), [
		[univention.admin.field('server')]
	])
]

mapping=univention.admin.mapping.mapping()
mapping.register('server', 'cn', None, univention.admin.mapping.ListToString)

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
		self.dn='%s=%s,%s' % (mapping.mapName('server'), mapping.mapValue('server', self.info['server']), self.position.getDn())

	def _ldap_addlist(self):
		searchBase=self.position.getDomain()
		if self.lo.searchDn(base=searchBase, filter='(&(objectClass=dhcpServer)(cn=%s))' % (self.info['server'])):
			raise univention.admin.uexceptions.dhcpServerAlreadyUsed, self.info['server']

		return [
			('objectClass', ['top', 'dhcpServer']),
			('dhcpServiceDN', self.superordinate.dn),
		]
	def _ldap_post_move(self, olddn):
		'''edit dhcpServiceDN'''
		oldServiceDN=self.lo.getAttr(self.dn, 'dhcpServiceDN')
		module=univention.admin.modules.identifyOne(self.position.getDn(), self.lo.get(self.position.getDn()))
		object=univention.admin.objects.get(module, None, self.lo, self.position, dn=self.position.getDn())
		shadow_module, shadow_object=univention.admin.objects.shadow(self.lo, module, object, self.position)
		self.lo.modify(self.dn, [('dhcpServiceDN', oldServiceDN[0], shadow_object.dn)])

def lookup(co, lo, filter_s, base='', superordinate=None, scope='sub', unique=0, required=0, timeout=-1, sizelimit=0):

	filter=univention.admin.filter.conjunction('&', [
	univention.admin.filter.expression('objectClass', 'dhcpServer')
	])

	if superordinate:
		filter.expressions.append(univention.admin.filter.expression('dhcpServiceDN', superordinate.dn))

	if filter_s:
		filter_p=univention.admin.filter.parse(filter_s)
		univention.admin.filter.walk(filter_p, univention.admin.mapping.mapRewrite, arg=mapping)
		filter.expressions.append(filter_p)

	res=[]
	for dn in lo.searchDn(unicode(filter), base, scope, unique, required, timeout, sizelimit):
		res.append((object(co, lo, None, dn, superordinate=superordinate)))
	return res

def identify(dn, attr):

	return 'dhcpServer' in attr.get('objectClass', [])
