#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Change version range of an existing extension
## tags: [udm.udm-ldapextensions]
## roles: [domaincontroller_master,domaincontroller_backup,domaincontroller_slave,memberserver]
## exposure: dangerous
## packages:
##   - univention-directory-manager-tools
## bugs:
##   - 38752

import base64
import bz2
import os

import pytest

from univention.config_registry import ucr
from univention.testing.strings import random_name, random_version
from univention.testing.udm_extensions import (
	VALID_EXTENSION_TYPES, get_absolute_extension_filename, get_extension_buffer, get_extension_name,
	get_package_name, get_package_version,
)
from univention.testing.utils import wait_for_replication

current_version = '%(version/version)s-%(version/patchlevel)s' % ucr


@pytest.fixture
def wait_before(wait_for_replication):
	yield
	# wait for replicate before test starts
	wait_for_replication()


@pytest.mark.tags('udm,udm-ldapextensions')
@pytest.mark.roles('domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver')
@pytest.mark.exposure('dangerous')
@pytest.mark.parametrize('extension_type', VALID_EXTENSION_TYPES)
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
def test_listener_version_change(udm, ucr, version_start, version_end, should_exist, extension_type, wait_before):
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
