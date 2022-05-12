#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Validate nagios for all computer roles
## tags: [udm-computers]
## roles: [domaincontroller_master]
## exposure: careful
## packages:
##   - univention-config
##   - univention-directory-manager-tools

import pytest

import univention.testing.udm as udm_test
from univention.testing.strings import random_name, random_string

COMPUTER_MODULES = udm_test.UCSTestUDM.COMPUTER_MODULES


@pytest.mark.tags('udm-computers')
@pytest.mark.roles('domaincontroller_master')
@pytest.mark.exposure('careful')
@pytest.mark.parametrize('role', COMPUTER_MODULES)
class Test_ComputerAllRoles():
	def test_all_roles_check_nagios(self, udm, lo, verify_ldap_object, role):
			"""Validate nagios for all computer roles"""

			forwardZone = udm.create_object('dns/forward_zone', zone='%s.%s' % (random_name(), random_name()), nameserver=random_string(numeric=False))
			nagiosService = udm.create_object('nagios/service', name=random_name(), checkCommand=random_string(), checkPeriod=random_string(), notificationPeriod=random_string())

			nagiosParentProperties = {
				'options': ['nagios'],
				'name': random_name(),
				'ip': '10.20.30.2'
			}
			# FIXME: workaround for remaining locks
			udm.addCleanupLock('aRecord', nagiosParentProperties['ip'])

			computerProperties = {
				'dnsEntryZoneForward': forwardZone,
				'nagiosServices': nagiosService,
				'nagiosContactEmail': '%s@%s.%s' % (random_name(), random_name(), random_name()),
				'nagiosParents': udm.create_object('computers/domaincontroller_backup', dnsEntryZoneForward=forwardZone, **nagiosParentProperties),
				'name': random_name(),
				'ip': '10.20.30.3',
				'options': ['posix', 'nagios']
			}
			# FIXME: workaround for remaining locks
			udm.addCleanupLock('aRecord', computerProperties['ip'])

			computer = udm.create_object(role, wait_for=True, **computerProperties)

			# validate that nagios related properties of computer are set correctly
			verify_ldap_object(computer, {
				'univentionNagiosEmail': [computerProperties['nagiosContactEmail']],
				'univentionNagiosEnabled': ['1'],
				'univentionNagiosParent': [b'%s.%s' % (nagiosParentProperties['name'].encode('UTF-8'), lo.getAttr(computerProperties['nagiosParents'], 'associatedDomain')[0])]
			})

			# check if computer has been added to nagios service
			verify_ldap_object(nagiosService, {'univentionNagiosHostname': [b'%s.%s' % (computerProperties['name'].encode('UTF-8'), lo.getAttr(computer, 'associatedDomain')[0])]})
