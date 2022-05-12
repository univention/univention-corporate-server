#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Create minimal object for all computer roles and check univentionLastUsedValue
## tags: [udm-computers,apptest]
## roles: [domaincontroller_master]
## exposure: careful
## packages:
##   - univention-config
##   - univention-directory-manager-tools

'''
Computer objects request a uidNumber when creating an object, but the value of
univentionLastUsedValue has never been incremented.
Since UCS 4.3-2erratumX this is no longer the case and univentionLastUsedValue
is never changed.
'''

import time

import pytest

import univention.testing.udm as udm_test
from univention.testing.strings import random_string

COMPUTER_MODULES = udm_test.UCSTestUDM.COMPUTER_MODULES


@pytest.fixture(scope='class')
def wait_for_replication_cleanup(wait_for_replication):
	yield
	wait_for_replication()


@pytest.mark.tags('udm-computers', 'apptest')
@pytest.mark.roles('domaincontroller_master')
@pytest.mark.exposure('careful')
@pytest.mark.parametrize('role', COMPUTER_MODULES)
class Test_ComputerAllRoles():
	def test_all_roles_univentionLastUsedValue(self, udm, ucr, lo, verify_ldap_object, wait_for_replication_cleanup, role):
				"""Create minimal object for all computer roles and check univentionLastUsedValue"""

				luv_dn = 'cn=uidNumber,cn=temporary,cn=univention,%s' % (ucr.get('ldap/base'),)

				lastUsedValue_old = lo.get(luv_dn).get('univentionLastUsedValue', [-1])[0]
				computer_dn = udm.create_object(role, name=random_string(), wait_for_replication=False)
				verify_ldap_object(computer_dn)
				lastUsedValue_new = lo.get(luv_dn).get('univentionLastUsedValue', [-1])[0]

				if role == 'computers/ipmanagedclient':
					assert lastUsedValue_old == lastUsedValue_new, f'Create {role} univentionLastUsedValue did change, but it should not!'
				else:
					assert lastUsedValue_old != lastUsedValue_new, f'Create {role} with automatic uidNumber: univentionLastUsedValue did not change, but it should!'

				lastUsedValue_old = lo.get(luv_dn).get('univentionLastUsedValue', [-1])[0]
				kwargs = {
					'dn': computer_dn,
					'description': 'modified at {}'.format(time.ctime()),
					'wait_for_replication': False,
				}
				computer_dn = udm.modify_object(role, **kwargs)
				verify_ldap_object(computer_dn, expected_attr={'description': [kwargs['description']]})
				lastUsedValue_new = lo.get(luv_dn).get('univentionLastUsedValue', [-1])[0]

				assert lastUsedValue_old == lastUsedValue_new, f'Modified {role} with specified uidNumber: univentionLastUsedValue did change, but it should not!'
