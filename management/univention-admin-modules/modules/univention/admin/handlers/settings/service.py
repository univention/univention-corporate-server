# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin module for handling services
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

module='settings/service'
superordinate='settings/cn'
childs=0
operations=['add','edit','remove','search','move']
short_description=_('Settings: Service')
long_description=''
options={}
property_descriptions={
	'name': univention.admin.property(
	        short_description=_('Service Name'),
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
	univention.admin.tab(_('General'),_('Basic Values'),[
	   [univention.admin.field("name")],
	   ])
	]


mapping=univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)

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
		self.dn='cn=%s,%s' % ( mapping.mapValue('name', self.info['name']), self.position.getDn())

	def _ldap_addlist(self):
		ocs=['univentionServiceObject']		

		
		return [
			('objectClass', ocs),
		]


	
def lookup(co, lo, filter_s, base='', superordinate=None, scope='sub', unique=0, required=0, timeout=-1, sizelimit=0):

	filter=univention.admin.filter.expression('objectClass', 'univentionServiceObject')

	if filter_s:
		filter_p=univention.admin.filter.parse(filter_s)
		univention.admin.filter.walk(filter_p, univention.admin.mapping.mapRewrite, arg=mapping)
		filter.expressions.append(filter_p)

	res=[]
	for dn in lo.searchDn(unicode(filter), base, scope, unique, required, timeout, sizelimit):
		res.append(object(co, lo, None, dn))
	return res

def identify(dn, attr, canonical=0):
	
	return 'univentionServiceObject' in attr.get('objectClass', [])
