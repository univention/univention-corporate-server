# -*- coding: utf-8 -*-
#
# Univention S4 Connector
#  this file defines the mapping between S4 and UCS
#
# Copyright 2004-2019 Univention GmbH
#
# https://www.univention.de/
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
# <https://www.gnu.org/licenses/>.

import os
import imp
import base64

import univention.s4connector.s4
import univention.s4connector.s4.mapping
import univention.s4connector.s4.password
import univention.s4connector.s4.sid_mapping
import univention.s4connector.s4.ntsecurity_descriptor
import univention.s4connector.s4.dns
import univention.s4connector.s4.dc
import univention.s4connector.s4.computer
import univention.s4connector.s4.user

from univention.s4connector.s4.mapping import ignore_filter_from_tmpl, ignore_filter_from_attr, configRegistry

global_ignore_subtree = [
	'cn=univention,@%@ldap/base@%@',
	'cn=policies,@%@ldap/base@%@',
	'cn=shares,@%@ldap/base@%@',
	'cn=printers,@%@ldap/base@%@',
	'cn=networks,@%@ldap/base@%@',
	'cn=kerberos,@%@ldap/base@%@',
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
	'DC=RootDNSServers,CN=MicrosoftDNS,DC=DomainDnsZones,@%@connector/s4/ldap/base@%@',
	'DC=RootDNSServers,CN=MicrosoftDNS,DC=ForestDnsZones,@%@connector/s4/ldap/base@%@',
	'DC=..TrustAnchors,CN=MicrosoftDNS,DC=ForestDnsZones,@%@connector/s4/ldap/base@%@',
	'CN=File Replication Service,CN=System,@%@connector/s4/ldap/base@%@',
	'CN=RpcServices,CN=System,@%@connector/s4/ldap/base@%@',
	'CN=Meetings,CN=System,@%@connector/s4/ldap/base@%@',
	'CN=AdminSDHolder,CN=System,@%@connector/s4/ldap/base@%@',
	'CN=BCKUPKEY_c490e871-a375-4b76-bd24-711e9e49fe5e Secret,CN=System,@%@connector/s4/ldap/base@%@',
	'CN=BCKUPKEY_PREFERRED Secret,CN=System,@%@connector/s4/ldap/base@%@',
	'ou=Grp Policy Users,@%@connector/s4/ldap/base@%@',
	'cn=ForeignSecurityPrincipals,@%@connector/s4/ldap/base@%@',
	'cn=Program Data,@%@connector/s4/ldap/base@%@',
	'cn=Configuration,@%@connector/s4/ldap/base@%@',
	'cn=opsi,@%@ldap/base@%@',
	'cn=Microsoft Exchange System Objects,@%@connector/s4/ldap/base@%@'
]

for k, v in configRegistry.items():
	if k.startswith('connector/s4/mapping/ignoresubtree/'):
		global_ignore_subtree.append(v)

if configRegistry.is_false('connector/s4/mapping/wmifilter', True):
	global_ignore_subtree.append('CN=WMIPolicy,CN=System,@%@connector/s4/ldap/base@%@')

if configRegistry.is_false('connector/s4/mapping/group/grouptype', False):
	global_ignore_subtree.append('cn=Builtin,@%@connector/s4/ldap/base@%@')

user_ignore_list = set(x.strip(' ') for x in configRegistry.get('connector/s4/mapping/user/attributes/ignorelist', '').split(','))
group_ignore_filter = ignore_filter_from_attr('cn', 'connector/s4/mapping/group/ignorelist')
if configRegistry.is_false('connector/s4/mapping/group/grouptype', False):
	group_ignore_filter = '(|{}{})'.format('(sambaGroupType=5)(groupType=5)', group_ignore_filter)

key_prefix = "connector/s4/mapping/group/table/"
group_mapping_table = {
	'cn': [(unicode(key[len(key_prefix):]), unicode(value)) for key, value in configRegistry.items() if key.startswith(key_prefix)]
}
if not group_mapping_table['cn']:
	group_mapping_table = {}

sid_sync_mode = 'sync'
sid_mapping = []
if configRegistry.is_true('connector/s4/mapping/sid', True):
	if configRegistry.is_true('connector/s4/mapping/sid_to_s4', False):
		sid_mapping.append(univention.s4connector.s4.sid_mapping.sid_to_s4_mapping)
	else:
		sid_mapping.append(None)
		sid_sync_mode = 'read'
	if configRegistry.is_true('connector/s4/mapping/sid_to_ucs', True):
		sid_mapping.append(univention.s4connector.s4.sid_mapping.sid_to_ucs_mapping)
	else:
		sid_mapping.append(None)
		sid_sync_mode = 'write'


def get_sid_mapping():
	if configRegistry.is_true('connector/s4/mapping/sid', True):
		return univention.s4connector.attribute(
			sync_mode=sid_sync_mode,
			mapping=tuple(sid_mapping),
			ldap_attribute='sambaSID',
			ucs_attribute='sambaRID',
			con_attribute='objectSid',
			single_value=True,
			compare_function=univention.s4connector.s4.compare_sid_lists,
		)


def _map_s4_to_udm_base64(property_name):
	def mapping(connector, key, obj):
		return list(map(lambda x: base64.encodestring(x).rstrip('\n'), obj['attributes'][property_name]))
	return mapping


def _map_ldap_to_s4(property_name):
	def mapping(connector, key, obj):
		return obj['attributes'][property_name]
	return mapping


sync_mode_ou = configRegistry.get('connector/s4/mapping/ou/syncmode', configRegistry.get('connector/s4/mapping/syncmode'))
sync_mode_gpo = configRegistry.get('connector/s4/mapping/gpo/syncmode', sync_mode_ou)
gpo_ntsd = configRegistry.is_true('connector/s4/mapping/gpo/ntsd', False)


