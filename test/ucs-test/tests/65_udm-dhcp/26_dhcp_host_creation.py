#!/usr/share/ucs-test/runner pytest-3
## desc: Create dhcp/host
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
	def test_dhcp_host_creation(self, udm):
		"""Create dhcp/host"""
		dhcp_service = udm.create_object('dhcp/service', service=uts.random_name())

		mac = 'ethernet 01:ff:78:38:ab:24'
		dhcp_host = udm.create_object('dhcp/host', host=uts.random_name(), hwaddress=mac, superordinate=dhcp_service)

		utils.verify_ldap_object(dhcp_host, {'dhcpHWAddress': [mac]})
