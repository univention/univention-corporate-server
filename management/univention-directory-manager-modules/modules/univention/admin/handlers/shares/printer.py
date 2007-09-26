# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin module for printers
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
import univention.admin.uldap
import univention.admin.syntax
import univention.admin.filter
import univention.admin.handlers
import univention.admin.localization

import univention.debug
import univention.admin.uexceptions

translation=univention.admin.localization.translation('univention.admin.handlers.shares')
_=translation.translate

class printerACLTypes(univention.admin.syntax.select):
        name='printerACLTypes'
        choices=[
		('allow all',_('Allow all users.')),
                ('allow',_('Allow only choosen users/groups.')),
                ('deny',_('Deny choosen users/groups.')),
                ]

module='shares/printer'
operations=['add','edit','remove','search','move']

childs=0
short_description=_('Print-Share: Printer')
long_description=''
options={
}
property_descriptions={
	'name': univention.admin.property(
			short_description=_('Name'),
			long_description='',
			syntax=univention.admin.syntax.printerName,
			multivalue=0,
			options=[],
			required=1,
			may_change=0,
			identifies=1
		),
	'location' : univention.admin.property(
			short_description = _( 'Location' ),
			long_description = '',
			syntax = univention.admin.syntax.string,
			multivalue = 0,
			options = [],
			required = 0,
			may_change = 1,
			identifies = 0
		),
	'description' : univention.admin.property(
			short_description = _( 'Description' ),
			long_description = '',
			syntax = univention.admin.syntax.string,
			multivalue = 0,
			options = [],
			required = 0,
			may_change = 1,
			identifies = 0
		),
	'spoolHost': univention.admin.property(
			short_description=_('Spool Host'),
			long_description='',
			syntax=univention.admin.syntax.spoolHost,
			multivalue=1,
			options=[],
			required=1,
			may_change=1,
			identifies=0
		),
	'uri': univention.admin.property(
			short_description=_('Protocol'),
			long_description='',
			syntax=univention.admin.syntax.printerURI,
			multivalue=0,
			options=[],
			required=1,
			may_change=1,
			identifies=0
		),
	'model': univention.admin.property(
			short_description=_('Printer Model'),
			long_description='',
			syntax=univention.admin.syntax.printersList,
			multivalue=0,
			options=[],
			required=1,
			may_change=1,
			identifies=0
		),
	'sambaName': univention.admin.property(
			short_description=_('Samba Name'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0,
			unique=1
		),
	'setQuota': univention.admin.property(
			short_description=_('Enable Quota Support'),
			long_description='',
			syntax=univention.admin.syntax.boolean,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'pagePrice': univention.admin.property(
			short_description=_('Price per Page'),
			long_description='',
			syntax=univention.admin.syntax.integer,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'jobPrice': univention.admin.property(
			short_description=_('Price per Print Job'),
			long_description='',
			syntax=univention.admin.syntax.integer,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'ACLtype': univention.admin.property(
			short_description=_('Access list'),
			long_description=_('Access list can allow or deny listed users and groups.'),
			syntax=printerACLTypes,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0,
			default="allow all"
		),
	'ACLUsers': univention.admin.property(
			short_description=_('Allowed/denied users'),
			long_description=_('For the given users printing is explicitly allowed or denied.'),
			syntax=univention.admin.syntax.userDn,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0,
		),
	'ACLGroups': univention.admin.property(
			short_description=_('Allowed/denied groups'),
			long_description=_('For the given groups printing is explicitly allowed or denied.'),
			syntax=univention.admin.syntax.groupDn,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0,
		),
}
layout=[
	univention.admin.tab(_('General'),_('General Settings'),[
			[univention.admin.field('name'), univention.admin.field('spoolHost')],
			[univention.admin.field('sambaName'), univention.admin.field('uri')],
			[ univention.admin.field( 'location' ), univention.admin.field( 'description' ) ],
			[univention.admin.field('setQuota'), univention.admin.field('model')],
			[univention.admin.field('pagePrice'),univention.admin.field('jobPrice')],
			]),
	univention.admin.tab(_('Access Control'),_('Access Control for users and groups'),[
			[univention.admin.field('ACLtype')],
			[univention.admin.field('ACLUsers')],
			[univention.admin.field('ACLGroups')],
			]),
]

def boolToString(value):
	if value == '1':
		return ['yes']
	else:
		return ['no']
def stringToBool(value):
	if value[0].lower() == 'yes':
		return '1'
	else:
		return '0'

mapping=univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('location', 'univentionPrinterLocation', None, univention.admin.mapping.ListToString)
mapping.register('description', 'description', None, univention.admin.mapping.ListToString)
mapping.register('spoolHost', 'univentionPrinterSpoolHost')
mapping.register('uri', 'univentionPrinterURI', None, univention.admin.mapping.ListToString)
mapping.register('model', 'univentionPrinterModel', None, univention.admin.mapping.ListToString)
mapping.register('sambaName', 'univentionPrinterSambaName', None, univention.admin.mapping.ListToString)
mapping.register('setQuota', 'univentionPrinterQuotaSupport', None, univention.admin.mapping.ListToString)
mapping.register('pagePrice', 'univentionPrinterPricePerPage', None, univention.admin.mapping.ListToString)
mapping.register('jobPrice', 'univentionPrinterPricePerJob', None, univention.admin.mapping.ListToString)
mapping.register('ACLUsers', 'univentionPrinterACLUsers')
mapping.register('ACLGroups', 'univentionPrinterACLGroups')
mapping.register('ACLtype', 'univentionPrinterACLtype', None, univention.admin.mapping.ListToString)

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
		self.save()

	def open(self):
		univention.admin.handlers.simpleLdap.open(self)
		self.save()

	def exists(self):
		return self._exists

	def _ldap_pre_create(self):
		self.dn='%s=%s,%s' % (mapping.mapName('name'), mapping.mapValue('name', self.info['name']), self.position.getDn())

	def _ldap_addlist(self):
		return [ ( 'objectClass', ['top', 'univentionPrinter'] ) ]

	def _ldap_pre_modify(self):# check for membership in a quota-printerclass
		if self.hasChanged('setQuota') and self.info['setQuota'] == '0':
			printergroups=self.lo.searchDn(filter='(&(objectClass=univentionPrinterGroup)(univentionPrinterQuotaSupport=1)(univentionPrinterSpoolHost=%s))'
										   % self.info['spoolHost'])
			group_cn=[]
			for pg_dn in printergroups:
				member_list=self.lo.search(base=pg_dn, attr=['univentionPrinterGroupMember','cn'])
				for member_cn in member_list[0][1]['univentionPrinterGroupMember']:
					if member_cn == self.info['name']:
						group_cn.append(member_list[0][1]['cn'][0])
			if len(group_cn) > 0:
				raise univention.admin.uexceptions.leavePrinterGroup, _('%s is member of following quota printer groups %s')%(self.info['name'],string.join(group_cn,", "))


	def _ldap_pre_remove(self): # check for last member in printerclass
		printergroups=self.lo.searchDn(filter='(&(objectClass=univentionPrinterGroup)(univentionPrinterSpoolHost=%s))'%self.info['spoolHost'])
		rm_attrib=[]
		for pg_dn in printergroups:
			member_list=self.lo.search( base=pg_dn, attr=['univentionPrinterGroupMember','cn'])
			for member_cn in member_list[0][1]['univentionPrinterGroupMember']:
				if member_cn == self.info['name']:
					rm_attrib.append(member_list[0][0])
					if len(member_list[0][1]['univentionPrinterGroupMember']) < 2:
						raise univention.admin.uexceptions.emptyPrinterGroup, _('%s is the last member of the printer group %s. ')%(self.info['name'],member_list[0][1]['cn'][0])
		printergroup_module=univention.admin.modules.get('shares/printergroup')
		for rm_dn in rm_attrib:
			printergroup_object=univention.admin.objects.get(printergroup_module, None, self.lo, position='', dn=rm_dn)
			printergroup_object.open()
			printergroup_object['groupMember'].remove(self.info['name'])
			printergroup_object.modify()

def lookup(co, lo, filter_s, base='', superordinate=None, scope='sub', unique=0, required=0, timeout=-1, sizelimit=0):

	filter=univention.admin.filter.conjunction('&', [
		univention.admin.filter.expression('objectClass', 'univentionPrinter'),
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

	return 'univentionPrinter' in attr.get('objectClass', [])
