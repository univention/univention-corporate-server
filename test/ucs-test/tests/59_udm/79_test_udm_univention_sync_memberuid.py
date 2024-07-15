#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Test the univention-sync-memberuid script
## tags: [udm]
## roles: [domaincontroller_master]
## exposure: careful
## packages:
## - univention-directory-manager-tools
## timeout: 0

import subprocess

import pytest


TOOL_PATH = '/usr/share/univention-directory-manager-tools/univention-sync-memberuid'


@pytest.fixture()
def inconsistent_membership(udm, lo):
    ret = {}
    ret['groups'] = []

    user_dn, user_name = udm.create_user()
    ret['user'] = (user_dn, user_name)

    for i in range(2):
        group_dn, group_name = udm.create_group()
        ret['groups'].append((group_dn, group_name))

        udm.modify_object("groups/group", dn=group_dn, users=[user_dn])

        lo.modify(group_dn, [('memberUid', user_name.encode('utf-8'), f"{user_name}+MODIFIED".encode('utf-8'))])

    return ret


def assert_memberUid_is_modified(lo, group_dn, user_name):
    result = lo.search(base=group_dn, scope="base")
    assert result[0][1]['memberUid'][0].decode('utf-8') == f"{user_name}+MODIFIED"


def assert_memberUid_is_correct(lo, group_dn, user_name):
    result = lo.search(base=group_dn, scope="base")
    assert result[0][1]['memberUid'][0].decode('utf-8') == f"{user_name}"


def test_inconsistent_membership(lo, inconsistent_membership):
    group_dn, _ = inconsistent_membership['groups'][0]
    _, user_name = inconsistent_membership['user']

    assert_memberUid_is_modified(lo, group_dn, user_name)
    subprocess.run(TOOL_PATH, check=True)
    assert_memberUid_is_correct(lo, group_dn, user_name)


def test_exclude_groups(lo, inconsistent_membership):
    group_dn1, _group_name1 = inconsistent_membership['groups'][0]
    group_dn2, group_name2 = inconsistent_membership['groups'][1]
    _user_dn, user_name = inconsistent_membership['user']

    assert_memberUid_is_modified(lo, group_dn1, user_name)
    assert_memberUid_is_modified(lo, group_dn2, user_name)

    subprocess.run([TOOL_PATH, '-x', group_name2], check=True)

    assert_memberUid_is_correct(lo, group_dn1, user_name)
    assert_memberUid_is_modified(lo, group_dn2, user_name)


def test_limit_to_group(lo, inconsistent_membership):
    group_dn1, group_name1 = inconsistent_membership['groups'][0]
    group_dn2, _group_name2 = inconsistent_membership['groups'][1]
    _user_dn, user_name = inconsistent_membership['user']

    assert_memberUid_is_modified(lo, group_dn1, user_name)
    assert_memberUid_is_modified(lo, group_dn2, user_name)

    subprocess.run([TOOL_PATH, '-g', group_name1], check=True)

    assert_memberUid_is_correct(lo, group_dn1, user_name)
    assert_memberUid_is_modified(lo, group_dn2, user_name)


def test_fix_multiple_groups_and_users(udm, lo):
    groups = []
    users = []
    for i in range(5):
        users.append(udm.create_user())
        groups.append(udm.create_group())

    for group in groups:
        group_dn = group[0]
        udm.modify_object("groups/group", dn=group_dn, users=[user[0] for user in users])

    def modify_memberUid(group, user):
        group_dn = group[0]
        user_name = user[1]
        lo.modify(group_dn, [('memberUid', user_name.encode('utf-8'), f"{user_name}+MODIFIED".encode('utf-8'))])

    modify_memberUid(groups[2], users[2])
    modify_memberUid(groups[0], users[4])
    modify_memberUid(groups[1], users[1])
    modify_memberUid(groups[3], users[0])
    modify_memberUid(groups[4], users[3])
    modify_memberUid(groups[0], users[2])
    modify_memberUid(groups[1], users[3])
    subprocess.run(TOOL_PATH, check=True)

    for group in groups:
        result = lo.search(base=group_dn, scope="base")[0]
        for memberUid in result[1]['memberUid']:
            memberUid = memberUid.decode('UTF-8')
            assert memberUid in [user[1] for user in users]
