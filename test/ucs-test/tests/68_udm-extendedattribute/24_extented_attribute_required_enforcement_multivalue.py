#!/usr/share/ucs-test/runner pytest-3
## desc: Check that required=True is enforced for multivalue extended attributes
## tags: [udm]
## roles: [domaincontroller_master]
## bugs: [31302]
## exposure: careful
## packages:
##   - univention-config
##   - univention-directory-manager-tools
## versions:
##  3.1-1: skip
##  3.2-0: fixed

import univention.testing.udm as udm_test
import univention.testing.strings as uts
import univention.testing.utils as utils
import pytest


class Test_UDMExtension(object):
	@pytest.mark.tags('udm')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	@pytest.mark.xfail(reason='wrong version')
	def test_extended_attribute_required_enforcement_multivalue(self, udm):
		"""Check that required=True is enforced for multivalue extended attributes"""
		# bugs: [31302]
		# versions:
		#  3.1-1: skip
		#  3.2-0: fixed
		udm.create_object(
			'settings/extended_attribute',
			position=udm.UNIVENTION_CONTAINER,
			name=uts.random_string(),
			shortDescription='Test short description',
			CLIName='univentionUCSTestAttribute',
			module='groups/group',
			objectClass='univentionFreeAttributes',
			ldapMapping='univentionFreeAttribute15',
			valueRequired='1',
			multivalue='1'
		)

		with pytest.raises(udm_test.UCSTestUDM_CreateUDMObjectFailed, message='UDM did not report an error while trying to create an object even though a required multivalue extended attribute was not given'):
			udm.create_group()
