#!/usr/share/ucs-test/runner pytest-3
## desc: Remove ranges during dhcp/subnet modification
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
	def test_dhcp_subnet_modification_remove_ranges(self, udm):
		"""Remove ranges during dhcp/subnet modification"""
		dhcp_service = udm.create_object('dhcp/service', service=uts.random_name())

		ranges = ['10.20.10.1 10.20.10.254', '10.20.30.1 10.20.30.254', '10.20.20.1 10.20.20.254', '10.20.40.1 10.20.40.254']
		dhcp_subnet = udm.create_object('dhcp/subnet', subnet='10.20.0.0', subnetmask='16', append={'range': ranges}, superordinate=dhcp_service)

		udm.modify_object('dhcp/subnet', dn=dhcp_subnet, remove={'range': ranges[:2]}, superordinate=dhcp_service)
		utils.verify_ldap_object(dhcp_subnet, {'dhcpRange': ranges[2:]})
