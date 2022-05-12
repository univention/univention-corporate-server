#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Test modifying shell for all computer roles (except computers/ipmanagedclient)
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
COMPUTER_MODULES_EXCEPT_IPMANAGEDCLIENT = [i for i in COMPUTER_MODULES if i != 'computers/ipmanagedclient']


@pytest.mark.tags('udm-computers')
@pytest.mark.roles('domaincontroller_master')
@pytest.mark.exposure('careful')
@pytest.mark.parametrize('role', COMPUTER_MODULES_EXCEPT_IPMANAGEDCLIENT)
class Test_ComputerAllRoles():
	def test_all_roles_modification_set_shell(self, udm, verify_ldap_object, role):
			"""Test modifying shell for all computer roles (except computers/ipmanagedclient)"""
			shell = random_string()

			computer = udm.create_object(role, name=random_name())
			udm.modify_object(role, dn=computer, shell=shell)
			verify_ldap_object(computer, {'loginShell': [shell]})
