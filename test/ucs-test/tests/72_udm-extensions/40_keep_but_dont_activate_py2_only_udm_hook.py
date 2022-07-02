#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Create Py2-only UDM hook extension object, expect it to be present in LDAP but not committed locally
## tags: [udm-ldapextensions]
## roles: [domaincontroller_master,domaincontroller_backup,domaincontroller_slave,memberserver]
## exposure: dangerous
## packages:
##   - univention-directory-manager-tools

import base64
import bz2
import os

import pytest

from univention.testing.strings import random_name, random_ucs_version, random_version
from univention.testing.udm_extensions import (
	get_extension_buffer, get_extension_filename, get_extension_name, get_package_name, get_package_version,
)
from univention.testing.utils import verify_ldap_object, wait_for_replication_and_postrun


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
