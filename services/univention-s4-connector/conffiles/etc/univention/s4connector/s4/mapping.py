# -*- coding: utf-8 -*-
#
# Univention S4 Connector
#  this file defines the mapping beetween S4 and UCS
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

import univention.s4connector.s4
import univention.s4connector.s4.mapping
import univention.s4connector.s4.password
import univention.s4connector.s4.sid_mapping

global_ignore_subtree=['cn=univention,@%@ldap/base@%@','cn=policies,@%@ldap/base@%@',
			'cn=shares,@%@ldap/base@%@','cn=printers,@%@ldap/base@%@',
			'cn=networks,@%@ldap/base@%@', 'cn=kerberos,@%@ldap/base@%@',
			'cn=dhcp,@%@ldap/base@%@', 'cn=dns,@%@ldap/base@%@',
			'cn=mail,@%@ldap/base@%@',
			'cn=samba,@%@ldap/base@%@','cn=nagios,@%@ldap/base@%@',
			'cn=System,@%@connector/s4/ldap/base@%@',
			'ou=Grp Policy Users,@%@connector/s4/ldap/base@%@',
			'cn=Builtin,@%@connector/s4/ldap/base@%@',
			'cn=ForeignSecurityPrincipals,@%@connector/s4/ldap/base@%@',
			'ou=Domain Controllers,@%@connector/s4/ldap/base@%@',
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
			ignore_filter='(|(uid=root)(uid=pcpatch)(cn=pcpatch)(CN=pcpatch)(uid=ucs-s4sync)(CN=ucs-s4sync))',

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
				},

			ucs_create_functions = [ univention.s4connector.set_ucs_passwd_user,
						 univention.s4connector.check_ucs_lastname_user,
						 univention.s4connector.set_primary_group_user
						 ],

			post_con_create_functions = [ univention.s4connector.s4.normalise_userAccountControl,
						 ],

			post_con_modify_functions=[
							univention.s4connector.s4.sid_mapping.sid_to_s4,
							univention.s4connector.s4.password.password_sync_ucs_to_s4,
						    univention.s4connector.s4.primary_group_sync_from_ucs,
						    univention.s4connector.s4.object_memberships_sync_from_ucs,
						    univention.s4connector.s4.disable_user_from_ucs,
						    ],

			post_ucs_modify_functions=[
							univention.s4connector.s4.sid_mapping.sid_to_ucs,
							univention.s4connector.s4.password.password_sync_s4_to_ucs,
						    univention.s4connector.s4.primary_group_sync_to_ucs,
						    univention.s4connector.s4.object_memberships_sync_to_ucs,
						    univention.s4connector.s4.disable_user_to_ucs,
						    ],

			post_attributes={
					'organisation': univention.s4connector.attribute (
							ucs_attribute='organisation',
							ldap_attribute='o',
							con_attribute='department',
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
					#'telephoneNumber': univention.s4connector.attribute ( # die Syntax erlaubt in AD mehr als in UCS
					#		ucs_attribute='phone',
					#		ldap_attribute='telephoneNumber',
					#		con_attribute='otherTelephone',
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
			},

		),

	'group': univention.s4connector.property (
			ucs_default_dn='cn=groups,@%@ldap/base@%@',
			con_default_dn='cn=Users,@%@connector/s4/ldap/base@%@',

			ucs_module='groups/group',

			sync_mode='@%@connector/s4/mapping/syncmode@%@',
			scope='sub',

			ignore_filter='(|(sambaGroupType=5)(groupType=5)(cn=Windows Hosts)(cn=DC Slave Hosts)(cn=DC Backup Hosts))',

			ignore_subtree = global_ignore_subtree,
			
			con_search_filter='objectClass=group',

			con_create_objectclass=['top', 'group'],

			post_con_modify_functions=[ univention.s4connector.s4.group_members_sync_from_ucs, univention.s4connector.s4.object_memberships_sync_from_ucs ],

			post_ucs_modify_functions=[ univention.s4connector.s4.group_members_sync_to_ucs, univention.s4connector.s4.object_memberships_sync_to_ucs ],

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
					),
				},

			mapping_table = {
						@!@
if baseConfig.has_key('connector/s4/mapping/group/language') and baseConfig['connector/s4/mapping/group/language'] in ['de','DE']:
	print """
				'cn': [( u'Domain Users' , u'Domänen-Benutzer'), ( u'Domain Users' , u'Domain Users'),
						(u'Domain Admins', u'Domänen-Admins'), (u'Domain Admins', u'Domain Admins'),
						(u'Windows Hosts', u'Domänencomputer'), (u'Windows Hosts', u'Windows Hosts'),
						(u'Domain Guests', u'Domänen-Gäste'), (u'Domain Guests', u'Domain Guests')]
					"""
					@!@
			},

		),

	'windowscomputer': univention.s4connector.property (
			ucs_default_dn='cn=computers,@%@ldap/base@%@',
			con_default_dn='cn=computers,@%@connector/s4/ldap/base@%@',
			ucs_module='computers/windows',

			sync_mode='@%@connector/s4/mapping/syncmode@%@',

			scope='sub',

			con_search_filter='(&(objectClass=computer)(userAccountControl:1.2.840.113556.1.4.803:=4096))',

			# ignore_filter='userAccountControl=4096',
			match_filter='(|(objectClass=univentionWindows)(objectClass=computer))',

			ignore_subtree = global_ignore_subtree,
			
			con_create_objectclass=['top', 'computer' ],

			con_create_attributes=[('userAccountControl', ['4096'])],

			#post_con_create_functions = [ univention.connector.s4.computers.

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
				},

		),
	'container': univention.s4connector.property (
			ucs_module='container/cn',

			sync_mode='@%@connector/s4/mapping/syncmode@%@',

			scope='sub',

			con_search_filter='(|(objectClass=container)(objectClass=builtinDomain))', # builtinDomain is cn=builtin (with group cn=Administrators)

			ignore_filter='(|(cn=mail)(cn=kerberos))',

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
				},

		),

	'ou': univention.s4connector.property (
			ucs_module='container/ou',

			sync_mode='@%@connector/s4/mapping/syncmode@%@',

			scope='sub',

			con_search_filter='objectClass=organizationalUnit',

			ignore_filter='',

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
				},
		),
}



