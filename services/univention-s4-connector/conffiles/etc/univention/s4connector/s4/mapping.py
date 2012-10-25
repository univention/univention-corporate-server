# -*- coding: utf-8 -*-
#
# Univention S4 Connector
#  this file defines the mapping beetween S4 and UCS
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

import univention.s4connector.s4
import univention.s4connector.s4.mapping
import univention.s4connector.s4.password
import univention.s4connector.s4.sid_mapping
import univention.s4connector.s4.dns
import univention.s4connector.s4.dc

global_ignore_subtree=['cn=univention,@%@ldap/base@%@','cn=policies,@%@ldap/base@%@',
			'cn=shares,@%@ldap/base@%@','cn=printers,@%@ldap/base@%@',
			'cn=networks,@%@ldap/base@%@', 'cn=kerberos,@%@ldap/base@%@',
			'cn=dhcp,@%@ldap/base@%@',
			'cn=mail,@%@ldap/base@%@',
			'cn=nagios,@%@ldap/base@%@',
			'CN=RAS and IAS Servers Access Check,CN=System,@%@connector/s4/ldap/base@%@',
			'CN=FileLinks,CN=System,@%@connector/s4/ldap/base@%@',
			'CN=WinsockServices,CN=System,@%@connector/s4/ldap/base@%@',
			'CN=RID Manager$,CN=System,@%@connector/s4/ldap/base@%@',
			'CN=Dfs-Configuration,CN=System,@%@connector/s4/ldap/base@%@',
			'CN=Server,CN=System,@%@connector/s4/ldap/base@%@',
			'CN=ComPartitionSets,CN=System,@%@connector/s4/ldap/base@%@',
			'CN=ComPartitions,CN=System,@%@connector/s4/ldap/base@%@',
			'CN=IP Security,CN=System,@%@connector/s4/ldap/base@%@',
			'CN=DFSR-GlobalSettings,CN=System,@%@connector/s4/ldap/base@%@',
			'CN=DomainUpdates,CN=System,@%@connector/s4/ldap/base@%@',
			'CN=Password Settings Container,CN=System,@%@connector/s4/ldap/base@%@',
			'DC=RootDNSServers,CN=MicrosoftDNS,CN=System,@%@connector/s4/ldap/base@%@',
			'CN=File Replication Service,CN=System,@%@connector/s4/ldap/base@%@',
			'CN=RpcServices,CN=System,@%@connector/s4/ldap/base@%@',
			'CN=Meetings,CN=System,@%@connector/s4/ldap/base@%@',
			'CN=AdminSDHolder,CN=System,@%@connector/s4/ldap/base@%@',
			'CN=WMIPolicy,CN=System,@%@connector/s4/ldap/base@%@',
			'CN=BCKUPKEY_c490e871-a375-4b76-bd24-711e9e49fe5e Secret,CN=System,@%@connector/s4/ldap/base@%@',
			'CN=BCKUPKEY_PREFERRED Secret,CN=System,@%@connector/s4/ldap/base@%@',
			'ou=Grp Policy Users,@%@connector/s4/ldap/base@%@',
			'cn=Builtin,@%@connector/s4/ldap/base@%@',
			'cn=ForeignSecurityPrincipals,@%@connector/s4/ldap/base@%@',
			'cn=Program Data,@%@connector/s4/ldap/base@%@',
			'cn=Configuration,@%@connector/s4/ldap/base@%@',
			'cn=opsi,@%@ldap/base@%@',
			'cn=Microsoft Exchange System Objects,@%@connector/s4/ldap/base@%@']


