#!/usr/share/ucs-test/runner pytest-3 -s -l -vv --tb=native
## desc: Test UMC OIDC login via keycloak
## tags: [keycloak]
## roles: [domaincontroller_master, domaincontroller_backup]
## exposure: dangerous

import pytest
import requests
from selenium.webdriver.common.by import By


@pytest.fixture(scope='session')
def umc_user_top_module_access(udm_session, ucr_proper):
    userdn, username = udm_session.create_user(wait_for=False)
    policy_dn = udm_session.create_object(
        "policies/umc",
        name=f"{username}_top",
        allow=f"cn=top-all,cn=operations,cn=UMC,cn=univention,{ucr_proper['ldap/base']}",
        position=f"cn=policies,{ucr_proper['ldap/base']}",
    )
    udm_session.modify_object("users/user", dn=userdn, policy_reference=policy_dn)
    return username


@pytest.fixture(scope='session')
def client_id_umc(ucr_proper):
    fqdn_oidc = ucr_proper.get('umc/oidc/rp/server', f"{ucr_proper['hostname'] }.{ucr_proper['domainname']}")
    return f'https://{fqdn_oidc}/univention/oidc/'


@pytest.fixture(scope='session')
def client_id_udm(ucr_proper):
    return f"https://{ucr_proper['hostname']}.{ucr_proper['domainname']}/univention/udm/"


@pytest.fixture(scope='session')
def client_secret_umc():
    with open('/etc/umc-oidc.secret') as fd:
        return fd.read().strip()


@pytest.fixture(scope='session')
def client_secret_udm():
    with open('/etc/udm-rest-oauth.secret') as fd:
        return fd.read().strip()


def test_login_regular_user(umc_login_via_keycloak, umc_user_top_module_access):
    assert umc_login_via_keycloak(umc_user_top_module_access, 'univention')


def test_udm_module_usable(umc_login_via_keycloak, account):
    selenium = umc_login_via_keycloak(account.username, account.bindpw)
    assert selenium
    selenium.find_element(By.XPATH, "//div[@class='umcGalleryName' and text()='Benutzer']").click()


def test_udm_rest_api_bearer_auth(keycloak_openid, client_id_udm, client_secret_udm, account):
    sess = keycloak_openid(client_id_udm, client_secret_key=client_secret_udm)
    tokens = sess.token(account.username, account.bindpw)
    headers = {
        'Authorization': f"Bearer {tokens['access_token']}",
        'Accept': 'application/json',
    }
    resp = requests.get(f'{client_id_udm}users/user/{account.binddn}', headers=headers)
    assert resp.status_code == 200
    assert resp.json()['dn'] == account.binddn


def test_udm_rest_api_bearer_auth_wrong_token(keycloak_openid, client_id_udm, client_id_umc, client_secret_umc, account):
    sess = keycloak_openid(client_id_umc, client_secret_key=client_secret_umc)
    tokens = sess.token(account.username, account.bindpw)
    headers = {
        'Authorization': f"Bearer {tokens['access_token']}",
        'Accept': 'application/json',
    }
    resp = requests.get(f'{client_id_udm}users/user/{account.binddn}', headers=headers)
    assert resp.status_code == 401


def test_umc_bearer_auth(keycloak_openid, umc_user_top_module_access, client_id_umc, client_secret_umc, ucr_proper):
    sess = keycloak_openid(client_id_umc, client_secret_key=client_secret_umc)
    fqdn_oidc = f"{ucr_proper['hostname'] }.{ucr_proper['domainname']}"
    tokens = sess.token(umc_user_top_module_access, 'univention')
    headers = {
        'Authorization': f"Bearer {tokens['access_token']}",
        'Accept': 'application/json',
        'Content-Type': 'application/json',
    }
    resp = requests.get(f'https://{fqdn_oidc}/univention/get/modules', headers=headers)
    assert resp.status_code == 200
    assert resp.json() == {
        'modules': []
    }
    resp = requests.post(f'https://{fqdn_oidc}/univention/command/top/query', headers=headers, data='{}')
    assert resp.status_code == 422
