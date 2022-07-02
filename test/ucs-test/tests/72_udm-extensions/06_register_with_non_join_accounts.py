#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Register UDM extension with non-join-accounts
## tags: [udm,udm-extensions,apptest]
## roles: [domaincontroller_master,domaincontroller_backup,domaincontroller_slave,memberserver]
## exposure: dangerous
## packages:
##   - univention-config
##   - univention-directory-manager-tools
##   - shell-univention-lib

import pytest

from univention.testing.debian_package import DebianPackage
from univention.testing.udm_extensions import (
	VALID_EXTENSION_TYPES, call_cmd, get_dn_of_extension_by_name, get_extension_buffer,
	get_extension_filename, get_extension_name, get_join_script_buffer, get_package_name,
	get_package_version, remove_extension_by_name,
)
from univention.testing.utils import wait_for_replication


@pytest.mark.tags('udm', 'udm-extensions', 'apptest')
@pytest.mark.roles('domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver')
@pytest.mark.exposure('dangerous')
@pytest.mark.parametrize('extension_type', VALID_EXTENSION_TYPES)
def test_register_with_non_join_accounts(udm, extension_type, ucr):
	"""Register UDM extension with non-join-accounts"""
	password = 'univention'
	dn, username = udm.create_user(password=password)
	print('========================= TESTING EXTENSION %s =============================' % extension_type)
	_test_extension(extension_type, dn, password)
	_test_extension(extension_type, ucr.get('ldap/hostdn'), open('/etc/machine.secret', 'r').read())


def _test_extension(extension_type, dn, password):
	package_name = get_package_name()
	package_version = get_package_version()
	extension_name = get_extension_name(extension_type)
	extension_filename = get_extension_filename(extension_type, extension_name)
	joinscript_buffer = get_join_script_buffer(extension_type, '/usr/share/%s/%s' % (package_name, extension_filename), version_start='5.0-0')
	extension_buffer = get_extension_buffer(extension_type, extension_name)

	package = DebianPackage(name=package_name, version=package_version)
	try:
		# create package and install it
		package.create_join_script_from_buffer('66%s.inst' % package_name, joinscript_buffer)
		package.create_usr_share_file_from_buffer(extension_filename, extension_buffer)
		package.build()
		package.install()

		exitcode = call_cmd(['/usr/lib/univention-install/66%s.inst' % package_name, '--binddn', dn, '--bindpwd', password], fail_on_error=False)
		assert exitcode, 'ERROR: registerLDAPExtension() did not fail even if machine account is used'

		# wait until removed object has been handled by the listener
		wait_for_replication()

		dnlist = get_dn_of_extension_by_name(extension_type, extension_name)
		assert not dnlist, 'ERROR: Machine account is able to create UDM %s extension' % (extension_type,)

	finally:
		print('Removing UDM extension from LDAP')
		remove_extension_by_name(extension_type, extension_name, fail_on_error=False)

		print('Uninstalling binary package %r' % package_name)
		package.uninstall()

		print('Removing source package')
		package.remove()
