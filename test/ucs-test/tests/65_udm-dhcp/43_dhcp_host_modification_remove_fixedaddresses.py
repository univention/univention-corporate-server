#!/usr/share/ucs-test/runner pytest-3
## desc: Remove fixedaddresses during dhcp/host modification
## tags: [udm]
## roles: [domaincontroller_master]
## exposure: careful
## packages:
##   - univention-config
##   - univention-directory-manager-tools


import pytest
import univention.testing.utils as utils
import univention.testing.strings as uts

class Test_DHCPHost(object):
	@pytest.mark.tags('udm')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	def test_dhcp_host_modification_remove_fixedaddresses(self, udm):
		"""Remove fixedaddresses during dhcp/host modification"""
		dhcp_service = udm.create_object('dhcp/service', service=uts.random_name())

		fixed_addresses = ['10.20.30.40', '10.20.30.50', '10.20.30.60', '10.20.30.70']
		dhcp_host = udm.create_object('dhcp/host', host=uts.random_name(), hwaddress='ethernet 01:ff:78:38:ab:24', superordinate=dhcp_service, append={'fixedaddress': fixed_addresses})

		udm.modify_object('dhcp/host', dn=dhcp_host, remove={'fixedaddress': fixed_addresses[:2]}, superordinate=dhcp_service)
		utils.verify_ldap_object(dhcp_host, {'univentionDhcpFixedAddress': fixed_addresses[2:]})
