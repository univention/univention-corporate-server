#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Test appending and removing dhcpEntryZone for all computer roles
## tags: [udm-computers]
## roles: [domaincontroller_master]
## bugs: [44937]
## exposure: careful
## packages:
##   - univention-config
##   - univention-directory-manager-tools

import ldap.dn
import pytest

import univention.testing.udm as udm_test
from univention.testing.strings import random_name

COMPUTER_MODULES = udm_test.UCSTestUDM.COMPUTER_MODULES


@pytest.mark.tags('udm-computers')
@pytest.mark.roles('domaincontroller_master')
@pytest.mark.exposure('careful')
@pytest.mark.parametrize('role', COMPUTER_MODULES)
def test_multiple_dhcp_entry_zones(udm, verify_ldap_object, role):
			"""Test appending and removing dhcpEntryZone for all computer roles"""
			# bugs: [44937]
			computerName = random_name()

			service = udm.create_object('dhcp/service', service=random_name())
			dhcpEntryZones = (
				[service, '10.20.30.40', '11:11:11:11:11:11'],
				[service, '10.20.30.41', '22:22:22:22:22:22'],
				[service, '10.20.30.42', '33:33:33:33:33:33'],
				[service, '10.20.30.43', '44:44:44:44:44:44']
			)

			computer = udm.create_object(role, name=computerName)

			udm.modify_object(role, dn=computer, append={
				'ip': [zone[1] for zone in dhcpEntryZones],
				'mac': [zone[2] for zone in dhcpEntryZones],
				'dhcpEntryZone': [' '.join(zone) for zone in dhcpEntryZones]
			})
			for i, (service, ip, mac) in enumerate(dhcpEntryZones, -1):
				addon = '' if i < 0 else '_uv%d' % (i,)
				verify_ldap_object('cn=%s%s,%s' % (computerName, addon, service), {
					'univentionDhcpFixedAddress': [ip],
					'dhcpHWAddress': ['ethernet %s' % mac]
				})

			udm.modify_object(role, dn=computer, remove={
				'ip': [zone[1] for zone in dhcpEntryZones[:2]],
				'mac': [zone[2] for zone in dhcpEntryZones[:2]],
				'dhcpEntryZone': [' '.join(zone) for zone in dhcpEntryZones[:2]]
			})
			for i, (service, ip, mac) in list(enumerate(dhcpEntryZones, -1))[:2]:
				addon = '' if i < 0 else '_uv%d' % (i,)
				verify_ldap_object('cn=%s%s,%s' % (ldap.dn.escape_dn_chars(computerName), addon, service), should_exist=False)

			for i, (service, ip, mac) in list(enumerate(dhcpEntryZones, -1))[2:]:
				addon = '' if i < 0 else '_uv%d' % (i,)
				verify_ldap_object('cn=%s%s,%s' % (ldap.dn.escape_dn_chars(computerName), addon, service), {
					'univentionDhcpFixedAddress': [ip],
					'dhcpHWAddress': ['ethernet %s' % mac]
				})
