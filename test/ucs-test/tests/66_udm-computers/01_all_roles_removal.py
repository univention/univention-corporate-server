#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Remove object for all computer roles
## tags: [udm-computers]
## roles: [domaincontroller_master]
## exposure: careful
## packages:
##   - univention-config
##   - univention-directory-manager-tools

import pytest

import univention.testing.udm as udm_test
from univention.testing.decorators import SetTimeout
from univention.testing.strings import random_string

COMPUTER_MODULES = udm_test.UCSTestUDM.COMPUTER_MODULES


@pytest.mark.tags('udm-computers')
@pytest.mark.roles('domaincontroller_master')
@pytest.mark.exposure('careful')
@pytest.mark.parametrize('role', COMPUTER_MODULES)
class Test_ComputerAllRoles():
	def test_all_role_removal(self, udm, verify_ldap_object, role):
			"""Remove object for all computer roles"""
			computer = udm.create_object(role, name=random_string())
			udm.remove_object(role, dn=computer)

			SetTimeout(verify_ldap_object)(computer, should_exist=False)
