#!/usr/share/ucs-test/runner pytest-3
## desc: Create a full ldap acl objects
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
def test_create_full_ldap_acl(udm, active):
	"""Create a full ldap acl objects"""
	acl_name = uts.random_name()
	filename = '90%s' % uts.random_name()
	data = '# acl test'
	package_version = '99.%s-%s' % (uts.random_int(), uts.random_int())
	package = uts.random_name(),
	appidentifier = '%s' % uts.random_name(),
	ucsversionstart = '1.2-0'
	ucsversionend = '1.3-99'

	acl = udm.create_object(
		'settings/ldapacl',
		position=udm.UNIVENTION_CONTAINER,
		name=acl_name,
		data=base64.b64encode(bz2.compress(data.encode('UTF-8'))).decode('ASCII'),
		filename=filename,
		package=package[0],
		packageversion=package_version,
		appidentifier=appidentifier,
		ucsversionstart=ucsversionstart,
		ucsversionend=ucsversionend,
		active=active)

	utils.verify_ldap_object(acl, {
		'cn': [acl_name],
		'univentionLDAPACLData': [bz2.compress(data.encode('UTF-8'))],
		'univentionLDAPACLFilename': [filename],
		'univentionOwnedByPackage': package,
		'univentionOwnedByPackageVersion': [package_version],
		'univentionAppIdentifier': appidentifier,
		'univentionUCSVersionStart': [ucsversionstart],
		'univentionUCSVersionEnd': [ucsversionend],
		'univentionLDAPACLActive': [active],
		'univentionObjectType': ['settings/ldapacl'],
	})
