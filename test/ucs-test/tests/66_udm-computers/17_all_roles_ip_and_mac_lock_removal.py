#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Check if IP and MAC address locks are removed after computer creation and modification for all computer roles
## tags: [udm-computers]
## roles: [domaincontroller_master]
## bugs: [15743]
## exposure: careful
## packages:
##   - univention-config
##   - univention-directory-manager-tools

import pytest

import univention.testing.udm as udm_test
from univention.testing.strings import random_name

COMPUTER_MODULES = udm_test.UCSTestUDM.COMPUTER_MODULES


@pytest.mark.tags('udm-computers')
@pytest.mark.roles('domaincontroller_master')
@pytest.mark.exposure('careful')
@pytest.mark.parametrize('role', COMPUTER_MODULES)
class Test_ComputerAllRoles():
	def test_all_roles_ip_and_mac_lock_removal(self, udm, ucr, verify_ldap_object, role):
			"""Check if IP and MAC address locks are removed after computer creation and modification for all computer roles"""
			# bugs: [15743]
			properties = {
				'ip': '10.20.30.40',
				'mac': '01:23:45:67:89:ab'
			}

			newProperties = {
				'ip': '10.20.30.41',
				'mac': '01:23:45:67:89:ac'
			}

			lockContainer = 'cn=temporary,cn=univention,%s' % ucr['ldap/base']

			computer = udm.create_object(role, name=random_name(), **properties)
			verify_ldap_object('cn=%s,cn=aRecord,%s' % (properties['ip'], lockContainer), should_exist=False)
			verify_ldap_object('cn=%s,cn=mac,%s' % (properties['mac'], lockContainer), should_exist=False)

			udm.modify_object(role, dn=computer, **newProperties)
			verify_ldap_object('cn=%s,cn=aRecord,%s' % (newProperties['ip'], lockContainer), should_exist=False)
			verify_ldap_object('cn=%s,cn=mac,%s' % (newProperties['mac'], lockContainer), should_exist=False)
