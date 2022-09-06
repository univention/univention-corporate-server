#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Test all udm extensions functionality
## tags: [udm,udm-extensions,udm-ldapextensions,apptest,fbest]
## roles: [domaincontroller_master,domaincontroller_backup,domaincontroller_slave,memberserver]
## exposure: dangerous
## packages:
##   - univention-config
##   - univention-directory-manager-tools
##   - shell-univention-lib

import base64
import bz2
import difflib
import grp
import hashlib
import os
import random
import stat
import subprocess

import pytest

from univention.config_registry import ucr
from univention.testing.debian_package import DebianPackage
from univention.testing.strings import random_name, random_ucs_version, random_version
from univention.testing.udm import UCSTestUDM_CreateUDMObjectFailed, UCSTestUDM_ModifyUDMObjectFailed
from univention.testing.udm_extensions import (
	VALID_EXTENSION_TYPES, call_cmd, call_join_script, call_unjoin_script, get_absolute_extension_filename,
	get_dn_of_extension_by_name, get_extension_buffer, get_extension_filename, get_extension_name,
	get_join_script_buffer, get_package_name, get_package_version, get_postinst_script_buffer,
	get_postrm_script_buffer, get_unjoin_script_buffer, remove_extension_by_name,
)
from univention.testing.utils import (
	verify_ldap_object, wait_for_replication, wait_for_replication_and_postrun,
	wait_for_s4connector_replication,
)

CWD = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture
def extension_type(request):
	result = request.param
	assert isinstance(result, str)
	return result


@pytest.fixture
def wait_before(wait_for_replication):
	yield
	# wait for replicate before test starts
	wait_for_replication()


