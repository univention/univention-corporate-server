#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Change version of an existing extension
## tags: [udm,udm-ldapextensions,apptest]
## roles: [domaincontroller_master,domaincontroller_backup,domaincontroller_slave,memberserver]
## exposure: dangerous
## packages:
##   - univention-directory-manager-tools

import base64
import bz2

import pytest

import univention.testing.udm as udm_test
from univention.testing.strings import random_name, random_ucs_version, random_version
from univention.testing.udm_extensions import (
	VALID_EXTENSION_TYPES, get_extension_buffer, get_extension_name, get_package_name, get_package_version,
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
def test_update_packageversion(udm, ucr, extension_type, wait_before):
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
			except udm_test.UCSTestUDM_ModifyUDMObjectFailed as ex:
				print('CAUGHT EXCEPTION: %s' % ex)
				if (oldversion < newversion):
					raise

		oldversion = newversion
