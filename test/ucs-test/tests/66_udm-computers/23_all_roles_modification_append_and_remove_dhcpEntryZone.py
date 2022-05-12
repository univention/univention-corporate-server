#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Test appending and removing dhcpEntryZone for all computer roles
## tags: [udm-computers]
## roles: [domaincontroller_master]
## exposure: careful
## packages:
##   - univention-config
##   - univention-directory-manager-tools

import ldap.dn
import pytest

from univention.testing.strings import random_name
from univention.testing.udm import UCSTestUDM

COMPUTER_MODULES = UCSTestUDM.COMPUTER_MODULES


@pytest.mark.tags('udm-computers')
@pytest.mark.roles('domaincontroller_master')
@pytest.mark.exposure('careful')
@pytest.mark.parametrize('role', COMPUTER_MODULES)
class Test_ComputerAllRoles():
	def test_all_roles_modification_append_and_remove_dhcpEntryZone(self, udm, verify_ldap_object, role):
			"""Test appending and removing dhcpEntryZone for all computer roles"""
			computerName = random_name()

			dhcpEntryZones = (
				['%s' % udm.create_object('dhcp/service', service=random_name()), '10.20.30.40', '11:11:11:11:11:11'],
				['%s' % udm.create_object('dhcp/service', service=random_name()), '10.20.30.41', '22:22:22:22:22:22'],
				['%s' % udm.create_object('dhcp/service', service=random_name()), '10.20.30.42', '33:33:33:33:33:33'],
				['%s' % udm.create_object('dhcp/service', service=random_name()), '10.20.30.43', '44:44:44:44:44:44']
			)

			computer = udm.create_object(role, name=computerName)

			udm.modify_object(role, dn=computer, append={
				'ip': [zone[1] for zone in dhcpEntryZones],
				'mac': [zone[2] for zone in dhcpEntryZones],
				'dhcpEntryZone': [' '.join(zone) for zone in dhcpEntryZones]
			})
			for service, ip, mac in dhcpEntryZones:
				verify_ldap_object('cn=%s,%s' % (computerName, service), {
					'univentionDhcpFixedAddress': [ip],
					'dhcpHWAddress': ['ethernet %s' % mac]
				})

			udm.modify_object(role, dn=computer, remove={
				'ip': [zone[1] for zone in dhcpEntryZones[:2]],
				'mac': [zone[2] for zone in dhcpEntryZones[:2]],
				'dhcpEntryZone': [' '.join(zone) for zone in dhcpEntryZones[:2]]
			})
			for service, ip, mac in dhcpEntryZones[:2]:
				verify_ldap_object('cn=%s,%s' % (ldap.dn.escape_dn_chars(computerName), service), should_exist=False)

			for service, ip, mac in dhcpEntryZones[2:]:
				verify_ldap_object('cn=%s,%s' % (ldap.dn.escape_dn_chars(computerName), service), {
					'univentionDhcpFixedAddress': [ip],
					'dhcpHWAddress': ['ethernet %s' % mac]
				})
