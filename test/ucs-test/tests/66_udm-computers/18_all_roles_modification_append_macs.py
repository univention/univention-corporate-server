#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Append macs during modification for all computer roles
## tags: [udm-computers,apptest]
## roles: [domaincontroller_master]
## exposure: careful
## packages:
##   - univention-config
##   - univention-directory-manager-tools

import pytest

import univention.testing.udm as udm_test
from univention.testing.strings import random_name

COMPUTER_MODULES = udm_test.UCSTestUDM.COMPUTER_MODULES


@pytest.mark.tags('udm-computers', 'apptest')
@pytest.mark.roles('domaincontroller_master')
@pytest.mark.exposure('careful')
@pytest.mark.parametrize('role', COMPUTER_MODULES)
class Test_ComputerAllRoles():
	def test_all_roles_modification_append_macs(self, udm, verify_ldap_object, role):
			"""Append macs during modification for all computer roles"""
			macAddresses = ['11:11:11:11:11:11', '22:22:22:22:22:22']

			for mac in macAddresses:  # FIXME: workaround for remaining locks
				udm.addCleanupLock('mac', mac)

			computer = udm.create_object(role, name=random_name())

			udm.modify_object(role, dn=computer, append={'mac': macAddresses[:2]})
			verify_ldap_object(computer, {'macAddress': macAddresses})
