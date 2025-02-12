#!/usr/share/ucs-test/runner pytest-3
## desc: Test groups/group
## tags: [udm,udm-groups,apptest]
## roles: [domaincontroller_master]
## exposure: safe
## packages:
##   - univention-config
##   - univention-directory-manager-tools

import pytest

from univention.admin import modules, uldap


@pytest.fixture()
def group():
    lo, position = uldap.getMachineConnection()
    modules.update()
    groups = modules.get('groups/group')
    modules.init(lo, position, groups)
    group = groups.object(None, lo, position)
    return group


def check_modlist(ml: list, added: list, removed: list, rdn: str = 'uid') -> None:
    print(ml)
    added_dn = [f'{rdn}={x},dc=base' for x in added]
    removed_dn = [f'{rdn}={x},dc=base' for x in removed]
    for attr, old, new in ml:
        if attr == 'uniqueMember':
            if old and not new:
                assert set(old) == {x.encode('UTF-8') for x in removed_dn}
            elif new and not old:
                assert set(new) == {x.encode('UTF-8') for x in added_dn}
            else:
                raise ValueError
        elif attr == 'memberUid':
            if old and not new:
                assert set(old) == {x.encode('UTF-8') for x in removed}
            elif new and not old:
                assert set(new) == {x.encode('UTF-8') for x in added}
            else:
                raise ValueError
        else:
            raise ValueError


def test_members_add(group):
    new_members = ['test1', 'TEST2', 'TEst3']
    group.info['users'] = [f'uid={x},dc=base' for x in new_members]
    ml = group._ldap_modlist()
    check_modlist(ml, new_members, [])


def test_members_add_case(group):
    new_members = ['test1', 'TEST2', 'TEst3']
    group.info['users'] = [f'UID={x},dc=base' for x in new_members]
    ml = group._ldap_modlist()
    check_modlist(ml, new_members, [], rdn='UID')


def test_members_modify(group):
    old_members = ['test1', 'TEST2', 'TEst3']
    new_members = ['test4', 'test5']
    group.oldinfo['users'] = [f'uid={x},dc=base' for x in old_members]
    group.info['users'] = [f'uid={x},dc=base' for x in new_members + old_members]
    ml = group._ldap_modlist()
    check_modlist(ml, new_members, [])


def test_members_remove(group):
    old_members = ['test1', 'TEST2', 'TEst3', 'test4', 'test5']
    new_members = ['test1', 'test5']
    group.oldinfo['users'] = [f'uid={x},dc=base' for x in old_members]
    group.info['users'] = [f'uid={x},dc=base' for x in new_members]
    ml = group._ldap_modlist()
    removed = list(set(old_members) - set(new_members))
    check_modlist(ml, [], removed)


def test_members_remove_case(group):
    old_members = ['test1', 'TEST2', 'TEst3', 'test4', 'test5']
    new_members = ['test1', 'test5']
    group.oldinfo['users'] = [f'uid={x},dc=base' for x in old_members]
    group.info['users'] = [f'UID={x},dc=base' for x in new_members]
    ml = group._ldap_modlist()
    removed = list(set(old_members) - set(new_members))
    check_modlist(ml, [], removed)


def test_members_remove_and_add(group):
    old_members = ['test1', 'TEST2', 'TEst3', 'test4', 'test5']
    new_members = ['test1', 'test5', 'test6', 'TEST7']
    group.oldinfo['users'] = [f'uid={x},dc=base' for x in old_members]
    group.info['users'] = [f'uid={x},dc=base' for x in new_members]
    ml = group._ldap_modlist()
    removed = list(set(old_members) - set(new_members))
    added = list(set(new_members) - set(old_members))
    check_modlist(ml, added, removed)


def test_members_dn_without_uid_nested_groups(group):
    new_members = ['test1', 'TEST2', 'TEst3']
    group.info['nestedGroups'] = [f'whatever={x},dc=base' for x in new_members]
    ml = group._ldap_modlist()
    check_modlist(ml, new_members, [], rdn='whatever')


def test_members_dn_without_uid_hosts(group):
    new_members = ['test1', 'TEST2', 'TEst3']
    group.info['hosts'] = [f'cn={x},dc=base' for x in new_members]
    ml = group._ldap_modlist()
    check_modlist(ml, new_members, [], rdn='cn')
