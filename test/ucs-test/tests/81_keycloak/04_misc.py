#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Various keycloak tests
## tags: [keycloak]
## roles: [domaincontroller_master, domaincontroller_backup]
## exposure: dangerous

import socket

import dns.resolver
import requests
from utils import (
    get_portal_tile, host_is_alive, keycloak_get_request, keycloak_sessions_by_user, run_command, wait_for_class,
    wait_for_id,
)

import univention.testing.ucr as ucr_test
import univention.testing.udm as udm_test
from univention.testing.utils import get_ldap_connection


def test_session_sync(ucr, portal_login_via_keycloak, portal_config, keycloak_config):
    """
    Test session sync between two keycloak servers.
    Configure system so that keycloak fqdn points to system one
    and login. Now configure system so that keycloak fqdn
    points to system two. Now check if browser session is still
    valid (SSO) in portal on system two.
    """
    ldap = get_ldap_connection()
    fqdn = ucr.get("keycloak/server/sso/fqdn", f"ucs-sso-ng.{ucr['domainname']}")
    addresses = [addr.address for addr in dns.resolver.query(fqdn, "A")]
    # check if there are enough keycloak hosts
    # make sure there is at least one scenario in jenkins with two keycloak host
    if len(addresses) < 2:
        return
    login_ip = addresses.pop()
    check_ip = addresses.pop()
    login_host = ldap.search(f"(&(arecord={login_ip})(objectClass=univentionHost))", attr=["cn"])[0][1].get("cn")[0].decode("utf-8")
    check_host = ldap.search(f"(&(arecord={check_ip})(objectClass=univentionHost))", attr=["cn"])[0][1].get("cn")[0].decode("utf-8")
    login_url = f"https://{login_host}.{ucr['domainname']}"
    check_url = f"https://{check_host}.{ucr['domainname']}"

    with ucr_test.UCSTestConfigRegistry() as _ucr, udm_test.UCSTestUDM() as udm:
        # set ucs-sso-ng to login ip
        _ucr.handler_set([f"hosts/static/{login_ip}={fqdn}"])
        assert socket.gethostbyname(fqdn) == login_ip
        # login on login_host
        username = udm.create_user()[1]
        print(f"login to {login_url} ({login_ip})")
        driver = portal_login_via_keycloak(username, "univention", url=login_url)
        # change ucs-sso-ng to check_ip
        _ucr.handler_unset([f"hosts/static/{login_ip}"])
        _ucr.handler_set([f"hosts/static/{check_ip}={fqdn}"])
        assert socket.gethostbyname(fqdn) == check_ip
        # check portal in check_url
        print(f"check session on {check_url} ({check_ip})")
        driver.get(check_url)
        wait_for_id(driver, portal_config.categories_id)
        get_portal_tile(driver, portal_config.sso_login_tile_de, portal_config).click()
        wait_for_id(driver, portal_config.header_menu_id).click()
        a = wait_for_class(driver, portal_config.portal_sidenavigation_username_class)[0]
        assert a.text == username
        # check sessions
        sessions = keycloak_sessions_by_user(keycloak_config, username)[0]
        assert f"{login_url}/univention/saml/metadata" in sessions["clients"].values()
        assert f"{check_url}/univention/saml/metadata" in sessions["clients"].values()


def test_every_umc_server_has_a_saml_client(ucr, keycloak_config):
    ldap = get_ldap_connection()
    umc_hosts = ldap.search("univentionService=Univention Management Console", attr=["cn"])
    umc_hosts = [f"{host[1]['cn'][0].decode('utf-8')}.{ucr['domainname']}" for host in umc_hosts]
    # check only hosts that are alive, we use pre-join templates in our test
    # that have more systems joined than we use in the tests, for these hosts
    # the saml client can't be created because they are not started
    umc_hosts = [host for host in umc_hosts if host_is_alive(host)]
    kc_clients = [client["clientId"] for client in keycloak_get_request(keycloak_config, "realms/ucs/clients")]
    for host in umc_hosts:
        assert f"https://{host}/univention/saml/metadata" in kc_clients


def test_master_realm_config(keycloak_config, ucr):
    # required actions master realm
    required_actions = keycloak_get_request(keycloak_config, "realms/master/authentication/required-actions")
    required_actions = [ra["alias"] for ra in required_actions if ra["enabled"]]
    assert "UNIVENTION_SELF_SERVICE" not in required_actions
    assert "UNIVENTION_UPDATE_PASSWORD" not in required_actions
    # ucs ldap federation and mapper
    ldap_federation = keycloak_get_request(keycloak_config, "realms/master/components?type=org.keycloak.storage.UserStorageProvider")
    ldap_federation = [lf for lf in ldap_federation if lf["name"] == "ldap-master-admin"][0]
    assert ldap_federation["providerId"] == "ldap"
    assert ldap_federation["config"]["enabled"] == ["true"]
    assert ldap_federation["config"]["editMode"] == ["READ_ONLY"]
    components = keycloak_get_request(keycloak_config, f"realms/master/components?parent={ldap_federation['id']}")
    components = [c["name"] for c in components]
    assert set(components) == {
        "admin-role",
        "last name",
        "modify date",
        "email",
        "creation date",
        "username",
        "first name",
    }


def test_ucs_realm_config(keycloak_config, ucr):
    # required actions ucs realm
    required_actions = keycloak_get_request(keycloak_config, "realms/ucs/authentication/required-actions")
    required_actions = [ra["alias"] for ra in required_actions if ra["enabled"]]
    assert "UNIVENTION_SELF_SERVICE" in required_actions
    assert "UNIVENTION_UPDATE_PASSWORD" in required_actions
    # ucs ldap federation and mapper
    ldap_federation = keycloak_get_request(keycloak_config, "realms/ucs/components?type=org.keycloak.storage.UserStorageProvider")
    ldap_federation = [lf for lf in ldap_federation if lf["name"] == "ldap-provider"][0]
    assert ldap_federation["providerId"] == "ldap"
    assert ldap_federation["config"]["enabled"] == ["true"]
    assert ldap_federation["config"]["editMode"] == ["READ_ONLY"]
    components = keycloak_get_request(keycloak_config, f"realms/ucs/components?parent={ldap_federation['id']}")
    components = [c["name"] for c in components]
    assert set(components) == {
        "uid",
        "creation date",
        "username",
        "last name",
        "first name",
        "Univention ldap mapper",
        "email",
        "modify date",
    }


def test_csp(keycloak_config, ucr):
    response = requests.post(keycloak_config.admin_url, headers={"Accept": "text/html"})
    assert response.headers["Content-Security-Policy"]
    assert f"*.{ucr['domainname']}" in response.headers["Content-Security-Policy"]

    with ucr_test.UCSTestConfigRegistry() as _ucr:
        # change app setting for csp
        _ucr.handler_set(['keycloak/csp/frame-ancestors=https://*.external.com'])
        run_command(['systemctl', 'restart', 'apache2'])

        # test again the
        response = requests.post(keycloak_config.admin_url, headers={"Accept": "text/html"})
        assert response.headers["Content-Security-Policy"]
        _ucr.load()
        assert f"{_ucr.get('keycloak/csp/frame-ancestors')}" in response.headers["Content-Security-Policy"]
