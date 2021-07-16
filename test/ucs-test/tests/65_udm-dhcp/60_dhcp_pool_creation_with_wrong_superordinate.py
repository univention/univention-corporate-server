#!/usr/share/ucs-test/runner pytest-3
## desc: Create dhcp/pool with wrong superordinate
## tags: [udm]
## roles: [domaincontroller_master]
## bugs: [13817, 31518]
## exposure: careful
## versions:
##  3.1-1: skip
##  4.1-4: fixed

import pytest
import univention.testing.utils as utils
import univention.testing.udm as udm_test
import univention.testing.strings as uts


class Test_DHCPPool(object):
	@pytest.mark.tags('udm')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	def test_dhcp_pool_creation_with_wrong_superordinate(self, udm):
		"""Create dhcp/pool with wrong superordinate"""
		# bugs: [13817, 31518]
		dhcpService = udm.create_object('dhcp/service', service=uts.random_string())
		try:
			udm.create_object('dhcp/pool', name=uts.random_string(), range='10.20.30.1 10.20.30.154', superordinate=dhcpService)
		except udm_test.UCSTestUDM_CreateUDMObjectFailed:
			pass
		else:
			utils.fail('UDM did not report an error while trying to create a dhcp/pool with DHCP service as superordinate')
