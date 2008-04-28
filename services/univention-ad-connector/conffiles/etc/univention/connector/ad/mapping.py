# -*- coding: utf-8 -*-
#
# Univention AD Connector
#  this file defines the mapping beetween AD and UCS
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

import univention.connector.ad
import univention.connector.ad.mapping
import univention.connector.ad.password

global_ignore_subtree=['cn=univention,@%@ldap/base@%@','cn=policies,@%@ldap/base@%@',
			'cn=shares,@%@ldap/base@%@','cn=printers,@%@ldap/base@%@',
			'cn=networks,@%@ldap/base@%@', 'cn=kerberos,@%@ldap/base@%@',
			'cn=dhcp,@%@ldap/base@%@', 'cn=dns,@%@ldap/base@%@',
			'cn=computers,@%@ldap/base@%@','cn=mail,@%@ldap/base@%@',
			'cn=System,@%@connector/ad/ldap/base@%@',
			'cn=Builtin,@%@connector/ad/ldap/base@%@',
			'cn=ForeignSecurityPrincipals,@%@connector/ad/ldap/base@%@',
			'ou=Domain Controllers,@%@connector/ad/ldap/base@%@',
			'cn=Program Data,@%@connector/ad/ldap/base@%@',
			'cn=Configuration,@%@connector/ad/ldap/base@%@',
			'cn=Microsoft Exchange System Objects,@%@connector/ad/ldap/base@%@']