s4_mapping = {
	'user': univention.s4connector.property (
			ucs_default_dn='cn=users,@%@ldap/base@%@',
			con_default_dn='cn=users,@%@connector/s4/ldap/base@%@',

			ucs_module='users/user',

			# read, write, sync, none
			sync_mode='@%@connector/s4/mapping/syncmode@%@',
			scope='sub',

			con_search_filter='(&(objectClass=user)(!(objectClass=computer))(userAccountControl:1.2.840.113556.1.4.803:=512))',
			match_filter='(&(|(&(objectClass=posixAccount)(objectClass=krb5Principal))(objectClass=user))(!(objectClass=univentionHost)))',
@!@
ignore_filter = ''
for user in configRegistry.get('connector/s4/mapping/user/ignorelist', '').split(','):
	if user:
		ignore_filter += '(uid=%s)(CN=%s)' % (user, user)
if ignore_filter:
	print "			ignore_filter='(|%s)'," % ignore_filter
@!@
			ignore_subtree = global_ignore_subtree,
			
			con_create_objectclass=['top', 'user', 'person', 'organizationalPerson'],

			dn_mapping_function=[ univention.s4connector.s4.user_dn_mapping ],

			# aus UCS Modul
			attributes= {
					'samAccountName': univention.s4connector.attribute (
							ucs_attribute='username',
							ldap_attribute='uid',
							con_attribute='sAMAccountName',
							required=1,
							compare_function=univention.s4connector.compare_lowercase,
						),
					'givenName' : univention.s4connector.attribute (
							ucs_attribute='firstname',
							ldap_attribute='givenName',
							con_attribute='givenName',
						),
					'sn': univention.s4connector.attribute (
							ucs_attribute='lastname',
							ldap_attribute='sn',
							con_attribute='sn',
						),
					@!@
import univention.s4connector.s4.sid_mapping
univention.s4connector.s4.sid_mapping.print_sid_mapping(configRegistry)
@!@
			},

			# These functions can extend the addlist while
			# creating an object in S4. Parameters are
			#	s4connector, property_type, object, addlist, serverctrls
			con_create_extenstions = [
							univention.s4connector.s4.add_primary_group_to_addlist,
			],
			ucs_create_functions = [
							univention.s4connector.set_ucs_passwd_user,
						 	univention.s4connector.check_ucs_lastname_user,
						 	univention.s4connector.set_primary_group_user,
							@!@
if configRegistry.is_true('connector/s4/mapping/sid_to_ucs', True) and not configRegistry.is_true('connector/s4/mapping/sid', True):
	print 'univention.s4connector.s4.sid_mapping.sid_to_ucs,'
@!@
						 	],

			post_con_create_functions = [
							univention.s4connector.s4.normalise_userAccountControl,
						 	],

			post_con_modify_functions=[
							@!@
if configRegistry.is_true('connector/s4/mapping/sid_to_s4', False) and not configRegistry.is_true('connector/s4/mapping/sid', True):
	print 'univention.s4connector.s4.sid_mapping.sid_to_s4,'
@!@
							univention.s4connector.s4.password.password_sync_ucs_to_s4,
						    univention.s4connector.s4.primary_group_sync_from_ucs,
						    univention.s4connector.s4.object_memberships_sync_from_ucs,
						    univention.s4connector.s4.disable_user_from_ucs,
						    ],

			post_ucs_modify_functions=[
							@!@
if configRegistry.is_true('connector/s4/mapping/sid_to_ucs', True) and not configRegistry.is_true('connector/s4/mapping/sid', True):
	print 'univention.s4connector.s4.sid_mapping.sid_to_ucs,'
@!@
							univention.s4connector.s4.password.password_sync_s4_to_ucs,
						    univention.s4connector.s4.primary_group_sync_to_ucs,
						    univention.s4connector.s4.object_memberships_sync_to_ucs,
						    univention.s4connector.s4.disable_user_to_ucs,
						    ],

			post_attributes={
					'organisation': univention.s4connector.attribute (
							ucs_attribute='organisation',
							ldap_attribute='o',
							con_attribute='company',
						),
					'organisation': univention.s4connector.attribute (
							ucs_attribute='organisation',
							ldap_attribute='o',
							con_attribute='company',
						),
					'description': univention.s4connector.attribute (
							ucs_attribute='description',
							ldap_attribute='description',
							con_attribute='description',
						),
					'mailPrimaryAddress': univention.s4connector.attribute (
							ucs_attribute='mailPrimaryAddress',
							ldap_attribute='mailPrimaryAddress',
							con_attribute='mail',
							reverse_attribute_check = True,
						),
					'street': univention.s4connector.attribute (
							ucs_attribute='street',
							ldap_attribute='street',
							con_attribute='streetAddress',
						),
					'city': univention.s4connector.attribute (
							ucs_attribute='city',
							ldap_attribute='l',
							con_attribute='l',
						),
					'postcode': univention.s4connector.attribute (
							ucs_attribute='postcode',
							ldap_attribute='postalCode',
							con_attribute='postalCode',
						),
					'sambaWorkstations': univention.s4connector.attribute (
							ucs_attribute='sambaUserWorkstations',
							ldap_attribute='sambaUserWorkstations',
							con_attribute='userWorkstations',
						),
					#'sambaLogonHours': univention.s4connector.attribute (
					#		ucs_attribute='sambaLogonHours',
					#		ldap_attribute='sambaLogonHours',
					#		con_attribute='logonHours',
					#	),
					'profilepath': univention.s4connector.attribute (
							ucs_attribute='profilepath',
							ldap_attribute='sambaProfilePath',
							con_attribute='profilePath',
						),
					'scriptpath': univention.s4connector.attribute (
							ucs_attribute='scriptpath',
							ldap_attribute='sambaLogonScript',
							con_attribute='scriptPath',
						),
					'homeDrive': univention.s4connector.attribute (
							ucs_attribute='homedrive',
							ldap_attribute='sambaHomeDrive',
							con_attribute='homeDrive',
						),
					'homeDirectory': univention.s4connector.attribute (
							ucs_attribute='sambahome',
							ldap_attribute='sambaHomePath',
							con_attribute='homeDirectory',
							reverse_attribute_check = True,
						),
					'telephoneNumber': univention.s4connector.attribute (
							ucs_attribute='phone',
							ldap_attribute='telephoneNumber',
							con_attribute='telephoneNumber',
							con_other_attribute='otherTelephone',
						),
					'homePhone': univention.s4connector.attribute (
							ucs_attribute='homeTelephoneNumber',
							ldap_attribute='homePhone',
							con_attribute='homePhone',
							con_other_attribute='otherHomePhone',
						),
					'mobilePhone': univention.s4connector.attribute (
							ucs_attribute='mobileTelephoneNumber',
							ldap_attribute='mobile',
							con_attribute='mobile',
							con_other_attribute='otherMobile',
						),
					'pager': univention.s4connector.attribute (
							ucs_attribute='pagerTelephoneNumber',
							ldap_attribute='pager',
							con_attribute='pager',
							con_other_attribute='otherPager',
						),
					'displayName': univention.s4connector.attribute (
							ucs_attribute='displayName',
							ldap_attribute='displayName',
							con_attribute='displayName',
						),
			},

		),

	'group': univention.s4connector.property (
			ucs_default_dn='cn=groups,@%@ldap/base@%@',
			con_default_dn='cn=Users,@%@connector/s4/ldap/base@%@',

			ucs_module='groups/group',

			sync_mode='@%@connector/s4/mapping/syncmode@%@',
			scope='sub',

@!@
ignore_filter = ''
for group in configRegistry.get('connector/s4/mapping/group/ignorelist', '').split(','):
	if group:
		ignore_filter += '(cn=%s)' % (group)
print "			ignore_filter='(|(sambaGroupType=5)(groupType=5)%s)'," % ignore_filter
@!@

			ignore_subtree = global_ignore_subtree,
			
			con_search_filter='objectClass=group',

			con_create_objectclass=['top', 'group'],

			post_con_modify_functions=[
							@!@
if configRegistry.is_true('connector/s4/mapping/sid_to_s4', False) and not configRegistry.is_true('connector/s4/mapping/sid', True):
	print 'univention.s4connector.s4.sid_mapping.sid_to_s4,'
@!@
							univention.s4connector.s4.group_members_sync_from_ucs,
							univention.s4connector.s4.object_memberships_sync_from_ucs
							],

			post_ucs_modify_functions=[
							@!@
if configRegistry.is_true('connector/s4/mapping/sid_to_ucs', True) and not configRegistry.is_true('connector/s4/mapping/sid', True):
	print 'univention.s4connector.s4.sid_mapping.sid_to_ucs,'
@!@
							univention.s4connector.s4.group_members_sync_to_ucs,
							univention.s4connector.s4.object_memberships_sync_to_ucs
							],

			dn_mapping_function=[ univention.s4connector.s4.group_dn_mapping ],

			attributes= {
					'cn': univention.s4connector.attribute (
							ucs_attribute='name',
							ldap_attribute='cn',
							con_attribute='sAMAccountName',
							required=1,
							compare_function=univention.s4connector.compare_lowercase,
						),
					'description': univention.s4connector.attribute (
							ucs_attribute='description',
							ldap_attribute='description',
							con_attribute='description',
						),
					'mailAddress': univention.s4connector.attribute (
							ucs_attribute='mailAddress',
							ldap_attribute='mailPrimaryAddress',
							con_attribute='mail',
							reverse_attribute_check = True,
					),
					@!@
import univention.s4connector.s4.sid_mapping
univention.s4connector.s4.sid_mapping.print_sid_mapping(configRegistry)
@!@
				},

			mapping_table = {
@!@
group_map = {}
key_prefix = "connector/s4/mapping/group/table/"
for key,value in configRegistry.items():
	if key.startswith(key_prefix):
		ucs_groupname = key[len(key_prefix):]
		group_map[ucs_groupname] = value
if group_map:
	print "\n\t\t\t'cn': ["
	for key,value in group_map.items():
		print "\t\t\t\t(u'%s', u'%s')," % (key, value)
	print "\t\t\t\t]"
@!@
			},

		),
	'dc': univention.s4connector.property (
			ucs_default_dn='cn=dc,cn=computers,@%@ldap/base@%@',
			con_default_dn='OU=Domain Controllers,@%@connector/s4/ldap/base@%@',
			ucs_module='computers/windows_domaincontroller',
			ucs_module_others=['computers/domaincontroller_master', 'computers/domaincontroller_backup', 'computers/domaincontroller_slave'],
			con_search_filter='(&(objectClass=computer)(userAccountControl:1.2.840.113556.1.4.803:=532480))',

			position_mapping = [( ',cn=dc,cn=computers,@%@ldap/base@%@', ',ou=Domain Controllers,@%@connector/s4/ldap/base@%@' )],

			match_filter='(|(&(objectClass=univentionDomainController)(univentionService=Samba 4))(objectClass=computer)(univentionServerRole=windows_domaincontroller))',

			dn_mapping_function=[ univention.s4connector.s4.dc_dn_mapping ],

			# Whether a DC joins to the samba 4 domain
			# the DC will be deleted.
			disable_delete_in_ucs = True,

			# Whether a DC is removed in UCS, the DC should be removed
			# in S4. By default a DC has a subobject wihtout any mapping
			# and this subobject would avoid a deletion of this DC in S4
			con_subtree_delete_objects = [ 'cn=rid set' ],
@!@
ignore_filter = ''
for dc in configRegistry.get('connector/s4/mapping/dc/ignorelist', '').split(','):
	if dc:
		ignore_filter += '(cn=%s)' % (dc)
if ignore_filter:
	print "			ignore_filter='(|%s)'," % ignore_filter
@!@
	
			con_create_objectclass=['top', 'computer' ],
			
			con_create_attributes=[
									('userAccountControl', ['532480']),
								  ],
	
			post_con_modify_functions=[
							@!@
if configRegistry.is_true('connector/s4/mapping/sid_to_s4', False) and not configRegistry.is_true('connector/s4/mapping/sid', True):
	print 'univention.s4connector.s4.sid_mapping.sid_to_s4,'
@!@
							univention.s4connector.s4.password.password_sync_ucs_to_s4,
						    ],
	
			post_ucs_modify_functions=[
							@!@
if configRegistry.is_true('connector/s4/mapping/sid_to_ucs', True) and not configRegistry.is_true('connector/s4/mapping/sid', True):
	print 'univention.s4connector.s4.sid_mapping.sid_to_ucs,'
@!@
							univention.s4connector.s4.password.password_sync_s4_to_ucs_no_userpassword,
						    ],
	
			attributes= {
					'cn': univention.s4connector.attribute (
							ucs_attribute='name',
							ldap_attribute='cn',
							con_attribute='cn',
							required=1,
							compare_function=univention.s4connector.compare_lowercase,
						),
					'samAccountName': univention.s4connector.attribute (
							ldap_attribute='uid',
							con_attribute='sAMAccountName',
							compare_function=univention.s4connector.compare_lowercase,
						),
					'description': univention.s4connector.attribute (
							ucs_attribute='description',
							ldap_attribute='description',
							con_attribute='description'
						),
					'operatingSystem': univention.s4connector.attribute (
							ucs_attribute='operatingSystem',
							ldap_attribute='univentionOperatingSystem',
							con_attribute='operatingSystem'
						),
					'operatingSystemVersion': univention.s4connector.attribute (
							ucs_attribute='operatingSystemVersion',
							ldap_attribute='univentionOperatingSystemVersion',
							con_attribute='operatingSystemVersion'
						),
					@!@
import univention.s4connector.s4.sid_mapping
univention.s4connector.s4.sid_mapping.print_sid_mapping(configRegistry)
@!@
				},
	
		),
	'windowscomputer': univention.s4connector.property (
			ucs_default_dn='cn=computers,@%@ldap/base@%@',
			con_default_dn='cn=computers,@%@connector/s4/ldap/base@%@',
			ucs_module='computers/windows',
			ucs_module_others=['computers/memberserver'],

			sync_mode='@%@connector/s4/mapping/syncmode@%@',

			scope='sub',

			dn_mapping_function=[ univention.s4connector.s4.windowscomputer_dn_mapping ],

			con_search_filter='(&(objectClass=computer)(userAccountControl:1.2.840.113556.1.4.803:=4096))',

			# ignore_filter='userAccountControl=4096',
			match_filter='(|(&(objectClass=univentionWindows)(!(univentionServerRole=windows_domaincontroller)))(objectClass=computer)(objectClass=univentionMemberServer))',

			ignore_subtree = global_ignore_subtree,
@!@
ignore_filter = ''
for computer in configRegistry.get('connector/s4/mapping/windowscomputer/ignorelist', '').split(','):
	if computer:
		ignore_filter += '(cn=%s)' % (computer)
if ignore_filter:
	print "			ignore_filter='(|%s)'," % ignore_filter
@!@

			con_create_objectclass=['top', 'computer' ],

			con_create_attributes=[('userAccountControl', ['4096'])],

			#post_con_create_functions = [ univention.connector.s4.computers.
			post_con_modify_functions=[
							@!@
if configRegistry.is_true('connector/s4/mapping/sid_to_s4', False) and not configRegistry.is_true('connector/s4/mapping/sid', True):
	print 'univention.s4connector.s4.sid_mapping.sid_to_s4,'
@!@
							univention.s4connector.s4.password.password_sync_ucs_to_s4,
						    ],

			post_ucs_modify_functions=[
							@!@
if configRegistry.is_true('connector/s4/mapping/sid_to_ucs', True) and not configRegistry.is_true('connector/s4/mapping/sid', True):
	print 'univention.s4connector.s4.sid_mapping.sid_to_ucs,'
@!@
							univention.s4connector.s4.password.password_sync_s4_to_ucs_no_userpassword,
						    ],

			attributes= {
					'cn': univention.s4connector.attribute (
							ucs_attribute='name',
							ldap_attribute='cn',
							con_attribute='cn',
							required=1,
							compare_function=univention.s4connector.compare_lowercase,
						),
					'samAccountName': univention.s4connector.attribute (
							ldap_attribute='uid',
							con_attribute='sAMAccountName',
							compare_function=univention.s4connector.compare_lowercase,
						),
					'description': univention.s4connector.attribute (
							ucs_attribute='description',
							ldap_attribute='description',
							con_attribute='description'
						),
					'operatingSystem': univention.s4connector.attribute (
							ucs_attribute='operatingSystem',
							ldap_attribute='univentionOperatingSystem',
							con_attribute='operatingSystem'
						),
					'operatingSystemVersion': univention.s4connector.attribute (
							ucs_attribute='operatingSystemVersion',
							ldap_attribute='univentionOperatingSystemVersion',
							con_attribute='operatingSystemVersion'
						),
					@!@
import univention.s4connector.s4.sid_mapping
univention.s4connector.s4.sid_mapping.print_sid_mapping(configRegistry)
@!@
				},

		),
	'dns': univention.s4connector.property (
			ucs_default_dn='cn=dns,@%@ldap/base@%@',
			con_default_dn='CN=MicrosoftDNS,CN=System,@%@connector/s4/ldap/base@%@',
			ucs_module='dns/dns',
			
			identify=univention.s4connector.s4.dns.identify,

			@!@
if configRegistry.get('connector/s4/mapping/dns/syncmode'):
	print "sync_mode='%s'," % configRegistry.get('connector/s4/mapping/dns/syncmode')
else:
	print "sync_mode='%s'," % configRegistry.get('connector/s4/mapping/syncmode')
@!@

			scope='sub',

			con_search_filter='(|(objectClass=dnsNode)(objectClass=dnsZone))',

			position_mapping = [( ',cn=dns,@%@ldap/base@%@', ',CN=MicrosoftDNS,CN=System,@%@connector/s4/ldap/base@%@' )],

@!@
ignore_filter = ''
for dns in configRegistry.get('connector/s4/mapping/dns/ignorelist', '').split(','):
	if dns:
		ignore_filter += '(%s)' % (dns)
if ignore_filter:
	print "			ignore_filter='(|%s)'," % ignore_filter
@!@

			ignore_subtree = global_ignore_subtree,
			
			con_sync_function = univention.s4connector.s4.dns.ucs2con,
			ucs_sync_function = univention.s4connector.s4.dns.con2ucs,

		),
@!@
if configRegistry.is_true('connector/s4/mapping/gpo', True):
	ignore_filter = ''
	for gpo in configRegistry.get('connector/s4/mapping/gpo/ignorelist', '').split(','):
		if gpo:
			ignore_filter += '(cn=%s)' % (gpo)
	print '''
	'msGPO': univention.s4connector.property (
			ucs_module='container/msgpo',

			sync_mode='@%@connector/s4/mapping/syncmode@%@',

			scope='sub',

			con_search_filter='(&(objectClass=container)(objectClass=groupPolicyContainer))',

			ignore_filter='%s',

			ignore_subtree = global_ignore_subtree,
			
			con_create_objectclass=['top', 'container', 'groupPolicyContainer' ],

			attributes= {
					'cn': univention.s4connector.attribute (
							ucs_attribute='name',
							ldap_attribute='cn',
							con_attribute='cn',
							required=1,
							compare_function=univention.s4connector.compare_lowercase,
						),
					'description': univention.s4connector.attribute (
							ucs_attribute='description',
							ldap_attribute='description',
							con_attribute='description'
						),
					'displayName': univention.s4connector.attribute (
							ucs_attribute='displayName',
							ldap_attribute='displayName',
							con_attribute='displayName'
						),
					'msGPOFlags': univention.s4connector.attribute (
							ucs_attribute='msGPOFlags',
							ldap_attribute='msGPOFlags',
							con_attribute='flags'
						),
					'msGPOVersionNumber': univention.s4connector.attribute (
							ucs_attribute='msGPOVersionNumber',
							ldap_attribute='msGPOVersionNumber',
							con_attribute='versionNumber'
						),
					'msGPOSystemFlags': univention.s4connector.attribute (
							ucs_attribute='msGPOSystemFlags',
							ldap_attribute='msGPOSystemFlags',
							con_attribute='systemFlags'
						),
					'msGPOFunctionalityVersion': univention.s4connector.attribute (
							ucs_attribute='msGPOFunctionalityVersion',
							ldap_attribute='msGPOFunctionalityVersion',
							con_attribute='gPCFunctionalityVersion'
						),
					'msGPOFileSysPath': univention.s4connector.attribute (
							ucs_attribute='msGPOFileSysPath',
							ldap_attribute='msGPOFileSysPath',
							con_attribute='gPCFileSysPath'
						),
					'msGPOMachineExtensionNames': univention.s4connector.attribute (
							ucs_attribute='msGPOMachineExtensionNames',
							ldap_attribute='msGPOMachineExtensionNames',
							con_attribute='gPCMachineExtensionNames'
						),
					'msGPOUserExtensionNames': univention.s4connector.attribute (
							ucs_attribute='msGPOUserExtensionNames',
							ldap_attribute='msGPOUserExtensionNames',
							con_attribute='gPCUserExtensionNames'
						),
				},

		),
''' % ignore_filter
@!@
	'container': univention.s4connector.property (
			ucs_module='container/cn',

			sync_mode='@%@connector/s4/mapping/syncmode@%@',

			scope='sub',

			con_search_filter='(&(|(objectClass=container)(objectClass=builtinDomain))(!(objectClass=groupPolicyContainer)))', # builtinDomain is cn=builtin (with group cn=Administrators)

@!@
ignore_filter = ''
for cn in configRegistry.get('connector/s4/mapping/container/ignorelist', 'mail,kerberos,MicrosoftDNS').split(','):
	if cn:
		ignore_filter += '(cn=%s)' % (cn)
if ignore_filter:
	print "			ignore_filter='(|%s)'," % ignore_filter
@!@

			ignore_subtree = global_ignore_subtree,
			
			con_create_objectclass=['top', 'container' ],

			attributes= {
					'cn': univention.s4connector.attribute (
							ucs_attribute='name',
							ldap_attribute='cn',
							con_attribute='cn',
							required=1,
							compare_function=univention.s4connector.compare_lowercase,
						),
					'description': univention.s4connector.attribute (
							ucs_attribute='description',
							ldap_attribute='description',
							con_attribute='description'
						),
@!@
if configRegistry.is_true('connector/s4/mapping/gpo', True):
	print '''
					'gPLink': univention.s4connector.attribute (
							ucs_attribute='gPLink',
							ldap_attribute='msGPOLink',
							con_attribute='gPLink'
						),
	'''
@!@
				},

		),

	'ou': univention.s4connector.property (
			ucs_module='container/ou',

			sync_mode='@%@connector/s4/mapping/syncmode@%@',

			scope='sub',

			con_search_filter='objectClass=organizationalUnit',

@!@
ignore_filter = ''
for ou in configRegistry.get('connector/s4/mapping/ou/ignorelist', '').split(','):
	if ou:
		ignore_filter += '(ou=%s)' % (ou)
if ignore_filter:
	print "			ignore_filter='(|%s)'," % ignore_filter
@!@

			ignore_subtree = global_ignore_subtree,

			con_create_objectclass=[ 'top', 'organizationalUnit' ],

			attributes= {
					'ou': univention.s4connector.attribute (
							ucs_attribute='name',
							ldap_attribute='ou',
							con_attribute='ou',
							required=1,
							compare_function=univention.s4connector.compare_lowercase,
						),
					'description': univention.s4connector.attribute (
							ucs_attribute='description',
							ldap_attribute='description',
							con_attribute='description'
						),
@!@
if configRegistry.is_true('connector/s4/mapping/gpo', True):
	print '''
					'gPLink': univention.s4connector.attribute (
							ucs_attribute='gPLink',
							ldap_attribute='msGPOLink',
							con_attribute='gPLink'
						),
	'''
@!@
				},
		),
	'container_dc': univention.s4connector.property (
			ucs_module='container/dc',
			ucs_default_dn='cn=samba,@%@ldap/base@%@',
			con_default_dn='@%@connector/s4/ldap/base@%@',
			
			@!@
if configRegistry.get('connector/s4/mapping/dc/syncmode'):
	print "sync_mode='%s'," % configRegistry.get('connector/s4/mapping/dc/syncmode')
else:
	print "sync_mode='%s'," % configRegistry.get('connector/s4/mapping/syncmode')
@!@

			scope='sub',

			identify=univention.s4connector.s4.dc.identify,

			con_search_filter='(|(objectClass=domain)(objectClass=sambaDomainName))',

@!@
ignore_filter = ''
for dns in configRegistry.get('connector/s4/mapping/dc/ignorelist', '').split(','):
	if dns:
		ignore_filter += '(%s)' % (dns)
if ignore_filter:
	print "			ignore_filter='(|%s)'," % ignore_filter
@!@

			ignore_subtree = global_ignore_subtree,
			
			con_sync_function = univention.s4connector.s4.dc.ucs2con,
			ucs_sync_function = univention.s4connector.s4.dc.con2ucs,

		),
}



