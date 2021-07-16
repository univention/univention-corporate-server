#!/usr/share/ucs-test/runner pytest-3
## desc: Remove dhcp/pool
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
	def test_pool_removal(self, udm):
		"""Remove dhcp/pool"""
		dhcp_service = udm.create_object('dhcp/service', service=uts.random_name())
		dhcp_subnet = udm.create_object('dhcp/subnet', subnet='10.20.30.0', subnetmask='24', superordinate=dhcp_service)

		dhcp_pool = udm.create_object('dhcp/pool', name=uts.random_name(), range='10.20.30.1 10.20.30.254', superordinate=dhcp_subnet)

		udm.remove_object('dhcp/pool', dn=dhcp_pool, superordinate=dhcp_subnet)
		utils.verify_ldap_object(dhcp_pool, should_exist=False)
