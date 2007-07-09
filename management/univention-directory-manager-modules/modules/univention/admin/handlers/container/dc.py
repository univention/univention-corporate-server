# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin module for the dc objects
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

import sys, string, ldap
import univention.admin.filter
import univention.admin.handlers
import univention.admin.password
import univention.admin.allocators
import univention.admin.localization

import univention.admin.handlers.settings.directory
import univention.admin.handlers.users.user
import univention.admin.handlers.groups.group

translation=univention.admin.localization.translation('univention.admin.handlers.container')
_=translation.translate

def makeDnsForwardZone(object, arg):
	return [object['name']+'.'+object.position.getPrintable()]
	
def makeSambaDomainName(object, arg):
	return [(object['name'].upper()+'.'+object.position.getPrintable()).upper()]

def makeSambaDomainSid(object, arg):
	return univention.admin.allocators.requestDomainSid(object.lo, object.position )

module='container/dc'
childs=1
operations=['search', 'edit']
short_description=_('Container: Domain')
long_description=''
options={
	'kerberos': univention.admin.option(
			short_description=_('Kerberos Realm'),
			default=1
		)
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
	'domainPassword': univention.admin.property(
			short_description=_('Domain Password'),
			long_description='',
			syntax=univention.admin.syntax.passwd,
			multivalue=0,
			options=[],
			required=1,
			may_change=0,
			identifies=0
		),
	'dnsForwardZone': univention.admin.property(
			short_description=_('DNS Forward Zone'),
			long_description='',
			syntax=univention.admin.syntax.dnsName,
			multivalue=1,
			options=[],
			required=0,
			default=(makeDnsForwardZone, [], ''),
			may_change=0,
			identifies=0
		),
	'dnsReverseZone': univention.admin.property(
			short_description=_('DNS Reverse Zone'),
			long_description='',
			syntax=univention.admin.syntax.reverseLookupSubnet,
			multivalue=1,
			options=[],
			required=0,
			may_change=0,
			identifies=0
		),
	'sambaDomainName': univention.admin.property(
			short_description=_('Samba Domain Name'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			default=(makeSambaDomainName, [], 'sambaDomain'),
			identifies=0
		),
	'sambaSID': univention.admin.property(
			short_description=_('Samba SID'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=[],
			required=0,
			may_change=0,
			identifies=0
		),
	'sambaNextUserRid': univention.admin.property(
			short_description=_('Samba Next User RID'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			default=('1000', []),
			identifies=0
		),
	'sambaNextGroupRid': univention.admin.property(
			short_description=_('Samba Next Group RID'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			default=('1000', []),
			identifies=0
		),
	'kerberosRealm': univention.admin.property(
			short_description=_('Kerberos Realm'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=['kerberos'],
			required=1,
			may_change=0,
			default=(makeSambaDomainName, [], 'sambaDomain'),
			identifies=0
		),
	'mailRelay': univention.admin.property(
			short_description=_('Mail Relay Server'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=1,
			required=0,
			may_change=1,
			identifies=0
		),
}
layout=[
	univention.admin.tab(_('General'),_('Basic Values'),[[univention.admin.field("name")]]),
	univention.admin.tab(_('Domain Password'),_('Administrator Password for this Domain'),[[univention.admin.field("domainPassword")]]),
	univention.admin.tab(_('DNS'),_('DNS Zones'),[
			[univention.admin.field("dnsForwardZone"),univention.admin.field("dnsReverseZone")]
		]),
	univention.admin.tab(_('Samba'),_('Samba Settings'),[
			[univention.admin.field("sambaDomainName"), univention.admin.field("sambaSID")],
			[univention.admin.field("sambaNextUserRid"), univention.admin.field("sambaNextGroupRid")]
		]),
	univention.admin.tab(_('Kerberos'), _('Kerberos Settings'),[
			[univention.admin.field('kerberosRealm')]
		]),
	univention.admin.tab(_('Mail'), _('Mail Settings'),[
			[univention.admin.field('mailRelay')]
		]),
]

mapping=univention.admin.mapping.mapping()
mapping.register('sambaDomainName', 'sambaDomainName')
mapping.register('sambaSID', 'sambaSID', None, univention.admin.mapping.ListToString)
mapping.register('sambaNextUserRid', 'sambaNextUserRid', None, univention.admin.mapping.ListToString)
mapping.register('sambaNextGroupRid', 'sambaNextGroupRid', None, univention.admin.mapping.ListToString)
mapping.register('kerberosRealm', 'krb5RealmName', None, univention.admin.mapping.ListToString)
mapping.register('mailRelay', 'mailRelay')

class object(univention.admin.handlers.simpleLdap):
	module=module

	def __init__(self, co, lo, position, dn='', superordinate=None, arg=None):
		global options
		global mapping
		global property_descriptions

		self.co=co
		self.lo=lo
		self.dn=dn
		self.position=position
		self._exists=0
		self.mapping=mapping
		self.descriptions=property_descriptions
		self.options = []
		self._define_options( options )

		self.alloc=[]

		univention.admin.handlers.simpleLdap.__init__(self, co, lo,  position, dn,superordinate)

	def open(self):
		univention.admin.handlers.simpleLdap.open(self)

		if self.dn:
			self['name']=ldap.explode_dn(self.dn,1)[0]

			self['domainPassword']='********'
			
			self['dnsForwardZone']=''
			self['dnsReverseZone']=''
			forward=self.lo.searchDn(base=self.dn, scope='domain', filter='(&(objectClass=dNSZone)(relativeDomainName=@)(!(zoneName=*.in-addr.arpa)))')
			for f in forward:
				self['dnsForwardZone'].append(f)
			reverse=self.lo.searchDn(base=self.dn, scope='domain', filter='(&(objectClass=dNSZone)(relativeDomainName=@)(zoneName=*.in-addr.arpa))')
			for r in reverse:
				self['dnsReverseZone'].append(r)

			if not 'krb5Realm' in self.oldattr.get('objectClass', []):
				iself._remove_option('kerberos')

	def exists(self):
		return self._exists
	
	def _ldap_pre_create(self):
		self.dn='%s=%s,%s' % (mapping.mapName('name'), mapping.mapValue('name', self.info['name']), self.position.getDn())

	def _ldap_addlist(self):
		ocs=['top', 'domain', 'sambaDomain', 'univentionDomain', 'univentionBase']
		if 'kerberos' in self.options:
			ocs.append('krb5Realm')
		return [
			('objectClass', ocs)
		]

	def _ldap_post_create(self):
		dnsname=self.position.getPrintable()
		self.lo.add('cn=users,'+self.dn,     [('objectClass', ['top', 'organizationalRole']), ('cn', ['users']  ) ] )
		self.lo.add('cn=groups,'+self.dn,    [('objectClass', ['top', 'organizationalRole']), ('cn', ['groups']  ) ] )
		self.lo.add('cn=computers,'+self.dn, [('objectClass', ['top', 'organizationalRole']), ('cn', ['computers']   ) ] )
		self.lo.add('cn=univention,'+self.dn,[('objectClass', ['top', 'organizationalRole']), ('cn', ['univention']   ) ] )
		self.lo.add('cn=dns,'+self.dn,		 [('objectClass', ['top', 'organizationalRole']), ('cn', ['dns']   ) ] )
		self.lo.add('cn=dhcp,'+self.dn,	   	 [('objectClass', ['top', 'organizationalRole']), ('cn', ['dhcp']   ) ] )
		self.lo.add('cn=policies,'+self.dn,	 [('objectClass', ['top', 'organizationalRole']), ('cn', ['policies']   ) ] )

		tmpPosition = univention.admin.uldap.position(self.position.getBase())
		tmpPosition.setDn(self.dn)

		directoryObject = univention.admin.objects.default('settings/directory', self.co, self.lo, tmpPosition )
		directoryObject['policy'] = 'cn=policies,%s' % self.dn
		directoryObject['dns'] = 'cn=dns,%s' % self.dn
		directoryObject['dhcp'] = 'cn=dhcp,%s' % self.dn
		directoryObject['users'] = 'cn=users,%s' % self.dn
		directoryObject['groups'] = 'cn=groups,%s' % self.dn
		directoryObject['computers'] = 'cn=computers,%s' % self.dn
		directoryObject.create()
	

		cryptPassword='{crypt}'+univention.admin.password.crypt(self['domainPassword'])
		ntPassword, lmPassword=univention.admin.password.ntlm(self['domainPassword']+"\n")
			
		rootSambaSID=None
		while rootSambaSID == None:
			rootSambaSID=univention.admin.allocators.requestUserSid(self.lo, tmpPosition, '0')
		#FIXME
		self.lo.add('uid=root,cn=users,'+self.dn, [ \
		                        ('objectClass', ['top', 'posixAccount', 'sambaSamAccount', 'shadowAccount', 'person', 'organizationalPerson', 'univentionPerson', 'inetOrgPerson']),\
		                        ('cn', ['root'] ),\
		                        ('uid', ['root']),\
		                        ('uidNumber', ['0']),\
		                        ('gidNumber', ['0']),\
		                        ('homeDirectory', ['/root']),\
		                        ('userPassword', [cryptPassword]),\
		                        ('loginShell', ['/bin/sh']),\
		                        ('sambaLMPassword', lmPassword),\
		                        ('sambaNTPassword', ntPassword),\
		                        ('sambaSID', [rootSambaSID]),\
		                        ('sambaAcctFlags', '[U          ]'),\
		                        ('sn', ['root'])] )

		self.lo.add('cn=default,cn=univention,'+self.dn, [ \
		                        ('objectClass', ['top', 'univentionDefault']),\
		                        ('univentionDefaultGroup', ['cn=Domain Users,cn=groups,'+tmpPosition.getDn()]),\
		                        ('cn', ['default'])] )

		self.lo.add('cn=temporary,cn=univention,'+self.dn, [ \
		                        ('objectClass', ['top', 'organizationalRole']),\
		                        ('cn', ['temporary'])] )

		self.lo.add('cn=sid,cn=temporary,cn=univention,'+self.dn, [ \
		                        ('objectClass', ['top', 'organizationalRole']),\
		                        ('cn', ['sid'])] )

		self.lo.add('cn=uidNumber,cn=temporary,cn=univention,'+self.dn, [ \
		                        ('objectClass', ['top', 'organizationalRole', 'univentionLastUsed']),\
								('univentionLastUsedValue', ['1000']), \
		                        ('cn', ['uidNumber'])] )

		self.lo.add('cn=gidNumber,cn=temporary,cn=univention,'+self.dn, [ \
		                        ('objectClass', ['top', 'organizationalRole', 'univentionLastUsed']),\
								('univentionLastUsedValue', ['1000']), \
		                        ('cn', ['gidNumber'])] )

		self.lo.add('cn=uid,cn=temporary,cn=univention,'+self.dn, [ \
		                        ('objectClass', ['top', 'organizationalRole']),\
		                        ('cn', ['uid'])] )

		self.lo.add('cn=gid,cn=temporary,cn=univention,'+self.dn, [ \
		                        ('objectClass', ['top', 'organizationalRole']),\
		                        ('cn', ['gid'])] )

		self.lo.add('cn=mail,cn=temporary,cn=univention,'+self.dn, [ \
		                        ('objectClass', ['top', 'organizationalRole']),\
		                        ('cn', ['mail'])] )

		self.lo.add('cn=aRecord,cn=temporary,cn=univention,'+self.dn, [ \
		                        ('objectClass', ['top', 'organizationalRole']),\
		                        ('cn', ['aRecord'])] )

		if self['dnsForwardZone']:
			for i in self['dnsForwardZone']:
				soa='nameserver root.%s.%s 1 28800 7200 604800 10800' % (self['name'],dnsname)
				self.lo.add('zoneName='+i+',cn=dns,'+self.dn, [ \
										('objectClass', ['top', 'dNSZone']),\
										('zoneName', [i]),\
										('dNSTTL', ['10800']),\
										('SOARecord', [soa]),\
										('NSRecord', ['nameserver']),\
										('relativeDomainName', ['@'])])

		if self['dnsReverseZone']:
			for i in self['dnsReverseZone']:

				ipList=i.split('.')
				ipList.reverse()
				c='.'
				ipString=c.join(ipList)
				zoneName=ipString+'.in-addr.arpa'
				soa='nameserver root.%s.%s 1 28800 7200 604800 10800' % (self['name'],dnsname)
				self.lo.add('zoneName='+zoneName+',cn=dns,'+self.dn, [ \
										('objectClass', ['top', 'dNSZone']),\
										('zoneName', [zoneName]),\
										('dNSTTL', ['10800']),\
										('SOARecord', [soa]),\
										('NSRecord', ['nameserver']),\
										('relativeDomainName', ['@'])])
		oldPos=tmpPosition.getDn()
		tmpPosition.setDn('cn=groups,'+tmpPosition.getDn())
		groupObject = univention.admin.objects.default('groups/group', self.co, self.lo, tmpPosition )
		groupObject['name']='Domain Users'
		groupObject.create()

		groupObject = univention.admin.objects.default('groups/group', self.co, self.lo, tmpPosition )
		groupObject['name']='Domain Guests'
		groupObject.create()

		groupObject = univention.admin.objects.default('groups/group', self.co, self.lo, tmpPosition )
		groupObject['name']='Domain Admins'
		groupObject.create()

		groupObject = univention.admin.objects.default('groups/group', self.co, self.lo, tmpPosition )
		groupObject['name']='Account Operators'
		groupObject.create()

		groupObject = univention.admin.objects.default('groups/group', self.co, self.lo, tmpPosition )
		groupObject['name']='Windows Hosts'
		groupObject.create()

		tmpPosition.setDn(oldPos)

	def _ldap_modlist(self):
		ml=univention.admin.handlers.simpleLdap._ldap_modlist(self)

		ocs=self.oldattr.get('objectClass', [])
		if not 'univentionMailDomain' in ocs:
			ml.insert(0, ('objectClass', '', 'univentionMailDomain'))
		
		return ml
	

	
def lookup(co, lo, filter_s, base='', superordinate=None, scope='sub', unique=0, required=0, timeout=-1, sizelimit=0):

	filter=univention.admin.filter.conjunction('&', [
		univention.admin.filter.expression('objectClass', 'univentionBase'),
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
	
	return 'univentionBase' in attr.get('objectClass', [])
