#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Create Py3-only UDM syntax extension object and test it via CLI
## tags: [udm,udm-ldapextensions,apptest]
## roles: [domaincontroller_master,domaincontroller_backup,domaincontroller_slave,memberserver]
## exposure: dangerous
## packages:
##   - univention-directory-manager-tools

import base64
import bz2

import pytest

import univention.testing.udm as udm_test
from univention.testing.strings import random_name, random_version
from univention.testing.udm_extensions import (
	get_extension_buffer, get_extension_filename, get_extension_name, get_package_name, get_package_version,
)
from univention.testing.utils import verify_ldap_object, wait_for_replication_and_postrun


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
	with pytest.raises(udm_test.UCSTestUDM_ModifyUDMObjectFailed) as exc:
		udm.modify_object('users/user', dn=user_dn, **userargs)
	assert 'Wrong value given for ucs-test-syntax' in str(exc.value)

	udm.__exit__(None, None, None)
	wait_for_replication_and_postrun()
	udm.stop_cli_server()
	udm = udm.__enter__()

	# test if user/user module is still ok after removing UDM module extension
	udm.create_user()
