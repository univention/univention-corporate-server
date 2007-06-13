# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin module for DNS TXT records
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

import sys, types, copy, string
import univention.admin.filter
import univention.admin.handlers
import univention.admin.handlers.dns.forward_zone
import univention.admin.localization

translation=univention.admin.localization.translation('univention.admin.handlers.dns')
_=translation.translate

module='dns/zone_txt_record'
operations=['add','edit','remove','search']
superordinate='dns/forward_zone'
usewizard=1
childs=0
short_description=_('DNS: Zone Text')
long_description=''
options={
}
property_descriptions={
	'txt': univention.admin.property(
			short_description=_('Text Record'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=[],
			required=1,
			may_change=1
		),
}
layout=[
	univention.admin.tab(_('General'), _('Basic Values'), fields=[
		[univention.admin.field('txt')]
	])
]
mapping=univention.admin.mapping.mapping()

def replace(item, old, new):
	if type(item) == types.ListType:
		newitem=copy.deepcopy(item)
		try:
			newitem.remove(old)
		except ValueError:
			pass
		newitem.append(new)
		return newitem
	else:
		raise ValueError


class object(univention.admin.handlers.simpleLdapSub):
	module=module

	def _updateZone(self):
		self.superordinate.open()
		self.superordinate.modify()

	def __init__(self, co, lo, position, dn='', superordinate=None, arg=None):
		self.co=co
		self.lo=lo
		self.dn=dn
		self.position=position
		self.superordinate=superordinate
		self.arg=arg
		self._exists=0
		self.descriptions=property_descriptions
		global mapping
		self.mapping=mapping


		if not superordinate:
			raise univention.admin.uexceptions.insufficientInformation, _( 'superordinate object not present' )

		univention.admin.handlers.simpleLdapSub.__init__(self, co, lo, position, superordinate.dn, superordinate)
		
		if arg:
			try:
				self['txt']=arg
				self._exists=1
			except Exception, e:
				self.dn=None
				return
		self.save()


	def exists(self):
		return self._exists
	
	def _ldap_modlist(self):
		ml=[]
		if self.hasChanged('txt'):
			oldattr=self.lo.getAttr(self.dn, 'tXTRecord')
			newattr=replace(oldattr, self.oldinfo.get('txt', ''), self.info['txt'])
			ml.append(('tXTRecord', oldattr, newattr))
		return ml
	
	def _ldap_dellist(self):
		ml=[]
		oldattr=self.lo.getAttr(self.dn, 'tXTRecord')
		newattr=copy.deepcopy(oldattr)
		toDelete=self.oldinfo['txt']
		newattr.remove(toDelete)
		ml.append(('tXTRecord', oldattr, newattr))
		return ml
	
	def _ldap_post_modify(self):
		if self.hasChanged(self.descriptions.keys()):
			self._updateZone()
	
	def _ldap_pre_remove(self):
		self.info['txt']=None
	
	def description(self):
		return self.info['txt']
	
def lookup(co, lo, filter_s, base='', superordinate=None,scope="sub", unique=0, required=0, timeout=-1, sizelimit=0):

	filter=univention.admin.filter.conjunction('&', [
		univention.admin.filter.expression('objectClass', 'dNSZone'),
		univention.admin.filter.expression('relativeDomainName', '@'),
		univention.admin.filter.conjunction('!', [univention.admin.filter.expression('zoneName', '*.in-addr.arpa')]),
		univention.admin.filter.expression('tXTRecord', '*'),
		])


	if superordinate:
		filter.expressions.append(univention.admin.filter.expression('zoneName', superordinate.mapping.mapValue('zone', superordinate['zone'])))

	if filter_s:
		filter_p=univention.admin.filter.parse(filter_s)
		univention.admin.filter.walk(filter_p, univention.admin.mapping.mapRewrite, arg=mapping)
		filter.expressions.append(filter_p)

	res=[]
	for dn, attr in lo.search(str(filter), base, scope, attr=['tXTRecord'], unique=unique, required=required, timeout=timeout, sizelimit=sizelimit):
		for txt in attr['tXTRecord']:
			res.append(object(co, lo, None, dn, superordinate=superordinate, arg=txt))
	return res

def identify(dn, attr, canonical=0):
	
	return not canonical and 'dNSZone' in attr.get('objectClass', []) and\
		attr.get('relativeDomainName', []) == ['@'] and\
		not attr['zoneName'][0].endswith('.in-addr.arpa') and\
		attr.has_key('tXTRecord')
