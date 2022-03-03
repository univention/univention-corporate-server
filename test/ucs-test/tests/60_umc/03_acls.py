#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Test UMC ACLs
## roles:
##  - domaincontroller_master
## packages:
##  - univention-directory-manager-tools
##  - univention-management-console
## exposure: dangerous


import pytest

from univention.lib.umc import Forbidden
from univention.testing.umc import Client


def test_acls(udm, ucr):
	test_user, username = udm.create_user(wait_for_replication=False, check_for_drs_replication=False, wait_for=False)
	hostname = ucr.get('hostname')

	operation_sets = []

	for i in range(1, 11):
		operation_sets.append(udm.create_object(
			'settings/umc_operationset',
			position="cn=operations,cn=UMC,cn=univention,%s" % udm.LDAP_BASE,
			name='join%s' % i,
			description='Join%s' % i,
			operation=["join/*", "lib/server/*"],
			wait_for_replication=False
		))
	policy_dn = udm.create_object(
		'policies/umc',
		position="cn=UMC,cn=policies,%s" % udm.LDAP_BASE,
		name='test-umc-policy',
		wait_for_replication=False
	)
	udm.modify_object('users/user', dn=test_user, policy_reference=policy_dn, wait_for_replication=False)

	def _test_new_acl(operation_set_dn, new_values, should_work=True):
		udm.modify_object('settings/umc_operationset', dn=operation_set_dn, hosts=new_values, wait_for_replication=False)
		udm.modify_object('policies/umc', dn=policy_dn, allow=operation_set_dn, wait_for_replication=False)

		if should_work:
			data = Client(None, username, 'univention').umc_command('join/scripts/query').result
			assert isinstance(data, list), data
		else:
			with pytest.raises(Forbidden):
				Client(None, username, 'univention').umc_command('join/scripts/query').result

	_test_new_acl(operation_sets[0], ['systemrole:domaincontroller_master', 'systemrole:domaincontroller_backup'])
	_test_new_acl(operation_sets[1], ['systemrole:domaincontroller_master'])
	_test_new_acl(operation_sets[2], ['systemrole:domaincontroller_backup'], False)
	_test_new_acl(operation_sets[3], ['foo', '%s' % hostname])
	_test_new_acl(operation_sets[4], ['*'])
	_test_new_acl(operation_sets[5], ['foo'], False)
	_test_new_acl(operation_sets[6], ['service:LDAP'])
	_test_new_acl(operation_sets[7], ['service:LDAP', 'service:FOO'])
	_test_new_acl(operation_sets[8], ['service:BAR'], False)
	_test_new_acl(operation_sets[9], ['*%s' % hostname[2:]])
