#!/usr/share/ucs-test/runner pytest-3
## desc: Create a valid ldap acl object
## tags: [udm-ldapextensions,apptest]
## roles: [domaincontroller_master]
## exposure: dangerous
## packages:
##   - univention-directory-manager-tools

import base64
import bz2

import pytest

import univention.testing.strings as uts
import univention.testing.utils as utils


@pytest.mark.tags('udm-ldapextensions', 'apptest')
@pytest.mark.roles('domaincontroller_master')
@pytest.mark.exposure('dangerous')
def test_create_ldap_acl(udm):
	"""Create a valid ldap acl object"""
	acl_name = uts.random_name()
	filename = '90%s' % uts.random_name()
	data = '# access to  *'
	acl = udm.create_object('settings/ldapacl', position=udm.UNIVENTION_CONTAINER, name=acl_name, filename=filename, data=base64.b64encode(bz2.compress(data.encode('UTF-8'))).decode('ASCII'))
	utils.verify_ldap_object(acl, {'cn': [acl_name]})

	udm.remove_object('settings/ldapacl', dn=acl)
	with pytest.raises(utils.LDAPObjectNotFound):
		utils.verify_ldap_object(acl, {'cn': [acl_name]}, retry_count=1)
