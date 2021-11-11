#!/usr/share/ucs-test/runner pytest-3
## desc: Check that mayChange=0 is enforced for settings/extended_attribute
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
	def test_extended_attribute_mayChange_enforcement(self, udm):
		"""Check that mayChange=0 is enforced for settings/extended_attribute"""
		properties = {
			'name': uts.random_name(),
			'shortDescription': uts.random_string(),
			'CLIName': uts.random_name(),
			'module': 'users/user',
			'objectClass': 'univentionFreeAttributes',
			'ldapMapping': 'univentionFreeAttribute15',
			'mayChange': '0'
		}

		udm.create_object('settings/extended_attribute', position=udm.UNIVENTION_CONTAINER, **properties)

		user = udm.create_user(**{properties['CLIName']: uts.random_string()})[0]
		with pytest.raises(udm_test.UCSTestUDM_ModifyUDMObjectFailed, message='UDM did not report an error while trying to modify a settings/extended_attribute value which may not change'):
			udm.modify_object('users/user', dn=user, **{properties['CLIName']: uts.random_string()})
