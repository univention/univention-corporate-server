#!/usr/share/ucs-test/runner pytest-3
## desc: Remove settings/extended_attribute
## tags: [udm]
## roles: [domaincontroller_master]
## exposure: careful
## packages:
##   - univention-config
##   - univention-directory-manager-tools


import univention.testing.strings as uts
import univention.testing.utils as utils
import pytest


@pytest.fixture
def properties():
	return {
		'name': uts.random_name(),
		'shortDescription': uts.random_string(),
		'CLIName': uts.random_name(),
		'module': 'users/user',
		'objectClass': 'univentionFreeAttributes',
		'ldapMapping': 'univentionFreeAttribute15'
	}


class Test_UDMExtension(object):
	@pytest.mark.tags('udm')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	def test_extended_attribute_removal(self, udm, properties):
		"""Remove settings/extended_attribute"""

		extended_attribute = udm.create_object('settings/extended_attribute', position=udm.UNIVENTION_CONTAINER, **properties)

		udm.remove_object('settings/extended_attribute', dn=extended_attribute)
		utils.verify_ldap_object(extended_attribute, should_exist=False)
