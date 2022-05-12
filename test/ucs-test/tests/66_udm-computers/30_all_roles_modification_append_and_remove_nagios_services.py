#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Test modifying nagiosServices for all computer roles
## tags: [udm-computers]
## roles: [domaincontroller_master]
## exposure: careful
## packages:
##   - univention-config
##   - univention-directory-manager-tools

import pytest

from univention.testing.strings import random_name, random_string
from univention.testing.udm import UCSTestUDM

COMPUTER_MODULES = UCSTestUDM.COMPUTER_MODULES


@pytest.mark.tags('udm-computers')
@pytest.mark.roles('domaincontroller_master')
@pytest.mark.exposure('careful')
@pytest.mark.parametrize('role', COMPUTER_MODULES)
class Test_ComputerAllRoles():
	def test_all_roles_modification_append_and_remove_nagios_services(self, udm, lo, verify_ldap_object, role):
			"""Test modifying nagiosServices for all computer roles"""
			nagiosServices = (
				udm.create_object('nagios/service', name=random_name(), checkCommand=random_string(), checkPeriod=random_string(), notificationPeriod=random_string()),
				udm.create_object('nagios/service', name=random_name(), checkCommand=random_string(), checkPeriod=random_string(), notificationPeriod=random_string()),
				udm.create_object('nagios/service', name=random_name(), checkCommand=random_string(), checkPeriod=random_string(), notificationPeriod=random_string()),
				udm.create_object('nagios/service', name=random_name(), checkCommand=random_string(), checkPeriod=random_string(), notificationPeriod=random_string())
			)
			computerIp = '10.20.30.2'
			computerName = random_name()

			# FIXME: workaround for remaining locks
			udm.addCleanupLock('aRecord', computerIp)

			# create computer, appending the first two nagiosServices
			computer = udm.create_object(
				role,
				options=['posix', 'nagios'],
				dnsEntryZoneForward=udm.create_object('dns/forward_zone', zone='%s.%s' % (random_name(), random_name()), nameserver=random_string(numeric=False)),
				name=computerName,
				ip=computerIp,
				wait_for=True,
			)
			computerAssociatedDomain = lo.getAttr(computer, 'associatedDomain')[0]

			udm.modify_object(role, dn=computer, append={'nagiosServices': nagiosServices})
			# validate that computer has been added to the new nagios services
			for nagiosService in nagiosServices:
				verify_ldap_object(nagiosService, {'univentionNagiosHostname': [b'%s.%s' % (computerName.encode('ASCII'), computerAssociatedDomain)]})

			# modify computer again, removing the nagios services which have been set during creation
			udm.modify_object(role, dn=computer, remove={'nagiosServices': nagiosServices[:2]})
			# validate that the computer has been removed from the related nagios services
			for nagiosService in nagiosServices[:2]:
				verify_ldap_object(nagiosService, {'univentionNagiosHostname': []})

			# validated that the computers is still set at the not removed nagios services
			for nagiosService in nagiosServices[2:]:
				verify_ldap_object(nagiosService, {'univentionNagiosHostname': [b'%s.%s' % (computerName.encode('ASCII'), computerAssociatedDomain)]})
