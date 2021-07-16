#!/usr/share/ucs-test/runner pytest-3
## desc: Append ranges during dhcp/pool modification
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
	def test_dhcp_pool_modification_append_addressranges(self, udm):
		"""Append ranges during dhcp/pool modification"""
		dhcp_service = udm.create_object('dhcp/service', service=uts.random_name())
		dhcp_subnet = udm.create_object('dhcp/subnet', subnet='10.20.30.0', subnetmask='24', superordinate=dhcp_service)

		ranges = ['10.20.30.11 10.20.30.15', '10.20.30.16 10.20.30.20', '10.20.30.21 10.20.30.25']
		dhcp_pool = udm.create_object('dhcp/pool', range=ranges[0], name=uts.random_name(), superordinate=dhcp_subnet)
		udm.modify_object('dhcp/pool', dn=dhcp_pool, superordinate=dhcp_subnet, append={'range': ranges[1:]})

		utils.verify_ldap_object(dhcp_pool, {'dhcpRange': ranges})
