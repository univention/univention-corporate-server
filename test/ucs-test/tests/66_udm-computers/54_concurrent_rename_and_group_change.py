#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: rename and change groups at once
## tags: [udm-computers]
## bugs: [41694]
## roles: [domaincontroller_master]
## exposure: careful

import pytest

from univention.testing.strings import random_string


@pytest.mark.tags('udm-computers')
@pytest.mark.roles('domaincontroller_master')
@pytest.mark.exposure('careful')
def test_concurrent_rename_and_group_change(udm, verify_ldap_object):
		"""rename and change groups at once"""
		# bugs: [41694]
		groupdn_a, name = udm.create_group()
		groupdn_b, name = udm.create_group()
		groupdn_c, name = udm.create_group()
		computerdn = udm.create_object('computers/ubuntu', name=random_string(), groups=[groupdn_a, groupdn_b])
		verify_ldap_object(groupdn_a, {'uniqueMember': [computerdn]})
		verify_ldap_object(groupdn_b, {'uniqueMember': [computerdn]})
		print('created %s in %s and %s' % (computerdn, groupdn_a, groupdn_b))

		new_name = random_string()
		computerdn_new = udm.modify_object('computers/ubuntu', dn=computerdn, name=new_name, remove={'groups': [groupdn_a]}, append={'groups': [groupdn_c]})
		print('moved to %s' % (computerdn_new,))
		verify_ldap_object(computerdn, should_exist=False)
		verify_ldap_object(computerdn_new, should_exist=True)
		verify_ldap_object(groupdn_b, {'uniqueMember': [computerdn_new]})
		verify_ldap_object(groupdn_c, {'uniqueMember': [computerdn_new]})
		verify_ldap_object(groupdn_a, {'uniqueMember': []})
