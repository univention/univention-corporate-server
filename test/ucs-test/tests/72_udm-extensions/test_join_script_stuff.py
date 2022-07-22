#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Test joinscript stuff and so on #TODO: fix description
## tags: [udm,udm-extensions,apptest]
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

import pytest

from univention.testing.debian_package import DebianPackage
from univention.testing.strings import random_name, random_ucs_version, random_version
from univention.testing.udm_extensions import (
	VALID_EXTENSION_TYPES,
	call_join_script,
	call_unjoin_script,
	get_absolute_extension_filename,
	get_dn_of_extension_by_name,
	get_extension_buffer,
	get_extension_filename,
	get_extension_name,
	get_join_script_buffer,
	get_package_name,
	get_package_version,
	get_unjoin_script_buffer,
	remove_extension_by_name,
)
from univention.testing.utils import verify_ldap_object, wait_for_replication


@pytest.mark.tags('udm', 'udm-extensions', 'apptest')
@pytest.mark.roles('domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver')
@pytest.mark.exposure('dangerous')
@pytest.mark.parametrize('extension_type', VALID_EXTENSION_TYPES)
def test_register_deregister_via_joinscript(extension_type):
	"""Register and deregister UDM extension via joinscript"""
	print('========================= TESTING EXTENSION %s =============================' % extension_type)
	package_name = get_package_name()
	package_version = get_package_version()
	extension_name = get_extension_name(extension_type)
	extension_filename = get_extension_filename(extension_type, extension_name)
	joinscript_buffer = get_join_script_buffer(extension_type, '/usr/share/%s/%s' % (package_name, extension_filename), version_start='5.0-0')
	unjoinscript_buffer = get_unjoin_script_buffer(extension_type, extension_name, package_name)
	extension_buffer = get_extension_buffer(extension_type, extension_name)

	package = DebianPackage(name=package_name, version=package_version)
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
@pytest.mark.parametrize('extension_type', VALID_EXTENSION_TYPES)
def test_register_and_verify_ldap_object(extension_type):
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
@pytest.mark.parametrize('extension_type', VALID_EXTENSION_TYPES)
def test_register_and_verify_test_app_id(extension_type):
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
@pytest.mark.parametrize('extension_type', VALID_EXTENSION_TYPES)
def test_register_and_verify_version_start_end(extension_type):
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


@pytest.mark.tags('udm', 'udm-extensions', 'apptest')
@pytest.mark.roles('domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver')
@pytest.mark.exposure('dangerous')
def test_register_and_verify_all():
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
def test_register_with_special_name_and_verify_all():
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
@pytest.mark.parametrize('extension_type', VALID_EXTENSION_TYPES)
def test_update_extension_via_package(extension_type):
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
@pytest.mark.parametrize('extension_type', VALID_EXTENSION_TYPES)
def test_update_extension_via_package_expected_fail(extension_type):
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
@pytest.mark.parametrize('extension_type', VALID_EXTENSION_TYPES)
def test_update_extension_via_other_packagename(extension_type):
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
	('umcregistration', '32_file_integrity_udm_module.xml', '/usr/share/univention-management-console/modules/udm-%s.xml'),
	('icon', '32_file_integrity_udm_module-16.png', '/usr/share/univention-management-console-frontend/js/dijit/themes/umc/icons/16x16/udm-%s.png'),
	('icon', '32_file_integrity_udm_module-50.png', '/usr/share/univention-management-console-frontend/js/dijit/themes/umc/icons/50x50/udm-%s.png'),
	('messagecatalog', 'it.mo', '/usr/share/locale/it/LC_MESSAGES/univention-admin-handlers-%s.mo'),
	('messagecatalog', 'de.mo', '/usr/share/locale/de/LC_MESSAGES/univention-admin-handlers-%s.mo'),
	('messagecatalog', 'es.mo', '/usr/share/locale/es/LC_MESSAGES/univention-admin-handlers-%s.mo'),
)


@pytest.mark.tags('udm', 'udm-extensions', 'apptest')
@pytest.mark.roles('domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver')
@pytest.mark.exposure('dangerous')
def test_file_integrity_udm_module():
	"""Register and deregister UDM extension via joinscript"""
	extension_type = 'module'
	package_name = get_package_name()
	package_version = get_package_version()
	extension_name = get_extension_name(extension_type)
	extension_filename = get_extension_filename(extension_type, extension_name)

	options = {}
	buffers = {}
	for option_type, filename, target_filename in TEST_DATA:
		buffers[filename] = open('/usr/share/ucs-test/72_udm-extensions/%s' % filename, 'rb').read()
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

		for option_type, src_fn, filename in TEST_DATA:
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

TEST_DATA = (
	('umcregistration', '32_file_integrity_udm_module.xml', '/usr/share/univention-management-console/modules/udm-%s.xml'),
	('umcmessagecatalog', 'de-ucs-test.mo', '/usr/share/univention-management-console/i18n/de/ucs-test.mo'),
	('umcmessagecatalog', 'fr-ucs-test.mo', '/usr/share/univention-management-console/i18n/fr/ucs-test.mo'),
)


@pytest.mark.tags('udm', 'udm-extensions', 'apptest')
@pytest.mark.roles('domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver')
@pytest.mark.exposure('dangerous')
def test_umcmessagecatalog():
	"""Register UMCMessageCatalog via joinscript"""
	extension_type = 'module'
	package_name = get_package_name()
	package_version = get_package_version()
	extension_name = get_extension_name(extension_type)
	extension_filename = get_extension_filename(extension_type, extension_name)

	options = {}
	buffers = {}
	for option_type, filename, target_filename in TEST_DATA:
		buffers[filename] = open('/usr/share/ucs-test/72_udm-extensions/%s' % filename, 'rb').read()
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

		for option_type, src_fn, filename in TEST_DATA:
			assert not (option_type == 'umcmessagecatalog' and not os.path.exists(filename)), 'ERROR: file %r of type %r does not exist' % (filename, option_type)
		dnlist = get_dn_of_extension_by_name(extension_type, extension_name)

		verify_ldap_object(dnlist[0], {
			'cn': [extension_name],
			'univentionUMCMessageCatalog;entry-de-ucs-test': [mo_file],
			'univentionUMCMessageCatalog;entry-fr-ucs-test': [mo_file],
		})

		call_unjoin_script('66%s-uninstall.uinst' % package_name)

	finally:
		print('Removing UDM extension from LDAP')
		remove_extension_by_name(extension_type, extension_name, fail_on_error=False)

		print('Uninstalling binary package %r' % package_name)
		package.uninstall()

		print('Removing source package')
		package.remove()
