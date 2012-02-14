# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin module for the DHCP pool
#
# Copyright 2004-2011 Univention GmbH
#
# http://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <http://www.gnu.org/licenses/>.

import copy
import string

from univention.admin.layout import Tab, Group
import univention.admin.filter
import univention.admin.handlers
import univention.admin.localization
import univention.admin.uexceptions

translation=univention.admin.localization.translation('univention.admin.handlers.dhcp')
_=translation.translate

module='dhcp/pool'
operations=['add','edit','remove','search']
superordinate = 'dhcp/subnet'
childs=0
usewizard=1
short_description=_('DHCP: Pool')
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
	'range': univention.admin.property(
			short_description=_('IP range for dynamic assignment'),
			long_description='',
			syntax=univention.admin.syntax.IPv4_AddressRange,
			multivalue=1,
			options=[],
			required=1,
			may_change=1,
			identifies=0
		),
	'failover_peer': univention.admin.property(
			short_description=_('Failover peer'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0,
		),
	'known_clients': univention.admin.property(
			short_description=_('Allow known clients'),
			long_description='',
			syntax=univention.admin.syntax.AllowDeny,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'unknown_clients': univention.admin.property(
			short_description=_('Allow unknown clients'),
			long_description='',
			syntax=univention.admin.syntax.AllowDeny,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'dynamic_bootp_clients': univention.admin.property(
			short_description=_('Allow dynamic BOOTP clients'),
			long_description='',
			syntax=univention.admin.syntax.AllowDeny,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'all_clients': univention.admin.property(
			short_description=_('All clients'),
			long_description='',
			syntax=univention.admin.syntax.AllowDeny,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
}

options={
}

layout = [
	Tab(_('General'), _('Basic settings'), layout = [
		Group( _( 'General' ), layout = [
			'name',
			'range'
		] ),
	] ),
	Tab( _( 'Advanced' ), _('Advanced DHCP pool options'), advanced = True, layout = [
		'failover_peer',
		[ 'known_clients', 'unknown_clients' ],
		[ 'dynamic_bootp_clients', 'all_clients' ]
	] )
]

def rangeMap( value ):
	return map( lambda x: ' '.join( x ), value )

def rangeUnmap( value ):
	return map( lambda x: x.split( ' ' ), value )

mapping=univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('range', 'dhcpRange', rangeMap, rangeUnmap)
mapping.register('failover_peer', 'univentionDhcpFailoverPeer', None, univention.admin.mapping.ListToString)

class object(univention.admin.handlers.simpleLdap):
	module=module

	def __init__(self, co, lo, position, dn='', superordinate=None, attributes = [] ):
		global mapping
		global property_descriptions

		self.mapping=mapping
		self.descriptions=property_descriptions

		if not superordinate:
			raise univention.admin.uexceptions.insufficientInformation, 'superordinate object not present'
		if not dn and not position:
			raise univention.admin.uexceptions.insufficientInformation, 'neither dn nor position present'

		univention.admin.handlers.simpleLdap.__init__(self, co, lo, position, dn, superordinate, attributes = attributes )

	def open(self):

		univention.admin.handlers.simpleLdap.open(self)

		for i in self.oldattr.get('dhcpPermitList', []):
			pos=i.find(' ')
			permit=i[:pos]
			name=i[pos+1:]
			if name == 'known clients':
				self['known_clients']=permit
			elif name == 'unknown clients':
				self['unknown_clients']=permit
			elif name == 'dynamic bootp clients':
				self['dynamic_bootp_clients']=permit
			elif name == 'all clients':
				self['all_clients']=permit

		self.save()


	def _ldap_pre_create(self):
		self.dn='%s=%s,%s' % (mapping.mapName('name'), mapping.mapValue('name', self.info['name']), self.position.getDn())

	def _ldap_addlist(self):
		return [
			('objectClass', ['top', 'univentionDhcpPool']),
		]
	
	def _ldap_modlist(self):
		ml=univention.admin.handlers.simpleLdap._ldap_modlist(self)
		if self.hasChanged(['known_clients', 'unknown_clients', 'dynamic_bootp_clients', 'all_clients']):
			old=self.oldattr.get('dhcpPermitList', [])
			new=copy.deepcopy(old)

			if self.oldinfo.has_key('known_clients') and self.oldinfo['known_clients']:
				new.remove(self.oldinfo['known_clients']+' known clients')
			if self.info.has_key('known_clients') and self.info['known_clients']:
				new.append(self.info['known_clients']+' known clients')
				
			if self.oldinfo.has_key('unknown_clients') and self.oldinfo['unknown_clients']:
				new.remove(self.oldinfo['unknown_clients']+' unknown clients')
			if self.info.has_key('unknown_clients') and self.info['unknown_clients']:
				new.append(self.info['unknown_clients']+' unknown clients')

			if self.oldinfo.has_key('dynamic_bootp_clients') and self.oldinfo['dynamic_bootp_clients']:
				new.remove(self.oldinfo['dynamic_bootp_clients']+' dynamic bootp clients')
			if self.info.has_key('dynamic_bootp_clients') and self.info['dynamic_bootp_clients']:
				new.append(self.info['dynamic_bootp_clients']+' dynamic bootp clients')
			
			if self.oldinfo.has_key('all_clients') and self.oldinfo['all_clients']:
				new.remove(self.oldinfo['all_clients']+' all clients')
			if self.info.has_key('all_clients') and self.info['all_clients']:
				new.append(self.info['all_clients']+' all clients')
				
			ml.append(('dhcpPermitList', old, new))
		if self.info.get('failover_peer', None) and not self.info.get('dynamic_bootp_clients', None) == 'deny':
			raise univention.admin.uexceptions.bootpXORFailover
		return ml

def lookup(co, lo, filter_s, base='', superordinate=None, scope='sub', unique=0, required=0, timeout=-1, sizelimit=0):

	filter=univention.admin.filter.conjunction('&', [
	univention.admin.filter.expression('objectClass', 'univentionDhcpPool')
	])

	if filter_s:
		filter_p=univention.admin.filter.parse(filter_s)
		univention.admin.filter.walk(filter_p, univention.admin.mapping.mapRewrite, arg=mapping)
		filter.expressions.append(filter_p)

	res=[]
	for dn, attrs in lo.search(unicode(filter), base, scope, [], unique, required, timeout, sizelimit):
		res.append((object(co, lo, None, dn=dn, superordinate=superordinate, attributes = attrs )))
	return res

def identify(dn, attr):
	return 'univentionDhcpPool' in attr.get('objectClass', [])
