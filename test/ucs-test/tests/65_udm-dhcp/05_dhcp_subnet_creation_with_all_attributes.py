#!/usr/share/ucs-test/runner pytest-3
## desc: Create dhcp/subnet with all attributes set
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
	def test_dhcp_subnet_creation_with_all_attributes(self, udm):
		"""Create dhcp/subnet with all attributes set"""
		dhcp_subnet_properties = {
			'subnet': '10.20.30.0',
			'subnetmask': '24',
			'broadcastaddress': '10.20.30.255',
			'range': '10.20.30.1 10.20.30.254'
		}

		dhcp_subnet = udm.create_object('dhcp/subnet', superordinate=udm.create_object('dhcp/service', service=uts.random_name()), **dhcp_subnet_properties)

		utils.verify_ldap_object(dhcp_subnet, {
			'cn': [dhcp_subnet_properties['subnet']],
			'dhcpNetMask': [dhcp_subnet_properties['subnetmask']],
			'univentionDhcpBroadcastAddress': [dhcp_subnet_properties['broadcastaddress']],
			'dhcpRange': [dhcp_subnet_properties['range']]
		})
