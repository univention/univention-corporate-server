# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin module for samba domain configuration
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

import string, os
import univention.admin.filter
import univention.admin.handlers
import univention.admin.password
import univention.admin.allocators
import univention.admin.localization

translation=univention.admin.localization.translation('univention.admin.handlers.settings')
_=translation.translate

def makeSambaDomainName(object, arg):
	return [(object['name'].upper()+'.'+object.position.getPrintable()).upper()]

def makeSambaDomainSid(object, arg):
	popen = os.popen('/usr/sbin/univention-newsid')
	sid = popen.read()[:-1]
	popen.close()
	return sid

module='settings/sambadomain'
childs=0
operations=['add','edit','remove','search','move']
short_description=_('Settings: Samba Domain')
long_description=''
options={}
property_descriptions={
	'name': univention.admin.property(
	        short_description=_('Samba Domain Name'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=[],
			required=1,
			may_change=1,
			identifies=1
			),
	'SID': univention.admin.property(
			short_description=_('Samba SID'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=[],
			required=0,
			may_change=0,
			default=(makeSambaDomainSid, [], 'sambaDomain'),
			identifies=0
			),
	'NextUserRid': univention.admin.property(
			short_description=_('Next User RID'),
			long_description='',
			syntax=univention.admin.syntax.integer,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			default=('1000', []),
			identifies=0
		),
	'NextGroupRid': univention.admin.property(
			short_description=_('Next Group RID'),
			long_description='',
			syntax=univention.admin.syntax.integer,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			default=('1000', []),
			identifies=0
			),
	'NextRid': univention.admin.property(
			short_description=_('Next RID'),
			long_description='',
			syntax=univention.admin.syntax.integer,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			default=('1000', []),
			identifies=0
			),
	}
layout=[
	univention.admin.tab(_('General'),_('Basic Values'),[
	   [univention.admin.field("name"), univention.admin.field("SID")],
	   [univention.admin.field("NextUserRid"), univention.admin.field("NextGroupRid")],
	   [univention.admin.field("NextRid")],
	   ])
	]


mapping=univention.admin.mapping.mapping()
mapping.register('name', 'sambaDomainName', None, univention.admin.mapping.ListToString)
mapping.register('SID', 'sambaSID', None, univention.admin.mapping.ListToString)
mapping.register('NextUserRid', 'sambaNextUserRid', None, univention.admin.mapping.ListToString)
mapping.register('NextGroupRid', 'sambaNextGroupRid', None, univention.admin.mapping.ListToString)
mapping.register('NextRid', 'sambaNextRid', None, univention.admin.mapping.ListToString)

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
 		self.options=[]

		self.alloc=[]

		univention.admin.handlers.simpleLdap.__init__(self, co, lo,  position, dn, superordinate)

	def open(self):
		univention.admin.handlers.simpleLdap.open(self)

	def exists(self):
		return self._exists
	
	def _ldap_pre_create(self):		
		self.dn='sambaDomainName=%s,%s' % ( mapping.mapValue('name', self.info['name']), self.position.getDn())

	def _ldap_addlist(self):
		ocs=['sambaDomain']		

		return [
			('objectClass', ocs),
		]

	
def lookup(co, lo, filter_s, base='', superordinate=None, scope='sub', unique=0, required=0, timeout=-1, sizelimit=0):

	filter=univention.admin.filter.conjunction('&', [
		univention.admin.filter.expression('objectClass', 'sambaDomain'),
		univention.admin.filter.conjunction('!', [univention.admin.filter.expression('objectClass', 'univentionDomain')]),
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
	
	return 'sambaDomain' in attr.get('objectClass', []) and not 'univentionDomain' in attr.get('objectClass', [])