s4_mapping = {
	'user': univention.s4connector.property(
		ucs_default_dn='cn=users,@%@ldap/base@%@',
		con_default_dn='cn=users,@%@connector/s4/ldap/base@%@',
		ucs_module='users/user',
		# read, write, sync, none
		sync_mode=configRegistry.get('connector/s4/mapping/user/syncmode', configRegistry.get('connector/s4/mapping/syncmode')),
		scope='sub',
		con_search_filter='(&(objectClass=user)(!(objectClass=computer))(userAccountControl:1.2.840.113556.1.4.803:=512))',
		match_filter='(&(|(&(objectClass=posixAccount)(objectClass=krb5Principal))(objectClass=user))(!(objectClass=univentionHost)))',
		ignore_filter=ignore_filter_from_tmpl('(uid={0!e})(CN={0!e})', 'connector/s4/mapping/user/ignorelist') or None,
		ignore_subtree=global_ignore_subtree,
		con_create_objectclass=['top', 'user', 'person', 'organizationalPerson'],
		dn_mapping_function=[univention.s4connector.s4.user_dn_mapping],
		attributes=dict((key, value) for key, value in {
			'samAccountName': univention.s4connector.attribute(
				ucs_attribute='username',
				ldap_attribute='uid',
				con_attribute='sAMAccountName',
				required=1,
				compare_function=univention.s4connector.compare_lowercase,
				single_value=True,
			),
			'givenName': univention.s4connector.attribute(
				ucs_attribute='firstname',
				ldap_attribute='givenName',
				con_attribute='givenName',
				single_value=True,
			),
			'displayName': univention.s4connector.attribute(
				ucs_attribute='displayName',
				ldap_attribute='displayName',
				con_attribute='displayName',
				single_value=True,
			),
			'sn': univention.s4connector.attribute(
				ucs_attribute='lastname',
				ldap_attribute='sn',
				con_attribute='sn',
				single_value=True,
			),
			'sid': get_sid_mapping(),
		}.items() if key not in user_ignore_list),
		# These functions can extend the addlist while
		# creating an object in S4. Parameters are
		#	s4connector, property_type, object, addlist, serverctrls
		con_create_extenstions=[
			univention.s4connector.s4.add_primary_group_to_addlist,
		],
		ucs_create_functions=filter(None, [
			univention.s4connector.set_ucs_passwd_user,
			univention.s4connector.check_ucs_lastname_user,
			univention.s4connector.set_primary_group_user,
			univention.s4connector.s4.sid_mapping.sid_to_ucs if configRegistry.is_true('connector/s4/mapping/sid_to_ucs', True) and not configRegistry.is_true('connector/s4/mapping/sid', True) else None,
		]),
		con_create_attributes=[('userAccountControl', ['512'])],  # accounts synced to samba4 alpha17 had userAccountControl == 544
		post_con_modify_functions=filter(None, [
			univention.s4connector.s4.sid_mapping.sid_to_s4 if configRegistry.is_true('connector/s4/mapping/sid_to_s4', False) and not configRegistry.is_true('connector/s4/mapping/sid', True) else None,
			univention.s4connector.s4.password.password_sync_ucs_to_s4,
			univention.s4connector.s4.password.lockout_sync_ucs_to_s4,
			univention.s4connector.s4.primary_group_sync_from_ucs,
			univention.s4connector.s4.object_memberships_sync_from_ucs,
			univention.s4connector.s4.disable_user_from_ucs,
		]),
		post_ucs_modify_functions=filter(None, [
			univention.s4connector.s4.sid_mapping.sid_to_ucs if configRegistry.is_true('connector/s4/mapping/sid_to_ucs', True) and not configRegistry.is_true('connector/s4/mapping/sid', True) else None,
			univention.s4connector.s4.password.password_sync_s4_to_ucs,
			univention.s4connector.s4.password.lockout_sync_s4_to_ucs,
			univention.s4connector.s4.primary_group_sync_to_ucs,
			univention.s4connector.s4.object_memberships_sync_to_ucs if configRegistry.get('connector/s4/mapping/group/syncmode') != 'write' else None,
			univention.s4connector.s4.disable_user_to_ucs,
		]),
		post_attributes=dict((key, value) for key, value in {
			'organisation': univention.s4connector.attribute(
				ucs_attribute='organisation',
				ldap_attribute='o',
				con_attribute='company',
				single_value=True,
			),
			'description': univention.s4connector.attribute(
				ucs_attribute='description',
				ldap_attribute='description',
				con_attribute='description',
				single_value=True,
			),
			'mailPrimaryAddress': univention.s4connector.attribute(
				ucs_attribute='mailPrimaryAddress',
				ldap_attribute='mailPrimaryAddress',
				con_attribute='mail',
				reverse_attribute_check=True,
				single_value=True,
			),
			'street': univention.s4connector.attribute(
				ucs_attribute='street',
				ldap_attribute='street',
				con_attribute='streetAddress',
				single_value=True,
			),
			'city': univention.s4connector.attribute(
				ucs_attribute='city',
				ldap_attribute='l',
				con_attribute='l',
				single_value=True,
			),
			'postcode': univention.s4connector.attribute(
				ucs_attribute='postcode',
				ldap_attribute='postalCode',
				con_attribute='postalCode',
				single_value=True,
			),
			'sambaWorkstations': univention.s4connector.attribute(
				ucs_attribute='sambaUserWorkstations',
				ldap_attribute='sambaUserWorkstations',
				con_attribute='userWorkstations',
				single_value=True,
			),
			#'sambaLogonHours': univention.s4connector.attribute(
			#	ucs_attribute='sambaLogonHours',
			#	ldap_attribute='sambaLogonHours',
			#	con_attribute='logonHours',
			#),
			'profilepath': univention.s4connector.attribute(
				ucs_attribute='profilepath',
				ldap_attribute='sambaProfilePath',
				con_attribute='profilePath',
				single_value=True,
			),
			'scriptpath': univention.s4connector.attribute(
				ucs_attribute='scriptpath',
				ldap_attribute='sambaLogonScript',
				con_attribute='scriptPath',
				single_value=True,
			),
			'homeDrive': univention.s4connector.attribute(
				ucs_attribute='homedrive',
				ldap_attribute='sambaHomeDrive',
				con_attribute='homeDrive',
				single_value=True,
			),
			'homeDirectory': univention.s4connector.attribute(
				ucs_attribute='sambahome',
				ldap_attribute='sambaHomePath',
				con_attribute='homeDirectory',
				reverse_attribute_check=True,
				single_value=True,
			),
			'telephoneNumber': univention.s4connector.attribute(
				ucs_attribute='phone',
				ldap_attribute='telephoneNumber',
				con_attribute='telephoneNumber',
				con_other_attribute='otherTelephone',
			),
			'homePhone': univention.s4connector.attribute(
				ucs_attribute='homeTelephoneNumber',
				ldap_attribute='homePhone',
				con_attribute='homePhone',
				con_other_attribute='otherHomePhone',
			),
			'mobilePhone': univention.s4connector.attribute(
				ucs_attribute='mobileTelephoneNumber',
				ldap_attribute='mobile',
				con_attribute='mobile',
				con_other_attribute='otherMobile',
			),
			'pager': univention.s4connector.attribute(
				ucs_attribute='pagerTelephoneNumber',
				ldap_attribute='pager',
				con_attribute='pager',
				con_other_attribute='otherPager',
			),
			'employeeType': univention.s4connector.attribute(
				ucs_attribute='employeeType',
				ldap_attribute='employeeType',
				con_attribute='employeeType',
				single_value=True,
			),
			'employeeNumber': univention.s4connector.attribute(
				ucs_attribute='employeeNumber',
				ldap_attribute='employeeNumber',
				con_attribute='employeeNumber',
				single_value=True,
			),
			#'state': univention.s4connector.attribute(
			#	ucs_attribute='state',
			#	ldap_attribute='st',
			#	con_attribute='st',
			#	single_value=True,
			#),
			#'country': univention.s4connector.attribute(
			#	ucs_attribute='country',
			#	ldap_attribute='c',
			#	con_attribute='c',
			#	single_value=True,
			#),
			'loginShell': univention.s4connector.attribute(
				ucs_attribute='shell',
				ldap_attribute='loginShell',
				con_attribute='loginShell',
				single_value=True,
			),
			'unixhome': univention.s4connector.attribute(
				ucs_attribute='unixhome',
				ldap_attribute='homeDirectory',
				con_attribute='unixHomeDirectory',
				single_value=True,
			),
			'title': univention.s4connector.attribute(
				ucs_attribute='title',
				ldap_attribute='title',
				con_attribute='personalTitle',
				single_value=True,
			),
			'gidNumber': univention.s4connector.attribute(
				ucs_attribute='gidNumber',
				ldap_attribute='gidNumber',
				con_attribute='gidNumber',
				single_value=True,
			),
			'uidNumber': univention.s4connector.attribute(
				ucs_attribute='uidNumber',
				ldap_attribute='uidNumber',
				con_attribute='uidNumber',
				single_value=True,
			),
			'departmentNumber': univention.s4connector.attribute(
				ucs_attribute='departmentNumber',
				ldap_attribute='departmentNumber',
				con_attribute='departmentNumber',
			),
			'roomNumber': univention.s4connector.attribute(
				ucs_attribute='roomNumber',
				ldap_attribute='roomNumber',
				con_attribute='roomNumber',
			),
			'userCertificate': univention.s4connector.attribute(
				mapping=(univention.s4connector.s4.user.userCertificate_sync_ucs_to_s4, univention.s4connector.s4.user.userCertificate_sync_s4_to_ucs),
				ucs_attribute='userCertificate',
				ldap_attribute='userCertificate;binary',
				con_attribute='userCertificate',
				udm_option='pki',
				single_value=True,
			),
			# Do not sync secretary, because we currently have no way to verify the existence of the DN which would cause rejects
			#'secretary': univention.s4connector.attribute(
			#	mapping=(univention.s4connector.s4.user.secretary_sync_ucs_to_s4, univention.s4connector.s4.user.secretary_sync_s4_to_ucs),
			#	ucs_attribute='secretary',
			#	ldap_attribute='secretary',
			#	con_attribute='secretary',
			#),
			'jpegPhoto': univention.s4connector.attribute(
				mapping=(univention.s4connector.s4.user.jpegPhoto_sync_ucs_to_s4, univention.s4connector.s4.user.jpegPhoto_sync_s4_to_ucs),
				ucs_attribute='jpegPhoto',
				ldap_attribute='jpegPhoto',
				con_attribute='jpegPhoto',
				single_value=True,
			),
			'preferredDeliveryMethod': univention.s4connector.attribute(
				mapping=(univention.s4connector.s4.user.prefdev_sync_ucs_to_s4, univention.s4connector.s4.user.prefdev_sync_s4_to_ucs),
				ucs_attribute='preferredDeliveryMethod',
				ldap_attribute='preferredDeliveryMethod',
				con_attribute='preferredDeliveryMethod',
				single_value=True,
			),
			'initials': univention.s4connector.attribute(
				ucs_attribute='initials',
				ldap_attribute='initials',
				con_attribute='initials',
				single_value=True,
			),
			'physicalDeliveryOfficeName': univention.s4connector.attribute(
				ucs_attribute='physicalDeliveryOfficeName',
				ldap_attribute='physicalDeliveryOfficeName',
				con_attribute='physicalDeliveryOfficeName',
				single_value=True,
			),
			'postOfficeBox': univention.s4connector.attribute(
				ucs_attribute='postOfficeBox',
				ldap_attribute='postOfficeBox',
				con_attribute='postOfficeBox',
			),
			'preferredLanguage': univention.s4connector.attribute(
				ucs_attribute='preferredLanguage',
				ldap_attribute='preferredLanguage',
				con_attribute='preferredLanguage',
				single_value=True,
			),
		}.items() if key not in user_ignore_list),
	),
	'group': univention.s4connector.property(
		ucs_default_dn='cn=groups,@%@ldap/base@%@',
		con_default_dn='cn=Users,@%@connector/s4/ldap/base@%@',
		ucs_module='groups/group',
		sync_mode=configRegistry.get('connector/s4/mapping/group/syncmode', configRegistry.get('connector/s4/mapping/syncmode')),
		scope='sub',
		ignore_filter=group_ignore_filter or None,
		ignore_subtree=global_ignore_subtree,
		con_search_filter='objectClass=group',
		con_create_objectclass=['top', 'group'],
		# These functions can extend the addlist while
		# creating an object in S4. Parameters are
		#	s4connector, property_type, object, addlist, serverctrls
		con_create_extenstions=[
			univention.s4connector.s4.check_for_local_group_and_extend_serverctrls_and_sid,
		],
		post_con_modify_functions=filter(None, [
			univention.s4connector.s4.sid_mapping.sid_to_s4 if configRegistry.is_true('connector/s4/mapping/sid_to_s4', False) and not configRegistry.is_true('connector/s4/mapping/sid', True) else None,
			univention.s4connector.s4.group_members_sync_from_ucs,
			univention.s4connector.s4.object_memberships_sync_from_ucs
		]),
		post_ucs_modify_functions=filter(None, [
			univention.s4connector.s4.sid_mapping.sid_to_ucs if configRegistry.is_true('connector/s4/mapping/sid_to_ucs', True) and not configRegistry.is_true('connector/s4/mapping/sid', True) else None,
			univention.s4connector.s4.group_members_sync_to_ucs,
			univention.s4connector.s4.object_memberships_sync_to_ucs
		]),
		dn_mapping_function=[univention.s4connector.s4.group_dn_mapping],
		attributes={
			'cn': univention.s4connector.attribute(
				ucs_attribute='name',
				ldap_attribute='cn',
				con_attribute='sAMAccountName',
				required=1,
				compare_function=univention.s4connector.compare_lowercase,
				single_value=True,
			),
			'description': univention.s4connector.attribute(
				ucs_attribute='description',
				ldap_attribute='description',
				con_attribute='description',
				single_value=True,
			),
			'groupType': univention.s4connector.attribute(
				ucs_attribute='adGroupType',
				ldap_attribute='univentionGroupType',
				con_attribute='groupType',
				single_value=True,
			),
			'mailAddress': univention.s4connector.attribute(
				ucs_attribute='mailAddress',
				ldap_attribute='mailPrimaryAddress',
				con_attribute='mail',
				reverse_attribute_check=True,
				single_value=True,
			),
			'sid': get_sid_mapping(),
		},
		mapping_table=group_mapping_table,
	),
	'dc': univention.s4connector.property(
		ucs_default_dn='cn=dc,cn=computers,@%@ldap/base@%@',
		con_default_dn='OU=Domain Controllers,@%@connector/s4/ldap/base@%@',
		ucs_module='computers/windows_domaincontroller',
		ucs_module_others=['computers/domaincontroller_master', 'computers/domaincontroller_backup', 'computers/domaincontroller_slave'],
		con_search_filter='(&(objectClass=computer)(userAccountControl:1.2.840.113556.1.4.803:=532480))',
		position_mapping=[(',cn=dc,cn=computers,@%@ldap/base@%@', ',ou=Domain Controllers,@%@connector/s4/ldap/base@%@')],
		match_filter='(|(&(objectClass=univentionDomainController)(univentionService=Samba 4))(objectClass=computer)(univentionServerRole=windows_domaincontroller))',
		dn_mapping_function=[univention.s4connector.s4.dc_dn_mapping],
		# When a DC joins to the samba 4 domain
		# the DC will be deleted.
		disable_delete_in_ucs=True,
		# When a DC is removed in UCS, the DC should be removed
		# in S4. By default a DC has a subobject wihtout any mapping
		# and this subobject would avoid a deletion of this DC in S4
		con_subtree_delete_objects=['objectClass=rIDSet', 'objectClass=connectionPoint', 'objectclass=nTFRSMember'],
		ignore_filter=ignore_filter_from_attr('cn', 'connector/s4/mapping/dc/ignorelist') or None,
		sync_mode=configRegistry.get('connector/s4/mapping/computer_dc/syncmode', configRegistry.get('connector/s4/mapping/syncmode')),
		con_create_objectclass=['top', 'computer'],
		con_create_attributes=[
			('userAccountControl', ['532480']),
		],
		post_con_modify_functions=filter(None, [
			univention.s4connector.s4.sid_mapping.sid_to_s4 if configRegistry.is_true('connector/s4/mapping/sid_to_s4', False) and not configRegistry.is_true('connector/s4/mapping/sid', True) else None,
			univention.s4connector.s4.password.password_sync_ucs_to_s4,
		]),
		post_ucs_modify_functions=filter(None, [
			univention.s4connector.s4.sid_mapping.sid_to_ucs if configRegistry.is_true('connector/s4/mapping/sid_to_ucs', True) and not configRegistry.is_true('connector/s4/mapping/sid', True) else None,
			univention.s4connector.s4.password.password_sync_s4_to_ucs_no_userpassword,
			univention.s4connector.s4.computer.checkAndConvertToMacOSX,
		]),
		attributes={
			'cn': univention.s4connector.attribute(
				ucs_attribute='name',
				ldap_attribute='cn',
				con_attribute='cn',
				required=1,
				compare_function=univention.s4connector.compare_lowercase,
				single_value=True,
			),
			'samAccountName': univention.s4connector.attribute(
				ldap_attribute='uid',
				con_attribute='sAMAccountName',
				compare_function=univention.s4connector.compare_lowercase,
				single_value=True,
			),
			'description': univention.s4connector.attribute(
				ucs_attribute='description',
				ldap_attribute='description',
				con_attribute='description',
				single_value=True,
			),
			'operatingSystem': univention.s4connector.attribute(
				ucs_attribute='operatingSystem',
				ldap_attribute='univentionOperatingSystem',
				con_attribute='operatingSystem',
				single_value=True,
			),
			'operatingSystemVersion': univention.s4connector.attribute(
				ucs_attribute='operatingSystemVersion',
				ldap_attribute='univentionOperatingSystemVersion',
				con_attribute='operatingSystemVersion',
				single_value=True,
			),
			'sid': get_sid_mapping(),
		},
	),
	'windowscomputer': univention.s4connector.property(
		ucs_default_dn='cn=computers,@%@ldap/base@%@',
		con_default_dn='cn=computers,@%@connector/s4/ldap/base@%@',
		ucs_module='computers/windows',
		ucs_module_others=['computers/memberserver', 'computers/ucc', 'computers/linux', 'computers/ubuntu', 'computers/macos'],
		sync_mode=configRegistry.get('connector/s4/mapping/computer/syncmode', configRegistry.get('connector/s4/mapping/syncmode')),
		scope='sub',
		dn_mapping_function=[univention.s4connector.s4.windowscomputer_dn_mapping],
		con_search_filter='(&(objectClass=computer)(userAccountControl:1.2.840.113556.1.4.803:=4096))',
		# ignore_filter='userAccountControl=4096',
		match_filter='(|(&(objectClass=univentionWindows)(!(univentionServerRole=windows_domaincontroller)))(objectClass=computer)(objectClass=univentionMemberServer)(objectClass=univentionUbuntuClient)(objectClass=univentionLinuxClient)(objectClass=univentionMacOSClient)(objectClass=univentionCorporateClient))',
		ignore_subtree=global_ignore_subtree,
		con_subtree_delete_objects=['objectClass=rIDSet', 'objectClass=connectionPoint', 'objectclass=nTFRSMember'],
		ignore_filter=ignore_filter_from_attr('cn', 'connector/s4/mapping/windowscomputer/ignorelist'),
		con_create_objectclass=['top', 'computer'],
		con_create_attributes=[('userAccountControl', ['4096'])],
		#post_con_create_functions=[univention.connector.s4.computers.
		post_con_modify_functions=filter(None, [
			univention.s4connector.s4.sid_mapping.sid_to_s4 if configRegistry.is_true('connector/s4/mapping/sid_to_s4', False) and not configRegistry.is_true('connector/s4/mapping/sid', True) else None,
			univention.s4connector.s4.password.password_sync_ucs_to_s4,
		]),
		post_ucs_modify_functions=filter(None, [
			univention.s4connector.s4.sid_mapping.sid_to_ucs if configRegistry.is_true('connector/s4/mapping/sid_to_ucs', True) and not configRegistry.is_true('connector/s4/mapping/sid', True) else None,
			univention.s4connector.s4.password.password_sync_s4_to_ucs_no_userpassword,
			univention.s4connector.s4.computer.checkAndConvertToMacOSX,
			univention.s4connector.s4.computer.windowscomputer_sync_s4_to_ucs_check_rename,
		]),
		attributes={
			'cn': univention.s4connector.attribute(
				ucs_attribute='name',
				ldap_attribute='cn',
				con_attribute='cn',
				required=1,
				compare_function=univention.s4connector.compare_lowercase,
				single_value=True,
			),
			'samAccountName': univention.s4connector.attribute(
				ldap_attribute='uid',
				con_attribute='sAMAccountName',
				compare_function=univention.s4connector.compare_lowercase,
				single_value=True,
			),
			'description': univention.s4connector.attribute(
				ucs_attribute='description',
				ldap_attribute='description',
				con_attribute='description',
				single_value=True,
			),
			'operatingSystem': univention.s4connector.attribute(
				ucs_attribute='operatingSystem',
				ldap_attribute='univentionOperatingSystem',
				con_attribute='operatingSystem',
				single_value=True,
			),
			'operatingSystemVersion': univention.s4connector.attribute(
				ucs_attribute='operatingSystemVersion',
				ldap_attribute='univentionOperatingSystemVersion',
				con_attribute='operatingSystemVersion',
				single_value=True,
			),
			'sid': get_sid_mapping(),
		},
	),
	'dns': univention.s4connector.property(
		ucs_default_dn='cn=dns,%(ldap/base)s' % configRegistry,
		con_default_dn='CN=MicrosoftDNS,%s,%s' % ("CN=System" if configRegistry.get('connector/s4/mapping/dns/position') == 'legacy' else "DC=DomainDnsZones", configRegistry['connector/s4/ldap/base']),
		ucs_module='dns/dns',
		ucs_module_others=['dns/forward_zone', 'dns/reverse_zone', 'dns/alias', 'dns/host_record', 'dns/srv_record', 'dns/ptr_record', 'dns/txt_record', 'dns/ns_record'],
		sync_mode=configRegistry.get('connector/s4/mapping/dns/syncmode') or configRegistry.get('connector/s4/mapping/syncmode', ''),
		scope='sub',
		con_search_filter='(|(objectClass=dnsNode)(objectClass=dnsZone))',
		dn_mapping_function=[univention.s4connector.s4.dns.dns_dn_mapping],
		ignore_filter=ignore_filter_from_attr('dc', 'connector/s4/mapping/dns/ignorelist'),
		ignore_subtree=global_ignore_subtree,
		con_sync_function=univention.s4connector.s4.dns.ucs2con,
		ucs_sync_function=univention.s4connector.s4.dns.con2ucs,
	),
	'msGPO': univention.s4connector.property(
		ucs_module='container/msgpo',
		sync_mode=str(sync_mode_gpo),
		scope='sub',
		con_search_filter='(&(objectClass=container)(objectClass=groupPolicyContainer))',
		ignore_filter=ignore_filter_from_attr('cn', 'connector/s4/mapping/gpo/ignorelist'),
		ignore_subtree=global_ignore_subtree,
		con_create_objectclass=['top', 'container', 'groupPolicyContainer'],
		attributes={
			'cn': univention.s4connector.attribute(
				ucs_attribute='name',
				ldap_attribute='cn',
				con_attribute='cn',
				required=1,
				compare_function=univention.s4connector.compare_lowercase,
				single_value=True,
			),
			'description': univention.s4connector.attribute(
				ucs_attribute='description',
				ldap_attribute='description',
				con_attribute='description',
				single_value=True,
			),
			'displayName': univention.s4connector.attribute(
				ucs_attribute='displayName',
				ldap_attribute='displayName',
				con_attribute='displayName',
				single_value=True,
			),
			'msGPOFlags': univention.s4connector.attribute(
				ucs_attribute='msGPOFlags',
				ldap_attribute='msGPOFlags',
				con_attribute='flags',
				single_value=True,
			),
			'msGPOVersionNumber': univention.s4connector.attribute(
				ucs_attribute='msGPOVersionNumber',
				ldap_attribute='msGPOVersionNumber',
				con_attribute='versionNumber',
				single_value=True,
			),
			'msGPOSystemFlags': univention.s4connector.attribute(
				ucs_attribute='msGPOSystemFlags',
				ldap_attribute='msGPOSystemFlags',
				con_attribute='systemFlags',
				single_value=True,
			),
			'msGPOFunctionalityVersion': univention.s4connector.attribute(
				ucs_attribute='msGPOFunctionalityVersion',
				ldap_attribute='msGPOFunctionalityVersion',
				con_attribute='gPCFunctionalityVersion',
				single_value=True,
			),
			'msGPOFileSysPath': univention.s4connector.attribute(
				ucs_attribute='msGPOFileSysPath',
				ldap_attribute='msGPOFileSysPath',
				con_attribute='gPCFileSysPath',
				single_value=True,
			),
			'msGPOMachineExtensionNames': univention.s4connector.attribute(
				ucs_attribute='msGPOMachineExtensionNames',
				ldap_attribute='msGPOMachineExtensionNames',
				con_attribute='gPCMachineExtensionNames',
				single_value=True,
			),
			'msGPOUserExtensionNames': univention.s4connector.attribute(
				ucs_attribute='msGPOUserExtensionNames',
				ldap_attribute='msGPOUserExtensionNames',
				con_attribute='gPCUserExtensionNames',
				single_value=True,
			),
			'msGPOWQLFilter': univention.s4connector.attribute(
				ucs_attribute='msGPOWQLFilter',
				ldap_attribute='msGPOWQLFilter',
				con_attribute='gPCWQLFilter',
				single_value=True,
			),
		},
		ucs_create_functions=[univention.s4connector.s4.ntsecurity_descriptor.ntsd_to_ucs] if gpo_ntsd else [],
		post_ucs_modify_functions=[univention.s4connector.s4.ntsecurity_descriptor.ntsd_to_ucs] if gpo_ntsd else [],
		post_con_create_functions=[univention.s4connector.s4.ntsecurity_descriptor.ntsd_to_s4] if gpo_ntsd else [],
		post_con_modify_functions=[univention.s4connector.s4.ntsecurity_descriptor.ntsd_to_s4] if gpo_ntsd else [],
	),
	'msWMIFilter': univention.s4connector.property(
		ucs_module='settings/mswmifilter',
		sync_mode=str(configRegistry.get('connector/s4/mapping/wmifilter/syncmode', sync_mode_ou)),
		scope='sub',
		con_search_filter='(objectClass=msWMI-Som)',
		ignore_filter=ignore_filter_from_attr('cn', 'connector/s4/mapping/wmifilter/ignorelist'),
		ignore_subtree=global_ignore_subtree,
		con_create_objectclass=['top', 'msWMI-Som'],
		attributes={
			'cn': univention.s4connector.attribute(
				ucs_attribute='id',
				ldap_attribute='msWMIID',
				con_attribute='msWMI-ID',
				required=1,
				single_value=True,
			),
			'name': univention.s4connector.attribute(
				ucs_attribute='name',
				ldap_attribute='msWMIName',
				con_attribute='msWMI-Name',
				required=1,
				single_value=True,
			),
			'description': univention.s4connector.attribute(
				ucs_attribute='description',
				ldap_attribute='description',
				con_attribute='description',
				single_value=True,
			),
			'displayName': univention.s4connector.attribute(
				ucs_attribute='displayName',
				ldap_attribute='displayName',
				con_attribute='displayName',
				single_value=True,
			),
			'author': univention.s4connector.attribute(
				ucs_attribute='author',
				ldap_attribute='msWMIAuthor',
				con_attribute='msWMI-Author',
				single_value=True,
			),
			'creationDate': univention.s4connector.attribute(
				ucs_attribute='creationDate',
				ldap_attribute='msWMICreationDate',
				con_attribute='msWMI-CreationDate',
				single_value=True,
			),
			'changeDate': univention.s4connector.attribute(
				ucs_attribute='changeDate',
				ldap_attribute='msWMIChangeDate',
				con_attribute='msWMI-ChangeDate',
				single_value=True,
			),
			'parm1': univention.s4connector.attribute(
				ucs_attribute='parm1',
				ldap_attribute='msWMIParm1',
				con_attribute='msWMI-Parm1',
				single_value=True,
			),
			'parm2': univention.s4connector.attribute(
				ucs_attribute='parm2',
				ldap_attribute='msWMIParm2',
				con_attribute='msWMI-Parm2',
				single_value=True,
			),
			'parm3': univention.s4connector.attribute(
				ucs_attribute='parm3',
				ldap_attribute='msWMIParm3',
				con_attribute='msWMI-Parm3',
				single_value=True,
			),
			'parm4': univention.s4connector.attribute(
				ucs_attribute='parm4',
				ldap_attribute='msWMIParm4',
				con_attribute='msWMI-Parm4',
				single_value=True,
			),
			'flags1': univention.s4connector.attribute(
				ucs_attribute='flags1',
				ldap_attribute='msWMIFlags1',
				con_attribute='msWMI-Flags1',
				single_value=True,
			),
			'flags2': univention.s4connector.attribute(
				ucs_attribute='flags2',
				ldap_attribute='msWMIFlags2',
				con_attribute='msWMI-Flags2',
				single_value=True,
			),
			'flags3': univention.s4connector.attribute(
				ucs_attribute='flags3',
				ldap_attribute='msWMIFlags3',
				con_attribute='msWMI-Flags3',
				single_value=True,
			),
			'flags4': univention.s4connector.attribute(
				ucs_attribute='flags4',
				ldap_attribute='msWMIFlags4',
				con_attribute='msWMI-Flags4',
				single_value=True,
			),
			'sourceOrganization': univention.s4connector.attribute(
				ucs_attribute='sourceOrganization',
				ldap_attribute='msWMISourceOrganization',
				con_attribute='msWMI-SourceOrganization',
				single_value=True,
			),
		},
	),
	'msPrintConnectionPolicy': univention.s4connector.property(
		ucs_module='settings/msprintconnectionpolicy',
		sync_mode=str(configRegistry.get('connector/s4/mapping/msprintconnectionpolicy/syncmode', sync_mode_gpo)),
		scope='sub',
		con_search_filter='(objectClass=msPrint-ConnectionPolicy)',
		ignore_filter=ignore_filter_from_attr('cn', 'connector/s4/mapping/msprintconnectionpolicy/ignorelist'),
		ignore_subtree=global_ignore_subtree,
		con_create_objectclass=['top', 'msPrint-ConnectionPolicy'],
		attributes={
			'cn': univention.s4connector.attribute(
				ucs_attribute='name',
				ldap_attribute='cn',
				con_attribute='cn',
				required=1,
				compare_function=univention.s4connector.compare_lowercase,
				single_value=True,
			),
			'description': univention.s4connector.attribute(
				ucs_attribute='description',
				ldap_attribute='description',
				con_attribute='description',
				single_value=True,
			),
			'displayName': univention.s4connector.attribute(
				ucs_attribute='displayName',
				ldap_attribute='displayName',
				con_attribute='displayName',
				single_value=True,
			),
			'msPrintAttributes': univention.s4connector.attribute(
				ucs_attribute='msPrintAttributes',
				ldap_attribute='msPrintAttributes',
				con_attribute='printAttributes',
				single_value=True,
			),
			'msPrinterName': univention.s4connector.attribute(
				ucs_attribute='msPrinterName',
				ldap_attribute='msPrinterName',
				con_attribute='printerName',
				single_value=True,
			),
			'msPrintServerName': univention.s4connector.attribute(
				ucs_attribute='msPrintServerName',
				ldap_attribute='msPrintServerName',
				con_attribute='serverName',
				single_value=True,
			),
			'msPrintUNCName': univention.s4connector.attribute(
				ucs_attribute='msPrintUNCName',
				ldap_attribute='msPrintUNCName',
				con_attribute='uNCName',
				single_value=True,
			),
		},
	),
	'ms/gpwl-wireless': univention.s4connector.property(
		ucs_module='ms/gpwl-wireless',
		sync_mode=str(configRegistry.get('connector/s4/mapping/gpwl/syncmode', configRegistry.get('connector/s4/mapping/syncmode'))),
		scope='sub',
		con_search_filter='(objectClass=ms-net-ieee-80211-GroupPolicy)',
		ignore_filter=ignore_filter_from_attr('cn', 'connector/s4/mapping/gpwl/ignorelist'),
		ignore_subtree=global_ignore_subtree,
		con_create_objectclass=['top', 'ms-net-ieee-80211-GroupPolicy'],
		attributes={
			'cn': univention.s4connector.attribute(
				ucs_attribute='name',
				ldap_attribute='cn',
				con_attribute='cn',
				required=1,
				compare_function=univention.s4connector.compare_lowercase,
				single_value=True,
			),
			'description': univention.s4connector.attribute(
				ucs_attribute='description',
				ldap_attribute='description',
				con_attribute='description',
				single_value=True,
			),
			'ms-net-ieee-80211-GP-PolicyReserved': univention.s4connector.attribute(
				ucs_attribute='ms-net-ieee-80211-GP-PolicyReserved',
				ldap_attribute='ms-net-ieee-80211-GP-PolicyReserved',
				con_attribute='ms-net-ieee-80211-GP-PolicyReserved',
				mapping=(_map_ldap_to_s4('ms-net-ieee-80211-GP-PolicyReserved'), _map_s4_to_udm_base64('ms-net-ieee-80211-GP-PolicyReserved')),
				single_value=True,
			),
			'ms-net-ieee-80211-GP-PolicyData': univention.s4connector.attribute(
				ucs_attribute='ms-net-ieee-80211-GP-PolicyData',
				ldap_attribute='ms-net-ieee-80211-GP-PolicyData',
				con_attribute='ms-net-ieee-80211-GP-PolicyData',
				single_value=True,
			),
			'ms-net-ieee-80211-GP-PolicyGUID': univention.s4connector.attribute(
				ucs_attribute='ms-net-ieee-80211-GP-PolicyGUID',
				ldap_attribute='ms-net-ieee-80211-GP-PolicyGUID',
				con_attribute='ms-net-ieee-80211-GP-PolicyGUID',
				single_value=True,
			),
		},
	),
	'ms/gpwl-wired': univention.s4connector.property(
		ucs_module='ms/gpwl-wired',
		sync_mode=str(configRegistry.get('connector/s4/mapping/gpwl/syncmode', configRegistry.get('connector/s4/mapping/syncmode'))),
		scope='sub',
		con_search_filter='(objectClass=ms-net-ieee-8023-GroupPolicy)',
		ignore_filter=ignore_filter_from_attr('cn', 'connector/s4/mapping/gpwl/ignorelist'),
		ignore_subtree=global_ignore_subtree,
		con_create_objectclass=['top', 'ms-net-ieee-8023-GroupPolicy'],
		attributes={
			'cn': univention.s4connector.attribute(
				ucs_attribute='name',
				ldap_attribute='cn',
				con_attribute='cn',
				required=1,
				compare_function=univention.s4connector.compare_lowercase,
				single_value=True,
			),
			'description': univention.s4connector.attribute(
				ucs_attribute='description',
				ldap_attribute='description',
				con_attribute='description',
				single_value=True,
			),
			'ms-net-ieee-8023-GP-PolicyReserved': univention.s4connector.attribute(
				ucs_attribute='ms-net-ieee-8023-GP-PolicyReserved',
				ldap_attribute='ms-net-ieee-8023-GP-PolicyReserved',
				con_attribute='ms-net-ieee-8023-GP-PolicyReserved',
				mapping=(_map_ldap_to_s4('ms-net-ieee-8023-GP-PolicyReserved'), _map_s4_to_udm_base64('ms-net-ieee-8023-GP-PolicyReserved')),
				single_value=True,
			),
			'ms-net-ieee-8023-GP-PolicyData': univention.s4connector.attribute(
				ucs_attribute='ms-net-ieee-8023-GP-PolicyData',
				ldap_attribute='ms-net-ieee-8023-GP-PolicyData',
				con_attribute='ms-net-ieee-8023-GP-PolicyData',
				single_value=True,
			),
			'ms-net-ieee-8023-GP-PolicyGUID': univention.s4connector.attribute(
				ucs_attribute='ms-net-ieee-8023-GP-PolicyGUID',
				ldap_attribute='ms-net-ieee-8023-GP-PolicyGUID',
				con_attribute='ms-net-ieee-8023-GP-PolicyGUID',
				single_value=True,
			),
		},
	),
	'ms/gpwl-wireless-blob': univention.s4connector.property(
		ucs_module='ms/gpwl-wireless-blob',
		sync_mode=str(configRegistry.get('connector/s4/mapping/gpwl/syncmode', configRegistry.get('connector/s4/mapping/syncmode'))),
		scope='sub',
		con_search_filter='(objectClass=msieee80211-Policy)',
		ignore_filter=ignore_filter_from_attr('cn', 'connector/s4/mapping/gpwl/ignorelist'),
		ignore_subtree=global_ignore_subtree,
		con_create_objectclass=['top', 'msieee80211-Policy'],
		attributes={
			'cn': univention.s4connector.attribute(
				ucs_attribute='name',
				ldap_attribute='cn',
				con_attribute='cn',
				required=1,
				compare_function=univention.s4connector.compare_lowercase,
				single_value=True,
			),
			'description': univention.s4connector.attribute(
				ucs_attribute='description',
				ldap_attribute='description',
				con_attribute='description',
				single_value=True,
			),
			'msieee80211-ID': univention.s4connector.attribute(
				ucs_attribute='msieee80211-ID',
				ldap_attribute='msieee80211-ID',
				con_attribute='msieee80211-ID',
				single_value=True,
			),
			'msieee80211-DataType': univention.s4connector.attribute(
				ucs_attribute='msieee80211-DataType',
				ldap_attribute='msieee80211-DataType',
				con_attribute='msieee80211-DataType',
				single_value=True,
			),
			'msieee80211-Data': univention.s4connector.attribute(
				ucs_attribute='msieee80211-Data',
				ldap_attribute='msieee80211-Data',
				con_attribute='msieee80211-Data',
				mapping=(_map_ldap_to_s4('msieee80211-Data'), _map_s4_to_udm_base64('msieee80211-Data')),
				single_value=True,
			),
		},
	),
	'container': univention.s4connector.property(
		ucs_module='container/cn',
		sync_mode=configRegistry.get('connector/s4/mapping/container/syncmode', configRegistry.get('connector/s4/mapping/syncmode')),
		scope='sub',
		con_search_filter='(&(|(objectClass=container)(objectClass=builtinDomain))(!(objectClass=groupPolicyContainer)))',  # builtinDomain is cn=builtin (with group cn=Administrators)
		ignore_filter=ignore_filter_from_attr('cn', 'connector/s4/mapping/container/ignorelist', 'mail,kerberos,MicrosoftDNS'),
		ignore_subtree=global_ignore_subtree,
		con_create_objectclass=['top', 'container'],
		attributes={
			'cn': univention.s4connector.attribute(
				ucs_attribute='name',
				ldap_attribute='cn',
				con_attribute='cn',
				required=1,
				compare_function=univention.s4connector.compare_lowercase,
				single_value=True,
			),
			'description': univention.s4connector.attribute(
				ucs_attribute='description',
				ldap_attribute='description',
				con_attribute='description',
				single_value=True,
			),
			'gPLink': univention.s4connector.attribute(
				ucs_attribute='gPLink',
				ldap_attribute='msGPOLink',
				con_attribute='gPLink',
				single_value=True,
			),
		},
	),
	'ms/gpipsec-filter': univention.s4connector.property(
		ucs_module='ms/gpipsec-filter',
		sync_mode=str(configRegistry.get('connector/s4/mapping/gpipsec/syncmode', configRegistry.get('connector/s4/mapping/syncmode'))),
		scope='sub',
		con_search_filter='(objectClass=ipsecFilter)',
		ignore_filter=ignore_filter_from_attr('cn', 'connector/s4/mapping/gpipsec/ignorelist'),
		ignore_subtree=global_ignore_subtree,
		con_create_objectclass=['top', 'ipsecFilter'],
		attributes={
			'cn': univention.s4connector.attribute(
				ucs_attribute='name',
				ldap_attribute='cn',
				con_attribute='cn',
				required=True,
				compare_function=univention.s4connector.compare_lowercase,
				single_value=True,
			),
			'description': univention.s4connector.attribute(
				ucs_attribute='description',
				ldap_attribute='description',
				con_attribute='description',
				single_value=True,
			),
			'ipsecOwnersReference': univention.s4connector.attribute(
				ucs_attribute='ipsecOwnersReference',
				ldap_attribute='ipsecOwnersReference',
				con_attribute='ipsecOwnersReference',
				compare_function=univention.s4connector.compare_lowercase,
				single_value=False,
			),
			'ipsecName': univention.s4connector.attribute(
				ucs_attribute='ipsecName',
				ldap_attribute='ipsecName',
				con_attribute='ipsecName',
				single_value=True,
			),
			'ipsecID': univention.s4connector.attribute(
				ucs_attribute='ipsecID',
				ldap_attribute='ipsecID',
				con_attribute='ipsecID',
				single_value=True,
			),
			'ipsecDataType': univention.s4connector.attribute(
				ucs_attribute='ipsecDataType',
				ldap_attribute='ipsecDataType',
				con_attribute='ipsecDataType',
				single_value=True,
			),
			'ipsecData': univention.s4connector.attribute(
				ucs_attribute='ipsecData',
				ldap_attribute='ipsecData',
				con_attribute='ipsecData',
				mapping=(_map_ldap_to_s4('ipsecData'), _map_s4_to_udm_base64('ipsecData')),
				single_value=True,
			),
		},
	),
	'ms/gpipsec-isakmp-policy': univention.s4connector.property(
		ucs_module='ms/gpipsec-isakmp-policy',
		sync_mode=str(configRegistry.get('connector/s4/mapping/gpipsec/syncmode', configRegistry.get('connector/s4/mapping/syncmode'))),
		scope='sub',
		con_search_filter='(objectClass=ipsecISAKMPPolicy)',
		ignore_filter=ignore_filter_from_attr('cn', 'connector/s4/mapping/gpipsec/ignorelist'),
		ignore_subtree=global_ignore_subtree,
		con_create_objectclass=['top', 'ipsecISAKMPPolicy'],
		attributes={
			'cn': univention.s4connector.attribute(
				ucs_attribute='name',
				ldap_attribute='cn',
				con_attribute='cn',
				required=True,
				compare_function=univention.s4connector.compare_lowercase,
				single_value=True,
			),
			'description': univention.s4connector.attribute(
				ucs_attribute='description',
				ldap_attribute='description',
				con_attribute='description',
				single_value=True,
			),
			'ipsecOwnersReference': univention.s4connector.attribute(
				ucs_attribute='ipsecOwnersReference',
				ldap_attribute='ipsecOwnersReference',
				con_attribute='ipsecOwnersReference',
				compare_function=univention.s4connector.compare_lowercase,
				single_value=False,
			),
			'ipsecName': univention.s4connector.attribute(
				ucs_attribute='ipsecName',
				ldap_attribute='ipsecName',
				con_attribute='ipsecName',
				single_value=True,
			),
			'ipsecID': univention.s4connector.attribute(
				ucs_attribute='ipsecID',
				ldap_attribute='ipsecID',
				con_attribute='ipsecID',
				single_value=True,
			),
			'ipsecDataType': univention.s4connector.attribute(
				ucs_attribute='ipsecDataType',
				ldap_attribute='ipsecDataType',
				con_attribute='ipsecDataType',
				single_value=True,
			),
			'ipsecData': univention.s4connector.attribute(
				ucs_attribute='ipsecData',
				ldap_attribute='ipsecData',
				con_attribute='ipsecData',
				mapping=(_map_ldap_to_s4('ipsecData'), _map_s4_to_udm_base64('ipsecData')),
				single_value=True,
			),
		},
	),
	'ms/gpipsec-negotiation-policy': univention.s4connector.property(
		ucs_module='ms/gpipsec-negotiation-policy',
		sync_mode=str(configRegistry.get('connector/s4/mapping/gpipsec/syncmode', configRegistry.get('connector/s4/mapping/syncmode'))),
		scope='sub',
		con_search_filter='(objectClass=ipsecNegotiationPolicy)',
		ignore_filter=ignore_filter_from_attr('cn', 'connector/s4/mapping/gpipsec/ignorelist'),
		ignore_subtree=global_ignore_subtree,
		con_create_objectclass=['top', 'ipsecNegotiationPolicy'],
		attributes={
			'cn': univention.s4connector.attribute(
				ucs_attribute='name',
				ldap_attribute='cn',
				con_attribute='cn',
				required=True,
				compare_function=univention.s4connector.compare_lowercase,
				single_value=True,
			),
			'description': univention.s4connector.attribute(
				ucs_attribute='description',
				ldap_attribute='description',
				con_attribute='description',
				single_value=True,
			),
			'ipsecOwnersReference': univention.s4connector.attribute(
				ucs_attribute='ipsecOwnersReference',
				ldap_attribute='ipsecOwnersReference',
				con_attribute='ipsecOwnersReference',
				compare_function=univention.s4connector.compare_lowercase,
				single_value=False,
			),
			'ipsecName': univention.s4connector.attribute(
				ucs_attribute='ipsecName',
				ldap_attribute='ipsecName',
				con_attribute='ipsecName',
				single_value=True,
			),
			'ipsecID': univention.s4connector.attribute(
				ucs_attribute='ipsecID',
				ldap_attribute='ipsecID',
				con_attribute='ipsecID',
				single_value=True,
			),
			'ipsecDataType': univention.s4connector.attribute(
				ucs_attribute='ipsecDataType',
				ldap_attribute='ipsecDataType',
				con_attribute='ipsecDataType',
				single_value=True,
			),
			'ipsecData': univention.s4connector.attribute(
				ucs_attribute='ipsecData',
				ldap_attribute='ipsecData',
				con_attribute='ipsecData',
				mapping=(_map_ldap_to_s4('ipsecData'), _map_s4_to_udm_base64('ipsecData')),
				single_value=True,
			),
			'iPSECNegotiationPolicyType': univention.s4connector.attribute(
				ucs_attribute='iPSECNegotiationPolicyType',
				ldap_attribute='iPSECNegotiationPolicyType',
				con_attribute='iPSECNegotiationPolicyType',
				single_value=True,
			),
			'iPSECNegotiationPolicyAction': univention.s4connector.attribute(
				ucs_attribute='iPSECNegotiationPolicyAction',
				ldap_attribute='iPSECNegotiationPolicyAction',
				con_attribute='iPSECNegotiationPolicyAction',
				single_value=True,
			),
		},
	),
	'ms/gpipsec-nfa': univention.s4connector.property(
		ucs_module='ms/gpipsec-nfa',
		sync_mode=str(configRegistry.get('connector/s4/mapping/gpipsec/syncmode', configRegistry.get('connector/s4/mapping/syncmode'))),
		scope='sub',
		con_search_filter='(objectClass=ipsecNFA)',
		ignore_filter=ignore_filter_from_attr('cn', 'connector/s4/mapping/gpipsec/ignorelist'),
		ignore_subtree=global_ignore_subtree,
		con_create_objectclass=['top', 'ipsecNFA'],
		attributes={
			'cn': univention.s4connector.attribute(
				ucs_attribute='name',
				ldap_attribute='cn',
				con_attribute='cn',
				required=True,
				compare_function=univention.s4connector.compare_lowercase,
				single_value=True,
			),
			'description': univention.s4connector.attribute(
				ucs_attribute='description',
				ldap_attribute='description',
				con_attribute='description',
				single_value=True,
			),
			'ipsecOwnersReference': univention.s4connector.attribute(
				ucs_attribute='ipsecOwnersReference',
				ldap_attribute='ipsecOwnersReference',
				con_attribute='ipsecOwnersReference',
				compare_function=univention.s4connector.compare_lowercase,
				single_value=False,
			),
			'ipsecName': univention.s4connector.attribute(
				ucs_attribute='ipsecName',
				ldap_attribute='ipsecName',
				con_attribute='ipsecName',
				single_value=True,
			),
			'ipsecID': univention.s4connector.attribute(
				ucs_attribute='ipsecID',
				ldap_attribute='ipsecID',
				con_attribute='ipsecID',
				single_value=True,
			),
			'ipsecDataType': univention.s4connector.attribute(
				ucs_attribute='ipsecDataType',
				ldap_attribute='ipsecDataType',
				con_attribute='ipsecDataType',
				single_value=True,
			),
			'ipsecData': univention.s4connector.attribute(
				ucs_attribute='ipsecData',
				ldap_attribute='ipsecData',
				con_attribute='ipsecData',
				mapping=(_map_ldap_to_s4('ipsecData'), _map_s4_to_udm_base64('ipsecData')),
				single_value=True,
			),
			'ipsecNegotiationPolicyReference': univention.s4connector.attribute(
				ucs_attribute='ipsecNegotiationPolicyReference',
				ldap_attribute='ipsecNegotiationPolicyReference',
				con_attribute='ipsecNegotiationPolicyReference',
				single_value=True,
			),
			'ipsecFilterReference': univention.s4connector.attribute(
				ucs_attribute='ipsecFilterReference',
				ldap_attribute='ipsecFilterReference',
				con_attribute='ipsecFilterReference',
				single_value=True,
			),
		},
	),
	'ms/gpipsec-policy': univention.s4connector.property(
		ucs_module='ms/gpipsec-policy',
		sync_mode=str(configRegistry.get('connector/s4/mapping/gpipsec/syncmode', configRegistry.get('connector/s4/mapping/syncmode'))),
		scope='sub',
		con_search_filter='(objectClass=ipsecPolicy)',
		ignore_filter=ignore_filter_from_attr('cn', 'connector/s4/mapping/gpipsec/ignorelist'),
		ignore_subtree=global_ignore_subtree,
		con_create_objectclass=['top', 'ipsecPolicy'],
		attributes={
			'cn': univention.s4connector.attribute(
				ucs_attribute='name',
				ldap_attribute='cn',
				con_attribute='cn',
				required=True,
				compare_function=univention.s4connector.compare_lowercase,
				single_value=True,
			),
			'description': univention.s4connector.attribute(
				ucs_attribute='description',
				ldap_attribute='description',
				con_attribute='description',
				single_value=True,
			),
			'ipsecOwnersReference': univention.s4connector.attribute(
				ucs_attribute='ipsecOwnersReference',
				ldap_attribute='ipsecOwnersReference',
				con_attribute='ipsecOwnersReference',
				compare_function=univention.s4connector.compare_lowercase,
				single_value=False,
			),
			'ipsecName': univention.s4connector.attribute(
				ucs_attribute='ipsecName',
				ldap_attribute='ipsecName',
				con_attribute='ipsecName',
				single_value=True,
			),
			'ipsecID': univention.s4connector.attribute(
				ucs_attribute='ipsecID',
				ldap_attribute='ipsecID',
				con_attribute='ipsecID',
				single_value=True,
			),
			'ipsecDataType': univention.s4connector.attribute(
				ucs_attribute='ipsecDataType',
				ldap_attribute='ipsecDataType',
				con_attribute='ipsecDataType',
				single_value=True,
			),
			'ipsecData': univention.s4connector.attribute(
				ucs_attribute='ipsecData',
				ldap_attribute='ipsecData',
				con_attribute='ipsecData',
				mapping=(_map_ldap_to_s4('ipsecData'), _map_s4_to_udm_base64('ipsecData')),
				single_value=True,
			),
			'ipsecNFAReference': univention.s4connector.attribute(
				ucs_attribute='ipsecNFAReference',
				ldap_attribute='ipsecNFAReference',
				con_attribute='ipsecNFAReference',
				single_value=True,
			),
			'ipsecISAKMPReference': univention.s4connector.attribute(
				ucs_attribute='ipsecISAKMPReference',
				ldap_attribute='ipsecISAKMPReference',
				con_attribute='ipsecISAKMPReference',
				single_value=True,
			),
		},
	),
	'ms/gpsi-category-registration': univention.s4connector.property(
		ucs_module='ms/gpsi-category-registration',
		sync_mode=str(configRegistry.get('connector/s4/mapping/gpsi/syncmode', configRegistry.get('connector/s4/mapping/syncmode'))),
		scope='sub',
		con_search_filter='(objectClass=categoryRegistration)',
		ignore_filter=ignore_filter_from_attr('cn', 'connector/s4/mapping/gpsi/ignorelist'),
		ignore_subtree=global_ignore_subtree,
		con_create_objectclass=['top', 'leaf', 'categoryRegistration'],
		attributes={
			'cn': univention.s4connector.attribute(
				ucs_attribute='name',
				ldap_attribute='cn',
				con_attribute='cn',
				required=True,
				compare_function=univention.s4connector.compare_lowercase,
				single_value=True,
			),
			'description': univention.s4connector.attribute(
				ucs_attribute='description',
				ldap_attribute='description',
				con_attribute='description',
				single_value=True,
			),
			'managedBy': univention.s4connector.attribute(
				ucs_attribute='managedBy',
				ldap_attribute='managedBy',
				con_attribute='managedBy',
				single_value=True,
			),
			'localizedDescription': univention.s4connector.attribute(
				ucs_attribute='localizedDescription',
				ldap_attribute='localizedDescription',
				con_attribute='localizedDescription',
				single_value=False,
			),
			'localeID': univention.s4connector.attribute(
				ucs_attribute='localeID',
				ldap_attribute='localeID',
				con_attribute='localeID',
				single_value=False,
			),
			'categoryId': univention.s4connector.attribute(
				ucs_attribute='categoryId',
				ldap_attribute='categoryId',
				con_attribute='categoryId',
				mapping=(_map_ldap_to_s4('categoryId'), _map_s4_to_udm_base64('categoryId')),
				single_value=True,
			),
		},
	),
	'ms/gpsi-class-store': univention.s4connector.property(
		ucs_module='ms/gpsi-class-store',
		sync_mode=str(configRegistry.get('connector/s4/mapping/gpsi/syncmode', configRegistry.get('connector/s4/mapping/syncmode'))),
		scope='sub',
		con_search_filter='(objectClass=classStore)',
		ignore_filter=ignore_filter_from_attr('cn', 'connector/s4/mapping/gpsi/ignorelist'),
		ignore_subtree=global_ignore_subtree,
		con_create_objectclass=['top', 'classStore'],
		attributes={
			'cn': univention.s4connector.attribute(
				ucs_attribute='name',
				ldap_attribute='cn',
				con_attribute='cn',
				required=True,
				compare_function=univention.s4connector.compare_lowercase,
				single_value=True,
			),
			'displayName': univention.s4connector.attribute(
				ucs_attribute='displayName',
				ldap_attribute='displayName',
				con_attribute='displayName',
				single_value=True,
			),
			'description': univention.s4connector.attribute(
				ucs_attribute='description',
				ldap_attribute='description',
				con_attribute='description',
				single_value=True,
			),
			'versionNumber': univention.s4connector.attribute(
				ucs_attribute='versionNumber',
				ldap_attribute='versionNumber',
				con_attribute='versionNumber',
				single_value=True,
			),
			'nextLevelStore': univention.s4connector.attribute(
				ucs_attribute='nextLevelStore',
				ldap_attribute='nextLevelStore',
				con_attribute='nextLevelStore',
				single_value=True,
			),
			'lastUpdateSequence': univention.s4connector.attribute(
				ucs_attribute='lastUpdateSequence',
				ldap_attribute='lastUpdateSequence',
				con_attribute='lastUpdateSequence',
				single_value=True,
			),
			'extensionName': univention.s4connector.attribute(
				ucs_attribute='extensionName',
				ldap_attribute='extensionName',
				con_attribute='extensionName',
				single_value=True,
			),
			'appSchemaVersion': univention.s4connector.attribute(
				ucs_attribute='appSchemaVersion',
				ldap_attribute='appSchemaVersion',
				con_attribute='appSchemaVersion',
				single_value=True,
			),

		},
	),
	'ms/gpsi-package-registration': univention.s4connector.property(
		ucs_module='ms/gpsi-package-registration',
		sync_mode=str(configRegistry.get('connector/s4/mapping/gpsi/syncmode', configRegistry.get('connector/s4/mapping/syncmode'))),
		scope='sub',
		con_search_filter='(objectClass=packageRegistration)',
		ignore_filter=ignore_filter_from_attr('cn', 'connector/s4/mapping/gpsi/ignorelist'),
		ignore_subtree=global_ignore_subtree,
		con_create_objectclass=['top', 'packageRegistration'],
		attributes={
			'cn': univention.s4connector.attribute(
				ucs_attribute='name',
				ldap_attribute='cn',
				con_attribute='cn',
				required=True,
				compare_function=univention.s4connector.compare_lowercase,
				single_value=True,
			),
			'displayName': univention.s4connector.attribute(
				ucs_attribute='displayName',
				ldap_attribute='displayName',
				con_attribute='displayName',
				single_value=True,
			),
			'description': univention.s4connector.attribute(
				ucs_attribute='description',
				ldap_attribute='description',
				con_attribute='description',
				single_value=True,
			),
			'versionNumberLo': univention.s4connector.attribute(
				ucs_attribute='versionNumberLo',
				ldap_attribute='versionNumberLo',
				con_attribute='versionNumberLo',
				single_value=True,
			),
			'versionNumberHi': univention.s4connector.attribute(
				ucs_attribute='versionNumberHi',
				ldap_attribute='versionNumberHi',
				con_attribute='versionNumberHi',
				single_value=True,
			),
			'vendor': univention.s4connector.attribute(
				ucs_attribute='vendor',
				ldap_attribute='vendor',
				con_attribute='vendor',
				single_value=True,
			),
			'url': univention.s4connector.attribute(
				ucs_attribute='url',
				ldap_attribute='url',
				con_attribute='url',
				single_value=False,
			),
			'revision': univention.s4connector.attribute(
				ucs_attribute='revision',
				ldap_attribute='revision',
				con_attribute='revision',
				single_value=True,
			),
			'upgradeProductCode': univention.s4connector.attribute(
				ucs_attribute='upgradeProductCode',
				ldap_attribute='upgradeProductCode',
				con_attribute='upgradeProductCode',
				mapping=(_map_ldap_to_s4('upgradeProductCode'), _map_s4_to_udm_base64('upgradeProductCode')),
				single_value=False,
			),
			'setupCommand': univention.s4connector.attribute(
				ucs_attribute='setupCommand',
				ldap_attribute='setupCommand',
				con_attribute='setupCommand',
				single_value=True,
			),
			'productCode': univention.s4connector.attribute(
				ucs_attribute='productCode',
				ldap_attribute='productCode',
				con_attribute='productCode',
				mapping=(_map_ldap_to_s4('productCode'), _map_s4_to_udm_base64('productCode')),
				single_value=True,
			),
			'packageType': univention.s4connector.attribute(
				ucs_attribute='packageType',
				ldap_attribute='packageType',
				con_attribute='packageType',
				single_value=True,
			),
			'packageName': univention.s4connector.attribute(
				ucs_attribute='packageName',
				ldap_attribute='packageName',
				con_attribute='packageName',
				single_value=True,
			),
			'packageFlags': univention.s4connector.attribute(
				ucs_attribute='packageFlags',
				ldap_attribute='packageFlags',
				con_attribute='packageFlags',
				single_value=True,
			),
			'msiScriptSize': univention.s4connector.attribute(
				ucs_attribute='msiScriptSize',
				ldap_attribute='msiScriptSize',
				con_attribute='msiScriptSize',
				single_value=True,
			),
			'msiScriptPath': univention.s4connector.attribute(
				ucs_attribute='msiScriptPath',
				ldap_attribute='msiScriptPath',
				con_attribute='msiScriptPath',
				single_value=True,
			),
			'msiScriptName': univention.s4connector.attribute(
				ucs_attribute='msiScriptName',
				ldap_attribute='msiScriptName',
				con_attribute='msiScriptName',
				single_value=True,
			),
			'msiScript': univention.s4connector.attribute(
				ucs_attribute='msiScript',
				ldap_attribute='msiScript',
				con_attribute='msiScript',
				mapping=(_map_ldap_to_s4('msiScript'), _map_s4_to_udm_base64('msiScript')),
				single_value=True,
			),
			'msiFileList': univention.s4connector.attribute(
				ucs_attribute='msiFileList',
				ldap_attribute='msiFileList',
				con_attribute='msiFileList',
				single_value=False,
			),
			'managedBy': univention.s4connector.attribute(
				ucs_attribute='managedBy',
				ldap_attribute='managedBy',
				con_attribute='managedBy',
				single_value=True,
			),
			'machineArchitecture': univention.s4connector.attribute(
				ucs_attribute='machineArchitecture',
				ldap_attribute='machineArchitecture',
				con_attribute='machineArchitecture',
				single_value=False,
			),
			'localeID': univention.s4connector.attribute(
				ucs_attribute='localeID',
				ldap_attribute='localeID',
				con_attribute='localeID',
				single_value=False,
			),
			'lastUpdateSequence': univention.s4connector.attribute(
				ucs_attribute='lastUpdateSequence',
				ldap_attribute='lastUpdateSequence',
				con_attribute='lastUpdateSequence',
				single_value=True,
			),
			'installUiLevel': univention.s4connector.attribute(
				ucs_attribute='installUiLevel',
				ldap_attribute='installUiLevel',
				con_attribute='installUiLevel',
				single_value=True,
			),
			'iconPath': univention.s4connector.attribute(
				ucs_attribute='iconPath',
				ldap_attribute='iconPath',
				con_attribute='iconPath',
				single_value=False,
			),
			'fileExtPriority': univention.s4connector.attribute(
				ucs_attribute='fileExtPriority',
				ldap_attribute='fileExtPriority',
				con_attribute='fileExtPriority',
				single_value=False,
			),
			'cOMTypelibId': univention.s4connector.attribute(
				ucs_attribute='cOMTypelibId',
				ldap_attribute='cOMTypelibId',
				con_attribute='cOMTypelibId',
				single_value=False,
			),
			'cOMProgID': univention.s4connector.attribute(
				ucs_attribute='cOMProgID',
				ldap_attribute='cOMProgID',
				con_attribute='cOMProgID',
				single_value=False,
			),
			'cOMInterfaceID': univention.s4connector.attribute(
				ucs_attribute='cOMInterfaceID',
				ldap_attribute='cOMInterfaceID',
				con_attribute='cOMInterfaceID',
				single_value=False,
			),
			'cOMClassID': univention.s4connector.attribute(
				ucs_attribute='cOMClassID',
				ldap_attribute='cOMClassID',
				con_attribute='cOMClassID',
				single_value=False,
			),
			'categories': univention.s4connector.attribute(
				ucs_attribute='categories',
				ldap_attribute='categories',
				con_attribute='categories',
				single_value=False,
			),
			'canUpgradeScript': univention.s4connector.attribute(
				ucs_attribute='canUpgradeScript',
				ldap_attribute='canUpgradeScript',
				con_attribute='canUpgradeScript',
				single_value=False,
			),
		},
	),
	'ou': univention.s4connector.property(
		ucs_module='container/ou',
		sync_mode=configRegistry.get('connector/s4/mapping/ou/syncmode', configRegistry.get('connector/s4/mapping/syncmode')),
		scope='sub',
		con_search_filter='objectClass=organizationalUnit',
		ignore_filter=ignore_filter_from_attr('ou', 'connector/s4/mapping/ou/ignorelist'),
		ignore_subtree=global_ignore_subtree,
		con_create_objectclass=['top', 'organizationalUnit'],
		attributes={
			'ou': univention.s4connector.attribute(
				ucs_attribute='name',
				ldap_attribute='ou',
				con_attribute='ou',
				required=1,
				compare_function=univention.s4connector.compare_lowercase,
				single_value=True,
			),
			'description': univention.s4connector.attribute(
				ucs_attribute='description',
				ldap_attribute='description',
				con_attribute='description',
				single_value=True,
			),
			'gPLink': univention.s4connector.attribute(
				ucs_attribute='gPLink',
				ldap_attribute='msGPOLink',
				con_attribute='gPLink',
				single_value=True,
			),
		},
	),
	'container_dc': univention.s4connector.property(
		ucs_module='container/dc',
		ucs_default_dn='cn=samba,@%@ldap/base@%@',
		con_default_dn='@%@connector/s4/ldap/base@%@',
		sync_mode=configRegistry.get('connector/s4/mapping/dc/syncmode', configRegistry.get('connector/s4/mapping/syncmode')),
		scope='sub',
		identify=univention.s4connector.s4.dc.identify,
		con_search_filter='(|(&(objectClass=domain)(!(|(name=DomainDnsZones)(name=ForestDnsZones))))(objectClass=sambaDomainName))',
		ignore_filter=ignore_filter_from_attr('cn', 'connector/s4/mapping/dc/ignorelist'),
		ignore_subtree=global_ignore_subtree,
		con_sync_function=univention.s4connector.s4.dc.ucs2con,
		ucs_sync_function=univention.s4connector.s4.dc.con2ucs,
	)
}

