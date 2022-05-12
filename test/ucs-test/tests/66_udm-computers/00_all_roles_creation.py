#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Create minimal object for all computer roles
## tags: [udm-computers,apptest]
## roles: [domaincontroller_master]
## exposure: careful
## packages:
##   - univention-config
##   - univention-directory-manager-tools

import pytest

import univention.testing.udm as udm_test
from univention.testing.strings import random_string

COMPUTER_MODULES = udm_test.UCSTestUDM.COMPUTER_MODULES


@pytest.mark.tags('udm-computers', 'apptest')
@pytest.mark.roles('domaincontroller_master')
@pytest.mark.exposure('careful')
@pytest.mark.parametrize('role', COMPUTER_MODULES)
class Test_ComputerAllRoles():
	def test_all_roles_creation(self, udm, verify_ldap_object, role):
			"""Create minimal object for all computer roles"""
			computer = udm.create_object(role, name=random_string())
			verify_ldap_object(computer)
