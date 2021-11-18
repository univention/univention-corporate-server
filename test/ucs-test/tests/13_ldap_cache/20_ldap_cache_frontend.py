#!/usr/share/ucs-test/runner pytest
## desc: Create a group with users and look at the frontend functions
## roles-not: [basesystem]
## exposure: dangerous
## packages:
##   - univention-group-membership-cache


from univention.ldap_cache.frontend import groups_for_user, users_in_group


def test_groups_for_user(udm, group1, group2, user1, dn_domain_users, dn_builtin_users):
    """
    Test if the groups for a user are returned correctly.
    """
    udm.modify_object('users/user', dn=user1, groups=[group1, group2], wait_for_replication=True)
    # cn=domain users,cn=groups is default created group
    result_groups = groups_for_user(user1)
    if dn_builtin_users.lower() in result_groups: result_groups.remove(dn_builtin_users.lower())
    assert sorted(result_groups) == sorted([dn_domain_users.lower(), group1.lower(), group2.lower()])


def test_groups_for_user_not_nested(udm, group1, group2, group3, user1, dn_domain_users, dn_builtin_users):
    """
    Test if the groups for a user are returned correctly.
    """

    udm.modify_object('groups/group', dn=group1, users=[user1], wait_for_replication=False)
    udm.modify_object('groups/group', dn=group2, nestedGroup=group1, wait_for_replication=False)
    udm.modify_object('groups/group', dn=group3, nestedGroup=group2, wait_for_replication=True)
    # cn=domain users,cn=groups is default created group
    result_groups = groups_for_user(user1, consider_nested_groups=False)
    assert sorted(result_groups) == sorted([dn_domain_users.lower(), group1.lower()])
    result_groups = groups_for_user(user1)
    if dn_builtin_users.lower() in result_groups: result_groups.remove(dn_builtin_users.lower())
    assert sorted(result_groups) == sorted([dn_domain_users.lower(), group1.lower(), group2.lower(), group3.lower()])


def test_users_in_group(udm, group1, group2, user1, user2, user3):
    """
    Test if the users in a group are returned correctly.
    """
    udm.modify_object('groups/group', dn=group1, users=[user1, user2, user3], wait_for_replication=True)
    assert sorted(users_in_group(group1)) == sorted([user1.lower(), user2.lower(), user3.lower()])
    assert users_in_group(group2) == []
    udm.modify_object('groups/group', dn=group2, nestedGroup=[group1], wait_for_replication=True)
    assert users_in_group(group2, consider_nested_groups=False) == []
    assert sorted(users_in_group(group2)) == sorted([user1.lower(), user2.lower(), user3.lower()])
