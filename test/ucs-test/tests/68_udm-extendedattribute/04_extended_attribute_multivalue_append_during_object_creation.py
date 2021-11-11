#!/usr/share/ucs-test/runner pytest-3
## desc: Append multivalue settings/extended_attribute values to object
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
	def test_extended_attribute_multivalue_append_during_object_creation(self, udm):
		"""Append multivalue settings/extended_attribute values to object"""
		properties = {
			'name': uts.random_name(),
			'shortDescription': uts.random_string(),
			'CLIName': uts.random_name(),
			'module': 'users/user',
			'objectClass': 'univentionFreeAttributes',
			'ldapMapping': 'univentionFreeAttribute15',
			'multivalue': '1'
		}

		extended_attribute = udm.create_object('settings/extended_attribute', position=udm.UNIVENTION_CONTAINER, **properties)

		# create user object and set extended attribute
		extended_attribute_values = [uts.random_string(), uts.random_string()]
		user = udm.create_user(append={properties['CLIName']: extended_attribute_values})[0]
		utils.verify_ldap_object(user, {properties['ldapMapping']: extended_attribute_values})
