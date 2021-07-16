#!/usr/share/ucs-test/runner pytest-3
## desc: Create dhcp/sharedsubnet with wrong superordinate
## tags: [udm]
## bugs: [31519]
## roles: [domaincontroller_master]
## exposure: careful
## packages:
##   - univention-config
##   - univention-directory-manager-tools
## versions:
##  4.4-3: fixed
##  3.1-1: skip


import pytest
import univention.testing.udm as udm_test
import univention.testing.strings as uts

class Test_DHCPSharedsubnet(object):
	@pytest.mark.tags('udm')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	def test_dhcp_sharedsubnet_creation_with_wrong_superordinate(self, udm):
		"""Create dhcp/sharedsubnet with wrong superordinate"""
		# bugs: [31519]
		dhcpService = udm.create_object('dhcp/service', service=uts.random_name())
		with pytest.raises(udm_test.UCSTestUDM_CreateUDMObjectFailed, match='.*is not a superordinate for dhcp/sharedsubnet.*') as exc:
			udm.create_object('dhcp/sharedsubnet', subnet='10.20.30.0', subnetmask='24', superordinate=dhcpService)
