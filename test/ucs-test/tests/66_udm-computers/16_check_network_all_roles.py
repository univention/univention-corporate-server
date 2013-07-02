#!/usr/share/ucs-test/runner python
## desc: Validate adoption of network properties during creation and modification for all computer roles
## tags: [udm-computers]
## roles: [domaincontroller_master]
## exposure: careful
## bugs: [15758]
## packages:
##   - univention-config
##   - univention-directory-manager-tools


import univention.testing.udm as udm_test
import univention.testing.strings as uts
import univention.testing.utils as utils
import univention.config_registry as configRegistry



if __name__ == '__main__':
	ldap = utils.get_ldap_connection()
	ucr = configRegistry.ConfigRegistry()
	ucr.load()

	with udm_test.UCSTestUDM() as udm:
		for role in udm.COMPUTER_MODULES:
			if role == 'macos':
				continue

			computerProperties = {
				'mac': '01:23:45:67:89:ab',
				'name': uts.random_name()
			}

			udm.addCleanupLock('aRecord', '10.20.30.2')
			udm.addCleanupLock('aRecord', '10.20.40.2')
			udm.addCleanupLock('mac', '01:23:45:67:89:ab')

			forwardZone1Name = '%s.%s' % (uts.random_name(), uts.random_name())
			forwardZone1 = udm.create_object('dns/forward_zone', zone = forwardZone1Name, nameserver = uts.random_string())
			reverseZone1 = udm.create_object('dns/reverse_zone', subnet = '10.20.30', nameserver = uts.random_string())
			dhcpService1 = udm.create_object('dhcp/service', service = uts.random_name())
			network1Properties = {
				'name': uts.random_name(),
				'network': '10.20.30.0',
				'netmask': '24',
				'dnsEntryZoneForward': forwardZone1,
				'dnsEntryZoneReverse': reverseZone1,
				'dhcpEntryZone': dhcpService1,
				'ipRange': '10.20.30.2 10.20.30.254'
			}
			network1 = udm.create_object('networks/network', **network1Properties)

			forwardZone2Name = '%s.%s' % (uts.random_name(), uts.random_name())
			forwardZone2 = udm.create_object('dns/forward_zone', zone = forwardZone2Name, nameserver = uts.random_string())
			reverseZone2 = udm.create_object('dns/reverse_zone', subnet = '10.20.40', nameserver = uts.random_string())
			dhcpService2 = udm.create_object('dhcp/service', service = uts.random_name())
			network2Properties = {
				'name': uts.random_name(),
				'network': '10.20.40.0',
				'netmask': '24',
				'dnsEntryZoneForward': forwardZone2,
				'dnsEntryZoneReverse': reverseZone2,
				'dhcpEntryZone': dhcpService2,
				'ipRange': '10.20.40.2 10.20.40.254'
			}
			network2 = udm.create_object('networks/network', **network2Properties)



			computer = udm.create_object('computers/%s' % role, network = network1, **computerProperties)
			if not utils.verify_ldap_object(computer, {
				'univentionNetworkLink': [network1],
				'aRecord': ['10.20.30.2']
			}):
				utils.fail('%s did not adopt all properties from network link during creation as expected' % role)
			if not utils.verify_ldap_object('relativeDomainName=%s,%s' % (computerProperties['name'], forwardZone1), {'aRecord': ['10.20.30.2']}):
				utils.fail('DNS host record for computers/%s differed from expectation after creation' % role)
			if not utils.verify_ldap_object('relativeDomainName=2,%s' % reverseZone1, {'pTRRecord': ['%s.%s.' % (computerProperties['name'], forwardZone1Name)]}):
				utils.fail('DNS PTR record for computers/%s differed from expectation after creation' % role)
			if not utils.verify_ldap_object('cn=%s,%s' % (computerProperties['name'], dhcpService1), {'univentionDhcpFixedAddress': ['10.20.30.2']}):
				utils.fail('DHCP entry for computers/%s differed from expectation after creation' % role)


			udm.modify_object('computers/%s' % role, dn = computer, network = network2)
			if not utils.verify_ldap_object(computer, {
				'univentionNetworkLink': [network2],
				'aRecord': ['10.20.40.2']
			}):
				utils.fail('%s did not adopt all properties from network link during modification as expected' % role)
			if not utils.verify_ldap_object('relativeDomainName=%s,%s' % (computerProperties['name'], forwardZone2), {'aRecord': ['10.20.40.2']}):
				utils.fail('DNS host record for computers/%s differed from expectation after modification' % role)
			if not utils.verify_ldap_object('relativeDomainName=2,%s' % reverseZone2, {'pTRRecord': ['%s.%s.' % (computerProperties['name'], forwardZone2Name)]}):
				utils.fail('DNS PTR record for computers/%s differed from expectation after modification' % role)
			if not utils.verify_ldap_object('cn=%s,%s' % (computerProperties['name'], dhcpService2), {'univentionDhcpFixedAddress': ['10.20.40.2']}):
				utils.fail('DHCP entry for computers/%s differed from expectation after modification' % role)

			if utils.verify_ldap_object('relativeDomainName=%s,%s' % (computerProperties['name'], forwardZone1)):
				utils.fail('Could still find old DNS host record of computers/%s after the nework link has been changed' % role)
			if utils.verify_ldap_object('relativeDomainName=2,%s' % reverseZone1):
				utils.fail('Could still find old DNS PTR record of computers/%s after the network link has been changed' % role)
			if utils.verify_ldap_object('cn=%s,%s' % (computerProperties['name'], dhcpService1)):
				utils.fail('Could still find old DHCP entry of computers/%s after the network link has been changed' % role)








			# full reset for next role
			udm.cleanup()
