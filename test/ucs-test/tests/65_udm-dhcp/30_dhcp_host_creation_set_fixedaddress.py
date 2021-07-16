#!/usr/share/ucs-test/runner pytest-3
## desc: Set fixedaddress during dhcp/host creation
## tags: [udm]
## roles: [domaincontroller_master]
## exposure: careful
## packages:
##   - univention-config
##   - univention-directory-manager-tools


import univention.testing.utils as utils
import pytest
import univention.testing.strings as uts

class Test_DHCPHost(object):
	@pytest.mark.tags('udm')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	def test_dhcp_host_creation_set_fixedaddress(self, udm):
		"""Set fixedaddress during dhcp/host creation"""
		dhcp_service = udm.create_object('dhcp/service', service=uts.random_name())

		fixed_address = '10.20.30.40'
		dhcp_host = udm.create_object('dhcp/host', host=uts.random_name(), hwaddress='ethernet 01:ff:78:38:ab:24', fixedaddress=fixed_address, superordinate=dhcp_service)
		utils.verify_ldap_object(dhcp_host, {'univentionDhcpFixedAddress': [fixed_address]})
