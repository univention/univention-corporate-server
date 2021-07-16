#!/usr/share/ucs-test/runner pytest-3
## desc: Set range during dhcp/subnet modification
## tags: [udm]
## roles: [domaincontroller_master]
## exposure: careful
## packages:
##   - univention-config
##   - univention-directory-manager-tools


import pytest
import univention.testing.utils as utils
import univention.testing.strings as uts

class Test_DHCPSubnet(object):
	@pytest.mark.tags('udm')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	def test_dhcp_subnet_modification_set_range(self, udm):
		"""Set range during dhcp/subnet modification"""
		dhcp_service = udm.create_object('dhcp/service', service=uts.random_name())

		dhcp_subnet = udm.create_object('dhcp/subnet', subnet='10.20.0.0', subnetmask='16', superordinate=dhcp_service)

		range = '10.20.10.1 10.20.10.254'
		udm.modify_object('dhcp/subnet', dn=dhcp_subnet, range=range, superordinate=dhcp_service)
		utils.verify_ldap_object(dhcp_subnet, {'dhcpRange': [range]})
