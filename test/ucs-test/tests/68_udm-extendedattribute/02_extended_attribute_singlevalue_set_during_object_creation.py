#!/usr/share/ucs-test/runner pytest-3
## desc: Set settings/extended_attribute value during object creation
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
	def test_extended_attribute_singlevalue_set_during_object_creation(self, udm, properties):
		"""Set settings/extended_attribute value during object creation"""

		extended_attribute = udm.create_object('settings/extended_attribute', position=udm.UNIVENTION_CONTAINER, **properties)

		# create user object with extended attribute set
		extended_attribute_value = uts.random_string()
		user = udm.create_user(**{properties['CLIName']: extended_attribute_value})[0]
		utils.verify_ldap_object(user, {properties['ldapMapping']: [extended_attribute_value]})
