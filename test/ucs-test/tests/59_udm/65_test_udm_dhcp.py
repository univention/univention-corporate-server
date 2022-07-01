#!/usr/share/ucs-test/runner pytest-3
## desc: Create dhcp/service
## tags: [udm, udm-dhcp]
## roles: [domaincontroller_master]
## exposure: careful
## packages:
##   - univention-config
##   - univention-directory-manager-tools

import pprint

import pytest

import univention.testing.strings as uts
import univention.testing.udm as udm_test
import univention.testing.utils as utils

SUBNET_IP4 = '10.20.30.0'
SUBNET_MASK_IP4 = '24'


class Test_DHCPService(object):

	@pytest.mark.tags('udm')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	def test_dhcp_service_creation(self, udm):
		"""Create dhcp/service"""
		dhcp_service = udm.create_object('dhcp/service', service=uts.random_name())
		utils.verify_ldap_object(dhcp_service)

	@pytest.mark.tags('udm')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	def test_dhcp_service_removal(self, udm):
		"""Remove dhcp/service"""
		dhcp_service = udm.create_object('dhcp/service', service=uts.random_name())

		udm.remove_object('dhcp/service', dn=dhcp_service)
		utils.verify_ldap_object(dhcp_service, should_exist=False)


class Test_DHCPServer(object):

	@pytest.mark.tags('udm')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	def test_dhcp_server_creation(self, udm):
		"""Create dhcp/server"""
		dhcp_service = udm.create_object('dhcp/service', service=uts.random_name())

		dhcp_server = udm.create_object('dhcp/server', superordinate=dhcp_service, server=uts.random_name())
		utils.verify_ldap_object(dhcp_server)

	@pytest.mark.tags('udm')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	def test_dhcp_server_removal(self, udm):
		"""Remove dhcp/server"""
		dhcp_service = udm.create_object('dhcp/service', service=uts.random_name())

		dhcp_server = udm.create_object('dhcp/server', server=uts.random_name(), superordinate=dhcp_service)

		udm.remove_object('dhcp/server', dn=dhcp_server, superordinate=dhcp_service)
		utils.verify_ldap_object(dhcp_server, should_exist=False)


