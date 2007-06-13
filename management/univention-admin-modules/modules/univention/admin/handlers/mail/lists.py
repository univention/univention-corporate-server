# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin module for mailinglists
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
import univention.admin.allocators
import univention.admin.localization

translation=univention.admin.localization.translation('univention.admin.handlers.mail')
_=translation.translate

module='mail/lists'
operations=['add','edit','remove','search','move']
usewizard=1

childs=0
short_description=_('Mail: Mailing Lists')
long_description=''

module_search_filter=univention.admin.filter.expression('objectClass', 'univentionKolabGroup'),

property_descriptions={
	'name': univention.admin.property(
			short_description=_('Name'),
			long_description='',
			syntax=univention.admin.syntax.gid,
			multivalue=0,
			required=1,
			may_change=1,
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
	'members': univention.admin.property(
			short_description=_('Members'),
			long_description='',
			syntax=univention.admin.syntax.emailAddress,
			multivalue=1,
			required=0,
			may_change=1,
			dontsearch=1,
			identifies=0
		),
	'mailAddress': univention.admin.property(
			short_description=_('Mail Address'),
			long_description='',
			syntax=univention.admin.syntax.emailAddress,
			multivalue=0,
			required=0,
			may_change=1,
			dontsearch=0,
			identifies=0
		)
}

layout=[
	univention.admin.tab(_('General'),_('Basic Values'),[
	[univention.admin.field("name"), univention.admin.field("description")],
	[univention.admin.field("mailAddress")],
	[univention.admin.field("members")]
	] ),
]

mapping=univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('description', 'description', None, univention.admin.mapping.ListToString)
mapping.register('members', 'univentionKolabMember')
mapping.register('mailAddress', 'mailPrimaryAddress', None, univention.admin.mapping.ListToString)

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

		self.alloc=[]

		univention.admin.handlers.simpleLdap.__init__(self, co, lo, position, dn, superordinate)


	def open(self):

		univention.admin.handlers.simpleLdap.open(self)

	def exists(self):
		return self._exists
	
	def _ldap_pre_create(self):
		self.dn='%s=%s,%s' % (mapping.mapName('name'), mapping.mapValue('name', self.info['name']), self.position.getDn())

	def _ldap_post_create(self):
		if self[ 'mailAddress' ]:
			univention.admin.allocators.confirm( self.lo, self.position, 'mailPrimaryAddress', self[ 'mailAddress' ] )

	def _ldap_post_modify( self ):
		if self[ 'mailAddress' ] and self.hasChanged( 'mailAddress' ):
			univention.admin.allocators.confirm( self.lo, self.position, 'mailPrimaryAddress', self[ 'mailAddress' ] )

	def _ldap_addlist(self):
		ocs=['top']
		al=[]
		ocs.append('univentionKolabGroup')
		# mail address MUST be unique
		if self[ 'mailAddress' ]:
			try:
				self.alloc.append( ( 'mailPrimaryAddress', self[ 'mailAddress' ] ) )
				univention.admin.allocators.request( self.lo, self.position, 'mailPrimaryAddress', value = self[ 'mailAddress' ] )
			except:
				univention.admin.allocators.release( self.lo, self.position, 'mailPrimaryAddress', value = self[ 'mailAddress' ] )
				raise univention.admin.uexceptions.mailAddressUsed

		al.insert(0, ('objectClass', ocs))
		return al

	def _ldap_modlist( self ):
		if self.hasChanged( 'mailAddress' ) and self[ 'mailAddress' ]:
			for i, j in self.alloc:
				if i == 'mailPrimaryAddress': break
			else:
				try:
					univention.admin.allocators.request( self.lo, self.position, 'mailPrimaryAddress', value = self[ 'mailAddress' ] )
				except:
					univention.admin.allocators.release( self.lo, self.position, 'mailPrimaryAddress', value = self[ 'mailAddress' ] )
					raise univention.admin.uexceptions.mailAddressUsed
		return univention.admin.handlers.simpleLdap._ldap_modlist( self )

	
def lookup(co, lo, filter_s, base='', superordinate=None, scope='sub', unique=0, required=0, timeout=-1, sizelimit=0):

	filter=univention.admin.filter.conjunction('&', [
		univention.admin.filter.expression('objectClass', 'univentionKolabGroup')
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
	
	return 'univentionKolabGroup' in attr.get('objectClass', [])

