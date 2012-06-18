# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin module for the dc objects
#
# Copyright 2004-2012 Univention GmbH
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

import ldap

from univention.admin.layout import Tab, Group
from univention.admin import configRegistry

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

def makeSambaDomainName(object, arg):
	return [(object['name'].upper()+'.'+object.position.getPrintable()).upper()]

module='container/dc'
childs=1
operations=['search', 'edit']
short_description=_('Container: Domain')
long_description=''
options={
	'kerberos': univention.admin.option(
			short_description=_('Kerberos realm'),
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
	'dnsForwardZone': univention.admin.property(
			short_description=_('DNS forward lookup zone'),
			long_description='',
			syntax=univention.admin.syntax.dnsName,
			multivalue=1,
			options=[],
			required=0,
			default = ( '<name>.%s' % configRegistry.get( 'domainname', '' ), [] ),
			may_change=0,
			identifies=0
		),
	'dnsReverseZone': univention.admin.property(
			short_description=_('DNS reverse lookup zone'),
			long_description='',
			syntax=univention.admin.syntax.reverseLookupSubnet,
			multivalue=1,
			options=[],
			required=0,
			may_change=0,
			identifies=0
		),
	'sambaDomainName': univention.admin.property(
			short_description=_('Samba domain name'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			default = ( configRegistry.get( 'domainname', '' ).upper(), [] ),
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
			short_description=_('Kerberos realm'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=['kerberos'],
			required=1,
			may_change=0,
			default = ( configRegistry.get( 'domainname', '' ).upper(), [] ),
			identifies=0
		),
}

layout = [
	Tab(_('General'),_('Basic settings'), layout = [
		Group( _( 'General' ), layout = [
			"name"
			] ),
		] ),
	Tab(_('DNS'),_('DNS Zones'), advanced = True, layout = [
			[ "dnsForwardZone", "dnsReverseZone" ]
		] ),
	Tab(_('Samba'),_('Samba Settings'), advanced = True, layout = [
			[ "sambaDomainName", "sambaSID" ],
			[ "sambaNextUserRid", "sambaNextGroupRid" ]
		] ),
	Tab(_('Kerberos'), _('Kerberos Settings'), advanced = True, layout = [
			'kerberosRealm'
		] ),
	]

mapping=univention.admin.mapping.mapping()
mapping.register('sambaDomainName', 'sambaDomainName')
mapping.register('sambaSID', 'sambaSID', None, univention.admin.mapping.ListToString)
mapping.register('sambaNextUserRid', 'sambaNextUserRid', None, univention.admin.mapping.ListToString)
mapping.register('sambaNextGroupRid', 'sambaNextGroupRid', None, univention.admin.mapping.ListToString)
mapping.register('kerberosRealm', 'krb5RealmName', None, univention.admin.mapping.ListToString)

class object(univention.admin.handlers.simpleLdap):
	module=module

	def __init__(self, co, lo, position, dn='', superordinate=None, attributes = [] ):
		global options
		global mapping
		global property_descriptions

		self.mapping=mapping
		self.descriptions=property_descriptions
		self.options = []
		self._define_options( options )

		self.alloc=[]

		univention.admin.handlers.simpleLdap.__init__(self, co, lo,  position, dn, superordinate, attributes = attributes )

	def open(self):
		univention.admin.handlers.simpleLdap.open(self)

		if self.dn:
			self['name']=ldap.explode_dn(self.dn,1)[0]

			
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


def lookup(co, lo, filter_s, base='', superordinate=None, scope='sub', unique=0, required=0, timeout=-1, sizelimit=0):

	filter=univention.admin.filter.conjunction('&', [
		univention.admin.filter.expression('objectClass', 'univentionBase'),
		])

	if filter_s:
		filter_p=univention.admin.filter.parse(filter_s)
		univention.admin.filter.walk(filter_p, univention.admin.mapping.mapRewrite, arg=mapping)
		filter.expressions.append(filter_p)

	res=[]
	for dn, attrs in lo.search(unicode(filter), base, scope, [], unique, required, timeout, sizelimit):
		res.append( object( co, lo, None, dn, attributes = attrs ) )
	return res

def identify(dn, attr, canonical=0):
	return 'univentionBase' in attr.get('objectClass', [])
