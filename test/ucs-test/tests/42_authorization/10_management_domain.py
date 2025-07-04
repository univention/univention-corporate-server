#!/usr/share/ucs-test/runner pytest-3 -s -l -vvv
## desc: Check external management domain with delegated administration
## bugs: [58113]
## roles:
##  - domaincontroller_master
##  - domaincontroller_backup
## exposure: dangerous

import pytest

from univention.testing.umc import ClientOIDC


@pytest.fixture
def manager_ou1_umc():
    client = ClientOIDC()
    client.authenticate('manager-ou1', 'univention', kc_idp_hint='oidc')
    return client


@pytest.fixture
def manager_all_umc():
    client = ClientOIDC()
    client.authenticate('manager-all', 'univention', kc_idp_hint='oidc')
    return client


def test_manager_ou1_oidc_umc_login(manager_ou1_umc):
    res = manager_ou1_umc.umc_get('modules')
    assert res.data.get('modules')


def test_manager_ou1_default_container_umc(manager_ou1_umc, ou):
    res = manager_ou1_umc.umc_command('udm/containers', {'objectType': 'users/user'}, 'users/user').result
    assert {x['id'] for x in res} == {ou.user_default_container}
    res = manager_ou1_umc.umc_command('udm/containers', {'objectType': 'groups/group'}, 'groups/group').result
    assert {x['id'] for x in res} == {ou.group_default_container}


def test_manager_all_default_container_umc(manager_all_umc, ou):
    res = manager_all_umc.umc_command('udm/containers', {'objectType': 'users/user'}, 'users/user').result
    assert len(res) == 15, res
