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
	print('========================= TESTING EXTENSION %s =============================' % extension_type)
	return request.param


@pytest.fixture
def version_start(request):
	return request.param


@pytest.fixture
def version_end(request):
	return request.param


@pytest.fixture
def active(request):
	return request.param


@pytest.fixture
def wait_before(wait_for_replication):
	yield
	# wait for replicate before test starts
	wait_for_replication()


@pytest.fixture
def package_name():
	return get_package_name()


@pytest.fixture
def package_version():
	return get_package_version()


@pytest.fixture
def extension_name(extension_type):
	extension_name = get_extension_name(extension_type)
	yield extension_name

	print('Removing UDM extension from LDAP')
	remove_extension_by_name(extension_type, extension_name, fail_on_error=False)


@pytest.fixture
def extension_filename(extension_type, extension_name):
	return get_extension_filename(extension_type, extension_name)


@pytest.fixture
def joinscript_buffer(extension_type, package_name, extension_filename):
	return get_join_script_buffer(extension_type, '/usr/share/%s/%s' % (package_name, extension_filename), version_start='5.0-0')


@pytest.fixture
def extension_buffer(extension_type, extension_name):
	return get_extension_buffer(extension_type, extension_name)


@pytest.fixture
def package(package_name, package_version):
	package = DebianPackage(name=package_name, version=package_version)
	yield package

	print('Uninstalling binary package %r' % package_name)
	package.uninstall()

	print('Removing source package')
	package.remove()


@pytest.fixture
def app_id():
	return '%s-%s' % (random_name(), random_version())


@pytest.fixture
def extension_dn(udm, ucr, extension_type, extension_name, extension_buffer, extension_filename, package_version, package_name, app_id, version_start, version_end):
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

	return dn


@pytest.mark.tags('udm', 'udm-extensions', 'apptest')
@pytest.mark.roles('domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver')
@pytest.mark.exposure('dangerous')
class Test_UDMExtensionsJoinscript:

	@pytest.mark.parametrize('extension_type', VALID_EXTENSION_TYPES, indirect=True)
	def test_register_and_verify_ldap_object(self, extension_type, package_name, package_version, extension_name, extension_filename, joinscript_buffer, extension_buffer, package):
		"""Register UDM extension and perform simple LDAP verification"""
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


class Test_UDMExtensions:

	@pytest.mark.tags('udm', 'udm-ldapextensions', 'apptest')
	@pytest.mark.roles('domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver')
	@pytest.mark.exposure('dangerous')
	@pytest.mark.parametrize('extension_type', VALID_EXTENSION_TYPES, indirect=True)
	@pytest.mark.parametrize('version_start, version_end, active', [(random_ucs_version(max_major=2), random_ucs_version(min_major=5), 'FALSE')], indirect=True)
	def test_listener_check_active(self, udm, extension_type, version_start, version_end, extension_name, extension_filename, extension_buffer, package_name, package_version, app_id, extension_dn, active):
		"""Change active flag to TRUE by domaincontroller master"""

		wait_for_replication_and_postrun()

		verify_ldap_object(extension_dn, {
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
