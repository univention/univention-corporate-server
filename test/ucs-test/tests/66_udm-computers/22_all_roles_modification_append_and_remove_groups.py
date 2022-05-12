#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Test appending and removing groups for all computer roles (except computers/ipmanagedclient)
## tags: [udm-computers]
## roles: [domaincontroller_master]
## exposure: careful
## packages:
##   - univention-config
##   - univention-directory-manager-tools

import pytest

from univention.testing import utils
from univention.testing.strings import random_name
from univention.testing.udm import UCSTestUDM

COMPUTER_MODULES = UCSTestUDM.COMPUTER_MODULES
COMPUTER_MODULES_EXCEPT_IPMANAGEDCLIENT = [i for i in COMPUTER_MODULES if i != 'computers/ipmanagedclient']


@pytest.mark.tags('udm-computers')
@pytest.mark.roles('domaincontroller_master')
@pytest.mark.exposure('careful')
@pytest.mark.parametrize('role', COMPUTER_MODULES_EXCEPT_IPMANAGEDCLIENT)
class Test_ComputerAllRoles():
	def test_all_roles_modification_append_and_remove_groups(self, udm, verify_ldap_object, role):
			"""Test appending and removing groups for all computer roles (except computers/ipmanagedclient)"""

			groups = (udm.create_group()[0], udm.create_group()[0], udm.create_group()[0], udm.create_group()[0])

			computerName = random_name()
			computer = udm.create_object(role, name=computerName)

			udm.modify_object(role, dn=computer, append={'groups': groups})
			utils.wait_for_connector_replication()
			# validate group memberships set during modification
			for group in groups:
				verify_ldap_object(group, {'memberUid': ['%s$' % computerName], 'uniqueMember': [computer]})

			udm.modify_object(role, dn=computer, remove={'groups': groups[:2]})
			utils.wait_for_connector_replication()
			# validate that group memberships of groups removed during seccond modification have been decomposed
			for group in groups[:2]:
				verify_ldap_object(group, {'memberUid': [], 'uniqueMember': []})

			# validate that the other group memberships are still unimpaired after seccond modification
			for group in groups[2:]:
				verify_ldap_object(group, {'memberUid': ['%s$' % computerName], 'uniqueMember': [computer]})
