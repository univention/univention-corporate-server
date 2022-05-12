#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Test setting inventoryNumber during modification for all computer roles
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
	def test_all_roles_modification_set_inventoryNumber(self, udm, verify_ldap_object, role):
			"""Test setting inventoryNumber during modification for all computer roles"""
			inventoryNumber = random_string()

			computer = udm.create_object(role, name=random_name())
			udm.modify_object(role, dn=computer, inventoryNumber=inventoryNumber)
			verify_ldap_object(computer, {'univentionInventoryNumber': [inventoryNumber]})
