#!/usr/share/ucs-test/runner pytest-3
## desc: Create dhcp/sharedsubnet with all attributes set
## tags: [udm]
## roles: [domaincontroller_master]
## exposure: careful
## packages:
##   - univention-config
##   - univention-directory-manager-tools


import pytest
import univention.testing.utils as utils
import univention.testing.strings as uts

class Test_DHCPSharedsubnet(object):
	@pytest.mark.tags('udm')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	def test_dhcp_sharedsubnet_creation_with_all_attributes(self, udm):
		"""Create dhcp/sharedsubnet with all attributes set"""
		dhcp_service = udm.create_object('dhcp/service', service=uts.random_name())
		dhcp_shared_network = udm.create_object('dhcp/shared', name=uts.random_name(), superordinate=dhcp_service)

		dhcp_shared_subnet_properties = {
			'subnet': '10.20.30.0',
			'subnetmask': '24',
			'broadcastaddress': '10.20.30.255',
			'range': '10.20.30.1 10.20.30.254'
		}

		dhcp_shared_subnet = udm.create_object('dhcp/sharedsubnet', superordinate=dhcp_shared_network, **dhcp_shared_subnet_properties)
		utils.verify_ldap_object(dhcp_shared_subnet, {
			'dhcpNetMask': [dhcp_shared_subnet_properties['subnetmask']],
			'dhcpRange': [dhcp_shared_subnet_properties['range']],
			'univentionDhcpBroadcastAddress': [dhcp_shared_subnet_properties['broadcastaddress']]
		})
