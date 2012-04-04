# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin module for the DC Backup hosts 
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
import univention.admin.password
import univention.admin.allocators
import univention.admin.localization
import univention.admin.uldap
import univention.admin.nagios as nagios
import univention.admin.handlers.dns.forward_zone
import univention.admin.handlers.dns.reverse_zone
import univention.admin.handlers.groups.group
import univention.admin.handlers.networks.network

translation=univention.admin.localization.translation('univention.admin.handlers.computers')
_=translation.translate

module='computers/domaincontroller_backup'
operations=['add','edit','remove','search','move']
usewizard=1
docleanup=1
childs=0
short_description=_('Computer: Domain Controller Backup')
long_description=''
options={
	'posix': univention.admin.option(
			short_description=_('Posix account'),
			default=1
		),
	'kerberos': univention.admin.option(
			short_description=_('Kerberos principal'),
			default=1
		),
	'samba': univention.admin.option(
			short_description=_('Samba account'),
			editable=1,
			default=1
		)
}
property_descriptions={
	'name': univention.admin.property(
			short_description=_('Domain controller name'),
			long_description='',
			syntax=univention.admin.syntax.hostName,
			multivalue=0,
			options=[],
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
	'domain': univention.admin.property(
			short_description=_('Domain'),
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
	'serverRole': univention.admin.property(
			short_description=_('System role'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'service': univention.admin.property(
			short_description=_('Service'),
			long_description='',
			syntax=univention.admin.syntax.Service,
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
	'password': univention.admin.property(
			short_description=_('Password'),
			long_description='',
			syntax=univention.admin.syntax.passwd,
			multivalue=0,
			options=['kerberos','posix', 'samba'],
			required=0,
			may_change=1,
			identifies=0,
			dontsearch=1
		),
	'unixhome': univention.admin.property(
			short_description=_('Unix home directory'),
			long_description='',
			syntax=univention.admin.syntax.absolutePath,
			multivalue=0,
			options=['posix'],
			required=1,
			may_change=1,
			identifies=0,
			default=('/dev/null', [])
		),
	'shell': univention.admin.property(
			short_description=_('Login shell'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=['posix'],
			required=0,
			may_change=1,
			identifies=0,
			default=('/bin/bash', [])
		),
	'primaryGroup': univention.admin.property(
			short_description=_('Primary group'),
			long_description='',
			syntax=univention.admin.syntax.primaryGroup2,
			multivalue=0,
			options=['posix'],
			required=1,
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
	'reinstalltext': univention.admin.property(
			short_description=_('Interactive installation'),
			long_description='',
			syntax=univention.admin.syntax.boolean,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'reinstalloption': univention.admin.property(
            short_description=_('additional start options'),
            long_description='',
            syntax=univention.admin.syntax.string,
            multivalue=0,
            options=[],
            required=0,
            may_change=1,
            identifies=0
        ),
	'instprofile': univention.admin.property(
			short_description=_('Name of installation profile'),
			long_description='',
			syntax=univention.admin.syntax.string,
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
			syntax=univention.admin.syntax.GroupDN,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			dontsearch=1,
			identifies=0
		),
}

layout = [
	Tab( _( 'General' ), _( 'Basic settings' ), layout = [
		Group( _( 'Computer account' ), layout = [
			[ 'name', 'description' ],
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
	Tab( _( 'Account' ), _( 'Account' ), advanced = True, layout = [
		'password',
		'primaryGroup'
		] ),
	Tab( _( 'Unix account' ), _( 'Unix account settings' ), advanced = True, layout = [
		[ 'unixhome', 'shell' ]
		] ),
	Tab( _( 'Services' ), _( 'Services' ), advanced = True, layout = [
		'service',
		] ),
	Tab( _( 'Deployment' ), _( 'Deployment' ), advanced = True, layout = [
		[ 'reinstall', 'reinstalltext' ],
		[ 'instprofile', 'reinstalloption' ]
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
mapping.register('domain', 'associatedDomain', None, univention.admin.mapping.ListToString)
mapping.register('inventoryNumber', 'univentionInventoryNumber')
mapping.register('serverRole', 'univentionServerRole')
mapping.register('mac', 'macAddress' )
mapping.register('inventoryNumber', 'univentionInventoryNumber')
mapping.register('reinstall', 'univentionServerReinstall', None, univention.admin.mapping.ListToString)
mapping.register('instprofile', 'univentionServerInstallationProfile', None, univention.admin.mapping.ListToString)
mapping.register('reinstalloption', 'univentionServerInstallationOption', None, univention.admin.mapping.ListToString)
mapping.register('reinstalltext', 'univentionServerInstallationText', None, univention.admin.mapping.ListToString)
mapping.register('network', 'univentionNetworkLink', None, univention.admin.mapping.ListToString)
mapping.register('unixhome', 'homeDirectory', None, univention.admin.mapping.ListToString)
mapping.register('shell', 'loginShell', None, univention.admin.mapping.ListToString)
mapping.register('service', 'univentionService')

# add Nagios extension
nagios.addPropertiesMappingOptionsAndLayout(property_descriptions, mapping, options, layout)


class object(univention.admin.handlers.simpleComputer, nagios.Support):
	module=module

	def __init__(self, co, lo, position, dn='', superordinate=None, attributes = [] ):
		global options
		global mapping
		global property_descriptions

		self.mapping=mapping
		self.descriptions=property_descriptions

		self.alloc=[]

		self.ipRequest=0

		self.newPrimaryGroupDn=0
		self.oldPrimaryGroupDn=0

		self.old_samba_option = False

		univention.admin.handlers.simpleComputer.__init__(self, co, lo, position, dn, superordinate, attributes)

		self.options = []
		if self.oldattr.has_key('objectClass'):
			ocs=self.oldattr['objectClass']
			if 'krb5Principal' in ocs and 'krb5KDCEntry' in ocs:
				self.options.append( 'kerberos' )
			if 'posixAccount' in ocs:
				self.options.append( 'posix' )
			if 'sambaSamAccount' in ocs:
				self.old_samba_option = True
				self.options.append( 'samba' )
		else:
			self._define_options( options )

		nagios.Support.__init__(self)

	def open(self):
		univention.admin.handlers.simpleComputer.open( self )
		self.nagios_open()

		self.modifypassword=0
		if self.dn:
			userPassword=self.oldattr.get('userPassword',[''])[0]
			if userPassword:
				self.info['password']=userPassword
				self.modifypassword=0

		self.newPrimaryGroupDn=0
		self.oldPrimaryGroupDn=0

		tmppos=univention.admin.uldap.position(self.position.getDomain())

		if self.dn:

			if 'posix' in self.options and not self.info.get( 'primaryGroup' ):
				primaryGroupNumber=self.oldattr.get('gidNumber',[''])[0]
				univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'primary group number = %s' % (primaryGroupNumber))
				if primaryGroupNumber:
					primaryGroupResult=self.lo.searchDn('(&(objectClass=posixGroup)(gidNumber='+primaryGroupNumber+'))')
					if primaryGroupResult:
						self['primaryGroup']=primaryGroupResult[0]
						univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'Set primary group = %s' % (self['primaryGroup']))
					else:
						self['primaryGroup']=None
						self.save()
						raise univention.admin.uexceptions.primaryGroup
				else:
					self['primaryGroup']=None
					self.save()
					raise univention.admin.uexceptions.primaryGroup

			self.save()

		else:
			self.modifypassword=0
			if 'posix' in self.options:
				res=univention.admin.config.getDefaultValue(self.lo, 'univentionDefaultDomainControllerMasterGroup', position=self.position)
				if res:
					self['primaryGroup']=res
					#self.save()



	def _ldap_pre_create(self):
		self.dn='%s=%s,%s' % (mapping.mapName('name'), mapping.mapValue('name', self.info['name']), self.position.getDn())
		if not self['password']:
			self['password']=self.oldattr.get('password',[''])[0]
			self.modifypassword=0
		univention.admin.handlers.simpleComputer._ldap_pre_create( self )

	def _ldap_addlist(self):
		ocs=['top', 'person', 'univentionHost', 'univentionDomainController']
		al=[]
		if 'kerberos' in self.options:
			domain=univention.admin.uldap.domain(self.lo, self.position)
			realm=domain.getKerberosRealm()
			if self.info.has_key('domain') and self.info['domain']:
				kerberos_domain=self.info['domain']
			else:
				kerberos_domain=domain.getKerberosRealm()
			tmppos=univention.admin.uldap.position(self.position.getDomain())

			if realm:
				ocs.extend(['krb5Principal', 'krb5KDCEntry'])
				al.append(('krb5PrincipalName', [self.krb5_principal()]))
				al.append(('krb5MaxLife', '86400'))
				al.append(('krb5MaxRenew', '604800'))
				al.append(('krb5KDCFlags', '126'))
				krb_key_version=str(int(self.oldattr.get('krb5KeyVersionNumber', ['0'])[0])+1)
				al.append(('krb5KeyVersionNumber', self.oldattr.get('krb5KeyVersionNumber', []), krb_key_version))
			else:
				# can't do kerberos
				self._remove_option( 'kerberos' )
		if 'posix' in self.options:
			self.uidNum=univention.admin.allocators.request(self.lo, self.position, 'uidNumber')
			self.alloc.append(('uidNumber',self.uidNum))
			if self['primaryGroup']:
				searchResult=self.lo.search(base=self['primaryGroup'], attr=['gidNumber'])
				for tmp,number in searchResult:
					gidNum = number['gidNumber'][0]
			else:
				gidNum='99999'
			ocs.extend(['posixAccount','shadowAccount'])
			al.append(('uidNumber', [self.uidNum]))
			al.append(('gidNumber', [gidNum]))

		if self.modifypassword or self['password']:
			if 'kerberos' in self.options:
				krb_keys=univention.admin.password.krb5_asn1(self.krb5_principal(), self['password'])
				al.append(('krb5Key', self.oldattr.get('password', ['1']), krb_keys))
			if 'posix' in self.options:
				password_crypt = "{crypt}%s" % (univention.admin.password.crypt(self['password']))
				al.append(('userPassword', self.oldattr.get('userPassword', [''])[0], password_crypt))
			#The password must be set via net rpc join
			#if 'samba' in self.options:
			#	password_nt, password_lm = univention.admin.password.ntlm(self['password'])
			#	al.append(('sambaNTPassword', self.oldattr.get('sambaNTPassword', [''])[0], password_nt))
			#	al.append(('sambaLMPassword', self.oldattr.get('sambaLMPassword', [''])[0], password_lm))

			self.modifypassword=0
		if 'samba' in self.options:
			acctFlags=univention.admin.samba.acctFlags(flags={'S':1})
			if self.s4connector_present:
				# In this case Samba 4 must create the SID, the s4 connector will sync the
				# new sambaSID back from Samba 4.
				self.machineSid='S-1-4-%s' % self.uidNum
			else:
				self.machineSid = self.getMachineSid(self.lo, self.position, self.uidNum)
				self.alloc.append(('sid',self.machineSid))
			ocs.append('sambaSamAccount')
			al.append(('sambaSID', [self.machineSid]))
			al.append(('sambaAcctFlags', [acctFlags.decode()]))
			al.append(('displayName', self.info['name']))
			self.old_samba_option = True

		al.insert(0, ('objectClass', ocs))
		al.append(('univentionServerRole', '', 'backup'))
		return al

	def _ldap_post_create(self):
		if 'posix' in self.options:
			if hasattr(self, 'uid') and self.uid:
				univention.admin.allocators.confirm(self.lo, self.position, 'uid', self.uid)
			univention.admin.handlers.simpleComputer.primary_group( self )
			univention.admin.handlers.simpleComputer.update_groups( self )
		univention.admin.handlers.simpleComputer._ldap_post_create( self )
		self.nagios_ldap_post_create()

	def _ldap_pre_remove(self):
		self.open()
		if 'posix' in self.options and self.oldattr.get( 'uidNumber' ):
			self.uidNum=self.oldattr['uidNumber'][0]

	def _ldap_post_remove(self):
		if 'posix' in self.options:
			univention.admin.allocators.release(self.lo, self.position, 'uidNumber', self.uidNum)
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
		# Need to clean up oldinfo. If remove was invoked, because the
		# creation of the object has failed, the next try will result in
		# a 'object class violation' (Bug #19343)
		self.oldinfo = {}

	def krb5_principal(self):
		domain=univention.admin.uldap.domain(self.lo, self.position)
		realm=domain.getKerberosRealm()
		if self.info.has_key('domain') and self.info['domain']:
			kerberos_domain=self.info['domain']
		else:
			kerberos_domain=domain.getKerberosRealm()
		return 'host/' + self['name']+'.'+kerberos_domain.lower()+'@'+realm

	def _ldap_post_modify(self):
		univention.admin.handlers.simpleComputer.primary_group( self )
		univention.admin.handlers.simpleComputer.update_groups( self )
		univention.admin.handlers.simpleComputer._ldap_post_modify( self )
		self.nagios_ldap_post_modify()

	def _ldap_pre_modify(self):
		if self.hasChanged('password'):
			if not self['password']:
				self['password']=self.oldattr.get('password',[''])[0]
				self.modifypassword=0
			elif not self.info['password']:
				self['password']=self.oldattr.get('password',[''])[0]
				self.modifypassword=0
			else:
				self.modifypassword=1
		self.nagios_ldap_pre_modify()
		univention.admin.handlers.simpleComputer._ldap_pre_modify( self )


	def _ldap_modlist(self):
		ml=univention.admin.handlers.simpleComputer._ldap_modlist( self )

		self.nagios_ldap_modlist(ml)

		if self.hasChanged('name'):
			if 'posix' in self.options:
				if hasattr(self, 'uidNum'):
					univention.admin.allocators.confirm(self.lo, self.position, 'uidNumber', self.uidNum)
				requested_uid="%s$" % self['name']
				try:
					self.uid=univention.admin.allocators.request(self.lo, self.position, 'uid', value=requested_uid)
				except Exception, e:
					self.cancel()
					raise univention.admin.uexceptions.uidAlreadyUsed, ': %s' % requested_uid
					return []

				self.alloc.append(('uid',self.uid))

				ml.append(('uid', self.oldattr.get('uid', [None])[0], self.uid))

			if 'samba' in self.options:
				ml.append(('displayName', self.oldattr.get('displayName', [None])[0], self['name']))

			if 'kerberos' in self.options:
				ml.append(('krb5PrincipalName', self.oldattr.get('krb5PrincipalName', []), [self.krb5_principal()]))

		if self.modifypassword and self['password']:
			if 'kerberos' in self.options:
				krb_keys=univention.admin.password.krb5_asn1(self.krb5_principal(), self['password'])
				krb_key_version=str(int(self.oldattr.get('krb5KeyVersionNumber', ['0'])[0])+1)
				ml.append(('krb5Key', self.oldattr.get('password', ['1']), krb_keys))
				ml.append(('krb5KeyVersionNumber', self.oldattr.get('krb5KeyVersionNumber', []), krb_key_version))
			if 'posix' in self.options:
				password_crypt = "{crypt}%s" % (univention.admin.password.crypt(self['password']))
				ml.append(('userPassword', self.oldattr.get('userPassword', [''])[0], password_crypt))
			#The password must be set via net rpc join
			#if 'samba' in self.options:
			#	password_nt, password_lm = univention.admin.password.ntlm(self['password'])
			#	ml.append(('sambaNTPassword', self.oldattr.get('sambaNTPassword', [''])[0], password_nt))
			#	ml.append(('sambaLMPassword', self.oldattr.get('sambaLMPassword', [''])[0], password_lm))

		# add samba option
		if 'samba' in self.options and not self.old_samba_option:
			acctFlags=univention.admin.samba.acctFlags(flags={'S':1})
			if self.s4connector_present:
				# In this case Samba 4 must create the SID, the s4 connector will sync the
				# new sambaSID back from Samba 4.
				self.machineSid='S-1-4-%s' % self.oldattr['uidNumber'][0]
			else:
				self.machineSid = self.getMachineSid(self.lo, self.position, self.oldattr['uidNumber'][0])
				self.alloc.append(('sid',self.machineSid))
			ml.insert(0, ('objectClass', '', 'sambaSamAccount'))
			ml.append(('sambaSID', '', [self.machineSid]))
			ml.append(('sambaAcctFlags', '', [acctFlags.decode()]))
			ml.append(('displayName', '', self.info['name']))
		if not 'samba' in self.options and self.old_samba_option:
			ocs=self.oldattr.get('objectClass', [])
			if 'sambaSamAccount' in ocs:
				ml.insert(0, ('objectClass', 'sambaSamAccount', ''))
			for key in [ 'sambaSID', 'sambaAcctFlags', 'sambaNTPassword', 'sambaLMPassword', 'sambaPwdLastSet', 'displayName' ]:
				if self.oldattr.get(key, []):
					ml.insert(0, (key, self.oldattr.get(key, []), ''))

		return ml



	def cleanup(self):
		self.open()
		self.nagios_cleanup()
		univention.admin.handlers.simpleComputer.cleanup( self )

	def cancel(self):
		for i,j in self.alloc:
			univention.debug.debug(univention.debug.ADMIN, univention.debug.WARN, 'cancel: release (%s): %s' % (i,j) )
			univention.admin.allocators.release(self.lo, self.position, i, j)

	def link(self):
		result = []
		if self['ip'] and len( self[ 'ip' ] ) > 0 and self['ip'][ 0 ]:
			result = [{ 'url': 'https://%s/univention-management-console/' % self['ip'][ 0 ],
						'ipaddr': self['ip'][ 0 ],
						}]
		if self.has_key('dnsEntryZoneForward') and self['dnsEntryZoneForward'] and len( self['dnsEntryZoneForward' ] ) > 0:
			zone = univention.admin.uldap.explodeDn( self['dnsEntryZoneForward'][0], 1)[0]
			if not result:
				result = [ { 'url': 'https://%s.%s/univention-management-console/' % (self['name'], zone) }]
			result[0]['fqdn'] = '%s.%s' % (self['name'], zone)
		if result:
			result[0]['name'] = _('Open Univention Management Console on this computer')
			return result
		return None

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
			univention.admin.filter.expression('objectClass', 'univentionDomainController'),
			univention.admin.filter.expression('univentionServerRole', 'backup'),
			])

		if filter_s:
			filter_p=univention.admin.filter.parse(filter_s)
			univention.admin.filter.walk(filter_p, rewrite, arg=mapping)
			filter.expressions.append(filter_p)

		for dn, attrs in lo.search(unicode(filter), base, scope, [], unique, required, timeout, sizelimit):
			res.append( object( co, lo, None, dn, attributes = attrs ) )
	return res

def identify(dn, attr, canonical=0):
	return 'univentionHost' in attr.get('objectClass', []) and 'univentionDomainController' in attr.get('objectClass', []) and 'backup' in attr.get('univentionServerRole', [])
