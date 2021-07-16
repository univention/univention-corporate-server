#!/usr/share/ucs-test/runner pytest-3
## desc: Check dhcp/pool attributes
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
	def test_dhcp_pool_creation_with_all_attributes(self, udm):
		"""Check dhcp/pool attributes"""
		dhcp_service = udm.create_object('dhcp/service', service=uts.random_name())
		dhcp_subnet = udm.create_object('dhcp/subnet', subnet='10.20.30.0', subnetmask='24', superordinate=dhcp_service)

		dhcp_pool_properties = {
			'name': uts.random_string(),
			'range': '10.20.30.40 10.20.30.50',
			'failover_peer': uts.random_string(),
			'known_clients': 'deny',
			'unknown_clients': 'allow',
			'dynamic_bootp_clients': 'deny',
			'all_clients': 'allow'
		}

		dhcp_pool = udm.create_object('dhcp/pool', superordinate=dhcp_subnet, **dhcp_pool_properties)

		utils.verify_ldap_object(dhcp_pool, {
			'dhcpRange': [dhcp_pool_properties['range']],
			'univentionDhcpFailoverPeer': [dhcp_pool_properties['failover_peer']],
			'dhcpPermitList': ['deny known clients', 'allow unknown clients', 'deny dynamic bootp clients', 'allow all clients']
		})