@pytest.mark.tags('udm', 'udm-extensions', 'apptest')
@pytest.mark.roles('domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver')
@pytest.mark.exposure('dangerous')
class Test_UDMExtensionsJoinscript:

	@pytest.mark.parametrize('extension_type', VALID_EXTENSION_TYPES, indirect=True)
	def test_register_deregister_via_joinscript(self, extension_type):
		"""Register and deregister UDM extension via joinscript"""
		package_name = get_package_name()
		package_version = get_package_version()
		extension_name = get_extension_name(extension_type)
		extension_filename = get_extension_filename(extension_type, extension_name)
		joinscript_buffer = get_join_script_buffer(extension_type, '/usr/share/%s/%s' % (package_name, extension_filename), version_start='5.0-0')
		unjoinscript_buffer = get_unjoin_script_buffer(extension_type, extension_name, package_name)
		extension_buffer = get_extension_buffer(extension_type, extension_name)

		package = DebianPackage(name=package_name, version=package_version)
		print('========================= TESTING EXTENSION %s =============================' % extension_type)
		try:
			# create package and install it
			package.create_join_script_from_buffer('66%s.inst' % package_name, joinscript_buffer)
			package.create_unjoin_script_from_buffer('66%s-uninstall.uinst' % package_name, unjoinscript_buffer)
			package.create_usr_share_file_from_buffer(extension_filename, extension_buffer)
			package.build()
			package.install()

			call_join_script('66%s.inst' % package_name)

			# wait until removed object has been handled by the listener
			wait_for_replication()

			dnlist = get_dn_of_extension_by_name(extension_type, extension_name)
			assert dnlist, 'ERROR: cannot find UDM extension object with cn=%s in LDAP' % extension_name

			# check if registered file has been replicated to local system
			target_fn = get_absolute_extension_filename(extension_type, extension_filename)
			assert os.path.exists(target_fn), 'ERROR: target file %s does not exist' % target_fn
			print('FILE REPLICATED: %r' % target_fn)

			# check replicated file has correct file mode
			current_mode = oct(os.stat(target_fn).st_mode & (stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO))
			expected_mode = '0o644'
			assert current_mode == expected_mode, 'ERROR: permissions of target file %s are not ok (current=%s  expected=%s)' % (target_fn, current_mode, expected_mode)
			print('PERMISSIONS OK: mode=%s' % current_mode)

			# check replicated file is own by root:nobody
			expected_groups = (0, grp.getgrnam('nogroup').gr_gid)
			expected_uid = 0
			current_uid = os.stat(target_fn).st_uid
			current_group = os.stat(target_fn).st_gid
			assert current_uid == expected_uid and current_group in expected_groups, 'ERROR: owner/group of target file %s is not ok (current=%s:%s  expected_uid=%s expected_gid=%s)' % (target_fn, current_uid, current_group, expected_uid, expected_groups)
			print('FILE OWNER/GROUP OK')

			# check if sha1(buffer) == sha1(file)
			hash_buffer = hashlib.sha1(extension_buffer.encode('UTF-8')).hexdigest()
			hash_file = hashlib.sha1(open(target_fn, 'rb').read()).hexdigest()
			print('HASH BUFFER: %r' % hash_buffer)
			print('HASH FILE: %r' % hash_file)
			assert hash_buffer == hash_file, 'ERROR: sha1 sums of file and buffer differ (fn=%s ; file=%s ; buffer=%s)' % (target_fn, hash_file, hash_buffer)

			call_unjoin_script('66%s-uninstall.uinst' % package_name)

			# wait until removed object has been handled by the listener
			wait_for_replication()

			dnlist = get_dn_of_extension_by_name(extension_type, extension_name)
			assert not dnlist, 'ERROR: UDM extension object with cn=%s is still present in LDAP' % extension_name

			# check if registered file has been removed from local system
			assert not os.path.exists(target_fn), 'ERROR: target file %s is still present' % target_fn

		finally:
			print('Removing UDM extension from LDAP')
			remove_extension_by_name(extension_type, extension_name, fail_on_error=False)

			print('Uninstalling binary package %r' % package_name)
			package.uninstall()

			print('Removing source package')
			package.remove()

	@pytest.mark.tags('udm', 'udm-extensions', 'apptest')
	@pytest.mark.roles('domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver')
	@pytest.mark.exposure('dangerous')
	@pytest.mark.parametrize('extension_type', VALID_EXTENSION_TYPES, indirect=True)
	def test_register_and_verify_ldap_object(self, extension_type):
		"""Register UDM extension and perform simple LDAP verification"""
		print('========================= TESTING EXTENSION %s =============================' % extension_type)
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

			call_join_script('66%s.inst' % package_name)

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

	@pytest.mark.tags('udm', 'udm-extensions', 'apptest')
	@pytest.mark.roles('domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver')
	@pytest.mark.exposure('dangerous')
	@pytest.mark.parametrize('extension_type', VALID_EXTENSION_TYPES, indirect=True)
	def test_register_and_verify_test_app_id(self, extension_type):
		"""Check setting of UNIVENTION_APP_ID for UDM extensions"""
		print('========================= TESTING EXTENSION %s =============================' % extension_type)
		package_name = get_package_name()
		package_version = get_package_version()
		extension_name = get_extension_name(extension_type)
		extension_filename = get_extension_filename(extension_type, extension_name)
		app_id = '%s-%s' % (random_name(), random_version())
		joinscript_buffer = get_join_script_buffer(
			extension_type,
			'/usr/share/%s/%s' % (package_name, extension_filename),
			app_id=app_id,
			version_start='5.0-0'
		)
		extension_buffer = get_extension_buffer(extension_type, extension_name)

		package = DebianPackage(name=package_name, version=package_version)
		try:
			# create package and install it
			package.create_join_script_from_buffer('66%s.inst' % package_name, joinscript_buffer)
			package.create_usr_share_file_from_buffer(extension_filename, extension_buffer)
			package.build()
			package.install()

			call_join_script('66%s.inst' % package_name)

			# wait until removed object has been handled by the listener
			wait_for_replication()

			dnlist = get_dn_of_extension_by_name(extension_type, extension_name)
			assert dnlist, 'Cannot find UDM %s extension with name %s in LDAP' % (extension_type, extension_name)
			verify_ldap_object(dnlist[0], {
				'cn': [extension_name],
				'univentionUDM%sFilename' % extension_type.capitalize(): ['%s.py' % extension_name],
				'univentionOwnedByPackage': [package_name],
				'univentionObjectType': ['settings/udm_%s' % extension_type],
				'univentionOwnedByPackageVersion': [package_version],
				'univentionUDM%sData' % extension_type.capitalize(): [bz2.compress(extension_buffer.encode('UTF-8'))],
				'univentionAppIdentifier': [app_id],
			})
		finally:
			print('Removing UDM extension from LDAP')
			remove_extension_by_name(extension_type, extension_name, fail_on_error=False)

			print('Uninstalling binary package %r' % package_name)
			package.uninstall()

			print('Removing source package')
			package.remove()

	@pytest.mark.tags('udm', 'udm-extensions', 'apptest')
	@pytest.mark.roles('domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver')
	@pytest.mark.exposure('dangerous')
	@pytest.mark.parametrize('extension_type', VALID_EXTENSION_TYPES, indirect=True)
	def test_register_and_verify_version_start_end(self, extension_type):
		"""Check setting of a version range for UDM extensions"""
		print('========================= TESTING EXTENSION %s =============================' % extension_type)
		package_name = get_package_name()
		package_version = get_package_version()
		extension_name = get_extension_name(extension_type)
		extension_filename = get_extension_filename(extension_type, extension_name)
		version_start = random_ucs_version(max_major=2)
		version_end = random_ucs_version(min_major=5)
		app_id = '%s-%s' % (random_name(), random_version())
		joinscript_buffer = get_join_script_buffer(
			extension_type,
			'/usr/share/%s/%s' % (package_name, extension_filename),
			app_id=app_id, version_start=version_start, version_end=version_end
		)
		extension_buffer = get_extension_buffer(extension_type, extension_name)
		print(joinscript_buffer)

		package = DebianPackage(name=package_name, version=package_version)
		try:
			# create package and install it
			package.create_join_script_from_buffer('66%s.inst' % package_name, joinscript_buffer)
			package.create_usr_share_file_from_buffer(extension_filename, extension_buffer)
			package.build()
			package.install()

			call_join_script('66%s.inst' % package_name)

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
				'univentionUCSVersionStart': [version_start],
				'univentionUCSVersionEnd': [version_end],
			})
		finally:
			print('Removing UDM extension from LDAP')
			remove_extension_by_name(extension_type, extension_name, fail_on_error=False)

			print('Uninstalling binary package %r' % package_name)
			package.uninstall()

			print('Removing source package')
			package.remove()

	@pytest.mark.tags('udm', 'udm-extensions', 'apptest')
	@pytest.mark.roles('domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver')
	@pytest.mark.exposure('dangerous')
	@pytest.mark.parametrize('extension_type', VALID_EXTENSION_TYPES, indirect=True)
	def test_register_with_non_join_accounts(self, udm, extension_type, ucr):
		"""Register UDM extension with non-join-accounts"""
		password = 'univention'
		dn, username = udm.create_user(password=password)
		print('========================= TESTING EXTENSION %s =============================' % extension_type)
		self._test_extension(extension_type, dn, password)
		self._test_extension(extension_type, ucr.get('ldap/hostdn'), open('/etc/machine.secret', 'r').read())

	def _test_extension(self, extension_type, dn, password):
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

	@pytest.mark.tags('udm', 'udm-extensions', 'apptest')
	@pytest.mark.roles('domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver')
	@pytest.mark.exposure('dangerous')
	def test_register_and_verify_all(self):
		"""Register and verify all UDM extension in one step"""
		package_name = get_package_name()
		package_version = get_package_version()
		# extension_name = get_extension_name(extension_type)
		# extension_filename = get_extension_filename(extension_type, extension_name)
		extension_name = {}
		extension_buffer = {}
		extension_filename = {}
		for extension_type in VALID_EXTENSION_TYPES:
			extension_name[extension_type] = get_extension_name(extension_type)
			extension_buffer[extension_type] = get_extension_buffer(extension_type, extension_name[extension_type])
			extension_filename[extension_type] = get_extension_filename(extension_type, extension_name[extension_type])

		data = {'package': package_name}
		data.update(extension_filename)
		joinscript_buffer = '''#!/bin/sh
	VERSION=1
	set -e
	. /usr/share/univention-join/joinscripthelper.lib
	joinscript_init
	. /usr/share/univention-lib/ldap.sh
	ucs_registerLDAPExtension "$@" --ucsversionstart 5.0-0 --udm_hook /usr/share/%(package)s/%(hook)s --udm_syntax /usr/share/%(package)s/%(syntax)s --udm_module /usr/share/%(package)s/%(module)s
	joinscript_save_current_version
	exit 0
	''' % data

		package = DebianPackage(name=package_name, version=package_version)
		try:
			# create package and install it
			package.create_join_script_from_buffer('66%s.inst' % package_name, joinscript_buffer)
			for extension_type in VALID_EXTENSION_TYPES:
				package.create_usr_share_file_from_buffer(extension_filename[extension_type], extension_buffer[extension_type])
			package.build()
			package.install()

			call_join_script('66%s.inst' % package_name)

			# wait until removed object has been handled by the listener
			wait_for_replication()

			for extension_type in VALID_EXTENSION_TYPES:
				dnlist = get_dn_of_extension_by_name(extension_type, extension_name[extension_type])
				assert dnlist, 'Cannot find UDM %s extension with name %s in LDAP' % (extension_type, extension_name[extension_type])
				verify_ldap_object(dnlist[0], {
					'cn': [extension_name[extension_type]],
					'univentionUDM%sFilename' % extension_type.capitalize(): [extension_filename[extension_type]],
					'univentionOwnedByPackage': [package_name],
					'univentionObjectType': ['settings/udm_%s' % extension_type],
					'univentionOwnedByPackageVersion': [package_version],
					'univentionUDM%sData' % extension_type.capitalize(): [bz2.compress(extension_buffer[extension_type].encode('UTF-8'))],
				})

		finally:
			print('Removing UDM extension from LDAP')
			for extension_type in VALID_EXTENSION_TYPES:
				remove_extension_by_name(extension_type, extension_name[extension_type], fail_on_error=False)

			print('Uninstalling binary package %r' % package_name)
			package.uninstall()

			print('Removing source package')
			package.remove()

	@pytest.mark.tags('udm', 'udm-extensions', 'apptest')
	@pytest.mark.roles('domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver')
	@pytest.mark.exposure('dangerous')
	def test_register_with_special_name_and_verify_all(self):
		"""Register and verify all UDM extension in one step"""
		objectname = "/".join([random_name(), random_name()])  # slash reqired for 'module'
		package_name = get_package_name()
		package_version = get_package_version()
		# extension_name = get_extension_name(extension_type)
		# extension_filename = get_extension_filename(extension_type, extension_name)
		extension_name = {}
		extension_objectname = {}
		extension_buffer = {}
		extension_filename = {}
		for extension_type in VALID_EXTENSION_TYPES:
			extension_name[extension_type] = get_extension_name(extension_type)
			extension_objectname[extension_type] = objectname
			extension_buffer[extension_type] = get_extension_buffer(extension_type, extension_name[extension_type])
			extension_filename[extension_type] = get_extension_filename(extension_type, extension_name[extension_type])

		data = {'package': package_name, 'objectname': objectname}
		data.update(extension_filename)
		joinscript_buffer = '''#!/bin/sh
	VERSION=1
	set -e
	. /usr/share/univention-join/joinscripthelper.lib
	joinscript_init
	. /usr/share/univention-lib/ldap.sh
	ucs_registerLDAPExtension "$@" --name "%(objectname)s" --ucsversionstart 5.0-0 --udm_hook /usr/share/%(package)s/%(hook)s --udm_syntax /usr/share/%(package)s/%(syntax)s --udm_module /usr/share/%(package)s/%(module)s
	joinscript_save_current_version
	exit 0
	''' % data

		package = DebianPackage(name=package_name, version=package_version)
		try:
			# create package and install it
			package.create_join_script_from_buffer('66%s.inst' % package_name, joinscript_buffer)
			for extension_type in VALID_EXTENSION_TYPES:
				package.create_usr_share_file_from_buffer(extension_filename[extension_type], extension_buffer[extension_type])
			package.build()
			package.install()

			call_join_script('66%s.inst' % package_name)

			# wait until removed object has been handled by the listener
			wait_for_replication()

			for extension_type in VALID_EXTENSION_TYPES:
				dnlist = get_dn_of_extension_by_name(extension_type, extension_objectname[extension_type])
				assert dnlist, 'Cannot find UDM %s extension with name %s in LDAP' % (extension_type, extension_objectname[extension_type])
				verify_ldap_object(dnlist[0], {
					'cn': [extension_objectname[extension_type]],
					'univentionUDM%sFilename' % extension_type.capitalize(): [extension_filename[extension_type]],
					'univentionOwnedByPackage': [package_name],
					'univentionObjectType': ['settings/udm_%s' % extension_type],
					'univentionOwnedByPackageVersion': [package_version],
					'univentionUDM%sData' % extension_type.capitalize(): [bz2.compress(extension_buffer[extension_type].encode('UTF-8'))],
				})

		finally:
			print('Removing UDM extension from LDAP')
			for extension_type in VALID_EXTENSION_TYPES:
				remove_extension_by_name(extension_type, extension_objectname[extension_type], fail_on_error=False)

			print('Uninstalling binary package %r' % package_name)
			package.uninstall()

			print('Removing source package')
			package.remove()

	@pytest.mark.tags('udm', 'udm-extensions', 'apptest')
	@pytest.mark.roles('domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver')
	@pytest.mark.exposure('dangerous')
	@pytest.mark.parametrize('extension_type', VALID_EXTENSION_TYPES, indirect=True)
	def test_update_extension_via_package(self, extension_type):
		"""Test extension update with correct version order"""
		print('========================= TESTING EXTENSION %s =============================' % extension_type)
		package_name = get_package_name()
		version = random_version()
		package_version_LOW = '%s.%d' % (version, random.randint(0, 4))
		package_version_HIGH = '%s.%d' % (version, random.randint(5, 9))
		extension_name = get_extension_name(extension_type)
		extension_filename = get_extension_filename(extension_type, extension_name)
		app_id = '%s-%s' % (random_name(), random_version())
		joinscript_version = 1

		packages = []
		try:
			for package_version in (package_version_LOW, package_version_HIGH):

				version_start = random_ucs_version(max_major=2)
				version_end = random_ucs_version(min_major=5)

				# create unique extension identifier
				extension_identifier = '%s_%s' % (extension_name, package_version.replace('.', '_'))
				extension_buffer = get_extension_buffer(extension_type, extension_name, extension_identifier)
				joinscript_buffer = get_join_script_buffer(
					extension_type,
					'/usr/share/%s/%s' % (package_name, extension_filename),
					app_id=app_id,
					joinscript_version=joinscript_version,
					version_start=version_start,
					version_end=version_end
				)
				joinscript_version += 1

				# create package and install it
				package = DebianPackage(name=package_name, version=package_version)
				packages.append(package)
				package.create_join_script_from_buffer('66%s.inst' % package_name, joinscript_buffer)
				package.create_usr_share_file_from_buffer(extension_filename, extension_buffer)
				package.build()
				package.install()

				call_join_script('66%s.inst' % package_name)

				# wait until removed object has been handled by the listener
				wait_for_replication()

				dnlist = get_dn_of_extension_by_name(extension_type, extension_name)
				assert dnlist, 'Cannot find UDM %s extension with name %s in LDAP' % (extension_type, extension_name)
				verify_ldap_object(dnlist[0], {
					'cn': [extension_name],
					'univentionUCSVersionStart': [version_start],
					'univentionUCSVersionEnd': [version_end],
				})

				content = open(get_absolute_extension_filename(extension_type, extension_filename)).read()
				assert not extension_identifier not in content, 'ERROR: UDM extension of package %d has not been written to disk (%s)' % (len(packages), extension_filename,)

		finally:
			print('Removing UDM extension from LDAP')
			remove_extension_by_name(extension_type, extension_name, fail_on_error=False)

			for package in packages:
				print('Uninstalling binary package %r' % package.get_package_name())
				package.uninstall()

			print('Removing source package')
			for package in packages:
				package.remove()

	@pytest.mark.tags('udm', 'udm-extensions', 'apptest')
	@pytest.mark.roles('domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver')
	@pytest.mark.exposure('dangerous')
	@pytest.mark.parametrize('extension_type', VALID_EXTENSION_TYPES, indirect=True)
	def test_update_extension_via_package_expected_fail(self, extension_type):
		"""Test extension update with wrong version order"""
		print('========================= TESTING EXTENSION %s =============================' % extension_type)
		package_name = get_package_name()
		version = random_version()
		package_version_LOW = '%s.%d' % (version, random.randint(0, 4))
		package_version_HIGH = '%s.%d' % (version, random.randint(5, 9))
		extension_name = get_extension_name(extension_type)
		extension_filename = get_extension_filename(extension_type, extension_name)
		app_id = '%s-%s' % (random_name(), random_version())
		joinscript_version = 1

		packages = []
		try:
			for package_version in (package_version_HIGH, package_version_LOW):
				# create unique extension identifier
				extension_identifier = '%s_%s' % (extension_name, package_version.replace('.', '_'))
				extension_buffer = get_extension_buffer(extension_type, extension_name, extension_identifier)
				joinscript_buffer = get_join_script_buffer(
					extension_type,
					'/usr/share/%s/%s' % (package_name, extension_filename),
					app_id=app_id,
					joinscript_version=joinscript_version,
					version_start='5.0-0'
				)
				joinscript_version += 1

				# create package and install it
				package = DebianPackage(name=package_name, version=package_version)
				packages.append(package)
				package.create_join_script_from_buffer('66%s.inst' % package_name, joinscript_buffer)
				package.create_usr_share_file_from_buffer(extension_filename, extension_buffer)
				package.build()
				package.install()

				exitcode = call_join_script('66%s.inst' % package_name, fail_on_error=False)
				if package_version == package_version_HIGH:
					assert not exitcode, 'The join script failed with exitcode %s' % exitcode
				else:
					if not exitcode:
						print('\nWARNING: a failure of the joinscript has been expected but in ran through\n')

				# wait until removed object has been handled by the listener
				wait_for_replication()

				content = open(get_absolute_extension_filename(extension_type, extension_filename)).read()
				assert not (package_version == package_version_HIGH and extension_identifier not in content), 'ERROR: UDM extension of package %d has not been written to disk (%s)' % (len(packages), extension_filename,)
				assert not (package_version == package_version_LOW and extension_identifier in content), 'ERROR: the extension update has been performed but should not (old version=%s ; new version=%s)' % (package_version_HIGH, package_version_LOW)

		finally:
			print('Removing UDM extension from LDAP')
			remove_extension_by_name(extension_type, extension_name, fail_on_error=False)

			for package in packages:
				print('Uninstalling binary package %r' % package.get_package_name())
				package.uninstall()

			print('Removing source package')
			for package in packages:
				package.remove()

	@pytest.mark.tags('udm', 'udm-extensions', 'apptest')
	@pytest.mark.roles('domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver')
	@pytest.mark.exposure('dangerous')
	@pytest.mark.parametrize('extension_type', VALID_EXTENSION_TYPES, indirect=True)
	def test_update_extension_via_other_packagename(self, extension_type):
		"""Test extension update with other package name"""
		print('========================= TESTING EXTENSION %s =============================' % extension_type)
		version = random_version()
		package_version_LOW = '%s.%d' % (version, random.randint(0, 4))
		package_version_HIGH = '%s.%d' % (version, random.randint(5, 9))
		extension_name = get_extension_name(extension_type)
		extension_filename = get_extension_filename(extension_type, extension_name)
		app_id = '%s-%s' % (random_name(), random_version())
		joinscript_version = 1

		packages = []
		try:
			for package_version in (package_version_LOW, package_version_HIGH):

				package_name = get_package_name()
				version_start = random_ucs_version(max_major=2)
				version_end = random_ucs_version(min_major=5)

				# create unique extension identifier
				extension_identifier = '%s_%s' % (extension_name, package_version.replace('.', '_'))
				extension_buffer = get_extension_buffer(extension_type, extension_name, extension_identifier)
				joinscript_buffer = get_join_script_buffer(
					extension_type,
					'/usr/share/%s/%s' % (package_name, extension_filename),
					app_id=app_id,
					joinscript_version=joinscript_version,
					version_start=version_start,
					version_end=version_end
				)
				joinscript_version += 1

				# create package and install it
				package = DebianPackage(name=package_name, version=package_version)
				packages.append(package)
				package.create_join_script_from_buffer('66%s.inst' % package_name, joinscript_buffer)
				package.create_usr_share_file_from_buffer(extension_filename, extension_buffer)
				package.build()
				package.install()

				call_join_script('66%s.inst' % package_name)

				# wait until removed object has been handled by the listener
				wait_for_replication()

				content = open(get_absolute_extension_filename(extension_type, extension_filename)).read()
				assert not extension_identifier not in content, 'ERROR: UDM extension of package %d has not been written to disk (%s)' % (len(packages), extension_filename,)

		finally:
			print('Removing UDM extension from LDAP')
			remove_extension_by_name(extension_type, extension_name, fail_on_error=False)

			for package in packages:
				print('Uninstalling binary package %r' % package.get_package_name())
				package.uninstall()

			print('Removing source package')
			for package in packages:
				package.remove()

	TEST_DATA = (
		('umcregistration', '72_file_integrity_udm_module.xml', '/usr/share/univention-management-console/modules/udm-%s.xml'),
		('icon', '72_file_integrity_udm_module-16.png', '/usr/share/univention-management-console-frontend/js/dijit/themes/umc/icons/16x16/udm-%s.png'),
		('icon', '72_file_integrity_udm_module-50.png', '/usr/share/univention-management-console-frontend/js/dijit/themes/umc/icons/50x50/udm-%s.png'),
		('messagecatalog', 'it.mo', '/usr/share/locale/it/LC_MESSAGES/univention-admin-handlers-%s.mo'),
		('messagecatalog', 'de.mo', '/usr/share/locale/de/LC_MESSAGES/univention-admin-handlers-%s.mo'),
		('messagecatalog', 'es.mo', '/usr/share/locale/es/LC_MESSAGES/univention-admin-handlers-%s.mo'),
	)

	@pytest.mark.tags('udm', 'udm-extensions', 'apptest', 'fbest')
	@pytest.mark.roles('domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver')
	@pytest.mark.exposure('dangerous')
	def test_file_integrity_udm_module(self):
		"""Register and deregister UDM extension via joinscript"""
		extension_type = 'module'
		package_name = get_package_name()
		package_version = get_package_version()
		extension_name = get_extension_name(extension_type)
		extension_filename = get_extension_filename(extension_type, extension_name)

		options = {}
		buffers = {}
		for option_type, filename, target_filename in self.TEST_DATA:
			buffers[filename] = open('%s/%s' % (CWD, filename), 'rb').read()
			options.setdefault(option_type, []).append('/usr/share/%s/%s' % (package_name, filename))

		joinscript_buffer = get_join_script_buffer(extension_type, '/usr/share/%s/%s' % (package_name, extension_filename), options=options, version_start='5.0-0')
		unjoinscript_buffer = get_unjoin_script_buffer(extension_type, extension_name, package_name)
		extension_buffer = get_extension_buffer(extension_type, extension_name)

		print(joinscript_buffer)

		package = DebianPackage(name=package_name, version=package_version)
		try:
			# create package and install it
			package.create_join_script_from_buffer('66%s.inst' % package_name, joinscript_buffer)
			package.create_unjoin_script_from_buffer('66%s-uninstall.uinst' % package_name, unjoinscript_buffer)
			package.create_usr_share_file_from_buffer(extension_filename, extension_buffer)
			for fn, data in buffers.items():
				package.create_usr_share_file_from_buffer(fn, data, 'wb')
			package.build()
			package.install()

			call_join_script('66%s.inst' % package_name)

			# wait until removed object has been handled by the listener
			wait_for_replication()

			dnlist = get_dn_of_extension_by_name(extension_type, extension_name)
			assert dnlist, 'ERROR: cannot find UDM extension object with cn=%s in LDAP' % extension_name

			# check if registered file has been replicated to local system
			target_fn = get_absolute_extension_filename(extension_type, extension_filename)
			assert os.path.exists(target_fn), 'ERROR: target file %s does not exist' % target_fn
			print('FILE REPLICATED: %r' % target_fn)

			# check if sha1(buffer) == sha1(file)
			hash_buffer = hashlib.sha1(extension_buffer.encode('UTf-8')).hexdigest()
			hash_file = hashlib.sha1(open(target_fn, 'rb').read()).hexdigest()
			print('HASH BUFFER: %r' % hash_buffer)
			print('HASH FILE: %r' % hash_file)
			assert hash_buffer == hash_file, ('\n'.join(difflib.context_diff(open(target_fn).read(), extension_buffer, fromfile='filename', tofile='buffer'))) + ('ERROR: sha1 sums of file and BUFFER DIffer (fn=%s ; file=%s ; buffer=%s)' % (target_fn, hash_file, hash_buffer))

			for option_type, src_fn, filename in self.TEST_DATA:
				filename = filename % extension_name.replace('/', '-')
				assert os.path.exists(filename), 'ERROR: file %r of type %r does not exist' % (filename, option_type)
				hash_buffer = hashlib.sha1(buffers[src_fn]).hexdigest()
				hash_file = hashlib.sha1(open(filename, 'rb').read()).hexdigest()
				assert hash_buffer == hash_file, ('\n'.join(difflib.context_diff(open(filename).read(), buffers[src_fn], fromfile='filename', tofile='buffer'))) + ('ERROR: sha1 sums of file and buffer differ (fn=%s ; file=%s ; buffer=%s)' % (filename, hash_file, hash_buffer))

			call_unjoin_script('66%s-uninstall.uinst' % package_name)

			# wait until removed object has been handled by the listener
			wait_for_replication()

			dnlist = get_dn_of_extension_by_name(extension_type, extension_name)
			assert not dnlist, 'ERROR: UDM extension object with cn=%s is still present in LDAP' % extension_name

			# check if registered file has been removed from local system
			assert not os.path.exists(target_fn), 'ERROR: target file %s is still present' % target_fn
			print('FILE HAS BEEN REMOVED: %r' % target_fn)

		finally:
			print('Removing UDM extension from LDAP')
			remove_extension_by_name(extension_type, extension_name, fail_on_error=False)

			print('Uninstalling binary package %r' % package_name)
			package.uninstall()

			print('Removing source package')
			package.remove()

	mo_file = base64.b64decode('''
	3hIElQAAAAAFAAAAHAAAAEQAAAAHAAAAbAAAAAAAAACIAAAADwAAAIkAAAAaAAAAmQAAAB0AAAC0AAAARQAAANIAAA
	A7AQAAGAEAAA8AAABUAgAAGAAAAGQCAAAfAAAAfQIAAEUAAACdAgAAAQAAAAAAAAAEAAAAAwAAAAAAAAACAAAABQAA
	AABLb3Bhbm8gQ29udGFjdHMAS29wYW5vIE5vbi1BY3RpdmUgQWNjb3VudHMATWFuYWdlbWVudCBvZiBLb3Bhbm8gQ2
	9udGFjdHMATWFuYWdlbWVudCBvZiBLb3Bhbm8gbm9uLWFjdGl2ZSBhY2NvdW50cywgcmVzb3VyY2VzIGFuZCBzaGFy
	ZWQgc3RvcmVzAFByb2plY3QtSWQtVmVyc2lvbjoga29wYW5vNHVjcwpSZXBvcnQtTXNnaWQtQnVncy1UbzogClBPVC
	1DcmVhdGlvbi1EYXRlOiAyMDE0LTAzLTI4IDE0OjExKzAxMDAKUE8tUmV2aXNpb24tRGF0ZTogMjAxMi0wMy0yOSAx
	MTo1MSswMjAwCkxhc3QtVHJhbnNsYXRvcjogcGFja2FnZXNAdW5pdmVudGlvbi5kZQpMYW5ndWFnZS1UZWFtOiBHZX
	JtYW4gPGRlQGxpLm9yZz4KTGFuZ3VhZ2U6IGRlCk1JTUUtVmVyc2lvbjogMS4wCkNvbnRlbnQtVHlwZTogdGV4dC9w
	bGFpbjsgY2hhcnNldD1VVEYtOApDb250ZW50LVRyYW5zZmVyLUVuY29kaW5nOiB1bmljb2RlCgBLb3Bhbm8gS29udG
	FrdGUAS29wYW5vIE5vbi1BY3RpdmUgS29udGVuAFZlcndhbHR1bmcgdm9uIEtvcGFubyBLb250YWt0ZW4AVmVyd2Fs
	dHVuZyB2b24gS29wYW5vIG5vbi1hY3RpdmUgS29udGVuLCBSZXNzb3VyY2VuIHVuZCBTaGFyZWQgU3RvcmVzAA==''')

	TEST_DATA_2 = (
		('umcregistration', '72_file_integrity_udm_module.xml', '/usr/share/univention-management-console/modules/udm-%s.xml'),
		('umcmessagecatalog', 'de-ucs-test.mo', '/usr/share/univention-management-console/i18n/de/ucs-test.mo'),
		('umcmessagecatalog', 'fr-ucs-test.mo', '/usr/share/univention-management-console/i18n/fr/ucs-test.mo'),
	)

	@pytest.mark.tags('udm', 'udm-extensions', 'apptest')
	@pytest.mark.roles('domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver')
	@pytest.mark.exposure('dangerous')
	def test_umcmessagecatalog(self):
		"""Register UMCMessageCatalog via joinscript"""
		extension_type = 'module'
		package_name = get_package_name()
		package_version = get_package_version()
		extension_name = get_extension_name(extension_type)
		extension_filename = get_extension_filename(extension_type, extension_name)

		options = {}
		buffers = {}
		for option_type, filename, target_filename in self.TEST_DATA_2:
			buffers[filename] = open('%s/%s' % (CWD, filename), 'rb').read()
			options.setdefault(option_type, []).append('/usr/share/%s/%s' % (package_name, filename))
		joinscript_buffer = get_join_script_buffer(
			extension_type,
			'/usr/share/%s/%s' % (package_name, extension_filename),
			options=options,
			joinscript_version=1,
			version_start=random_ucs_version(max_major=2),
			version_end=random_ucs_version(min_major=5)
		)
		unjoinscript_buffer = get_unjoin_script_buffer(extension_type, extension_name, package_name)
		extension_buffer = get_extension_buffer(extension_type, extension_name)

		package = DebianPackage(name=package_name, version=package_version)
		try:
			# create package and install it
			package.create_join_script_from_buffer('66%s.inst' % package_name, joinscript_buffer)
			package.create_unjoin_script_from_buffer('66%s-uninstall.uinst' % package_name, unjoinscript_buffer)
			package.create_usr_share_file_from_buffer(extension_filename, extension_buffer)
			for fn, data in buffers.items():
				package.create_usr_share_file_from_buffer(fn, data, 'wb')
			package.build()
			package.install()

			call_join_script('66%s.inst' % package_name)

			# wait until removed object has been handled by the listener
			wait_for_replication()

			dnlist = get_dn_of_extension_by_name(extension_type, extension_name)
			assert dnlist, 'ERROR: cannot find UDM extension object with cn=%s in LDAP' % extension_name

			# check if registered file has been replicated to local system
			target_fn = get_absolute_extension_filename(extension_type, extension_filename)
			assert os.path.exists(target_fn), 'ERROR: target file %s does not exist' % target_fn
			print('FILE REPLICATED: %r' % target_fn)

			for option_type, src_fn, filename in self.TEST_DATA_2:
				assert not (option_type == 'umcmessagecatalog' and not os.path.exists(filename)), 'ERROR: file %r of type %r does not exist' % (filename, option_type)
			dnlist = get_dn_of_extension_by_name(extension_type, extension_name)

			verify_ldap_object(dnlist[0], {
				'cn': [extension_name],
				'univentionUMCMessageCatalog;entry-de-ucs-test': [self.mo_file],
				'univentionUMCMessageCatalog;entry-fr-ucs-test': [self.mo_file],
			})

			call_unjoin_script('66%s-uninstall.uinst' % package_name)

		finally:
			print('Removing UDM extension from LDAP')
			remove_extension_by_name(extension_type, extension_name, fail_on_error=False)

			print('Uninstalling binary package %r' % package_name)
			package.uninstall()

			print('Removing source package')
			package.remove()


