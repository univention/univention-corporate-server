#!/usr/share/ucs-test/runner pytest-3
## desc: Create dhcp/subnet
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
	def test_dhcp_subnet_creation(self, udm):
		"""Create dhcp/subnet"""
		dhcp_service = udm.create_object('dhcp/service', service=uts.random_name())

		subnet_mask = '24'
		subnet = '10.20.30.0'
		dhcp_subnet = udm.create_object('dhcp/subnet', superordinate=dhcp_service, subnet=subnet, subnetmask=subnet_mask)

		utils.verify_ldap_object(dhcp_subnet, {'dhcpNetMask': [subnet_mask], 'cn': [subnet]})
