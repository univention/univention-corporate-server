#!/usr/share/ucs-test/runner pytest-3
## desc: Remove required settings/extended_attribute single value
## tags: [udm]
## roles: [domaincontroller_master]
## exposure: careful
## packages:
##   - univention-config
##   - univention-directory-manager-tools


import univention.testing.strings as uts
import univention.testing.utils as utils
import univention.testing.udm as udm_test
import pytest


class Test_UDMExtension(object):
	@pytest.mark.tags('udm')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	def test_extended_attribute_remove_required_singlevalue_2(self, udm):
		"""Remove required settings/extended_attribute single value"""
		properties = {
			'name': uts.random_name(),
			'shortDescription': uts.random_string(),
			'CLIName': uts.random_name(),
			'module': 'groups/group',
			'objectClass': 'univentionFreeAttributes',
			'ldapMapping': 'univentionFreeAttribute15',
			'valueRequired': '1'
		}

		udm.create_object('settings/extended_attribute', position=udm.UNIVENTION_CONTAINER, **properties)

		extended_attribute_value = uts.random_string()
		group = udm.create_group(**{properties['CLIName']: extended_attribute_value})[0]

		with pytest.raises(udm_test.UCSTestUDM_ModifyUDMObjectFailed, message='UDM did not report an error while trying to remove a required settings/extended_attribute single value from object'):
			udm.modify_object('groups/group', dn=group, remove={properties['CLIName']: [extended_attribute_value]})