class Test_UDMExtensions:

	@pytest.mark.tags('udm', 'udm-ldapextensions', 'apptest')
	@pytest.mark.roles('domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver')
	@pytest.mark.exposure('dangerous')
	@pytest.mark.parametrize('extension_type', VALID_EXTENSION_TYPES, indirect=True)
	def test_create_via_udm_cli(self, udm, ucr, extension_type):
		"""Create full UDM extension objects via CLI"""
		print('========================= TESTING EXTENSION %s =============================' % extension_type)
		for active in ['TRUE', 'FALSE']:
			extension_name = get_extension_name(extension_type)
			extension_filename = get_extension_filename(extension_type, extension_name)
			extension_buffer = get_extension_buffer(extension_type, extension_name)

			package_name = get_package_name()
			package_version = get_package_version()
			app_id = '%s-%s' % (random_name(), random_version())
			version_start = random_ucs_version(max_major=2)
			version_end = random_ucs_version(min_major=5)

			dn = udm.create_object(
				'settings/udm_%s' % extension_type,
				name=extension_name,
				data=base64.b64encode(bz2.compress(extension_buffer.encode("UTF-8"))).decode("ASCII"),
				filename=extension_filename,
				packageversion=package_version,
				appidentifier=app_id,
				package=package_name,
				ucsversionstart=version_start,
				ucsversionend=version_end,
				active=active,
				position='cn=udm_%s,cn=univention,%s' % (extension_type, ucr['ldap/base'])
			)

			verify_ldap_object(dn, {
				'cn': [extension_name],
				'univentionUDM%sFilename' % extension_type.capitalize(): [extension_filename],
				'univentionOwnedByPackage': [package_name],
				'univentionObjectType': ['settings/udm_%s' % extension_type],
				'univentionOwnedByPackageVersion': [package_version],
				'univentionUDM%sData' % extension_type.capitalize(): [bz2.compress(extension_buffer.encode('UTF-8'))],
				'univentionAppIdentifier': [app_id],
				'univentionUCSVersionStart': [version_start],
				'univentionUCSVersionEnd': [version_end],
			})

	@pytest.mark.tags('udm', 'udm-ldapextensions', 'apptest')
	@pytest.mark.roles('domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver')
	@pytest.mark.exposure('dangerous')
	@pytest.mark.parametrize('extension_type', VALID_EXTENSION_TYPES, indirect=True)
	@pytest.mark.parametrize('version_start,version_end,should_exist', [
		('1.0-0', '2.4-4', False),   # range below current version
		('6.0-0', '9.9-9', False),   # range above current version
		('4.0-0', '9.9-9', True),    # current version in range
		('1.0-0', '%s-%s' % (ucr.get('version/version'), ucr.get('version/patchlevel')), True),  # upper limit of range is current version
		('%s-%s' % (ucr.get('version/version'), ucr.get('version/patchlevel')), '9.9-9', True),  # lower limit of range is current version
	])
	def test_listener_version_start_end(self, udm, ucr, extension_type, version_start, version_end, should_exist, wait_before):
		"""Create extensions with different version ranges"""

		print('========================= TESTING EXTENSION %s =============================' % extension_type)
		package_name = get_package_name()
		package_version = get_package_version()
		app_id = '%s-%s' % (random_name(), random_version())

		print('=== Testing range from %s to %s with expected result exists=%s ===' % (version_start, version_end, should_exist))
		extension_name = get_extension_name(extension_type)
		extension_filename = get_extension_filename(extension_type, extension_name)
		extension_buffer = get_extension_buffer(extension_type, extension_name)

		udm.create_object(
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
			position='cn=custom attributes,cn=univention,%s' % ucr.get('ldap/base')
		)

		# wait for replication before local filesystem is checked
		wait_for_replication()

		# check if registered file has been replicated to local system
		target_fn = get_absolute_extension_filename(extension_type, extension_filename)
		exists = os.path.exists(target_fn)
		assert not exists != should_exist, 'ERROR: expected filesystem status mismatch (exists=%s should_exist=%s)' % (exists, should_exist)

		# wait for replication before local filesystem is checked
		udm.cleanup()
		wait_for_replication()
		assert not os.path.exists(target_fn), 'ERROR: file %s should not exist' % target_fn

	@pytest.mark.tags('udm', 'udm-ldapextensions', 'apptest')
	@pytest.mark.roles('domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver')
	@pytest.mark.exposure('dangerous')
	@pytest.mark.parametrize('extension_type', VALID_EXTENSION_TYPES, indirect=True)
	def test_rename_object(self, udm, extension_type, ucr):
		"""Rename UDM extension object"""
		print('========================= TESTING EXTENSION %s =============================' % extension_type)
		extension_name = get_extension_name(extension_type)
		extension_filename = get_extension_filename(extension_type, extension_name)
		extension_buffer = get_extension_buffer(extension_type, extension_name)

		package_name = get_package_name()
		package_version = get_package_version()
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
		assert os.path.exists(target_fn), 'ERROR: expected file does not exist (%s)' % (target_fn)

		extension_name2 = random_name()
		if extension_type == 'module':
			extension_name2 = 'ucstest/%s' % extension_name2
		extension_filename2 = get_extension_filename(extension_type, extension_name2)
		expected_dn = dn.replace(extension_name, extension_name2)

		udm.modify_object('settings/udm_%s' % extension_type, dn=dn, name=extension_name2, filename=extension_filename2)
		dnlist = get_dn_of_extension_by_name(extension_type, extension_name2)
		assert dnlist, 'ERROR: rename of udm %s extension object %s to %s failed' % (extension_type, extension_name, extension_name2)
		assert dnlist[0] == expected_dn, 'ERROR: rename successful but expected DN is not equal to actual DN (%r vs %r)' % (expected_dn, dnlist[0])

		# check if registered file is still present with the old name
		target_fn = get_absolute_extension_filename(extension_type, extension_filename)
		target_fn2 = get_absolute_extension_filename(extension_type, extension_filename2)
		assert not os.path.exists(target_fn), 'ERROR: expected file exist (%s) while it should be removed' % (target_fn)
		assert os.path.exists(target_fn2), 'ERROR: expected file does not exist (%s)' % (target_fn2)

		remove_extension_by_name(extension_type, extension_name, fail_on_error=False)
		remove_extension_by_name(extension_type, extension_name2, fail_on_error=False)

		wait_for_replication()

		# check if registered file has been removed
		target_fn = get_absolute_extension_filename(extension_type, extension_filename)
		assert not os.path.exists(target_fn), 'ERROR: file exists unexpectedly (%s)' % (target_fn)

	@pytest.mark.tags('udm', 'udm-ldapextensions', 'apptest')
	@pytest.mark.roles('domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver')
	@pytest.mark.exposure('dangerous')
	@pytest.mark.parametrize('extension_type', VALID_EXTENSION_TYPES, indirect=True)
	def test_listener_check_active(self, udm, extension_type, ucr):
		"""Change active flag to TRUE by domaincontroller master"""
		print('========================= TESTING EXTENSION %s =============================' % extension_type)
		extension_name = get_extension_name(extension_type)
		extension_filename = get_extension_filename(extension_type, extension_name)
		extension_buffer = get_extension_buffer(extension_type, extension_name)

		package_name = get_package_name()
		package_version = get_package_version()
		app_id = '%s-%s' % (random_name(), random_version())
		version_start = random_ucs_version(max_major=2)
		version_end = random_ucs_version(min_major=5)

		dn = udm.create_object(
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

		wait_for_replication_and_postrun()

		verify_ldap_object(dn, {
			'cn': [extension_name],
			'univentionUDM%sFilename' % extension_type.capitalize(): [extension_filename],
			'univentionOwnedByPackage': [package_name],
			'univentionObjectType': ['settings/udm_%s' % extension_type],
			'univentionOwnedByPackageVersion': [package_version],
			'univentionUDM%sData' % extension_type.capitalize(): [bz2.compress(extension_buffer.encode('UTF-8'))],
			'univentionAppIdentifier': [app_id],
			'univentionUCSVersionStart': [version_start],
			'univentionUCSVersionEnd': [version_end],
			'univentionUDM%sActive' % extension_type.capitalize(): ['TRUE'],
		})

	@pytest.mark.tags('udm', 'udm-ldapextensions', 'apptest')
	@pytest.mark.roles('domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver')
	@pytest.mark.exposure('dangerous')
	@pytest.mark.parametrize('extension_type', VALID_EXTENSION_TYPES, indirect=True)
	@pytest.mark.parametrize('version_start,version_end', [
		(random_ucs_version(max_major=2), random_name()),
		(random_name(), random_ucs_version(min_major=5)),
		(random_name(), random_name())
	])
	def test_create_with_invalid_ucsversions(self, udm, extension_type, version_start, version_end):
		"""Create full UDM extension objects via CLI"""
		print('========================= TESTING EXTENSION %s =============================' % extension_type)
		extension_name = get_extension_name(extension_type)
		extension_filename = get_extension_filename(extension_type, extension_name)
		extension_buffer = get_extension_buffer(extension_type, extension_name)

		package_name = get_package_name()
		package_version = get_package_version()
		app_id = '%s-%s' % (random_name(), random_version())

		with pytest.raises(UCSTestUDM_CreateUDMObjectFailed):
			udm.create_object(
				'settings/udm_%s' % extension_type,
				name=extension_name,
				data=base64.b64encode(bz2.compress(extension_buffer.encode("UTF-8"))).decode("ASCII"),
				filename=extension_filename,
				packageversion=package_version,
				appidentifier=app_id,
				package=package_name,
				ucsversionstart=version_start,
				ucsversionend=version_end,
				active='FALSE'
			)

	@pytest.mark.tags('udm', 'udm-ldapextensions', 'apptest')
	@pytest.mark.roles('domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver')
	@pytest.mark.exposure('dangerous')
	@pytest.mark.parametrize('extension_type', VALID_EXTENSION_TYPES, indirect=True)
	def test_file_integrity(self, udm, ucr, extension_type, wait_before):
		"""Check permissions of distributed extension file"""
		print('========================= TESTING EXTENSION %s =============================' % extension_type)
		package_name = get_package_name()
		package_version = get_package_version()
		app_id = '%s-%s' % (random_name(), random_version())
		version_start = random_ucs_version(max_major=2)
		version_end = random_ucs_version(min_major=5)

		extension_name = get_extension_name(extension_type)
		extension_filename = get_extension_filename(extension_type, extension_name)
		extension_buffer = get_extension_buffer(extension_type, extension_name)

		udm.create_object(
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
			position='cn=custom attributes,cn=univention,%s' % ucr.get('ldap/base')
		)

		# wait for replication before local filesystem is checked
		wait_for_replication()

		# check if registered file has been replicated to local system
		target_fn = get_absolute_extension_filename(extension_type, extension_filename)
		assert os.path.exists(target_fn), 'ERROR: expected UDM extension does not exist in filesystem (%s)' % (target_fn, )

		# check if sha1(buffer) == sha1(file)
		hash_buffer = hashlib.sha1(extension_buffer.encode('UTF-8')).hexdigest()
		hash_file = hashlib.sha1(open(target_fn, 'rb').read()).hexdigest()
		assert not hash_buffer != hash_file, 'ERROR: sha1 sums of file and buffer differ (fn=%s ; file=%s ; buffer=%s)' % (target_fn, hash_file, hash_buffer)

		# check replicated file has correct file mode
		current_mode = oct(os.stat(target_fn).st_mode & (stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO))
		expected_mode = '0o644'
		assert not current_mode != expected_mode, 'ERROR: permissions of target file %s are not ok (current=%s  expected=%s)' % (target_fn, current_mode, expected_mode)

		# check replicated file is own by root:nobody
		expected_groups = (0, grp.getgrnam('nogroup').gr_gid)
		expected_uid = 0
		current_uid = os.stat(target_fn).st_uid
		current_group = os.stat(target_fn).st_gid
		assert not (current_uid != expected_uid or current_group not in expected_groups), 'ERROR: owner/group of target file %s is not ok (current=%s:%s  expected_uid=%s expected_gid=%s)' % (target_fn, current_uid, current_group, expected_uid, expected_groups)

		udm.cleanup()
		# wait for replication before local filesystem is checked
		wait_for_replication()
		assert not os.path.exists(target_fn), 'ERROR: file %s should not exist' % target_fn

	@pytest.mark.tags('udm', 'udm-ldapextensions', 'apptest')
	@pytest.mark.roles('domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver')
	@pytest.mark.exposure('dangerous')
	def test_test_py2_and_3_udm_module(self, udm, ucr):
		"""Create UDM module extension object and test it via CLI"""
		extension_type = 'module'
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

		dn = udm.create_object(
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

		wait_for_replication()
		udm.stop_cli_server()

		verify_ldap_object(dn, {
			'cn': [extension_name],
			'univentionUDM%sFilename' % extension_type.capitalize(): [extension_filename],
			'univentionOwnedByPackage': [package_name],
			'univentionObjectType': ['settings/udm_%s' % extension_type],
			'univentionOwnedByPackageVersion': [package_version],
			'univentionUDM%sData' % extension_type.capitalize(): [bz2.compress(extension_buffer.encode('UTF-8'))],
			'univentionUDM%sActive' % extension_type.capitalize(): ['TRUE'],

		})

		output, stderr = subprocess.Popen(['udm', 'modules'], stdout=subprocess.PIPE).communicate()
		assert extension_name.encode('UTF-8') in output, 'ERROR: udm cli server has not been reloaded yet or module registration failed'

		extension_dn = udm.create_object(extension_name, position=ucr.get('ldap/base'), name=object_name)
		udm.remove_object(extension_name, dn=extension_dn)

		udm.__exit__(None, None, None)
		wait_for_replication()
		udm.stop_cli_server()
		udm = udm.__enter__()

		# test if user/user module is still ok after removing UDM module extension
		udm.create_user()

	@pytest.mark.tags('udm', 'udm-ldapextensions', 'apptest')
	@pytest.mark.roles('domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver')
	@pytest.mark.exposure('dangerous')
	def test_test_py3_only_udm_module(self, udm, ucr):
		"""Create Py3-only UDM module extension object and test it via CLI"""
		extension_type = 'module'
		extension_name = get_extension_name(extension_type)
		extension_filename = get_extension_filename(extension_type, extension_name)
		extension_buffer = get_extension_buffer(extension_type, extension_name)
		object_name = random_name()

		package_name = get_package_name()
		package_version = get_package_version()
		app_id = '%s-%s' % (random_name(), random_version())
		version_start = '5.0-0'
		version_end = ''

		udm.create_object(
			'container/cn',
			name='udm_%s' % (extension_type,),
			position='cn=univention,%s' % (ucr['ldap/base'],),
			ignore_exists=True
		)

		dn = udm.create_object(
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

		wait_for_replication()
		udm.stop_cli_server()

		verify_ldap_object(dn, {
			'cn': [extension_name],
			'univentionUDM%sFilename' % extension_type.capitalize(): [extension_filename],
			'univentionOwnedByPackage': [package_name],
			'univentionObjectType': ['settings/udm_%s' % extension_type],
			'univentionOwnedByPackageVersion': [package_version],
			'univentionUDM%sData' % extension_type.capitalize(): [bz2.compress(extension_buffer.encode('UTF-8'))],
			'univentionUDM%sActive' % extension_type.capitalize(): ['TRUE'],

		})

		output, stderr = subprocess.Popen(['udm', 'modules'], stdout=subprocess.PIPE).communicate()
		assert extension_name.encode('UTF-8') in output, 'ERROR: udm cli server has not been reloaded yet or module registration failed'

		extension_dn = udm.create_object(extension_name, position=ucr.get('ldap/base'), name=object_name)
		udm.remove_object(extension_name, dn=extension_dn)

		udm.__exit__(None, None, None)
		wait_for_replication()
		udm.stop_cli_server()
		udm = udm.__enter__()

		# test if user/user module is still ok after removing UDM module extension
		udm.create_user()

	@pytest.mark.tags('udm-ldapextensions')
	@pytest.mark.roles('domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver')
	@pytest.mark.exposure('dangerous')
	def test_keep_but_dont_activate_py2_only_udm_hook(self, udm, ucr):
		"""Create Py2-only UDM hook extension object, expect it to be present in LDAP but not committed locally"""

		extension_type = 'hook'
		extension_name = get_extension_name(extension_type)
		extension_filename = get_extension_filename(extension_type, extension_name)
		extension_buffer = get_extension_buffer(extension_type, extension_name)

		package_name = get_package_name()
		package_version = get_package_version()
		app_id = '%s-%s' % (random_name(), random_version())
		version_start = random_ucs_version(max_major=4)
		version_end = '4.4-99'

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

		udm.create_object(
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

		verify_ldap_object(extension_dn, {
			'cn': [extension_name],
			'univentionUDM%sFilename' % extension_type.capitalize(): [extension_filename],
			'univentionOwnedByPackage': [package_name],
			'univentionObjectType': ['settings/udm_%s' % extension_type],
			'univentionOwnedByPackageVersion': [package_version],
			'univentionUDM%sData' % extension_type.capitalize(): [bz2.compress(extension_buffer.encode('UTF-8'))],
			'univentionUDM%sActive' % extension_type.capitalize(): ['FALSE'],
		})

		assert not os.path.exists('/usr/lib/python2.7/dist-packages/univention/admin/hooks.d/%s' % (extension_filename,))

		udm.cleanup()
		wait_for_replication_and_postrun()
		udm.stop_cli_server()

	@pytest.mark.tags('udm-ldapextensions')
	@pytest.mark.roles('domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver')
	@pytest.mark.exposure('dangerous')
	def test_remove_py2_only_udm_hook(self, udm, ucr):
		"""Create Py2-only UDM hook extension object, expect it to get removed"""

		extension_type = 'hook'
		extension_name = get_extension_name(extension_type)
		extension_filename = get_extension_filename(extension_type, extension_name)
		extension_buffer = get_extension_buffer(extension_type, extension_name)

		package_name = get_package_name()
		package_version = get_package_version()
		app_id = '%s-%s' % (random_name(), random_version())
		version_start = random_ucs_version(max_major=4)
		version_end = ''

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

		udm.create_object(
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

		verify_ldap_object(extension_dn, {
			'cn': [extension_name],
			'univentionUDM%sFilename' % extension_type.capitalize(): [extension_filename],
			'univentionOwnedByPackage': [package_name],
			'univentionObjectType': ['settings/udm_%s' % extension_type],
			'univentionOwnedByPackageVersion': [package_version],
			'univentionUDM%sData' % extension_type.capitalize(): [bz2.compress(extension_buffer.encode('UTF-8'))],
			'univentionUDM%sActive' % extension_type.capitalize(): ['TRUE'],
		}, should_exist=False, retry_count=3, delay=1)

		udm.cleanup()
		wait_for_replication_and_postrun()
		udm.stop_cli_server()

	@pytest.mark.tags('udm-ldapextensions')
	@pytest.mark.roles('domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver')
	@pytest.mark.exposure('dangerous')
	def test_test_py2_and_3_udm_hook(self, udm, ucr):
		"""Create UDM hook extension object and test it via CLI"""
		extension_type = 'hook'
		extension_name = get_extension_name(extension_type)
		extension_filename = get_extension_filename(extension_type, extension_name)
		extension_buffer = get_extension_buffer(extension_type, extension_name)

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

		udm.create_object(
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

		udm.__exit__(None, None, None)
		wait_for_replication_and_postrun()
		udm.stop_cli_server()
		udm = udm.__enter__()

		# test if user/user module is still ok after removing UDM module extension
		# TODO: can't use fixture because of that
		udm.create_user()

	@pytest.mark.tags('udm-ldapextensions')
	@pytest.mark.roles('domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver')
	@pytest.mark.exposure('dangerous')
	def test_test_py3_only_udm_hook(self, udm, ucr):
		"""Create Py3-only UDM hook extension object and test it via CLI"""
		extension_type = 'hook'
		extension_name = get_extension_name(extension_type)
		extension_filename = get_extension_filename(extension_type, extension_name)
		extension_buffer = get_extension_buffer(extension_type, extension_name)

		package_name = get_package_name()
		package_version = get_package_version()
		app_id = '%s-%s' % (random_name(), random_version())
		version_start = '5.0-0'
		version_end = ''

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

		udm.create_object(
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

		udm.__exit__(None, None, None)
		wait_for_replication_and_postrun()
		udm.stop_cli_server()
		udm = udm.__enter__()

		# test if user/user module is still ok after removing UDM module extension
		udm.create_user()

	@pytest.mark.tags('udm', 'udm-ldapextensions', 'apptest')
	@pytest.mark.roles('domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver')
	@pytest.mark.exposure('dangerous')
	def test_keep_but_dont_activate_py2_only_udm_syntax(self, udm, ucr):
		"""Create Py2-only UDM syntax extension object, expect it to get removed"""
		extension_type = 'syntax'
		extension_name = get_extension_name(extension_type)
		extension_filename = get_extension_filename(extension_type, extension_name)
		extension_buffer = get_extension_buffer(extension_type, extension_name)

		package_name = get_package_name()
		package_version = get_package_version()
		app_id = '%s-%s' % (random_name(), random_version())
		version_start = random_ucs_version(max_major=4)
		version_end = '4.4-99'

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

		udm.create_object(
			'settings/extended_attribute',
			position='cn=custom attributes,cn=univention,%s' % ucr.get('ldap/base'),
			objectClass='univentionFreeAttributes',
			groupPosition='1',
			module='users/user',
			overwriteTab='0',
			shortDescription='UCS Test Extended Attribute',
			groupName='UCS TEST: test_udm_syntax',
			valueRequired='0',
			CLIName='ucstest%s' % extension_name.upper(),
			longDescription='UCS Test Extended Attribute',
			doNotSearch='0',
			tabName='UCS TEST',
			syntax=extension_name,
			tabAdvanced='0',
			name='UCStest-syntax-extension-%s' % extension_name,
			mayChange='1',
			multivalue='0',
			ldapMapping='univentionFreeAttribute20',
			notEditable='0',
			tabPosition='1'
		)

		wait_for_replication_and_postrun()

		verify_ldap_object(extension_dn, {
			'cn': [extension_name],
			'univentionUDM%sFilename' % extension_type.capitalize(): [extension_filename],
			'univentionOwnedByPackage': [package_name],
			'univentionObjectType': ['settings/udm_%s' % extension_type],
			'univentionOwnedByPackageVersion': [package_version],
			'univentionUDM%sData' % extension_type.capitalize(): [bz2.compress(extension_buffer.encode('UTF-8'))],
			'univentionUDM%sActive' % extension_type.capitalize(): ['FALSE'],
		})

		assert not os.path.exists('/usr/lib/python2.7/dist-packages/univention/admin/syntax.d/%s' % (extension_filename,))

		udm.cleanup()
		wait_for_replication_and_postrun()
		udm.stop_cli_server()

	@pytest.mark.tags('udm', 'udm-ldapextensions', 'apptest')
	@pytest.mark.roles('domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver')
	@pytest.mark.exposure('dangerous')
	def test_remove_py2_only_udm_syntax(self, udm, ucr):
		"""Create Py2-only UDM syntax extension object, expect it to get removed"""
		extension_type = 'syntax'
		extension_name = get_extension_name(extension_type)
		extension_filename = get_extension_filename(extension_type, extension_name)
		extension_buffer = get_extension_buffer(extension_type, extension_name)

		package_name = get_package_name()
		package_version = get_package_version()
		app_id = '%s-%s' % (random_name(), random_version())
		version_start = random_ucs_version(max_major=4)
		version_end = ''

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

		udm.create_object(
			'settings/extended_attribute',
			position='cn=custom attributes,cn=univention,%s' % ucr.get('ldap/base'),
			objectClass='univentionFreeAttributes',
			groupPosition='1',
			module='users/user',
			overwriteTab='0',
			shortDescription='UCS Test Extended Attribute',
			groupName='UCS TEST: test_udm_syntax',
			valueRequired='0',
			CLIName='ucstest%s' % extension_name.upper(),
			longDescription='UCS Test Extended Attribute',
			doNotSearch='0',
			tabName='UCS TEST',
			syntax=extension_name,
			tabAdvanced='0',
			name='UCStest-syntax-extension-%s' % extension_name,
			mayChange='1',
			multivalue='0',
			ldapMapping='univentionFreeAttribute20',
			notEditable='0',
			tabPosition='1'
		)

		wait_for_replication_and_postrun()

		verify_ldap_object(extension_dn, {
			'cn': [extension_name],
			'univentionUDM%sFilename' % extension_type.capitalize(): [extension_filename],
			'univentionOwnedByPackage': [package_name],
			'univentionObjectType': ['settings/udm_%s' % extension_type],
			'univentionOwnedByPackageVersion': [package_version],
			'univentionUDM%sData' % extension_type.capitalize(): [bz2.compress(extension_buffer.encode('UTF-8'))],
			'univentionUDM%sActive' % extension_type.capitalize(): ['TRUE'],
		}, should_exist=False, retry_count=3, delay=1)

		udm.cleanup()
		wait_for_replication_and_postrun()
		udm.stop_cli_server()

	@pytest.mark.tags('udm', 'udm-ldapextensions', 'apptest')
	@pytest.mark.roles('domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver')
	@pytest.mark.exposure('dangerous')
	def test_test_py2_and_3_udm_syntax(self, udm, ucr):
		"""Create UDM syntax extension object and test it via CLI"""

		extension_type = 'syntax'
		extension_name = get_extension_name(extension_type)
		extension_filename = get_extension_filename(extension_type, extension_name)
		extension_buffer = get_extension_buffer(extension_type, extension_name)

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

		udm.create_object(
			'settings/extended_attribute',
			position='cn=custom attributes,cn=univention,%s' % ucr.get('ldap/base'),
			objectClass='univentionFreeAttributes',
			groupPosition='1',
			module='users/user',
			overwriteTab='0',
			shortDescription='UCS Test Extended Attribute',
			groupName='UCS TEST: test_udm_syntax',
			valueRequired='0',
			CLIName='ucstest%s' % extension_name.upper(),
			longDescription='UCS Test Extended Attribute',
			doNotSearch='0',
			tabName='UCS TEST',
			syntax=extension_name,
			tabAdvanced='0',
			name='UCStest-syntax-extension-%s' % extension_name,
			mayChange='1',
			multivalue='0',
			ldapMapping='univentionFreeAttribute20',
			notEditable='0',
			tabPosition='1'
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

		# create user and set extended attribute with valid value
		value = 'ucstest-%s' % random_name()
		userargs = {'ucstest%s' % extension_name.upper(): value}
		user_dn, username = udm.create_user(**userargs)

		# modify user and set extended attribute with invalid value (according to assigned syntax)
		userargs = {'ucstest%s' % extension_name.upper(): random_name()}
		with pytest.raises(UCSTestUDM_ModifyUDMObjectFailed) as exc:
			udm.modify_object('users/user', dn=user_dn, **userargs)
		assert 'Wrong value given for ucs-test-syntax' in str(exc.value)

		udm.__exit__(None, None, None)
		wait_for_replication_and_postrun()
		udm.stop_cli_server()
		udm = udm.__enter__()

		# test if user/user module is still ok after removing UDM module extension
		udm.create_user()

	@pytest.mark.tags('udm', 'udm-ldapextensions', 'apptest')
	@pytest.mark.roles('domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver')
	@pytest.mark.exposure('dangerous')
	def test_test_py3_only_udm_syntax(self, udm, ucr):
		"""Create Py3-only UDM syntax extension object and test it via CLI"""
		extension_type = 'syntax'
		extension_name = get_extension_name(extension_type)
		extension_filename = get_extension_filename(extension_type, extension_name)
		extension_buffer = get_extension_buffer(extension_type, extension_name)

		package_name = get_package_name()
		package_version = get_package_version()
		app_id = '%s-%s' % (random_name(), random_version())
		version_start = '5.0-0'
		version_end = ''

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

		udm.create_object(
			'settings/extended_attribute',
			position='cn=custom attributes,cn=univention,%s' % ucr.get('ldap/base'),
			objectClass='univentionFreeAttributes',
			groupPosition='1',
			module='users/user',
			overwriteTab='0',
			shortDescription='UCS Test Extended Attribute',
			groupName='UCS TEST: test_udm_syntax',
			valueRequired='0',
			CLIName='ucstest%s' % extension_name.upper(),
			longDescription='UCS Test Extended Attribute',
			doNotSearch='0',
			tabName='UCS TEST',
			syntax=extension_name,
			tabAdvanced='0',
			name='UCStest-syntax-extension-%s' % extension_name,
			mayChange='1',
			multivalue='0',
			ldapMapping='univentionFreeAttribute20',
			notEditable='0',
			tabPosition='1'
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

		# create user and set extended attribute with valid value
		value = 'ucstest-%s' % random_name()
		userargs = {'ucstest%s' % extension_name.upper(): value}
		user_dn, username = udm.create_user(**userargs)

		# modify user and set extended attribute with invalid value (according to assigned syntax)
		userargs = {'ucstest%s' % extension_name.upper(): random_name()}
		with pytest.raises(UCSTestUDM_ModifyUDMObjectFailed) as exc:
			udm.modify_object('users/user', dn=user_dn, **userargs)
		assert 'Wrong value given for ucs-test-syntax' in str(exc.value)

		udm.__exit__(None, None, None)
		wait_for_replication_and_postrun()
		udm.stop_cli_server()
		udm = udm.__enter__()

		# test if user/user module is still ok after removing UDM module extension
		udm.create_user()

	@pytest.mark.tags('udm', 'udm-ldapextensions', 'apptest')
	@pytest.mark.roles('domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver')
	@pytest.mark.exposure('dangerous')
	def test_keep_but_dont_activate_py2_only_udm_module(self, udm, ucr):
		"""Create Py2-only UDM module extension object, expect it to get removed"""
		extension_type = 'module'
		extension_name = get_extension_name(extension_type)
		extension_filename = get_extension_filename(extension_type, extension_name)
		extension_buffer = get_extension_buffer(extension_type, extension_name)

		package_name = get_package_name()
		package_version = get_package_version()
		app_id = '%s-%s' % (random_name(), random_version())
		version_start = random_ucs_version(max_major=4)
		version_end = '4.4-99'

		dn = udm.create_object(
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

		wait_for_replication()

		verify_ldap_object(dn, {
			'cn': [extension_name],
			'univentionUDM%sFilename' % extension_type.capitalize(): [extension_filename],
			'univentionOwnedByPackage': [package_name],
			'univentionObjectType': ['settings/udm_%s' % extension_type],
			'univentionOwnedByPackageVersion': [package_version],
			'univentionUDM%sData' % extension_type.capitalize(): [bz2.compress(extension_buffer.encode('UTF-8'))],
			'univentionUDM%sActive' % extension_type.capitalize(): ['FALSE'],
		})

		assert not os.path.exists('/usr/lib/python2.7/dist-packages/univention/admin/handlers/%s' % (extension_filename,))

		udm.cleanup()
		wait_for_replication()
		udm.stop_cli_server()

	@pytest.mark.tags('udm', 'udm-ldapextensions', 'apptest')
	@pytest.mark.roles('domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver')
	@pytest.mark.exposure('dangerous')
	def test_remove_py2_only_udm_module(self, udm, ucr):
		"""Create Py2-only UDM module extension object, expect it to get removed"""

		extension_type = 'module'
		extension_name = get_extension_name(extension_type)
		extension_filename = get_extension_filename(extension_type, extension_name)
		extension_buffer = get_extension_buffer(extension_type, extension_name)

		package_name = get_package_name()
		package_version = get_package_version()
		app_id = '%s-%s' % (random_name(), random_version())
		version_start = random_ucs_version(max_major=4)
		version_end = ''

		dn = udm.create_object(
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

		wait_for_replication()

		verify_ldap_object(dn, {
			'cn': [extension_name],
			'univentionUDM%sFilename' % extension_type.capitalize(): [extension_filename],
			'univentionOwnedByPackage': [package_name],
			'univentionObjectType': ['settings/udm_%s' % extension_type],
			'univentionOwnedByPackageVersion': [package_version],
			'univentionUDM%sData' % extension_type.capitalize(): [bz2.compress(extension_buffer.encode('UTF-8'))],
			'univentionUDM%sActive' % extension_type.capitalize(): ['TRUE'],
		}, should_exist=False, retry_count=3, delay=1)

		udm.cleanup()
		wait_for_replication()
		udm.stop_cli_server()


@pytest.mark.exposure('dangerous')
@pytest.mark.parametrize('extension_type', VALID_EXTENSION_TYPES, indirect=True)
class Test_UDMExtensionSpecial:

	@pytest.mark.tags('udm', 'udm-extensions', 'apptest')
	@pytest.mark.roles('domaincontroller_master')
	def test_register_deregister_via_postinst(self, extension_type):
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

	current_version = '%(version/version)s-%(version/patchlevel)s' % ucr

	@pytest.mark.tags('udm,udm-ldapextensions')
	@pytest.mark.roles('domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver')
	@pytest.mark.parametrize('version_start,version_end,should_exist', [
		('1.0-0', '1.0-1', False),   # range below current version
		('1.0-0', '3.2-3', False),   # range below current version
		(current_version, current_version, True),    # current version in range
		('7.0-0', '9.9-9', False),   # range above current version
		('1.0-0', '9.9-9', True),    # current version in range
		('1.0-0', current_version, True),  # upper limit of range is current version
		(current_version, '9.9-9', True),  # lower limit of range is current version
		('9.0-0', '9.1-0', False),   # range above current version
	])
	def test_listener_version_change(self, udm, ucr, version_start, version_end, should_exist, extension_type, wait_before):
		"""Change version range of an existing extension"""
		print('========================= TESTING EXTENSION %s =============================' % extension_type)
		package_name = get_package_name()
		package_version = get_package_version()
		app_id = '%s-%s' % (random_name(), random_version())
		dn = None

		print('=== Testing range from %s to %s with expected result exists=%s ===' % (version_start, version_end, should_exist))
		extension_name = get_extension_name(extension_type)
		extension_buffer = get_extension_buffer(extension_type, extension_name)

		properties = {
			'data': base64.b64encode(bz2.compress(extension_buffer.encode('UTF-8'))).decode('ASCII'),
			'filename': '%s.py' % extension_name,
			'packageversion': package_version,
			'appidentifier': app_id,
			'package': package_name,
			'ucsversionstart': version_start,
			'ucsversionend': version_end,
			'position': 'cn=custom attributes,cn=univention,%s' % ucr.get('ldap/base'),
			'active': 'FALSE'}

		if not dn:
			dn = udm.create_object('settings/udm_%s' % extension_type, name=extension_name, **properties)
		else:
			udm.modify_object('settings/udm_%s' % extension_type, dn=dn, **properties)

		# wait for replication before local filesystem is checked
		wait_for_replication()

		# check if registered file has been replicated to local system
		target_fn = get_absolute_extension_filename(extension_type, '%s.py' % extension_name)
		exists = os.path.exists(target_fn)
		assert not exists != should_exist, 'ERROR: expected filesystem status mismatch (exists=%s should_exist=%s)' % (exists, should_exist)

		# wait for replication before local filesystem is checked
		udm.cleanup()
		wait_for_replication()
		assert not os.path.exists(target_fn), 'ERROR: file %s should not exist' % target_fn

	@pytest.mark.tags('udm', 'udm-ldapextensions', 'apptest')
	@pytest.mark.roles('domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver')
	@pytest.mark.exposure('dangerous')
	def test_update_packageversion(self, udm, ucr, extension_type, wait_before):
		"""Change version of an existing extension"""
		print('========================= TESTING EXTENSION %s =============================' % extension_type)
		package_name = get_package_name()
		package_version_base = get_package_version()
		app_id = '%s-%s' % (random_name(), random_version())
		version_start = random_ucs_version(max_major=2)
		version_end = random_ucs_version(min_major=5)
		dn = None

		oldversion = 0
		for newversion in (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 8, 9, 3, 0):
			package_version = '%s-%d' % (package_version_base, newversion)

			extension_name = get_extension_name(extension_type)
			extension_buffer = get_extension_buffer(extension_type, extension_name)

			properties = {
				'data': base64.b64encode(bz2.compress(extension_buffer.encode('UTF-8'))).decode('ASCII'),
				'filename': '%s.py' % extension_name,
				'packageversion': package_version,
				'appidentifier': app_id,
				'package': package_name,
				'ucsversionstart': version_start,
				'ucsversionend': version_end,
				'active': 'FALSE'
			}

			if not dn:
				dn = udm.create_object(
					'settings/udm_%s' % extension_type,
					name=extension_name,
					position=udm.UNIVENTION_CONTAINER,
					**properties
				)
			else:
				try:
					udm.modify_object(
						'settings/udm_%s' % extension_type,
						dn=dn,
						**properties
					)
				except UCSTestUDM_ModifyUDMObjectFailed as ex:
					print('CAUGHT EXCEPTION: %s' % ex)
					if oldversion < newversion:
						raise

			oldversion = newversion

	@pytest.mark.tags('udm', 'udm-ldapextensions', 'apptest')
	@pytest.mark.roles('domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver')
	@pytest.mark.exposure('dangerous')
	def test_filename_attack(self, udm, extension_type, wait_before):
		"""Test liability to a simple filename attack"""

		filename = 'ucs_test_64_filename_attack'
		version_start = random_ucs_version(max_major=2)
		version_end = random_ucs_version(min_major=5)

		print('========================= TESTING EXTENSION %s =============================' % extension_type)
		package_name = get_package_name()
		package_version = get_package_version()
		extension_name = get_extension_name(extension_type)
		extension_buffer = '# THIS IS NOT GOOD!'

		try:
			udm.create_object(
				'settings/udm_%s' % extension_type,
				name=extension_name,
				data=base64.b64encode(bz2.compress(extension_buffer.encode("UTF-8"))).decode("ASCII"),
				filename='../' * 20 + 'tmp/%s' % filename,
				packageversion=package_version,
				package=package_name,
				ucsversionstart=version_start,
				ucsversionend=version_end,
				active='FALSE'
			)
		except UCSTestUDM_CreateUDMObjectFailed:
			print('NOTICE: creating malicious UDM %s extension object failed' % extension_type)
			return  # FIXME: remove from test matrix

		# wait for replication before local filesystem is checked
		wait_for_replication()

		# check if registered file has been replicated to local system
		assert not os.path.exists('/tmp/%s' % filename), 'ERROR: path attack possible'

		assert not os.path.islink('/tmp/%s' % filename), 'ERROR: path attack possible'

		assert not os.path.isfile('/tmp/%s' % filename), 'ERROR: path attack possible'
