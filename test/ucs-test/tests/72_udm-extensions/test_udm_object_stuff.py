#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Create full UDM extension objects via CLI
## tags: [udm,udm-ldapextensions,apptest]
## roles: [domaincontroller_master,domaincontroller_backup,domaincontroller_slave,memberserver]
## exposure: dangerous
## packages:
##   - univention-directory-manager-tools

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
# TODO: refactor so that this is no longer needed. use udm_extensions instead!
from univention.testing.strings import random_name, random_ucs_version, random_version
from univention.testing.udm import UCSTestUDM_CreateUDMObjectFailed, UCSTestUDM_ModifyUDMObjectFailed
from univention.testing.udm_extensions import (
	VALID_EXTENSION_TYPES,
	call_cmd,
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
from univention.testing.utils import(
	verify_ldap_object,
	wait_for_replication,
	wait_for_replication_and_postrun,
	wait_for_s4connector_replication
)


@pytest.fixture
def wait_before(wait_for_replication):
	yield
	# wait for replicate before test starts
	wait_for_replication()


@pytest.mark.tags('udm', 'udm-ldapextensions', 'apptest')
@pytest.mark.roles('domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver')
@pytest.mark.exposure('dangerous')
@pytest.mark.parametrize('extension_type', VALID_EXTENSION_TYPES)
def test_create_via_udm_cli(udm, ucr, extension_type):
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
@pytest.mark.parametrize('extension_type', VALID_EXTENSION_TYPES)
@pytest.mark.parametrize('version_start,version_end,should_exist', [
	('1.0-0', '2.4-4', False),   # range below current version
	('6.0-0', '9.9-9', False),   # range above current version
	('4.0-0', '9.9-9', True),    # current version in range
	('1.0-0', '%s-%s' % (ucr.get('version/version'), ucr.get('version/patchlevel')), True),  # upper limit of range is current version
	('%s-%s' % (ucr.get('version/version'), ucr.get('version/patchlevel')), '9.9-9', True),  # lower limit of range is current version
])
def test_listener_version_start_end(udm, ucr, extension_type, version_start, version_end, should_exist, wait_before):
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
@pytest.mark.parametrize('extension_type', VALID_EXTENSION_TYPES)
def test_rename_object(udm, extension_type, ucr):
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
@pytest.mark.parametrize('extension_type', VALID_EXTENSION_TYPES)
def test_listener_check_active(udm, extension_type, ucr):
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
@pytest.mark.parametrize('extension_type', VALID_EXTENSION_TYPES)
@pytest.mark.parametrize('version_start,version_end', [
	(random_ucs_version(max_major=2), random_name()),
	(random_name(), random_ucs_version(min_major=5)),
	(random_name(), random_name())
])
def test_create_with_invalid_ucsversions(udm, extension_type, version_start, version_end):
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
@pytest.mark.parametrize('extension_type', VALID_EXTENSION_TYPES)
def test_file_integrity(udm, ucr, extension_type, wait_before):
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
def test_test_py2_and_3_udm_module(udm, ucr):
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
def test_test_py3_only_udm_module(udm, ucr):
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
def test_keep_but_dont_activate_py2_only_udm_hook(udm, ucr):
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

	assert(not os.path.exists('/usr/lib/python2.7/dist-packages/univention/admin/hooks.d/%s' % (extension_filename,)))

	udm.cleanup()
	wait_for_replication_and_postrun()
	udm.stop_cli_server()


@pytest.mark.tags('udm-ldapextensions')
@pytest.mark.roles('domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver')
@pytest.mark.exposure('dangerous')
def test_remove_py2_only_udm_hook(udm, ucr):
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
def test_test_py2_and_3_udm_hook(udm, ucr):
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
def test_test_py3_only_udm_hook(udm, ucr):
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
def test_keep_but_dont_activate_py2_only_udm_syntax(udm, ucr):
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

	assert(not os.path.exists('/usr/lib/python2.7/dist-packages/univention/admin/syntax.d/%s' % (extension_filename,)))

	udm.cleanup()
	wait_for_replication_and_postrun()
	udm.stop_cli_server()


@pytest.mark.tags('udm', 'udm-ldapextensions', 'apptest')
@pytest.mark.roles('domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver')
@pytest.mark.exposure('dangerous')
def test_remove_py2_only_udm_syntax(udm, ucr):
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
def test_test_py2_and_3_udm_syntax(udm, ucr):
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
def test_test_py3_only_udm_syntax(udm, ucr):
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
def test_keep_but_dont_activate_py2_only_udm_module(udm, ucr):
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

	assert(not os.path.exists('/usr/lib/python2.7/dist-packages/univention/admin/handlers/%s' % (extension_filename,)))

	udm.cleanup()
	wait_for_replication()
	udm.stop_cli_server()


@pytest.mark.tags('udm', 'udm-ldapextensions', 'apptest')
@pytest.mark.roles('domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver')
@pytest.mark.exposure('dangerous')
def test_remove_py2_only_udm_module(udm, ucr):
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
