#!/usr/share/ucs-test/runner pytest-3
## desc: Create a full ldap schema objects
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
@pytest.mark.parametrize('active', ['TRUE', 'FALSE'])
def test_create_full_ldap_schema(udm, active):
	"""Create a full ldap schema objects"""
	schema_name = uts.random_name()
	filename = '90%s' % uts.random_name()
	data = '# schema test'
	package_version = '99.%s-%s' % (uts.random_int(), uts.random_int())
	package = uts.random_name(),
	appidentifier = '%s' % uts.random_name(),

	schema = udm.create_object(
		'settings/ldapschema',
		position=udm.UNIVENTION_CONTAINER,
		name=schema_name,
		data=base64.b64encode(bz2.compress(data.encode('UTF-8'))).decode('ASCII'),
		filename=filename,
		packageversion=package_version,
		appidentifier=appidentifier,
		package=package[0],
		active=active)

	utils.verify_ldap_object(schema, {
		'cn': [schema_name],
		'univentionLDAPSchemaData': [bz2.compress(data.encode('UTF-8'))],
		'univentionLDAPSchemaFilename': [filename],
		'univentionOwnedByPackage': package,
		'univentionOwnedByPackageVersion': [package_version],
		'univentionAppIdentifier': appidentifier,
		'univentionLDAPSchemaActive': [active],
		'univentionObjectType': ['settings/ldapschema'],
	})
