# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin module for the windows hosts
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

import sys, string, ldap, copy
import univention.admin.filter
import univention.admin.config
import univention.admin.handlers
import univention.admin.password
import univention.admin.password
import univention.admin.localization
import univention.admin.uldap
import univention.admin.nagios as nagios
import univention.admin.handlers.dns.forward_zone
import univention.admin.handlers.dns.reverse_zone
import univention.admin.handlers.groups.group
import univention.admin.handlers.dhcp.service
import univention.admin.handlers.networks.network

translation=univention.admin.localization.translation('univention.admin.handlers.computers')
_=translation.translate

module='computers/windows'
operations=['add','edit','remove','search','move']
usewizard=1
docleanup=1
childs=0
short_description=_('Computer: Windows')
long_description=''
options={
	'samba': univention.admin.option(
			short_description=_('Samba account'),
			default=1
		)
}
property_descriptions={
	'name': univention.admin.property(
			short_description=_('Hostname'),
			long_description='',
			syntax=univention.admin.syntax.windowsHostName,
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
			syntax=univention.admin.syntax.macAddress,
			multivalue=1,
			options=[],
			required=0,
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
			required=0,
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
	'machineAccountGroup': univention.admin.property(
			short_description=_('Machine account group'),
			long_description='',
			syntax=univention.admin.syntax.primaryGroup,
			multivalue=0,
			options=[],
			required=1,
			dontsearch=1,
			may_change=1,
			identifies=0
		),
	'ntCompatibility': univention.admin.property(
			short_description=_('Initialize password with hostname'),
			long_description='Needed To Join NT4 Worstations',
			syntax=univention.admin.syntax.boolean,
			multivalue=0,
			options=[],
			required=0,
			dontsearch=1,
			may_change=1,
			identifies=0
		),
	'reinstall': univention.admin.property(
			short_description=_('(Re-)install on next boot'),
			long_description='',
			syntax=univention.admin.syntax.boolean,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
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
			syntax=univention.admin.syntax.groupDn,
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
layout=[
	univention.admin.tab(_('General'),_('Windows computer'),[
			[univention.admin.field("name"), univention.admin.field("description")],
			[univention.admin.field("mac"), univention.admin.field('network')],
			[univention.admin.field("inventoryNumber")],
		]),
	univention.admin.tab(_('IP'),_('IP'),[
			[univention.admin.field("ip")],
		]),
	univention.admin.tab(_('Machine account'),_('Machine account settings'),[
			[univention.admin.field("machineAccountGroup")],
			[univention.admin.field("ntCompatibility")]
		], advanced = True),
	univention.admin.tab(_('DNS'),_('DNS Forward and Reverse Lookup Zone'),[
			[univention.admin.field("dnsEntryZoneForward")],
			[univention.admin.field("dnsEntryZoneReverse")]
		]),
	univention.admin.tab(_('DHCP'),_('DHCP'),[
			[univention.admin.field("dhcpEntryZone")]
		]),
	univention.admin.tab(_('Deployment'),_('Deployment'),[
			[univention.admin.field("reinstall")]
		], advanced = True),
	univention.admin.tab(_('Groups'),_('Group memberships'),[
			[univention.admin.field("groups")],
		], advanced = True)
]

mapping=univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('description', 'description', None, univention.admin.mapping.ListToString)
mapping.register('inventoryNumber', 'univentionInventoryNumber')
mapping.register('mac', 'macAddress' )
mapping.register('ip', 'aRecord' )
mapping.register('network', 'univentionNetworkLink', None, univention.admin.mapping.ListToString)
mapping.register('reinstall', 'univentionWindowsReinstall', None, univention.admin.mapping.ListToString)
mapping.register('domain', 'associatedDomain', None, univention.admin.mapping.ListToString)


# add Nagios extension
nagios.addPropertiesMappingOptionsAndLayout(property_descriptions, mapping, options, layout)


class object(univention.admin.handlers.simpleComputer, nagios.Support):
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

		self.oldPrimaryGroup=None
		self.newPrimaryGroup=None

		self.alloc=[]
		self.options = []

		self.ipRequest=0

		univention.admin.handlers.simpleComputer.__init__(self, co, lo, position, dn, superordinate)
		nagios.Support.__init__(self)

	def open(self):
		global options
		univention.admin.handlers.simpleComputer.open( self )
		self.nagios_open()

		self.old_pwd=''


		if self.oldattr.has_key('objectClass'):
			ocs=self.oldattr['objectClass']
			if 'sambaSamAccount' in ocs:
				self.options.append( 'samba' )
		else:
			self._define_options( options )

		if self.dn:
			if self['name']:
				s=self.descriptions['name'].syntax
				try:
					username_match=s.parse(self['name'])
				except univention.admin.uexceptions.valueError,e: # name contains already umlauts, so we switch
					self.set_name_umlauts()

		if not self.dn:
			self['machineAccountGroup']=univention.admin.config.getDefaultValue(self.lo, 'computerGroup', position=self.position)
			if not self['machineAccountGroup']:
				self.save()
				raise univention.admin.uexceptions.primaryGroup
			self.newPrimaryGroup=self['machineAccountGroup']
			return

		machineGidNum=self.oldattr.get('gidNumber',[None])[0]
		univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'old gidNumber: %s' % machineGidNum)
		if not machineGidNum:
			self['machineAccountGroup']=None
			self.save()
			raise univention.admin.uexceptions.primaryGroup
		machineGroupResult=self.lo.searchDn('(&(objectClass=posixGroup)(gidNumber=%s))' % machineGidNum)
		if not machineGroupResult:
			self['machineAccountGroup']=None
			self.save()
			raise univention.admin.uexceptions.primaryGroup
		self['machineAccountGroup']=machineGroupResult[0]
		self.oldPrimaryGroup=self['machineAccountGroup']

		self.save()

	def exists(self):
		return self._exists
	
	def set_name_umlauts(self, umlauts=1):
		self.uid_umlauts=umlauts
		if umlauts:
			self.descriptions['name'] = univention.admin.property(
				short_description=_('Hostname'),
				long_description='',
				syntax=univention.admin.syntax.dnsName_umlauts,
				multivalue=0,
				options=[],
				required=1,
				may_change=0,
				identifies=1
				)
		else:
			self.descriptions['name'] = univention.admin.property(
				short_description=_('Hostname'),
				long_description='',
				syntax=univention.admin.syntax.dnsName,
				multivalue=0,
				options=[],
				required=1,
				may_change=0,
				identifies=1
				)

	def _ldap_pre_create(self):
		self.dn='%s=%s,%s' % (mapping.mapName('name'), mapping.mapValue('name', self.info['name']), self.position.getDn())
		univention.admin.handlers.simpleComputer._ldap_pre_create( self )

	def _ldap_addlist(self):

		self.uidNum = None
		self.machineSid = None
		while not self.uidNum or not self.machineSid:
			self.uidNum=univention.admin.allocators.request(self.lo, self.position, 'uidNumber')
			if self.uidNum:
				self.alloc.append(('uidNumber',self.uidNum))
				try:
					self.machineSid=univention.admin.allocators.requestUserSid(self.lo, self.position, self.uidNum)
				except:
					pass
				else:
					self.alloc.append(('sid',self.machineSid))
			else:
				self.machineSid=None

		acctFlags=univention.admin.samba.acctFlags(flags={'W':1})

		al=[]
		ocs=['top', 'univentionHost','univentionWindows', 'posixAccount', 'person']

		if 'samba' in self.options:
			ocs.append('sambaSamAccount')
			al.append(('sambaSID', [self.machineSid]))
			al.append(('sambaAcctFlags', [acctFlags.decode()]))
			
		al.extend([
			('uidNumber', [self.uidNum]),
			('homeDirectory', ['/dev/null']),
			('loginShell', ['/bin/false'])
		])

		al.insert(0, ('objectClass', ocs))

		return al

	def _ldap_post_create(self):
		# check uniqueMember entry
		if self.hasChanged('machineAccountGroup'):
			self.newPrimaryGroup=self['machineAccountGroup']

		if self.oldPrimaryGroup and self.newPrimaryGroup:
			members=self.lo.getAttr(self.oldPrimaryGroup, 'uniqueMember')
			newmembers=copy.deepcopy(members)
			if self.dn in newmembers:
				newmembers.remove(self.dn)
				self.lo.modify(self.oldPrimaryGroup, [('uniqueMember', members, newmembers)])
				self.oldPrimaryGroup=None
			
		if self.newPrimaryGroup:
			members=self.lo.getAttr(self.newPrimaryGroup, 'uniqueMember')
			newmembers=copy.deepcopy(members)
			newmembers.append(self.dn)
			self.lo.modify(self.newPrimaryGroup, [('uniqueMember', members, newmembers)])
			self.newPrimaryGroup=None

		univention.admin.handlers.simpleComputer._ldap_post_create( self )


		if hasattr(self, 'uidNum') and self.uidNum and hasattr(self, 'machineSid') and self.machineSid:
			univention.admin.allocators.confirm(self.lo, self.position, 'uidNumber', self.uidNum)
			univention.admin.allocators.confirm(self.lo, self.position, 'sid', self.machineSid)

		if hasattr(self, 'uid') and self.uid:
			univention.admin.allocators.confirm(self.lo, self.position, 'uid', self.uid)

		self.nagios_ldap_post_create()


	def _ldap_post_modify(self):
		if self.hasChanged('machineAccountGroup'):
			self.newPrimaryGroup=self['machineAccountGroup']

		if self.oldPrimaryGroup and self.newPrimaryGroup:
			members=self.lo.getAttr(self.oldPrimaryGroup, 'uniqueMember')
			newmembers=copy.deepcopy(members)
			if self.dn in newmembers: # may be removed by changing the group directly
				newmembers.remove(self.dn)
				self.lo.modify(self.oldPrimaryGroup, [('uniqueMember', members, newmembers)])
				self.oldPrimaryGroup=None
			
		if self.newPrimaryGroup:
			members=self.lo.getAttr(self.newPrimaryGroup, 'uniqueMember')
			newmembers=copy.deepcopy(members)
			if not self.dn in members:
				newmembers.append(self.dn)
				self.lo.modify(self.newPrimaryGroup, [('uniqueMember', members, newmembers)])
				self.newPrimaryGroup=None

		univention.admin.handlers.simpleComputer._ldap_post_modify( self )
		self.nagios_ldap_post_modify()

		if self.hasChanged('name') and self['name'] and hasattr(self, 'uid') and self.uid:
			univention.admin.allocators.confirm(self.lo, self.position, 'uid', self.uid)

	def _ldap_modlist(self):
		ml=univention.admin.handlers.simpleComputer._ldap_modlist( self )
		self.nagios_ldap_modlist(ml)

		if self.hasChanged('machineAccountGroup') and self['machineAccountGroup']:
			try:
				gidNum=self.lo.getAttr(self['machineAccountGroup'], 'gidNumber')[0]
				univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'new gidNumber: %s' % gidNum)
			except IndexError:
				raise univention.admin.uexceptions.groupNotFound, ': %s' % self['machineAccountGroup']
			ml.append(('gidNumber', self.oldattr.get('gidNumber', [None])[0], gidNum))
		
		if self.hasChanged('ntCompatibility') and self['ntCompatibility'] == '1':
			password_nt, password_lm = univention.admin.password.ntlm(self['name'].replace('$','').lower())
			ml.append(('sambaNTPassword', self.oldattr.get('sambaNTPassword', [''])[0], password_nt))
			ml.append(('sambaLMPassword', self.oldattr.get('sambaLMPassword', [''])[0], password_lm))

		if self.hasChanged('name') and self['name']:
			error=0
			requested_uid="%s$" % self['name']
			self.uid=None
			try:
				self.uid=univention.admin.allocators.request(self.lo, self.position, 'uid', value=requested_uid)
			except Exception, e:
				error=1

			if not self.uid or error:
				del(self.info['name'])
				self.oldinfo={}
				self.dn=None
				self._exists=0
				raise univention.admin.uexceptions.uidAlreadyUsed, ': %s' % requested_uid
				return []

			self.alloc.append(('uid', self.uid))
			ml.append(('uid', self.oldattr.get('uid', [None])[0], self.uid))
			
		return ml

	def _ldap_pre_modify(self):
		self.nagios_ldap_pre_modify()
		univention.admin.handlers.simpleComputer._ldap_pre_modify( self )

	def _ldap_post_remove(self):
		f=univention.admin.filter.expression('uniqueMember', self.dn)
		groupObjects=univention.admin.handlers.groups.group.lookup(self.co, self.lo, filter_s=f)
		if groupObjects:
			for i in range(0, len(groupObjects)):
				groupObjects[i].open()
				if self.dn in groupObjects[i]['users']:
					groupObjects[i]['users'].remove(self.dn)
					groupObjects[i].modify(ignore_license=1)
		self.nagios_ldap_post_remove()
		univention.admin.handlers.simpleComputer._ldap_post_remove( self )

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

	filter=univention.admin.filter.conjunction('&', [
		univention.admin.filter.expression('objectClass', 'univentionHost'),
		univention.admin.filter.expression('objectClass', 'univentionWindows'),
		univention.admin.filter.expression('objectClass', 'posixAccount'),
		univention.admin.filter.conjunction('!',[univention.admin.filter.expression('sambaAcctFlags', '[I          ]')]),
		])

	if filter_s:
		filter_p=univention.admin.filter.parse(filter_s)
		univention.admin.filter.walk(filter_p, rewrite, arg=mapping)
		filter.expressions.append(filter_p)

	res=[]
	for dn in lo.searchDn(unicode(filter), base, scope, unique, required, timeout, sizelimit):
		res.append(object(co, lo, None, dn))
	return res

def identify(dn, attr, canonical=0):
	
	return 'univentionHost' in attr.get('objectClass', []) and\
		'univentionWindows' in attr.get('objectClass', []) and\
		'posixAccount' in attr.get('objectClass', []) and not\
		'[I          ]' in attr.get('sambaAcctFlags', [])
