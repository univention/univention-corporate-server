#!/usr/share/ucs-test/runner python
## desc: Test appending and removing dhcpEntryZones for all computer roles
## tags: [udm-computers, new]
## roles: [domaincontroller_master]
## exposure: careful
## packages:
##   - univention-config
##   - univention-directory-manager-tools


import univention.testing.udm as udm_test
import univention.testing.strings as uts
import univention.testing.utils as utils


if __name__ == '__main__':
	for role in udm_test.UCSTestUDM.COMPUTER_MODULES:
		computerName = uts.random_name()

		with udm_test.UCSTestUDM() as udm:
			dhcpEntryZones = (
				['%s' % udm.create_object('dhcp/service', service = uts.random_name()), '10.20.30.40', '11:11:11:11:11:11'],
				['%s' % udm.create_object('dhcp/service', service = uts.random_name()), '10.20.30.41', '22:22:22:22:22:22'],
				['%s' % udm.create_object('dhcp/service', service = uts.random_name()), '10.20.30.42', '33:33:33:33:33:33'],
				['%s' % udm.create_object('dhcp/service', service = uts.random_name()), '10.20.30.43', '44:44:44:44:44:44']
			)

			computer = udm.create_object(role, name = computerName, append = {
				'ip': [zone[1] for zone in dhcpEntryZones[:2]],
				'mac': [zone[2] for zone in dhcpEntryZones[:2]],
				'dhcpEntryZone': [' '.join(zone) for zone in dhcpEntryZones[:2]]
			})
			for service, ip, mac in dhcpEntryZones[:2]:
				if not utils.verify_ldap_object('cn=%s,%s' % (computerName, service), {
					'univentionDhcpFixedAddress': [ip],
					'dhcpHWAddress': ['ethernet %s' % mac]
				}):
					utils.fail('DHCP host object for %s in %s differed from expectation' % (role, service))

			udm.modify_object(role, dn = computer, append = {
				'ip': [zone[1] for zone in dhcpEntryZones[2:]],
				'mac': [zone[2] for zone in dhcpEntryZones[2:]],
				'dhcpEntryZone': [' '.join(zone) for zone in dhcpEntryZones[2:]]
			})
			for service, ip, mac in dhcpEntryZones:
				if not utils.verify_ldap_object('cn=%s,%s' % (computerName, service), {
					'univentionDhcpFixedAddress': [ip],
					'dhcpHWAddress': ['ethernet %s' % mac]
				}):
					utils.fail('DHCP host object for %s in %s differed from expectation' % (role, service))
		
			udm.modify_object(role, dn = computer, remove = {
				'ip': [zone[1] for zone in dhcpEntryZones[:2]],
				'mac': [zone[2] for zone in dhcpEntryZones[:2]],
				'dhcpEntryZone': [' '.join(zone) for zone in dhcpEntryZones[:2]]
			})
			for service, ip, mac in dhcpEntryZones[:2]:
				if utils.verify_ldap_object('cn=%s,%s' % (computerName, service)):
					utils.fail('Could still find DHCP host object for %s in %s after the related dhcpEntryZone entry should have been removed' % (role, service))

			for service, ip, mac in dhcpEntryZones[2:]:
				if not utils.verify_ldap_object('cn=%s,%s' % (computerName, service), {
					'univentionDhcpFixedAddress': [ip],
					'dhcpHWAddress': ['ethernet %s' % mac]
				}):
					utils.fail('DHCP host object for %s in %s has been removed eventhough it should have not' % (role, service))

