#!/usr/share/ucs-test/runner pytest-3
## desc: Create a valid ldap schema object
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
def test_create_ldap_schema(udm):
	"""Create a valid ldap schema object"""
	schema_name = uts.random_name()
	filename = '90%s' % uts.random_name()
	data = '# schema test'
	schema = udm.create_object('settings/ldapschema', position=udm.UNIVENTION_CONTAINER, name=schema_name, filename=filename, data=(base64.b64encode(bz2.compress(data.encode('UTF-8')))).decode('ASCII'))
	utils.verify_ldap_object(schema, {'cn': [schema_name]})

	udm.remove_object('settings/ldapschema', dn=schema)
	with pytest.raises(utils.LDAPObjectNotFound):
		utils.verify_ldap_object(schema, {'cn': [schema_name]}, retry_count=1)
