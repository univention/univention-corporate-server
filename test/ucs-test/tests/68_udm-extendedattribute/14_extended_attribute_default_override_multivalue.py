#!/usr/share/ucs-test/runner pytest-3
## desc: Default value of multi value settings/extended_attribute is overridden by explicitly given values
## tags: [udm]
## roles: [domaincontroller_master]
## exposure: careful
## packages:
##   - univention-config
##   - univention-directory-manager-tools


import univention.testing.strings as uts
import univention.testing.utils as utils
import pytest


class Test_UDMExtension(object):
	@pytest.mark.tags('udm')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	def test_extended_attribute_default_override_multivalue(self, udm):
		"""Default value of multi value settings/extended_attribute is overridden by explicitly given values"""
		properties = {
			'name': uts.random_name(),
			'shortDescription': uts.random_string(),
			'CLIName': uts.random_name(),
			'module': 'users/user',
			'objectClass': 'univentionFreeAttributes',
			'ldapMapping': 'univentionFreeAttribute15',
			'multivalue': '1',
			'default': uts.random_string()
		}

		extended_attribute = udm.create_object('settings/extended_attribute', position=udm.UNIVENTION_CONTAINER, **properties)

		extended_attribute_value = uts.random_string()
		user = udm.create_user(**{properties['CLIName']: extended_attribute_value})[0]
		utils.verify_ldap_object(user, {properties['ldapMapping']: [extended_attribute_value]})
