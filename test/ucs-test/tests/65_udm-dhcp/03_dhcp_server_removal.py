#!/usr/share/ucs-test/runner pytest-3
## desc: Remove dhcp/server
## tags: [udm]
## roles: [domaincontroller_master]
## exposure: careful
## packages:
##   - univention-config
##   - univention-directory-manager-tools


import pytest
import univention.testing.utils as utils
import univention.testing.strings as uts

class Test_DHCPServer(object):
	@pytest.mark.tags('udm')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	def test_dhcp_server_removal(self, udm):
		"""Remove dhcp/server"""
		dhcp_service = udm.create_object('dhcp/service', service=uts.random_name())

		dhcp_server = udm.create_object('dhcp/server', server=uts.random_name(), superordinate=dhcp_service)

		udm.remove_object('dhcp/server', dn=dhcp_server, superordinate=dhcp_service)
		utils.verify_ldap_object(dhcp_server, should_exist=False)
