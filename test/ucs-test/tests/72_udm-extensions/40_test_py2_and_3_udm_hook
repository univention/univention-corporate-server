#!/usr/share/ucs-test/runner python3
## desc: Create UDM hook extension object and test it via CLI
## tags: [udm-ldapextensions]
## roles: [domaincontroller_master,domaincontroller_backup,domaincontroller_slave,memberserver]
## exposure: dangerous
## packages:
##   - univention-directory-manager-tools

import base64
import bz2

import univention.testing.udm as udm_test
from univention.config_registry import ConfigRegistry
from univention.testing.strings import random_name, random_ucs_version, random_version
from univention.testing.udm_extensions import (
	get_extension_buffer, get_extension_filename, get_extension_name, get_package_name, get_package_version,
)
from univention.testing.utils import (
	verify_ldap_object, wait_for_replication, wait_for_replication_and_postrun,
	wait_for_s4connector_replication,
)

if __name__ == '__main__':
	ucr = ConfigRegistry()
	ucr.load()

	with udm_test.UCSTestUDM() as udm:
		extension_type = 'hook'
		extension_name = get_extension_name(extension_type)
		extension_filename = get_extension_filename(extension_type, extension_name)
		extension_buffer = get_extension_buffer(extension_type, extension_name)
		object_name = random_name()

		package_name = get_package_name()
		package_version = get_package_version()
		app_id = '%s-%s' % (random_name(), random_version())
		version_start = random_ucs_version(max_major=2)
		version_end = random_ucs_version(min_major=5)

		udm.create_object(
			'container/cn',
			name='udm_%s' % (extension_type,),
			position='cn=univention,%s' % (ucr['ldap/base'],),
			ignore_exists=True
		)

		extension_dn = udm.create_object(
			'settings/udm_%s' % extension_type,
			name=extension_name,
			data=base64.b64encode(bz2.compress(extension_buffer.encode("UTF-8"))).decode("ASCII"),
			filename=extension_filename,
			packageversion=package_version,
			appidentifier=app_id,
			package=package_name,
			ucsversionstart=version_start,
			ucsversionend=version_end,
			active='FALSE',
			position='cn=udm_%s,cn=univention,%s' % (extension_type, ucr['ldap/base'])
		)

		extattr_dn = udm.create_object(
			'settings/extended_attribute',
			position='cn=custom attributes,cn=univention,%s' % ucr.get('ldap/base'),
			objectClass='univentionFreeAttributes',
			groupPosition='1',
			module='users/user',
			overwriteTab='0',
			hook=extension_name,
			shortDescription='UCS Test Extended Attribute %s' % extension_name,
			groupName='UCS TEST: test_udm_syntax',
			valueRequired='0',
			CLIName='ucstest%s' % extension_name.upper(),
			longDescription='UCS Test Extended Attribute',
			doNotSearch='0',
			tabName='UCS TEST',
			syntax='string',
			tabAdvanced='0',
			name='UCStest-hook-extension-%s' % extension_name,
			mayChange='1',
			multivalue='0',
			ldapMapping='univentionFreeAttribute20',
			notEditable='0',
			tabPosition='2'
		)

		wait_for_replication_and_postrun()
		udm.stop_cli_server()

		verify_ldap_object(extension_dn, {
			'cn': [extension_name],
			'univentionUDM%sFilename' % extension_type.capitalize(): [extension_filename],
			'univentionOwnedByPackage': [package_name],
			'univentionObjectType': ['settings/udm_%s' % extension_type],
			'univentionOwnedByPackageVersion': [package_version],
			'univentionUDM%sData' % extension_type.capitalize(): [bz2.compress(extension_buffer.encode('UTF-8'))],
			'univentionUDM%sActive' % extension_type.capitalize(): ['TRUE'],

		})

		# create user
		user_dn, username = udm.create_user()
		# We also need to wait for the replication on backup or slave
		wait_for_replication()
		wait_for_s4connector_replication()

		# set lastname of user ==> hook should set description
		lastname = random_name()
		udm.modify_object('users/user', dn=user_dn, lastname=lastname)
		# We also need to wait for the replication on backup or slave
		wait_for_replication()
		wait_for_s4connector_replication()
		verify_ldap_object(user_dn, {
			'uid': [username],
			'sn': [lastname],
			'description': ['USERNAME=%s  LASTNAME=%s' % (username, lastname)],
		})

		# set lastname of user ==> hook should set description
		lastname = random_name()
		udm.modify_object('users/user', dn=user_dn, lastname=lastname)
		# We also need to wait for the replication on backup or slave
		wait_for_replication()
		wait_for_s4connector_replication()
		verify_ldap_object(user_dn, {
			'uid': [username],
			'sn': [lastname],
			'description': ['USERNAME=%s  LASTNAME=%s' % (username, lastname)],
		})

	wait_for_replication_and_postrun()
	udm.stop_cli_server()

	with udm_test.UCSTestUDM() as udm:
		# test if user/user module is still ok after removing UDM module extension
		udm.create_user()
