#!/usr/share/ucs-test/runner pytest-3
## desc: Create dhcp/server
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
	def test_dhcp_server_creation(self, udm):
		"""Create dhcp/server"""
		dhcp_service = udm.create_object('dhcp/service', service=uts.random_name())

		dhcp_server = udm.create_object('dhcp/server', superordinate=dhcp_service, server=uts.random_name())
		utils.verify_ldap_object(dhcp_server)
