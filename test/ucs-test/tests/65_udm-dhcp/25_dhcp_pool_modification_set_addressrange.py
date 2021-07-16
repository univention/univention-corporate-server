#!/usr/share/ucs-test/runner pytest-3
## desc: Set range during dhcp/pool modification
## tags: [udm]
## roles: [domaincontroller_master]
## exposure: careful
## packages:
##   - univention-config
##   - univention-directory-manager-tools


import pytest
import univention.testing.utils as utils
import univention.testing.strings as uts


class Test_DHCPPool(object):
	@pytest.mark.tags('udm')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	def test_dhcp_pool_modification_set_addressrange(self, udm):
		"""Set range during dhcp/pool modification"""
		dhcp_service = udm.create_object('dhcp/service', service=uts.random_name())
		dhcp_subnet = udm.create_object('dhcp/subnet', subnet='10.20.30.0', subnetmask='24', superordinate=dhcp_service)

		dhcp_pool = udm.create_object('dhcp/pool', range='10.20.30.16 10.20.30.20', name=uts.random_name(), superordinate=dhcp_subnet)

		range = '10.20.30.11 10.20.30.15'
		udm.modify_object('dhcp/pool', dn=dhcp_pool, superordinate=dhcp_subnet, range=range)
		utils.verify_ldap_object(dhcp_pool, {'dhcpRange': [range]})
