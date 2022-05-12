#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Test appending and removing IP addresses for all computer roles
## tags: [udm-computers,apptest]
## roles: [domaincontroller_master]
## exposure: careful
## packages:
##   - univention-config
##   - univention-directory-manager-tools

import pytest

from univention.testing.strings import random_name
from univention.testing.udm import UCSTestUDM

COMPUTER_MODULES = UCSTestUDM.COMPUTER_MODULES


@pytest.mark.tags('udm-computers', 'apptest')
@pytest.mark.roles('domaincontroller_master')
@pytest.mark.exposure('careful')
@pytest.mark.parametrize('role', COMPUTER_MODULES)
class Test_ComputerAllRoles():
	def test_all_roles_modification_append_and_remove_ip(self, udm, verify_ldap_object, role):
			"""Test appending and removing IP addresses for all computer roles"""
			ipAddresses = ('10.20.30.40', '10.20.30.41', '10.20.30.42', '10.20.30.43')
			for ip in ipAddresses:  # FIXME: workaround for remaining locks
				udm.addCleanupLock('aRecord', ip)

			computer = udm.create_object(role, name=random_name(), append={'ip': ipAddresses[:2]})
			verify_ldap_object(computer, {'aRecord': ipAddresses[:2]})

			udm.modify_object(role, dn=computer, append={'ip': ipAddresses[2:]})
			verify_ldap_object(computer, {'aRecord': ipAddresses})

			udm.modify_object(role, dn=computer, remove={'ip': ipAddresses[:2]})
			verify_ldap_object(computer, {'aRecord': ipAddresses[2:]})
