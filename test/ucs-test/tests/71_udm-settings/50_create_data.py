#!/usr/share/ucs-test/runner pytest-3
## desc: Create a settings/data object
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


@pytest.mark.roles('domaincontroller_master')
@pytest.mark.tags('udm-ldapextensions', 'apptest')
@pytest.mark.exposure('dangerous')
def test_create_data(udm, ucr):
	"""Create a settings/data object"""
	data = uts.random_name(500)
	kwargs = dict(
		position='cn=data,cn=univention,{}'.format(ucr['ldap/base']),
		name=uts.random_name(),
		filename=uts.random_name(),
		description=uts.random_name(),
		data_type=uts.random_name(),
		data=base64.b64encode(bz2.compress(data.encode('UTF-8'))).decode('ASCII'),
		ucsversionstart=uts.random_ucs_version(),
		ucsversionend=uts.random_ucs_version(),
		meta=[uts.random_name(), uts.random_name()],
		package=uts.random_name(),
		packageversion=uts.random_version(),
	)

	dn = udm.create_object('settings/data', **kwargs)

	utils.verify_ldap_object(
		dn,
		{
			'cn': [kwargs['name']],
			'description': [kwargs['description']],
			'univentionDataFilename': [kwargs['filename']],
			'univentionDataType': [kwargs['data_type']],
			'univentionData': [bz2.compress(data.encode('UTF-8'))],
			'univentionUCSVersionStart': [kwargs['ucsversionstart']],
			'univentionUCSVersionEnd': [kwargs['ucsversionend']],
			'univentionDataMeta': kwargs['meta'],
			'univentionOwnedByPackage': [kwargs['package']],
			'univentionOwnedByPackageVersion': [kwargs['packageversion']],
		}
	)
