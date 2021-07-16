#!/usr/share/ucs-test/runner pytest-3
## desc: Create dhcp/sharedsubnet and dhcp/subnet with invalid values
## tags: [udm]
## bugs: [44135]
## roles: [domaincontroller_master]
## exposure: careful
## packages:
##   - univention-config
##   - univention-directory-manager-tools


import pytest
import univention.testing.udm as udm_test
import univention.testing.strings as uts

class Test_DHCPSubnet(object):
	@pytest.mark.tags('udm')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	def test_dhcp_subnet_invalid_values(self, udm):
		"""Create dhcp/sharedsubnet and dhcp/subnet with invalid values"""
		# bugs: [44135]
		dhcpService = udm.create_object('dhcp/service', service=uts.random_name())
		with pytest.raises(udm_test.UCSTestUDM_CreateUDMObjectFailed) as exc:
			udm.create_object('dhcp/subnet', subnet='10.20.30.0', subnetmask='16', superordinate=dhcpService)
		assert 'The subnet mask does not match the subnet.' in str(exc.value), exc.value

		shared = udm.create_object('dhcp/shared', name=uts.random_name(), superordinate=dhcpService)

		with pytest.raises(udm_test.UCSTestUDM_CreateUDMObjectFailed) as exc:
			udm.create_object('dhcp/sharedsubnet', subnet='10.20.30.0', subnetmask='16', superordinate=shared)
		assert 'The subnet mask does not match the subnet.' in str(exc.value), exc.value