ad_mapping = {
	'user': univention.connector.property (
			ucs_default_dn='cn=users,@%@ldap/base@%@',
			con_default_dn='cn=users,@%@connector/ad/ldap/base@%@',

			ucs_module='users/user',

			# read, write, sync, none
			sync_mode='@%@connector/ad/mapping/syncmode@%@',
			scope='sub',

			con_search_filter='(&(objectClass=user)(!objectClass=computer))',
			match_filter='(|(&(objectClass=posixAccount)(objectClass=sambaSamAccount))(objectClass=user))',
			ignore_filter='(|(uid=root)(uid=Administrator)(cn=Administrator)(CN=Administrator)(userAccountControl=2080))',

			ignore_subtree = global_ignore_subtree,
			
			con_create_objectclass=['top', 'user', 'person', 'organizationalPerson'],

			dn_mapping_function=[ univention.connector.ad.user_dn_mapping ],

			# aus UCS Modul
			attributes= {
					'samAccountName': univention.connector.attribute (
							ucs_attribute='username',
							ldap_attribute='uid',
							con_attribute='sAMAccountName',
							required=1,
							compare_function=univention.connector.compare_lowercase,
						),
					'givenName' : univention.connector.attribute (
							ucs_attribute='firstname',
							ldap_attribute='givenName',
							con_attribute='givenName',
						),
					'sn': univention.connector.attribute (
							ucs_attribute='lastname',
							ldap_attribute='sn',
							con_attribute='sn',
						),
				},

			ucs_create_functions = [ univention.connector.set_ucs_passwd_user,
						 univention.connector.check_ucs_lastname_user,
						 univention.connector.set_primary_group_user
						 ],

			post_con_modify_functions=[ univention.connector.ad.password.password_sync_ucs,
						    univention.connector.ad.primary_group_sync_from_ucs,
						    univention.connector.ad.object_memberships_sync_from_ucs,
						    univention.connector.ad.disable_user_from_ucs,
						    ],

			post_ucs_modify_functions=[ univention.connector.ad.password.password_sync,
						    univention.connector.ad.primary_group_sync_to_ucs,
						    univention.connector.ad.object_memberships_sync_to_ucs,
						    univention.connector.ad.disable_user_to_ucs,
						    ],

			post_attributes={
					'organisation': univention.connector.attribute (
							ucs_attribute='organisation',
							ldap_attribute='o',
							con_attribute='department',
						),
						@!@
if baseConfig.has_key('connector/ad/mapping/user/exchange') and baseConfig['connector/ad/mapping/user/exchange'] in ['yes','true']:
	print """
					'Exchange-Homeserver': univention.connector.attribute (
							ucs_attribute='Exchange-Homeserver',
							ldap_attribute='univentionADmsExchHomeServerName',
							con_attribute='msExchHomeServerName',
					),
					'Exchange-homeMDB': univention.connector.attribute (
							ucs_attribute='Exchange-homeMDB',
							ldap_attribute='univentionADhomeMDB',
							con_attribute='homeMDB',
					),
					'Exchange-Nickname': univention.connector.attribute (
							ucs_attribute='Exchange-Nickname',
							ldap_attribute='univentionADmailNickname',
							con_attribute='mailNickname',
					),
					"""
if not baseConfig.has_key('connector/ad/windows_version') or baseConfig['connector/ad/mapping/user/win2000/description'].lower() in ['yes', 'true'] or baseConfig['connector/ad/windows_version'] != 'win2000':
	print """
					'description': univention.connector.attribute (
						ucs_attribute='description',
						ldap_attribute='description',
						con_attribute='description',
					),
					"""
if baseConfig.has_key('connector/ad/mapping/user/primarymail') and baseConfig['connector/ad/mapping/user/primarymail'] in ['yes','true']:
	print """
					'mailPrimaryAddress': univention.connector.attribute (
						ucs_attribute='mailPrimaryAddress',
						ldap_attribute='mailPrimaryAddress',
						con_attribute='mail',
					),
					"""
@!@
					'street': univention.connector.attribute (
							ucs_attribute='street',
							ldap_attribute='street',
							con_attribute='streetAddress',
						),
					'city': univention.connector.attribute (
							ucs_attribute='city',
							ldap_attribute='l',
							con_attribute='l',
						),
					'postcode': univention.connector.attribute (
							ucs_attribute='postcode',
							ldap_attribute='postalCode',
							con_attribute='postalCode',
						),
					#'telephoneNumber': univention.connector.attribute ( # die Syntax erlaubt in AD mehr als in UCS
					#		ucs_attribute='phone',
					#		ldap_attribute='telephoneNumber',
					#		con_attribute='otherTelephone',
					#	),
					'profilepath': univention.connector.attribute (
							ucs_attribute='profilepath',
							ldap_attribute='sambaProfilePath',
							con_attribute='profilePath',
						),
					'scriptpath': univention.connector.attribute (
							ucs_attribute='scriptpath',
							ldap_attribute='sambaLogonScript',
							con_attribute='scriptPath',
						),
			},

		),

	'group': univention.connector.property (
			ucs_default_dn='cn=groups,@%@ldap/base@%@',
			con_default_dn='cn=Users,@%@connector/ad/ldap/base@%@',

			ucs_module='groups/group',

			sync_mode='@%@connector/ad/mapping/syncmode@%@',
			scope='sub',

			ignore_filter='(|(sambaGroupType=5)(groupType=5))',

			ignore_subtree = global_ignore_subtree,
			
			con_search_filter='objectClass=group',

			con_create_objectclass=['top', 'group'],

			post_con_modify_functions=[ univention.connector.ad.group_members_sync_from_ucs, univention.connector.ad.object_memberships_sync_from_ucs ],

			post_ucs_modify_functions=[ univention.connector.ad.group_members_sync_to_ucs, univention.connector.ad.object_memberships_sync_to_ucs ],

			dn_mapping_function=[ univention.connector.ad.group_dn_mapping ],

			attributes= {
					'cn': univention.connector.attribute (
							ucs_attribute='name',
							ldap_attribute='cn',
							con_attribute='sAMAccountName',
							required=1,
							compare_function=univention.connector.compare_lowercase,
						),
						@!@
if not baseConfig.has_key('connector/ad/windows_version') or baseConfig['connector/ad/mapping/group/win2000/description'].lower() in ['yes', 'true'] or baseConfig['connector/ad/windows_version'] != 'win2000':
	print """
					'description': univention.connector.attribute (
							ucs_attribute='description',
							ldap_attribute='description',
							con_attribute='description',
						),
					"""
if baseConfig.has_key('connector/ad/mapping/group/primarymail') and baseConfig['connector/ad/mapping/group/primarymail'] in ['yes','true']:
	print """
					'mailAddress': univention.connector.attribute (
						ucs_attribute='mailAddress',
						ldap_attribute='mailPrimaryAddress',
						con_attribute='mail',
					),
					'Exchange-Nickname': univention.connector.attribute (
						ucs_attribute='Exchange-Nickname',
						ldap_attribute='univentionADmailNickname',
						con_attribute='mailNickname',
					),
					"""
					@!@
				},

			mapping_table = {
						@!@
if baseConfig.has_key('connector/ad/mapping/group/language') and baseConfig['connector/ad/mapping/group/language'] in ['de','DE']:
	print """
				'cn': [( u'Domain Users' , u'Domänen-Benutzer'), ( u'Domain Users' , u'Domain Users'),
						(u'Domain Admins', u'Domänen-Admins'), (u'Domain Admins', u'Domain Admins'),
						(u'Windows Hosts', u'Domänencomputer'), (u'Windows Hosts', u'Windows Hosts'),
						(u'Domain Guests', u'Domänen-Gäste'), (u'Domain Guests', u'Domain Guests')]
					"""
					@!@
			},

		),

	'container': univention.connector.property (
			ucs_module='container/cn',

			sync_mode='@%@connector/ad/mapping/syncmode@%@',

			scope='sub',

			con_search_filter='(|(objectClass=container)(objectClass=builtinDomain))', # builtinDomain is cn=builtin (with group cn=Administrators)

			ignore_filter='(|(cn=mail)(cn=kerberos))',

			ignore_subtree = global_ignore_subtree,
			
			con_create_objectclass=['top', 'container' ],

			attributes= {
					'cn': univention.connector.attribute (
							ucs_attribute='name',
							ldap_attribute='cn',
							con_attribute='cn',
							required=1,
							compare_function=univention.connector.compare_lowercase,
						),
					'description': univention.connector.attribute (
							ucs_attribute='description',
							ldap_attribute='description',
							con_attribute='description'
						),
				},

		),

	'ou': univention.connector.property (
			ucs_module='container/ou',

			sync_mode='@%@connector/ad/mapping/syncmode@%@',

			scope='sub',

			con_search_filter='objectClass=organizationalUnit',

			ignore_filter='',

			ignore_subtree = global_ignore_subtree,

			con_create_objectclass=[ 'top', 'organizationalUnit' ],

			attributes= {
					'ou': univention.connector.attribute (
							ucs_attribute='name',
							ldap_attribute='ou',
							con_attribute='ou',
							required=1,
							compare_function=univention.connector.compare_lowercase,
						),
					'description': univention.connector.attribute (
							ucs_attribute='description',
							ldap_attribute='description',
							con_attribute='description'
						),
				},
		),
}