class Test_DHCPSubnet(object):
	@pytest.mark.tags('udm')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	def test_dhcp_subnet_creation(self, udm):
		"""Create dhcp/subnet"""
		dhcp_service = udm.create_object('dhcp/service', service=uts.random_name())

		subnet_mask = SUBNET_MASK_IP4
		subnet = SUBNET_IP4
		dhcp_subnet = udm.create_object('dhcp/subnet', superordinate=dhcp_service, subnet=subnet, subnetmask=subnet_mask)

		utils.verify_ldap_object(dhcp_subnet, {'dhcpNetMask': [subnet_mask], 'cn': [subnet]})

	@pytest.mark.tags('udm')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	def test_dhcp_subnet_creation_with_all_attributes(self, udm):
		"""Create dhcp/subnet with all attributes set"""
		dhcp_subnet_properties = {
			'subnet': SUBNET_IP4,
			'subnetmask': SUBNET_MASK_IP4,
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

	@pytest.mark.tags('udm')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	def test_dhcp_subnet_creation_append_ranges(self, udm):
		"""Append ranges during dhcp/subnet creation"""
		dhcp_service = udm.create_object('dhcp/service', service=uts.random_name())

		ranges = ['10.20.10.1 10.20.10.254', '10.20.30.1 10.20.30.254']
		dhcp_subnet = udm.create_object('dhcp/subnet', subnet='10.20.0.0', subnetmask='16', append={'range': ranges}, superordinate=dhcp_service)

		utils.verify_ldap_object(dhcp_subnet, {'dhcpRange': ranges})

	@pytest.mark.tags('udm')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	def test_dhcp_subnet_modification_append_ranges(self, udm):
		"""Append ranges during dhcp/subnet modification"""
		dhcp_service = udm.create_object('dhcp/service', service=uts.random_name())

		dhcp_subnet = udm.create_object('dhcp/subnet', subnet='10.20.0.0', subnetmask='16', superordinate=dhcp_service)

		ranges = ['10.20.10.1 10.20.10.254', '10.20.30.1 10.20.30.254']
		udm.modify_object('dhcp/subnet', dn=dhcp_subnet, append={'range': ranges}, superordinate=dhcp_service)
		utils.verify_ldap_object(dhcp_subnet, {'dhcpRange': ranges})

	@pytest.mark.tags('udm')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	def test_dhcp_subnet_creation_set_range(self, udm):
		"""Set range during dhcp/subnet creation"""
		dhcp_service = udm.create_object('dhcp/service', service=uts.random_name())

		range = '10.20.10.1 10.20.10.254'
		dhcp_subnet = udm.create_object('dhcp/subnet', subnet='10.20.0.0', subnetmask='16', range=range, superordinate=dhcp_service)

		utils.verify_ldap_object(dhcp_subnet, {'dhcpRange': [range]})

	@pytest.mark.tags('udm')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	def test_dhcp_subnet_modification_set_range(self, udm):
		"""Set range during dhcp/subnet modification"""
		dhcp_service = udm.create_object('dhcp/service', service=uts.random_name())

		dhcp_subnet = udm.create_object('dhcp/subnet', subnet='10.20.0.0', subnetmask='16', superordinate=dhcp_service)

		range = '10.20.10.1 10.20.10.254'
		udm.modify_object('dhcp/subnet', dn=dhcp_subnet, range=range, superordinate=dhcp_service)
		utils.verify_ldap_object(dhcp_subnet, {'dhcpRange': [range]})

	@pytest.mark.tags('udm')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	def test_dhcp_subnet_modification_remove_ranges(self, udm):
		"""Remove ranges during dhcp/subnet modification"""
		dhcp_service = udm.create_object('dhcp/service', service=uts.random_name())

		ranges = ['10.20.10.1 10.20.10.254', '10.20.30.1 10.20.30.254', '10.20.20.1 10.20.20.254', '10.20.40.1 10.20.40.254']
		dhcp_subnet = udm.create_object('dhcp/subnet', subnet='10.20.0.0', subnetmask='16', append={'range': ranges}, superordinate=dhcp_service)

		udm.modify_object('dhcp/subnet', dn=dhcp_subnet, remove={'range': ranges[:2]}, superordinate=dhcp_service)
		utils.verify_ldap_object(dhcp_subnet, {'dhcpRange': ranges[2:]})

	@pytest.mark.tags('udm')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	def test_dhcp_subnet_invalid_values(self, udm):
		"""Create dhcp/sharedsubnet and dhcp/subnet with invalid values"""
		# bugs: [44135]
		dhcpService = udm.create_object('dhcp/service', service=uts.random_name())
		with pytest.raises(udm_test.UCSTestUDM_CreateUDMObjectFailed) as exc:
			udm.create_object('dhcp/subnet', subnet=SUBNET_IP4, subnetmask='16', superordinate=dhcpService)
		assert 'The subnet mask does not match the subnet.' in str(exc.value), exc.value

		shared = udm.create_object('dhcp/shared', name=uts.random_name(), superordinate=dhcpService)

		with pytest.raises(udm_test.UCSTestUDM_CreateUDMObjectFailed) as exc:
			udm.create_object('dhcp/sharedsubnet', subnet=SUBNET_IP4, subnetmask='16', superordinate=shared)
		assert 'The subnet mask does not match the subnet.' in str(exc.value), exc.value


class Test_DHCPPool(object):

	@pytest.mark.tags('udm')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	def test_pool_creation(self, udm):
		"""Create dhcp/pool"""
		dhcp_service = udm.create_object('dhcp/service', service=uts.random_name())
		dhcp_subnet = udm.create_object('dhcp/subnet', subnet=SUBNET_IP4, subnetmask=SUBNET_MASK_IP4, superordinate=dhcp_service)

		range = '10.20.30.1 10.20.30.254'
		name = uts.random_name()
		dhcp_pool = udm.create_object('dhcp/pool', name=name, range=range, superordinate=dhcp_subnet)
		utils.verify_ldap_object(dhcp_pool, {'dhcpRange': [range], 'cn': [name]})

	@pytest.mark.tags('udm')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	def test_pool_removal(self, udm):
		"""Remove dhcp/pool"""
		dhcp_service = udm.create_object('dhcp/service', service=uts.random_name())
		dhcp_subnet = udm.create_object('dhcp/subnet', subnet=SUBNET_IP4, subnetmask=SUBNET_MASK_IP4, superordinate=dhcp_service)

		dhcp_pool = udm.create_object('dhcp/pool', name=uts.random_name(), range='10.20.30.1 10.20.30.254', superordinate=dhcp_subnet)

		udm.remove_object('dhcp/pool', dn=dhcp_pool, superordinate=dhcp_subnet)
		utils.verify_ldap_object(dhcp_pool, should_exist=False)

	@pytest.mark.tags('udm')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	def test_dhcp_pool_creation_with_all_attributes(self, udm):
		"""Check dhcp/pool attributes"""
		dhcp_service = udm.create_object('dhcp/service', service=uts.random_name())
		dhcp_subnet = udm.create_object('dhcp/subnet', subnet=SUBNET_IP4, subnetmask=SUBNET_MASK_IP4, superordinate=dhcp_service)

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

	@pytest.mark.tags('udm')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	def test_dhcp_pool_creation_append_addressranges(self, udm):
		"""Append ranges during dhcp/pool creation"""
		dhcp_service = udm.create_object('dhcp/service', service=uts.random_name())
		dhcp_subnet = udm.create_object('dhcp/subnet', subnet=SUBNET_IP4, subnetmask=SUBNET_MASK_IP4, superordinate=dhcp_service)

		ranges = ['10.20.30.11 10.20.30.15', '10.20.30.16 10.20.30.20']
		dhcp_pool = udm.create_object('dhcp/pool', name=uts.random_string(), append={'range': ranges}, superordinate=dhcp_subnet)
		utils.verify_ldap_object(dhcp_pool, {'dhcpRange': ranges})

	@pytest.mark.tags('udm')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	def test_dhcp_pool_modification_append_addressranges(self, udm):
		"""Append ranges during dhcp/pool modification"""
		dhcp_service = udm.create_object('dhcp/service', service=uts.random_name())
		dhcp_subnet = udm.create_object('dhcp/subnet', subnet=SUBNET_IP4, subnetmask=SUBNET_MASK_IP4, superordinate=dhcp_service)

		ranges = ['10.20.30.11 10.20.30.15', '10.20.30.16 10.20.30.20', '10.20.30.21 10.20.30.25']
		dhcp_pool = udm.create_object('dhcp/pool', range=ranges[0], name=uts.random_name(), superordinate=dhcp_subnet)
		udm.modify_object('dhcp/pool', dn=dhcp_pool, superordinate=dhcp_subnet, append={'range': ranges[1:]})

		utils.verify_ldap_object(dhcp_pool, {'dhcpRange': ranges})

	@pytest.mark.tags('udm')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	def test_dhcp_pool_creation_set_addressrange(self, udm):
		"""Set range during dhcp/pool creation"""
		dhcp_service = udm.create_object('dhcp/service', service=uts.random_name())
		dhcp_subnet = udm.create_object('dhcp/subnet', subnet=SUBNET_IP4, subnetmask=SUBNET_MASK_IP4, superordinate=dhcp_service)

		range = '10.20.30.11 10.20.30.15'
		dhcp_pool = udm.create_object('dhcp/pool', name=uts.random_string(), range=range, superordinate=dhcp_subnet)
		utils.verify_ldap_object(dhcp_pool, {'dhcpRange': [range]})

	@pytest.mark.tags('udm')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	def test_dhcp_pool_modification_set_addressrange(self, udm):
		"""Set range during dhcp/pool modification"""
		dhcp_service = udm.create_object('dhcp/service', service=uts.random_name())
		dhcp_subnet = udm.create_object('dhcp/subnet', subnet=SUBNET_IP4, subnetmask=SUBNET_MASK_IP4, superordinate=dhcp_service)

		dhcp_pool = udm.create_object('dhcp/pool', range='10.20.30.16 10.20.30.20', name=uts.random_name(), superordinate=dhcp_subnet)

		range = '10.20.30.11 10.20.30.15'
		udm.modify_object('dhcp/pool', dn=dhcp_pool, superordinate=dhcp_subnet, range=range)
		utils.verify_ldap_object(dhcp_pool, {'dhcpRange': [range]})

	@pytest.mark.tags('udm')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	def test_dhcp_host_creation(self, udm):
		"""Create dhcp/host"""
		dhcp_service = udm.create_object('dhcp/service', service=uts.random_name())

		mac = 'ethernet 01:ff:78:38:ab:24'
		dhcp_host = udm.create_object('dhcp/host', host=uts.random_name(), hwaddress=mac, superordinate=dhcp_service)

		utils.verify_ldap_object(dhcp_host, {'dhcpHWAddress': [mac]})

	@pytest.mark.tags('udm')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	def test_dhcp_pool_modification_remove_addressranges(self, udm):
		"""Remove ranges during dhcp/pool modification"""
		dhcp_service = udm.create_object('dhcp/service', service=uts.random_name())
		dhcp_subnet = udm.create_object('dhcp/subnet', subnet=SUBNET_IP4, subnetmask=SUBNET_MASK_IP4, superordinate=dhcp_service)

		ranges = ['10.20.30.11 10.20.30.15', '10.20.30.16 10.20.30.20', '10.20.30.21 10.20.30.25', '10.20.30.30 10.20.30.35']
		dhcp_pool = udm.create_object('dhcp/pool', append={'range': ranges}, name=uts.random_name(), superordinate=dhcp_subnet)
		udm.modify_object('dhcp/pool', dn=dhcp_pool, superordinate=dhcp_subnet, remove={'range': ranges[:2]})
		utils.verify_ldap_object(dhcp_pool, {'dhcpRange': ranges[2:]})

	@pytest.mark.tags('udm')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	def test_dhcp_pool_creation_with_wrong_superordinate(self, udm):
		"""Create dhcp/pool with wrong superordinate"""
		# bugs: [13817, 31518]
		dhcpService = udm.create_object('dhcp/service', service=uts.random_string())
		try:
			udm.create_object('dhcp/pool', name=uts.random_string(), range='10.20.30.1 10.20.30.154', superordinate=dhcpService)
		except udm_test.UCSTestUDM_CreateUDMObjectFailed:
			pass
		else:
			utils.fail('UDM did not report an error while trying to create a dhcp/pool with DHCP service as superordinate')


class Test_DHCPHost(object):

	@pytest.mark.tags('udm')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	def test_dhcp_host_removal(self, udm):
		"""Remove dhcp/host"""
		dhcp_service = udm.create_object('dhcp/service', service=uts.random_name())

		dhcp_host = udm.create_object('dhcp/host', host=uts.random_name(), hwaddress='ethernet 01:ff:78:38:ab:24', superordinate=dhcp_service)

		udm.remove_object('dhcp/host', dn=dhcp_host, superordinate=dhcp_service)
		utils.verify_ldap_object(dhcp_host, should_exist=False)

	@pytest.mark.tags('udm')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	def test_dhcp_host_creation_append_fixedaddresses(self, udm):
		"""Append fixedaddresses during dhcp/host creation"""
		dhcp_service = udm.create_object('dhcp/service', service=uts.random_name())

		fixed_addresses = ['10.20.30.40', '10.20.30.50']
		dhcp_host = udm.create_object('dhcp/host', host=uts.random_name(), hwaddress='ethernet 01:ff:78:38:ab:24', append={'fixedaddress': fixed_addresses}, superordinate=dhcp_service)
		utils.verify_ldap_object(dhcp_host, {'univentionDhcpFixedAddress': fixed_addresses})

	@pytest.mark.tags('udm')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	def test_dhcp_host_modification_append_fixedaddresses(self, udm):
		"""Append fixedaddresses during dhcp/host modification"""
		dhcp_service = udm.create_object('dhcp/service', service=uts.random_name())

		dhcp_host = udm.create_object('dhcp/host', host=uts.random_name(), hwaddress='ethernet 01:ff:78:38:ab:24', superordinate=dhcp_service)

		fixed_addresses = ['10.20.30.40', '10.20.30.50']
		udm.modify_object('dhcp/host', dn=dhcp_host, append={'fixedaddress': fixed_addresses}, superordinate=dhcp_service)
		utils.verify_ldap_object(dhcp_host, {'univentionDhcpFixedAddress': fixed_addresses})

	@pytest.mark.tags('udm')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	def test_dhcp_host_creation_set_fixedaddress(self, udm):
		"""Set fixedaddress during dhcp/host creation"""
		dhcp_service = udm.create_object('dhcp/service', service=uts.random_name())

		fixed_address = '10.20.30.40'
		dhcp_host = udm.create_object('dhcp/host', host=uts.random_name(), hwaddress='ethernet 01:ff:78:38:ab:24', fixedaddress=fixed_address, superordinate=dhcp_service)
		utils.verify_ldap_object(dhcp_host, {'univentionDhcpFixedAddress': [fixed_address]})

	@pytest.mark.tags('udm')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	def test_dhcp_host_modification_set_fixedaddress(self, udm):
		"""Set fixedaddress during dhcp/host modification"""
		dhcp_service = udm.create_object('dhcp/service', service=uts.random_name())

		dhcp_host = udm.create_object('dhcp/host', host=uts.random_name(), hwaddress='ethernet 01:ff:78:38:ab:24', superordinate=dhcp_service)

		fixed_address = '10.20.30.40'
		udm.modify_object('dhcp/host', dn=dhcp_host, fixedaddress=fixed_address, superordinate=dhcp_service)
		utils.verify_ldap_object(dhcp_host, {'univentionDhcpFixedAddress': [fixed_address]})

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


class Test_DHCPSharednetwork(object):

	@pytest.mark.tags('udm')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	def test_dhcp_sharednetwork_creation(self, udm):
		dhcp_service = udm.create_object('dhcp/service', service=uts.random_name())

		dhcp_shared_network = udm.create_object('dhcp/shared', name=uts.random_name(), superordinate=dhcp_service)
		utils.verify_ldap_object(dhcp_shared_network)

	@pytest.mark.tags('udm')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	def test_dhcp_sharednetwork_removal(self, udm):
		"""Remove dhcp/shared"""
		dhcp_service = udm.create_object('dhcp/service', service=uts.random_name())

		dhcp_shared_network = udm.create_object('dhcp/shared', name=uts.random_name(), superordinate=dhcp_service)

		udm.remove_object('dhcp/shared', dn=dhcp_shared_network, superordinate=dhcp_service)
		utils.verify_ldap_object(dhcp_shared_network, should_exist=False)

	@pytest.mark.tags('udm')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	def test_dhcp_sharedsubnet_creation(self, udm):
		"""Create dhcp/sharedsubnet"""
		dhcp_service = udm.create_object('dhcp/service', service=uts.random_name())
		dhcp_shared_network = udm.create_object('dhcp/shared', name=uts.random_name(), superordinate=dhcp_service)

		subnet_mask = SUBNET_MASK_IP4
		dhcp_shared_subnet = udm.create_object('dhcp/sharedsubnet', superordinate=dhcp_shared_network, subnet=SUBNET_IP4, subnetmask=subnet_mask)
		utils.verify_ldap_object(dhcp_shared_subnet, {'dhcpNetMask': [subnet_mask]})

	@pytest.mark.tags('udm')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	def test_dhcp_sharedsubnet_removal(self, udm):
		"""Remove dhcp/sharedsubnet"""
		dhcp_service = udm.create_object('dhcp/service', service=uts.random_name())
		dhcp_shared_network = udm.create_object('dhcp/shared', name=uts.random_name(), superordinate=dhcp_service)

		dhcp_shared_subnet = udm.create_object('dhcp/sharedsubnet', superordinate=dhcp_shared_network, subnet=SUBNET_IP4, subnetmask=SUBNET_MASK_IP4)

		udm.remove_object('dhcp/sharedsubnet', dn=dhcp_shared_subnet, superordinate=dhcp_shared_network)
		utils.verify_ldap_object(dhcp_shared_subnet, should_exist=False)

	@pytest.mark.tags('udm')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	def test_dhcp_sharedsubnet_creation_with_all_attributes(self, udm):
		"""Create dhcp/sharedsubnet with all attributes set"""
		dhcp_service = udm.create_object('dhcp/service', service=uts.random_name())
		dhcp_shared_network = udm.create_object('dhcp/shared', name=uts.random_name(), superordinate=dhcp_service)

		dhcp_shared_subnet_properties = {
			'subnet': SUBNET_IP4,
			'subnetmask': SUBNET_MASK_IP4,
			'broadcastaddress': '10.20.30.255',
			'range': '10.20.30.1 10.20.30.254'
		}

		dhcp_shared_subnet = udm.create_object('dhcp/sharedsubnet', superordinate=dhcp_shared_network, **dhcp_shared_subnet_properties)
		utils.verify_ldap_object(dhcp_shared_subnet, {
			'dhcpNetMask': [dhcp_shared_subnet_properties['subnetmask']],
			'dhcpRange': [dhcp_shared_subnet_properties['range']],
			'univentionDhcpBroadcastAddress': [dhcp_shared_subnet_properties['broadcastaddress']]
		})

	@pytest.mark.tags('udm')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	def test_dhcp_sharedsubnet_creation_append_ranges(self, udm):
		"""Append ranges during dhcp/sharedsubnet creation"""
		dhcp_service = udm.create_object('dhcp/service', service=uts.random_name())
		dhcp_shared_network = udm.create_object('dhcp/shared', name=uts.random_name(), superordinate=dhcp_service)

		ranges = ['10.20.30.1 10.20.30.5', '10.20.30.6 10.20.30.10']
		dhcp_shared_subnet = udm.create_object('dhcp/sharedsubnet', subnet=SUBNET_IP4, subnetmask=SUBNET_MASK_IP4, append={'range': ranges}, superordinate=dhcp_shared_network)
		utils.verify_ldap_object(dhcp_shared_subnet, {'dhcpRange': ranges})

	@pytest.mark.tags('udm')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	def test_dhcp_sharedsubnet_modification_append_ranges(self, udm):
		"""Append ranges during dhcp/sharedsubnet modification"""
		dhcp_service = udm.create_object('dhcp/service', service=uts.random_name())
		dhcp_shared_network = udm.create_object('dhcp/shared', name=uts.random_name(), superordinate=dhcp_service)

		dhcp_shared_subnet = udm.create_object('dhcp/sharedsubnet', subnet=SUBNET_IP4, subnetmask=SUBNET_MASK_IP4, superordinate=dhcp_shared_network)

		ranges = ['10.20.30.1 10.20.30.5', '10.20.30.6 10.20.30.10']
		udm.modify_object('dhcp/sharedsubnet', dn=dhcp_shared_subnet, superordinate=dhcp_shared_network, append={'range': ranges})
		utils.verify_ldap_object(dhcp_shared_subnet, {'dhcpRange': ranges})

	@pytest.mark.tags('udm')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	def test_dhcp_sharedsubnet_creation_set_range(self, udm):
		"""Set range during dhcp/sharedsubnet creation"""
		dhcp_service = udm.create_object('dhcp/service', service=uts.random_name())
		dhcp_shared_network = udm.create_object('dhcp/shared', name=uts.random_name(), superordinate=dhcp_service)

		range = '10.20.30.1 10.20.30.5'
		dhcp_shared_subnet = udm.create_object('dhcp/sharedsubnet', subnet=SUBNET_IP4, subnetmask=SUBNET_MASK_IP4, range=range, superordinate=dhcp_shared_network)
		utils.verify_ldap_object(dhcp_shared_subnet, {'dhcpRange': [range]})

	@pytest.mark.tags('udm')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	def test_dhcp_sharedsubnet_modification_set_range(self, udm):
		"""Sed range during dhcp/sharedsubnet modification"""
		dhcp_service = udm.create_object('dhcp/service', service=uts.random_name())
		dhcp_shared_network = udm.create_object('dhcp/shared', name=uts.random_name(), superordinate=dhcp_service)

		dhcp_shared_subnet = udm.create_object('dhcp/sharedsubnet', subnet=SUBNET_IP4, subnetmask=SUBNET_MASK_IP4, superordinate=dhcp_shared_network)

		range = '10.20.30.1 10.20.30.5'
		udm.modify_object('dhcp/sharedsubnet', dn=dhcp_shared_subnet, superordinate=dhcp_shared_network, range=range)
		utils.verify_ldap_object(dhcp_shared_subnet, {'dhcpRange': [range]})


class Test_DHCPSharedsubnet(object):
	@pytest.mark.tags('udm')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	def test_dhcp_sharedsubnet_modification_remove_ranges(self, udm):
		"""Remove ranges during dhcp/sharedsubnet modification"""
		dhcp_service = udm.create_object('dhcp/service', service=uts.random_name())
		dhcp_shared_network = udm.create_object('dhcp/shared', name=uts.random_name(), superordinate=dhcp_service)

		ranges = ['10.20.30.1 10.20.30.5', '10.20.30.6 10.20.30.10', '10.20.30.15 10.20.30.20', '10.20.30.25 10.20.30.30']
		dhcp_shared_subnet = udm.create_object('dhcp/sharedsubnet', subnet=SUBNET_IP4, subnetmask=SUBNET_MASK_IP4, superordinate=dhcp_shared_network, append={'range': ranges})

		udm.modify_object('dhcp/sharedsubnet', dn=dhcp_shared_subnet, superordinate=dhcp_shared_network, remove={'range': ranges[:2]})
		utils.verify_ldap_object(dhcp_shared_subnet, {'dhcpRange': ranges[2:]})

	@pytest.mark.tags('udm')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	def test_dhcp_sharedsubnet_creation_with_wrong_superordinate(self, udm):
		"""Create dhcp/sharedsubnet with wrong superordinate"""
		# bugs: [31519]
		dhcpService = udm.create_object('dhcp/service', service=uts.random_name())
		with pytest.raises(udm_test.UCSTestUDM_CreateUDMObjectFailed, match='.*is not a superordinate for dhcp/sharedsubnet.*'):
			udm.create_object('dhcp/sharedsubnet', subnet=SUBNET_IP4, subnetmask=SUBNET_MASK_IP4, superordinate=dhcpService)


@pytest.mark.tags('udm')
@pytest.mark.roles('domaincontroller_master')
@pytest.mark.exposure('careful')
def test_udm_cli_policies_output(udm):
	"""test UDM-CLI code for --policies={1,2}"""
	dhcp_service = udm.create_object('dhcp/service', service=uts.random_name())

	subnet_mask = SUBNET_MASK_IP4
	subnet = SUBNET_IP4
	dhcp_subnet = udm.create_object('dhcp/subnet', superordinate=dhcp_service, subnet=subnet, subnetmask=subnet_mask)

	dhcp_host = udm.create_object('dhcp/host', superordinate=dhcp_subnet, host=uts.random_name(), hwaddress='ethernet 01:ff:78:38:ab:24', fixedaddress='10.20.30.123')

	host = udm.list_objects('dhcp/host', position=dhcp_host, policies=1)[0][1]
	pprint.pprint(host)
	required = {'Policy-based Settings', 'Subnet-based Settings', 'Merged Settings'}
	assert set(host) & required == required

	host = udm.list_objects('dhcp/host', position=dhcp_host, policies=2)[0][1]
	pprint.pprint(host)
	required = {'univentionPWLength', 'univentionPWHistoryLen'}
	assert set(host['Policy-based Settings']) & required == required
	assert set(host['Subnet-based Settings']) & required == required
	assert set(host['Merged Settings']) & required == required
