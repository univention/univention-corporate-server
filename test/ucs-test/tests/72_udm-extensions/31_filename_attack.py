#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Test liability to a simple filename attack
## tags: [udm,udm-ldapextensions,apptest]
## roles: [domaincontroller_master,domaincontroller_backup,domaincontroller_slave,memberserver]
## exposure: dangerous
## packages:
##   - univention-directory-manager-tools

import base64
import bz2
import os

import pytest

import univention.testing.udm as udm_test
from univention.testing.strings import random_ucs_version
from univention.testing.udm_extensions import (
	VALID_EXTENSION_TYPES, get_extension_name, get_package_name, get_package_version,
)
from univention.testing.utils import wait_for_replication


@pytest.fixture
def wait_before(wait_for_replication):
	yield
	# wait for replicate before test starts
	wait_for_replication()


@pytest.mark.tags('udm', 'udm-ldapextensions', 'apptest')
@pytest.mark.roles('domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver')
@pytest.mark.exposure('dangerous')
@pytest.mark.parametrize('extension_type', VALID_EXTENSION_TYPES)
def test_filename_attack(udm, extension_type, wait_before):
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
	except udm_test.UCSTestUDM_CreateUDMObjectFailed:
		print('NOTICE: creating malicious UDM %s extension object failed' % extension_type)
		return  # FIXME: remove from test matrix

	# wait for replication before local filesystem is checked
	wait_for_replication()

	# check if registered file has been replicated to local system
	assert not os.path.exists('/tmp/%s' % filename), 'ERROR: path attack possible'

	assert not os.path.islink('/tmp/%s' % filename), 'ERROR: path attack possible'

	assert not os.path.isfile('/tmp/%s' % filename), 'ERROR: path attack possible'
