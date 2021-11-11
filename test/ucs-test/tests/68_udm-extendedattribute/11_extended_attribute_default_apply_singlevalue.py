#!/usr/share/ucs-test/runner pytest-3
## desc: Default value gets applied for single value settings/extended_attribute when a value is not explicitly given
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
	def test_extended_attribute_default_apply_singlevalue(self, udm):
		"""Default value gets applied for single value settings/extended_attribute when a value is not explicitly given"""
		properties = {
			'name': uts.random_name(),
			'shortDescription': uts.random_string(),
			'CLIName': uts.random_name(),
			'module': 'users/user',
			'objectClass': 'univentionFreeAttributes',
			'ldapMapping': 'univentionFreeAttribute15',
			'default': uts.random_string()
		}

		extended_attribute = udm.create_object('settings/extended_attribute', position=udm.UNIVENTION_CONTAINER, **properties)

		user = udm.create_user()[0]
		utils.verify_ldap_object(user, {properties['ldapMapping']: [properties['default']]})
