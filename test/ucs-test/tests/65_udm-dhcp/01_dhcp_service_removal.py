#!/usr/share/ucs-test/runner pytest-3
## desc: Remove dhcp/service
## tags: [udm]
## roles: [domaincontroller_master]
## exposure: careful
## packages:
##   - univention-config
##   - univention-directory-manager-tools


import pytest
import univention.testing.utils as utils
import univention.testing.strings as uts

class Test_DHCPService(object):
	@pytest.mark.tags('udm')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	def test_dhcp_servoce_removal(self, udm):
		"""Remove dhcp/service"""
		dhcp_service = udm.create_object('dhcp/service', service=uts.random_name())

		udm.remove_object('dhcp/service', dn=dhcp_service)
		utils.verify_ldap_object(dhcp_service, should_exist=False)
