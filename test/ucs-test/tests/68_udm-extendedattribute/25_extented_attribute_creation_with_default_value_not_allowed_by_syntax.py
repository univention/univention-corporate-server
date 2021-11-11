#!/usr/share/ucs-test/runner pytest-3
## desc: Create settings/extented_attribute with a value for it's default which is not valid for it's syntax value
## tags: [udm]
## roles: [domaincontroller_master]
## exposure: careful
## packages:
##   - univention-config
##   - univention-directory-manager-tools
## versions:
##   3.2-0: skip

import univention.testing.udm as udm_test
import univention.testing.utils as utils
import univention.testing.strings as uts
import pytest


class Test_UDMExtension(object):
	@pytest.mark.tags('udm')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	@pytest.mark.xfail(reason='wrong version')
	def test_extented_attribute_creation_with_default_value_not_allowed_by_syntax(self, udm):
		"""Create settings/extented_attribute with a value for it's default which is not valid for it's syntax value"""
		# versions:
		#   3.2-0: skip
		with pytest.raises(udm_test.UCSTestUDM_CreateUDMObjectFailed):
			udm.create_object(
				'settings/extended_attribute',
				position=udm.UNIVENTION_CONTAINER,
				name=uts.random_name(),
				shortDescription=uts.random_string(),
				CLIName=uts.random_string(),
				module='users/user',
				objectClass='univentionFreeAttributes',
				ldapMapping='univentionFreeAttribute15',
				syntax='integer',
				default='notaninteger'
			)
