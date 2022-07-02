#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Register and deregister UDM extension via postinst
## tags: [udm,udm-extensions,apptest]
## roles: [domaincontroller_master]
## exposure: dangerous
## packages:
##   - univention-config
##   - univention-directory-manager-tools
##   - shell-univention-lib

import bz2

import pytest

from univention.testing.debian_package import DebianPackage
from univention.testing.udm_extensions import (
	VALID_EXTENSION_TYPES, get_dn_of_extension_by_name, get_extension_buffer, get_extension_filename,
	get_extension_name, get_package_name, get_package_version, get_postinst_script_buffer,
	get_postrm_script_buffer, remove_extension_by_name,
)
from univention.testing.utils import verify_ldap_object, wait_for_replication


@pytest.mark.tags('udm', 'udm-extensions', 'apptest')
@pytest.mark.roles('domaincontroller_master')
@pytest.mark.exposure('dangerous')
@pytest.mark.parametrize('extension_type', VALID_EXTENSION_TYPES)
def test_register_deregister_via_postinst(extension_type):
	"""Register and deregister UDM extension via postinst"""
	print('========================= TESTING EXTENSION %s =============================' % extension_type)
	package_name = get_package_name()
	package_version = get_package_version()
	extension_name = get_extension_name(extension_type)
	extension_filename = get_extension_filename(extension_type, extension_name)
	extension_buffer = get_extension_buffer(extension_type, extension_name)
	postinst_buffer = get_postinst_script_buffer(extension_type, '/usr/share/%s/%s' % (package_name, extension_filename), version_start='5.0-0')
	postrm_buffer = get_postrm_script_buffer(extension_type, extension_name, package_name)

	package = DebianPackage(name=package_name, version=package_version)
	try:
		# create package and install it
		package.create_debian_file_from_buffer('%s.postinst' % package_name, postinst_buffer)
		package.create_debian_file_from_buffer('%s.postrm' % package_name, postrm_buffer)
		package.create_usr_share_file_from_buffer(extension_filename, extension_buffer)
		package.build()
		package.install()

		# wait until removed object has been handled by the listener
		wait_for_replication()

		dnlist = get_dn_of_extension_by_name(extension_type, extension_name)
		assert dnlist, 'Cannot find UDM %s extension with name %s in LDAP' % (extension_type, extension_name)
		verify_ldap_object(dnlist[0], {
			'cn': [extension_name],
			'univentionUDM%sFilename' % extension_type.capitalize(): [extension_filename],
			'univentionOwnedByPackage': [package_name],
			'univentionObjectType': ['settings/udm_%s' % extension_type],
			'univentionOwnedByPackageVersion': [package_version],
			'univentionUDM%sData' % extension_type.capitalize(): [bz2.compress(extension_buffer.encode('UTF-8'))],
		})

	finally:
		print('Removing UDM extension from LDAP')
		remove_extension_by_name(extension_type, extension_name, fail_on_error=False)

		print('Uninstalling binary package %r' % package_name)
		package.uninstall()

		print('Removing source package')
		package.remove()

	dnlist = get_dn_of_extension_by_name(extension_type, extension_name)
	assert not dnlist, 'ERROR: UDM extension object with cn=%s is still present in LDAP' % extension_name
