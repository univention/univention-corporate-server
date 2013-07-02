#!/usr/share/ucs-test/runner python
## desc: Create maximal computers/ipmanagedclient and validate it's attributes as well as automatically created referring objects
## tags: [udm-computers]
## roles: [domaincontroller_master]
## exposure: careful
## packages:
##   - univention-config
##   - univention-directory-manager-tools


import smbpasswd
import univention.testing.udm as udm_test
import univention.testing.strings as uts
import univention.testing.utils as utils


if __name__ == '__main__':
	objectType = 'computers/ipmanagedclient'
	with udm_test.UCSTestUDM() as udm:
		dhcpZone = udm.create_object('dhcp/service', service = uts.random_name())
		
		properties = {
			'name': uts.random_name(),
			'description': uts.random_string(),
			'domain': '%s.%s' % (uts.random_name(), uts.random_name()),
			'mac': '01:23:45:67:89:ab',
			'network': udm.create_object('networks/network', name = uts.random_name(), network = '10.20.30.0', netmask = '24'),
			'ip': '10.20.30.2',
			'dnsEntryZoneForward': udm.create_object('dns/forward_zone', zone = '%s.%s' % (uts.random_name(), uts.random_name()), nameserver = uts.random_string()),
			'dnsEntryZoneReverse': udm.create_object('dns/reverse_zone', subnet = '10.20.30', nameserver = uts.random_string()),
			'inventoryNumber': uts.random_string(),
		}
		properties['dhcpEntryZone'] = '%s %s %s' % (dhcpZone, properties['ip'], properties['mac'])

		expectedLdap = {
			'cn': [properties['name']],
			'sn': [properties['name']],
			'description': [properties['description']],
			'associatedDomain': [properties['domain']],
			'macAddress': [properties['mac']],
			'univentionNetworkLink': [properties['network']],
			'aRecord': [properties['ip']],
			'univentionInventoryNumber': [properties['inventoryNumber']],
		}

		udm.addCleanupLock('aRecord', expectedLdap['aRecord'])
		udm.addCleanupLock('mac', expectedLdap['macAddress'])


		# validate computer ldap object
		computerDN = udm.create_object(objectType, **properties)
		if not utils.verify_ldap_object(computerDN, expectedLdap):
			utils.fail()

		# validate related DHCP host object
		if not utils.verify_ldap_object('cn=%s,%s' % (properties['name'], dhcpZone), {
			'dhcpHWAddress': ['ethernet %s' % properties['mac']],
			'univentionDhcpFixedAddress': [properties['ip']]
		}):
			utils.fail('Automatically created DHCP host object differs from expectation')

		# validate related A record
		if not utils.verify_ldap_object('relativeDomainName=%s,%s' % (properties['name'], properties['dnsEntryZoneForward']), {
			'aRecord': [properties['ip']],
			'relativeDomainName': [properties['name']],
			'zoneName': [properties['dnsEntryZoneForward'].split('zoneName=')[1].split(',')[0]]
		}):
			utils.fail('Automatically created A record differs from expectation')
		
		# validate related PTR record
		if not utils.verify_ldap_object('relativeDomainName=2,%s' % properties['dnsEntryZoneReverse'], {
			'relativeDomainName': '2',
			'pTRRecord': ['%s.%s.' % (properties['name'], properties['dnsEntryZoneForward'].split('zoneName=')[1].split(',')[0])],
			'zoneName': [properties['dnsEntryZoneReverse'].split('zoneName=')[1].split(',')[0]]
		}):
			utils.fail('Automatically created PTR record differs from expectation')
