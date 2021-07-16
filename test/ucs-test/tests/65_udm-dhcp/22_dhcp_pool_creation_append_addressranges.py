#!/usr/share/ucs-test/runner pytest-3
## desc: Append ranges during dhcp/pool creation
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
	def test_dhcp_pool_creation_append_addressranges(self, udm):
		"""Append ranges during dhcp/pool creation"""
		dhcp_service = udm.create_object('dhcp/service', service=uts.random_name())
		dhcp_subnet = udm.create_object('dhcp/subnet', subnet='10.20.30.0', subnetmask='24', superordinate=dhcp_service)

		ranges = ['10.20.30.11 10.20.30.15', '10.20.30.16 10.20.30.20']
		dhcp_pool = udm.create_object('dhcp/pool', name=uts.random_string(), append={'range': ranges}, superordinate=dhcp_subnet)
		utils.verify_ldap_object(dhcp_pool, {'dhcpRange': ranges})
