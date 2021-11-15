#!/usr/share/ucs-test/runner python
## desc: Quota share cache; create and remove shares
## roles-not: [basesystem]
## exposure: careful
## packages:
##   - univention-group-membership-cache

import pytest

from univention.testing.utils import wait_for_replication
from univention.ldap_cache.frontend import groups_for_user, users_in_group

def test_groups_for_user(udm, group1, group2, user1):
    """
    Test if the groups for a user are returned correctly.
    """
    udm.modify_object('groups/group', dn=group1, users=[user1], wait_for_replication=False)
    udm.modify_object('groups/group', dn=group2, users=[user1], wait_for_replication=False)
    wait_for_replication()
    # cn=domain users,cn=groups is default created group
    result_groups = groups_for_user(user1)
    assert all(elem in result_groups for elem in [group1, group2])


def test_groups_for_user_not_nested(udm, group1, group2, group3, user1):
    """
    Test if the groups for a user are returned correctly.
    """

    udm.modify_object('groups/group', dn=group1, users=[user1], wait_for_replication=False)
    udm.modify_object('groups/group', dn=group2, nestedGroup=group1, wait_for_replication=False)
    udm.modify_object('groups/group', dn=group3, nestedGroup=group2, wait_for_replication=False)
    wait_for_replication()
    # cn=domain users,cn=groups is default created group
    result_groups = groups_for_user(user1, consider_nested_groups=False)
    print(result_groups)
    assert all(elem in result_groups for elem in [group1])
    assert all(elem not in result_groups for elem in [group2, group3])
    result_groups = groups_for_user(user1)
    assert all(elem in result_groups for elem in [group1, group3, group3])
1

def test_users_in_group(udm, group1, user1, user2, user3):
    """
    Test if the users in a group are returned correctly.
    """
    udm.modify_object('groups/group', dn=group1, users=[user1, user2, user3], wait_for_replication=False)
    wait_for_replication()
    assert sorted(users_in_group(group1)) == sorted([user1, user2, user3])