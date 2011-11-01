# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin module for the thin clients
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

from univention.admin.layout import Tab, Group
import univention.admin.filter
import univention.admin.handlers
import univention.admin.localization
import univention.admin.nagios as nagios
import univention.admin.handlers.dns.forward_zone
import univention.admin.handlers.dns.reverse_zone
import univention.admin.handlers.dns.host_record
import univention.admin.uldap
import univention.admin.handlers.networks.network

translation=univention.admin.localization.translation('univention.admin.handlers.computers')
_=translation.translate

module='computers/thinclient'
operations=['add','edit','remove','search','move']
usewizard=1
docleanup=1
childs=0
short_description=_('Computer: Thin Client')
long_description=''
options={
}
property_descriptions={
	'name': univention.admin.property(
			short_description=_('Name'),
			long_description='',
			syntax=univention.admin.syntax.hostName,
			multivalue=0,
			options=[],
			required=1,
			may_change=0,
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
	'mac': univention.admin.property(
			short_description=_('MAC address'),
			long_description='',
			syntax=univention.admin.syntax.MAC_Address,
			multivalue=1,
			options=[],
			required=1,
			may_change=1,
			identifies=0
		),
	'network': univention.admin.property(
			short_description=_('Network'),
			long_description='',
			syntax=univention.admin.syntax.network,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'ip': univention.admin.property(
			short_description=_('IP address'),
			long_description='',
			syntax=univention.admin.syntax.ipAddress,
			multivalue=1,
			options=[],
			required=1,
			may_change=1,
			identifies=0
		),
	'dnsEntryZoneForward': univention.admin.property(
			short_description=_('Forward zone for DNS entry'),
			long_description='',
			syntax=univention.admin.syntax.dnsEntry,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			dontsearch=1,
			identifies=0
		),
	'dnsEntryZoneReverse': univention.admin.property(
			short_description=_('Reverse zone for DNS entry'),
			long_description='',
			syntax=univention.admin.syntax.dnsEntryReverse,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			dontsearch=1,
			identifies=0
		),
	'dnsEntryZoneAlias': univention.admin.property(
			short_description=_('Zone for DNS alias'),
			long_description='',
			syntax=univention.admin.syntax.dnsEntryAlias,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			dontsearch=1,
			identifies=0
		),
	'dnsAlias': univention.admin.property(
			short_description=_('DNS alias'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'dhcpEntryZone': univention.admin.property(
			short_description=_('DHCP service'),
			long_description='',
			syntax=univention.admin.syntax.dhcpEntry,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			dontsearch=1,
			identifies=0
		),
	'inventoryNumber': univention.admin.property(
			short_description=_('Inventory number'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'groups': univention.admin.property(
			short_description=_('Groups'),
			long_description='',
			syntax=univention.admin.syntax.GroupDN,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			dontsearch=1,
			identifies=0
		),
	'domain': univention.admin.property(
			short_description=_('Domain'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			required=0,
			may_change=1,
			identifies=0
		),
}

layout = [
	Tab( _( 'General' ), _( 'Basic settings' ), layout = [
		Group( _( 'Computer account' ), layout = [
			[ 'name' , 'description' ],
			'inventoryNumber',
		] ),
		Group( _( 'Network settings ' ), layout = [
			'network',
			[ 'mac', 'ip', ],
		] ),
		Group( _( 'DNS Forward and Reverse Lookup Zone' ), layout = [
			'dnsEntryZoneForward',
			'dnsEntryZoneReverse',
		] ),
		Group( _( 'DHCP' ), layout = [
			'dhcpEntryZone'
		] ),
		] ),
	Tab( _( 'Groups' ), _( 'Group memberships' ), advanced = True, layout = [
		'groups',
		] ),
	Tab( _( 'DNS alias' ),_( 'Alias DNS entry' ), advanced = True, layout = [
		'dnsEntryZoneAlias'
		] ),
]

mapping=univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('description', 'description', None, univention.admin.mapping.ListToString)
mapping.register('inventoryNumber', 'univentionInventoryNumber')
mapping.register('mac', 'macAddress' )
mapping.register('network', 'univentionNetworkLink', None, univention.admin.mapping.ListToString)
mapping.register('domain', 'associatedDomain', None, univention.admin.mapping.ListToString)

# add Nagios extension
nagios.addPropertiesMappingOptionsAndLayout(property_descriptions, mapping, options, layout)


class object(univention.admin.handlers.simpleComputer, nagios.Support):
	module=module

	def __init__(self, co, lo, position, dn='', superordinate=None, attributes = [] ):
		global mapping
		global property_descriptions

		self.mapping=mapping
		self.descriptions=property_descriptions

		self.alloc=[]
		self.options = []

		self.ipRequest=0

		univention.admin.handlers.simpleComputer.__init__(self, co, lo, position, dn, superordinate)
		nagios.Support.__init__(self)

		self.save( )

	def open(self):

		univention.admin.handlers.simpleComputer.open( self )
		self.nagios_open()

		if not self.dn:
			return

		self.save()

	def _ldap_pre_create(self):
		self.dn='%s=%s,%s' % (mapping.mapName('name'), mapping.mapValue('name', self.info['name']), self.position.getDn())
		univention.admin.handlers.simpleComputer._ldap_pre_create( self )

	def _ldap_pre_modify(self):
		self.nagios_ldap_pre_modify()
		super(object, self)._ldap_pre_modify()

	def _ldap_addlist(self):
		return [ ('objectClass', ['top', 'person', 'univentionHost', 'univentionThinClient']) ]

	def _ldap_post_create(self):
		univention.admin.handlers.simpleComputer._ldap_post_create( self )
		self.nagios_ldap_post_create()

	def _ldap_post_modify(self):
		super(object, self)._ldap_post_modify()
		self.nagios_ldap_post_modify()

	def _ldap_post_remove(self):
		self.nagios_ldap_post_remove()
		univention.admin.handlers.simpleComputer._ldap_post_remove( self )

	def _ldap_modlist(self):
		ml=super(object, self)._ldap_modlist()
		self.nagios_ldap_modlist(ml)
		return ml

	def cleanup(self):
		self.open()
		self.nagios_cleanup()
		univention.admin.handlers.simpleComputer.cleanup( self )

	def cancel(self):
		for i,j in self.alloc:
			univention.debug.debug(univention.debug.ADMIN, univention.debug.WARN, 'cancel: release (%s): %s' % (i,j) )
			univention.admin.allocators.release(self.lo, self.position, i, j)

def rewrite(filter, mapping):
	if filter.variable == 'ip':
		filter.variable='aRecord'
	else:
		univention.admin.mapping.mapRewrite(filter, mapping)

def lookup(co, lo, filter_s, base='', superordinate=None, scope='sub', unique=0, required=0, timeout=-1, sizelimit=0):

	res=[]
	filter_s = univention.admin.filter.replace_fqdn_filter( filter_s )
	if str(filter_s).find('(dnsAlias=') != -1:
		filter_s=univention.admin.handlers.dns.alias.lookup_alias_filter(lo, filter_s)
		if filter_s:
			res+=lookup(co, lo, filter_s, base, superordinate, scope, unique, required, timeout, sizelimit)
	else:
		filter=univention.admin.filter.conjunction('&', [
			univention.admin.filter.expression('objectClass', 'univentionHost'),
			univention.admin.filter.expression('objectClass', 'univentionThinClient'),
			])

		if filter_s:
			filter_p=univention.admin.filter.parse(filter_s)
			univention.admin.filter.walk(filter_p, rewrite, arg=mapping)
			filter.expressions.append(filter_p)

		for dn, attrs in lo.search(unicode(filter), base, scope, [], unique, required, timeout, sizelimit):
			res.append( object( co, lo, None, dn, attributes = attrs ) )
	return res

def identify(dn, attr, canonical=0):
	
	return 'univentionHost' in attr.get('objectClass', []) and 'univentionThinClient' in attr.get('objectClass', [])

