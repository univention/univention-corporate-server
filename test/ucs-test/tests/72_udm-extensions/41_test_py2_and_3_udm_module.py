#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Create UDM module extension object and test it via CLI
## tags: [udm,udm-ldapextensions,apptest]
## roles: [domaincontroller_master,domaincontroller_backup,domaincontroller_slave,memberserver]
## exposure: dangerous
## packages:
##   - univention-directory-manager-tools

import base64
import bz2
import subprocess

import pytest

from univention.testing.strings import random_name, random_ucs_version, random_version
from univention.testing.udm_extensions import (
	get_extension_buffer, get_extension_filename, get_extension_name, get_package_name, get_package_version,
)
from univention.testing.utils import verify_ldap_object, wait_for_replication


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
