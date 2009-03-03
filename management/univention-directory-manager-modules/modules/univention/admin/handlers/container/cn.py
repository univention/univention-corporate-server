# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin module for the container objects
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
import univention.admin.uldap
import univention.admin.syntax
import univention.admin.filter
import univention.admin.handlers
import univention.admin.localization

translation=univention.admin.localization.translation('univention.admin.handlers.container')
_=translation.translate

module='container/cn'
operations=['add','edit','remove','search','move','subtree_move']
childs=1
short_description=_('Container: Container')
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
	'policyPath': univention.admin.property(
			short_description=_('Add to standard policy containers'),
			long_description='',
			syntax=univention.admin.syntax.boolean,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'dhcpPath': univention.admin.property(
			short_description=_('Add to standard DHCP containers'),
			long_description='',
			syntax=univention.admin.syntax.boolean,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'dnsPath': univention.admin.property(
			short_description=_('Add to standard DNS containers'),
			long_description='',
			syntax=univention.admin.syntax.boolean,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'userPath': univention.admin.property(
			short_description=_('Add to standard user containers'),
			long_description='',
			syntax=univention.admin.syntax.boolean,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'groupPath': univention.admin.property(
			short_description=_('Add to standard group containers'),
			long_description='',
			syntax=univention.admin.syntax.boolean,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'computerPath': univention.admin.property(
			short_description=_('Add to standard computer containers'),
			long_description='',
			syntax=univention.admin.syntax.boolean,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'networkPath': univention.admin.property(
			short_description=_('Add to standard network containers'),
			long_description='',
			syntax=univention.admin.syntax.boolean,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'sharePath': univention.admin.property(
			short_description=_('Add to standard share containers'),
			long_description='',
			syntax=univention.admin.syntax.boolean,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'printerPath': univention.admin.property(
			short_description=_('Add to standard printer containers'),
			long_description='',
			syntax=univention.admin.syntax.boolean,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'mailPath': univention.admin.property(
			short_description=_('Add to standard mail containers'),
			long_description='',
			syntax=univention.admin.syntax.boolean,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'licensePath': univention.admin.property(
			short_description=_('Add to standard license containers'),
			long_description='',
			syntax=univention.admin.syntax.boolean,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'description': univention.admin.property(
			short_description=_('Description'),
			long_description='',
			syntax=univention.admin.syntax.string,
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
layout=[
	univention.admin.tab(_('General'),_('Basic settings'),[
			[univention.admin.field("name"), univention.admin.field("description")],
			]),
	univention.admin.tab(_('Container settings'),_('Default position when adding objects'),[
			[univention.admin.field("userPath"), univention.admin.field("groupPath")],
			[univention.admin.field("computerPath"), univention.admin.field("policyPath")],
			[univention.admin.field("dnsPath"), univention.admin.field("dhcpPath")],
			[univention.admin.field("networkPath"), univention.admin.field("sharePath")],
			[univention.admin.field("printerPath"), univention.admin.field("mailPath")],
			[ univention.admin.field("licensePath")],
			], advanced = True)
]

mapping=univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('description', 'description', None, univention.admin.mapping.ListToString)

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
		self.default_dn=''

		univention.admin.handlers.simpleLdap.__init__(self, co, lo, position, dn, superordinate)

		self.save()

	def open(self):
		univention.admin.handlers.simpleLdap.open(self)

		pathResult = self.lo.get('cn=directory,cn=univention,'+self.position.getDomain())
		self.default_dn='cn=directory,cn=univention,'+self.position.getDomain()
		if not pathResult:
			pathResult = self.lo.get('cn=default containers,cn=univention,'+self.position.getDomain())
			self.default_dn='cn=default containers,cn=univention,'+self.position.getDomain()

		self.pathKeys=['userPath','groupPath','computerPath','policyPath','dnsPath','dhcpPath','networkPath', 'sharePath', 'printerPath', 'mailPath', 'licensePath']
		self.ldapKeys=['univentionUsersObject','univentionGroupsObject','univentionComputersObject','univentionPolicyObject','univentionDnsObject','univentionDhcpObject','univentionNetworksObject', 'univentionSharesObject', 'univentionPrintersObject', 'univentionMailObject', 'univentionLicenseObject']

		for key in self.pathKeys:
			self[key]='0'

		for i in range(0,len(self.pathKeys)):
			if pathResult.has_key(self.ldapKeys[i]):
				for j in pathResult[self.ldapKeys[i]]:
					if j == self.dn:
						self[self.pathKeys[i]]='1'

		self.save()

	def exists(self):
		return self._exists

	def _ldap_pre_create(self):
		self.dn='%s=%s,%s' % (mapping.mapName('name'), mapping.mapValue('name', self.info['name']), self.position.getDn())

	def _ldap_post_create(self):
		changes=[]

		for i in range(0,len(self.pathKeys)):
			if self.oldinfo[self.pathKeys[i]] != self.info[self.pathKeys[i]]:
				entries=self.lo.getAttr(self.default_dn,self.ldapKeys[i])
				if self.info[self.pathKeys[i]] == '0':
					if self.dn in entries:
						changes.append((self.ldapKeys[i],self.dn,''))
				else:
					if not self.dn in entries:
						changes.append((self.ldapKeys[i],'',self.dn))

		if changes:
			self.lo.modify(self.default_dn,changes)

	def _ldap_post_modify(self):
		changes=[]

		for i in range(0,len(self.pathKeys)):
			if self.oldinfo[self.pathKeys[i]] != self.info[self.pathKeys[i]]:
				if self.info[self.pathKeys[i]] == '0':
					changes.append((self.ldapKeys[i],self.dn,''))
				else:
					changes.append((self.ldapKeys[i],'',self.dn))
		if changes:
			self.lo.modify(self.default_dn,changes)

	def _ldap_post_move(self, olddn):
		settings_module=univention.admin.modules.get('settings/directory')
		settings_object=univention.admin.objects.get(settings_module, None, self.lo, position='', dn=self.default_dn)
		settings_object.open()
		for attr in ['dns','license','computers','shares','groups','printers','policies','dhcp','networks','users','mail']:
			if olddn in settings_object[attr]:
				settings_object[attr].remove(olddn)
				settings_object[attr].append(self.dn)
		settings_object.modify()

	def _ldap_pre_remove(self):
		changes=[]

		self.open()

		for i in range(0,len(self.pathKeys)):
			if self.oldinfo[self.pathKeys[i]] == '1':
				changes.append((self.ldapKeys[i],self.dn,''))
		self.lo.modify(self.default_dn,changes)


	def _ldap_addlist(self):
		return [
			('objectClass', ['top', 'organizationalRole'])
		]

def lookup(co, lo, filter_s, base='', superordinate=None, scope='sub', unique=0, required=0, timeout=-1, sizelimit=0):

	filter=univention.admin.filter.conjunction('&', [
		univention.admin.filter.expression('objectClass', 'organizationalRole'),
		univention.admin.filter.conjunction('!', [univention.admin.filter.expression('cn', 'univention')])
		])

	if filter_s:
		filter_p=univention.admin.filter.parse(filter_s)
		univention.admin.filter.walk(filter_p, univention.admin.mapping.mapRewrite, arg=mapping)
		filter.expressions.append(filter_p)

	res=[]
	for dn in lo.searchDn(unicode(filter), base, scope, unique, required, timeout, sizelimit):
		res.append(object(co, lo, None, dn))
	return res

def identify(dn, attr, canonical=0):

	return 'organizationalRole' in attr.get('objectClass', []) and not attr.get('cn', []) == ['univention']
