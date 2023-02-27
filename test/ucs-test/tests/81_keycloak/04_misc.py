#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Various keycloak tests
## tags: [keycloak]
## roles: [domaincontroller_master, domaincontroller_backup]
## exposure: dangerous


import socket

import dns.resolver
from utils import get_portal_tile, keycloak_sessions_by_user, wait_for_class, wait_for_id

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
    fqdn = ucr["keycloak/server/sso/fqdn"]
    addresses = []
    for addr in dns.resolver.query(fqdn, "A"):
        addresses.append(addr.address)
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
