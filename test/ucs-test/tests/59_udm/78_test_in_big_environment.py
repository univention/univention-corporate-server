#!/usr/share/ucs-test/runner pytest-3
## desc: Test udm performance in a big environment
## tags:
##   - big_environment
##   - performance
## exposure: dangerous
## packages:
##   - univention-directory-manager-tools

import time
from random import sample
from typing import Callable

import pytest

import univention.admin
from univention.admin.rest.client import UDM as UDM_REST
from univention.config_registry import ucr
from univention.testing import utils
from univention.udm import UDM


USERS = 200000
USER_WITH_NESTED_GROUPS = ['testuser160549', 'testuser549', 'testuser120549', 'testuser140549', 'testuser180549', 'testuser100549', 'testuser100547', 'testuser180547']


users_mod = UDM.machine().version(2).get('users/user')
admin_account = utils.UCSTestDomainAdminCredentials()
udm_rest = UDM_REST(
    uri='https://%(hostname)s.%(domainname)s/univention/udm/' % ucr,
    username=admin_account.username,
    password=admin_account.bindpw,
)
udm_rest_users = udm_rest.get('users/user')


def open_users(users: int = 100, roles: bool = False) -> None:
    for x in sample(range(1, USERS), users):
        dn = f'uid=testuser{x},cn=users,{ucr["ldap/base"]}'
        user = users_mod.get(dn)
        if roles:
            user._orig_udm_object.open_guardian()
            assert len(user._orig_udm_object.info.get('guardianInheritedRoles', [])) > 290
        else:
            assert len(user._orig_udm_object.info.get('guardianInheritedRoles', [])) == 0


def open_users_rest(users: int = 100, roles: bool = False) -> None:
    properties = ['*', 'guardianInheritedRoles'] if roles else ['*']
    for x in sample(range(1, USERS), users):
        s_filter = f'uid=testuser{x}'
        # TODO use get(dn)?
        res = udm_rest_users.search(s_filter, opened=True, properties=properties)
        res = next(iter(res))
        if roles:
            assert len(res.properties.get('guardianInheritedRoles', [])) > 290
        else:
            assert len(res.properties.get('guardianInheritedRoles', [])) == 0


@pytest.fixture(scope='session')
def open_once():
    # TODO some kind of initialization, makes the first request after open_* faster
    open_users(users=1)
    open_users_rest(users=1)


def run_test(func: Callable[[int, bool], None], *args, **kwargs) -> float:
    t_total = 0.0
    reps = 3
    for i in range(reps):
        univention.admin.guardian_roles.get_group_role.cache_clear()
        t0 = time.monotonic()
        func(*args, **kwargs)
        t_total += time.monotonic() - t0
    d = t_total / reps
    print(f'{func.__name__} - {kwargs}: {d}')
    return d


@pytest.mark.parametrize("users,roles,maxt", [
    (1, True, 0.6),
    (1, False, 0.02),
    (10, True, 0.6),
    (10, False, 0.07),
    (100, True, 1.5),
    (100, False, 1.0),
    (1000, True, 9.0),
    (1000, False, 6.0),
])
def test_get_user(users: int, roles: bool, maxt: float, open_once) -> None:
    assert run_test(open_users, users=users, roles=roles) < maxt


@pytest.mark.parametrize("users,roles,maxt", [
    (1, True, 0.3),
    (1, False, 0.07),
    (10, True, 0.7),
    (10, False, 0.8),
    (100, True, 8.0),
    (100, False, 7.0),
    (1000, True, 75.0),
    (1000, False, 70.0),
])
def test_rest_get_user(users: int, roles: bool, maxt: float, open_once) -> None:
    assert run_test(open_users_rest, users=users, roles=True) < maxt
