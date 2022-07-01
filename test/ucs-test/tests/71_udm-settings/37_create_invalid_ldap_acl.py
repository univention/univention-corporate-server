#!/usr/share/ucs-test/runner pytest-3
## desc: Try to create invalid ldap acl objects
## tags: [udm-ldapextensions,apptest]
## roles: [domaincontroller_master]
## exposure: dangerous
## packages:
##   - univention-directory-manager-tools

import base64
import bz2

import pytest

import univention.testing.strings as uts
import univention.testing.udm as udm_test


@pytest.mark.tags('udm-ldapextensions', 'apptest')
@pytest.mark.roles('domaincontroller_master')
@pytest.mark.exposure('dangerous')
def test_create_invalid_ldap_acl(udm):
	"""Try to create invalid ldap acl objects"""
	acl_name = uts.random_name()
	filename = '/90%s' % uts.random_name()
	data = '# acl test'
	with pytest.raises(udm_test.UCSTestUDM_CreateUDMObjectFailed):
		udm.create_object('settings/ldapacl', name=acl_name, filename=filename, data=base64.b64encode(bz2.compress(data.encode('UTF-8'))).decode('ASCII'))

	acl_name = uts.random_name()
	filename = '90%s' % uts.random_name()
	data = '# acl test'
	with pytest.raises(udm_test.UCSTestUDM_CreateUDMObjectFailed):
		udm.create_object('settings/ldapacl', name=acl_name, filename=filename, data=base64.b64encode(data.encode('UTF-8')).decode('ASCII'))

	acl_name = uts.random_name()
	filename = '90%s' % uts.random_name()
	data = '# acl test'
	with pytest.raises(udm_test.UCSTestUDM_CreateUDMObjectFailed):
		udm.create_object('settings/ldapacl', name=acl_name, filename=filename, data=base64.b64encode(bz2.compress(data.encode('UTF-8'))).decode('ASCII'), active='YES')
