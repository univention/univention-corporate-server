#!/usr/share/ucs-test/runner pytest-3
## desc: Test udm performance in a big environment
## tags: [big_environment]
## exposure: dangerous
## packages:
##   - univention-directory-manager-tools

import time
from random import sample

import univention.admin
from univention.admin.rest.client import UDM as UDM_REST
from univention.config_registry import ConfigRegistry
from univention.testing import utils
from univention.udm import UDM


USERS = 200000
USER_WITH_NESTED_GROUPS = ['testuser160549', 'testuser549', 'testuser120549', 'testuser140549', 'testuser180549', 'testuser100549', 'testuser100547', 'testuser180547']


users_mod = UDM.machine().version(2).get('users/user')
groups_mod = UDM.admin().version(2).get('groups/group')
ucr = ConfigRegistry()
ucr.load()
admin_account = utils.UCSTestDomainAdminCredentials()
udm_rest = UDM_REST(
    uri='https://%(hostname)s.%(domainname)s/univention/udm/' % ucr,
    username=admin_account.username,
    password=admin_account.bindpw,
)
udm_rest_users = udm_rest.get('users/user')


def open_users(users: int = 100, roles: bool = False) -> None:
    users = [f'uid=testuser{x},cn=users,{ucr["ldap/base"]}' for x in sample(range(1, USERS), users)]
    for dn in users:
        user = users_mod.get(dn)
        if roles:
            user._orig_udm_object.open_guardian()
            assert len(user._orig_udm_object.info.get('guardianInheritedRoles', [])) > 290
        else:
            assert len(user._orig_udm_object.info.get('guardianInheritedRoles', [])) == 0


def open_users_rest(users: int = 100, roles: bool = False) -> None:
    users = [f'uid=testuser{x}' for x in sample(range(1, USERS), users)]
    properties = ['*']
    if roles:
        properties = ['*', 'guardianInheritedRoles']
    for s_filter in users:
        # TODO use get(dn)?
        res = udm_rest_users.search(s_filter, opened=True, properties=properties)
        res = next(iter(res))
        if roles:
            assert len(res.properties.get('guardianInheritedRoles', [])) > 290
        else:
            assert len(res.properties.get('guardianInheritedRoles', [])) == 0


def run_test(func, *args, **kwargs):
    t_total = 0
    reps = 3
    for i in range(reps):
        # TODO some kind of initialization, makes the first request after open_* faster
        open_users(users=1)
        open_users_rest(users=1)
        univention.admin.guardian_roles.get_group_role.cache_clear()
        t0 = time.time()
        func(*args, **kwargs)
        t_total += time.time() - t0
    d = t_total / reps
    print(f'{func.__name__} - {kwargs}: {d}')
    return d


def test_get_1_user():
    users = 1
    assert run_test(open_users, users=users, roles=True) < 0.8
    assert run_test(open_users, users=users, roles=False) < 0.04


def test_get_10_user():
    users = 10
    assert run_test(open_users, users=users, roles=True) < 0.8
    assert run_test(open_users, users=users, roles=False) < 0.1


def test_get_100_user():
    users = 100
    assert run_test(open_users, users=users, roles=True) < 1.8
    assert run_test(open_users, users=users, roles=False) < 1


def test_get_1000_user():
    users = 1000
    assert run_test(open_users, users=users, roles=True) < 10
    assert run_test(open_users, users=users, roles=False) < 7


def test_rest_get_1_user():
    users = 1
    assert run_test(open_users_rest, users=users, roles=True) < 0.4
    assert run_test(open_users_rest, users=users, roles=False) < 0.2


def test_rest_get_10_user():
    users = 10
    assert run_test(open_users_rest, users=users, roles=True) < 1.5
    assert run_test(open_users_rest, users=users, roles=False) < 1.3


def test_rest_get_100_user():
    users = 100
    assert run_test(open_users_rest, users=users, roles=True) < 10
    assert run_test(open_users_rest, users=users, roles=False) < 15


def test_rest_get_1000_user():
    users = 1000
    assert run_test(open_users_rest, users=users, roles=True) < 120
    assert run_test(open_users_rest, users=users, roles=False) < 100


def test_remove_one_user_from_big_group():
    allowed_run_time = 15
    groups = [
        'cn=testgroup400,cn=groups,dc=ucs,dc=test',
        'cn=testgroup800,cn=groups,dc=ucs,dc=test',
        'cn=testgroup1200,cn=groups,dc=ucs,dc=test',
    ]

    modification = {}
    for dn in groups:
        group = groups_mod.get(dn)
        assert len(group.props.users) >= 199999, len(group.props.users)
        user = sample(group.props.users, 1)[0]
        modification[group] = user

    # now the check
    try:
        duration = 0
        for group_obj, user_dn in modification.items():
            group_obj.props.users.remove(user_dn)
            ts = time.time()
            group_obj.save()
            duration += time.time() - ts
        duration_per_run = duration / len(groups)
        assert duration_per_run < allowed_run_time, f'move took longer than {allowed_run_time}s - {duration_per_run}s'
    finally:
        for group_obj, user_dn in modification.items():
            if user_dn not in group_obj.props.users:
                group_obj.props.users.append(user_dn)
            group_obj.save()
