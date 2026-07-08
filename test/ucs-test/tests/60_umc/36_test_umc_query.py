#!/usr/share/ucs-test/runner pytest-3 -s -l -vvv
## desc: test for umc udm/query
## roles:
##  - domaincontroller_master
## packages:
##  - univention-management-console-module-udm
## packages-not:
##  - univention-samba4
## exposure: dangerous

import pytest

from univention.testing import ucr as _ucr
from univention.testing.umc import Client


@pytest.fixture(scope='session')
def create_users(udm_session, ldap_base, random_username):
    position = udm_session.create_object('container/cn', name=random_username(), position=ldap_base, wait_for_replication=False)
    username = f"ABC{random_username()}"
    username2 = f"DEF{random_username()}"
    udm_session.create_user(position=position, username=username, wait_for_replication=False)
    udm_session.create_user(position=position, username=username2, wait_for_replication=True)
    return position


@pytest.fixture
def auto_substring_search(restart_umc_server, request):
    auto_substring = "true" if request.param else "false"
    try:
        with _ucr.UCSTestConfigRegistry() as ucr:
            ucr.handler_set([f"directory/manager/web/auto_substring_search={auto_substring}"])
            restart_umc_server()
            yield
    finally:
        restart_umc_server()


@pytest.fixture
def umc_client():
    return Client.get_test_connection()


@pytest.mark.parametrize(
    "auto_substring_search,results", [
        (True, [2, 2, 1, 1]),
        (False, [2, 2, 0, 1]),
    ],
    indirect=["auto_substring_search"],
    ids=["true", "false"],
)
def test_query_auto_substring_search(auto_substring_search, create_users, umc_client, results):
    options = {
        "objectType": "users/user",
        "container": create_users,
        "objectProperty": "None",
    }
    flavor = "users/user"
    # 1. no filter value, we should get everything
    options["objectPropertyValue"] = ""
    res = umc_client.umc_command("udm/query", options, flavor)
    assert len(res.result) == results[0]
    # 2. wildcard, we should get everything
    options["objectPropertyValue"] = "*"
    res = umc_client.umc_command("udm/query", options, flavor)
    assert len(res.result) == results[1]
    # 3. auto substring search, should find 1 result for auto_substring_search=true and 0 for auto_substring_search=false
    options["objectPropertyValue"] = "ABC"
    res = umc_client.umc_command("udm/query", options, flavor)
    assert len(res.result) == results[2]
    # 4. wildcard substring, we should find 1 result
    options["objectPropertyValue"] = "ABC*"
    res = umc_client.umc_command("udm/query", options, flavor)
    assert len(res.result) == results[3]
