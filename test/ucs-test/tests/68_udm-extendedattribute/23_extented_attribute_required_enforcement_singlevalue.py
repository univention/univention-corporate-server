#!/usr/share/ucs-test/runner pytest-3
## desc: Check that required=True is enforced for singlevalue extended attributes
## tags: [udm]
## roles: [domaincontroller_master]
## exposure: careful
## packages:
##   - univention-config
##   - univention-directory-manager-tools

import univention.testing.udm as udm_test
import univention.testing.strings as uts
import univention.testing.utils as utils
import pytest


class Test_UDMExtension(object):
	@pytest.mark.tags('udm')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	def test_extented_attribute_required_enforcement_singlevalue(self, udm):
		"""Check that required=True is enforced for singlevalue extended attributes"""
		udm.create_object(
			'settings/extended_attribute',
			position=udm.UNIVENTION_CONTAINER,
			name=uts.random_string(),
			shortDescription='Test short description',
			CLIName='univentionUCSTestAttribute',
			module='groups/group',
			objectClass='univentionFreeAttributes',
			ldapMapping='univentionFreeAttribute15',
			valueRequired='1'
		)

		# try creating an udm object without the just created extended attribute given (expected to fail)
		with pytest.raises(udm_test.UCSTestUDM_CreateUDMObjectFailed, message='UDM did not report an error while trying to create an object even though a required single value extended attribute was not given'):
			udm.create_group()