if not configRegistry.is_true('connector/s4/mapping/gpo', True):
	s4_mapping['container'].attributes.pop('gPLink')
if not configRegistry.is_true('connector/s4/mapping/gpo', True):
	s4_mapping['ou'].attributes.pop('gPLink')
if not configRegistry.is_true('connector/s4/mapping/group/grouptype', True):
	s4_mapping['group'].attributes.pop('groupType')

if not configRegistry.is_true('connector/s4/mapping/gpo', True):
	s4_mapping.pop('msGPO')
if not configRegistry.is_true('connector/s4/mapping/wmifilter', False):
	s4_mapping.pop('msWMIFilter')
if not configRegistry.is_true('connector/s4/mapping/msprintconnectionpolicy', False):
	s4_mapping.pop('msPrintConnectionPolicy')
if not configRegistry.is_true('connector/s4/mapping/msgpwl', False):
	s4_mapping.pop('ms/gpwl-wireless')
	s4_mapping.pop('ms/gpwl-wired')
	s4_mapping.pop('ms/gpwl-wireless-blob')
if not configRegistry.is_true('connector/s4/mapping/msgpipsec', False):
	s4_mapping.pop('ms/gpipsec-filter')
	s4_mapping.pop('ms/gpipsec-isakmp-policy')
	s4_mapping.pop('ms/gpipsec-negotiation-policy')
	s4_mapping.pop('ms/gpipsec-nfa')
	s4_mapping.pop('ms/gpipsec-policy')
if not configRegistry.is_true('connector/s4/mapping/msgpsi', False):
	s4_mapping.pop('ms/gpsi-category-registration')
	s4_mapping.pop('ms/gpsi-class-store')
	s4_mapping.pop('ms/gpsi-package-registration')

#print 'global_ignore_subtree = %r' % (global_ignore_subtree,)
#print 's4_mapping = %s' % (pprint.pformat(s4_mapping, indent=4, width=250),)

try:
	mapping_hook = imp.load_source('localmapping', os.path.join(os.path.dirname(__file__), 'localmapping.py')).mapping_hook
except (IOError, AttributeError):
	pass
else:
	s4_mapping = mapping_hook(s4_mapping)
