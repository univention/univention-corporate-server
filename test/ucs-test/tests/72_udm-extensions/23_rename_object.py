#!/usr/share/ucs-test/runner python3
## desc: Rename UDM extension object
## tags: [udm,udm-ldapextensions,apptest]
## roles: [domaincontroller_master,domaincontroller_backup,domaincontroller_slave,memberserver]
## exposure: dangerous
## packages:
##   - univention-directory-manager-tools

import base64
import bz2
import os

import univention.testing.udm as udm_test
from univention.config_registry import ConfigRegistry
from univention.testing.strings import random_name, random_ucs_version, random_version
from univention.testing.udm_extensions import (
	VALID_EXTENSION_TYPES, get_absolute_extension_filename, get_dn_of_extension_by_name,
	get_extension_buffer, get_extension_filename, get_extension_name, get_package_name, get_package_version,
	remove_extension_by_name,
)
from univention.testing.utils import fail, verify_ldap_object, wait_for_replication

if __name__ == '__main__':
	ucr = ConfigRegistry()
	ucr.load()

	with udm_test.UCSTestUDM() as udm:
		for extension_type in VALID_EXTENSION_TYPES:
			print('========================= TESTING EXTENSION %s =============================' % extension_type)
			extension_name = get_extension_name(extension_type)
			extension_filename = get_extension_filename(extension_type, extension_name)
			extension_buffer = get_extension_buffer(extension_type, extension_name)

			package_name = get_package_name()
			package_version = get_package_version()
			app_id = '%s-%s' % (random_name(), random_version())
			version_start = random_ucs_version(max_major=2)
			version_end = random_ucs_version(min_major=5)

			# create object
			dn = udm.create_object(
				'settings/udm_%s' % extension_type,
				name=extension_name,
				data=base64.b64encode(bz2.compress(extension_buffer.encode("UTF-8"))).decode("ASCII"),
				filename=extension_filename,
				packageversion=package_version,
				package=package_name,
				active='TRUE',
				ucsversionstart=version_start,
				ucsversionend=version_end,
				position='cn=udm_%s,cn=univention,%s' % (extension_type, ucr['ldap/base'])
			)

			# check object
			verify_ldap_object(dn, {
				'cn': [extension_name],
				'univentionUDM%sFilename' % extension_type.capitalize(): [extension_filename],
				'univentionOwnedByPackage': [package_name],
				'univentionObjectType': ['settings/udm_%s' % extension_type],
				'univentionOwnedByPackageVersion': [package_version],
				'univentionUDM%sData' % extension_type.capitalize(): [bz2.compress(extension_buffer.encode('UTF-8'))],
			})

			# check if registered file has been replicated to local system
			target_fn = get_absolute_extension_filename(extension_type, extension_filename)
			if not os.path.exists(target_fn):
				fail('ERROR: expected file does not exist (%s)' % (target_fn))

			extension_name2 = random_name()
			if extension_type == 'module':
				extension_name2 = 'ucstest/%s' % extension_name2
			extension_filename2 = get_extension_filename(extension_type, extension_name2)
			expected_dn = dn.replace(extension_name, extension_name2)

			udm.modify_object('settings/udm_%s' % extension_type, dn=dn, name=extension_name2, filename=extension_filename2)
			dnlist = get_dn_of_extension_by_name(extension_type, extension_name2)
			if not dnlist:
				fail('ERROR: rename of udm %s extension object %s to %s failed' % (extension_type, extension_name, extension_name2))
			if not dnlist[0] == expected_dn:
				fail('ERROR: rename successful but expected DN is not equal to actual DN (%r vs %r)' % (expected_dn, dnlist[0]))

			# check if registered file is still present with the old name
			target_fn = get_absolute_extension_filename(extension_type, extension_filename)
			target_fn2 = get_absolute_extension_filename(extension_type, extension_filename2)
			if os.path.exists(target_fn):
				fail('ERROR: expected file exist (%s) while it should be removed' % (target_fn))
			if not os.path.exists(target_fn2):
				fail('ERROR: expected file does not exist (%s)' % (target_fn2))

			remove_extension_by_name(extension_type, extension_name, fail_on_error=False)
			remove_extension_by_name(extension_type, extension_name2, fail_on_error=False)

			wait_for_replication()

			# check if registered file has been removed
			target_fn = get_absolute_extension_filename(extension_type, extension_filename)
			if os.path.exists(target_fn):
				fail('ERROR: file exists unexpectedly (%s)' % (target_fn))
