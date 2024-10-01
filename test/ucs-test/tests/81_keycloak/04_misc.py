#!/usr/share/ucs-test/runner /usr/share/ucs-test/playwright
## desc: Various keycloak tests
## tags: [keycloak]
## roles: [domaincontroller_master, domaincontroller_backup]
## exposure: dangerous

import os
import shutil
import socket

import dns.resolver
import pytest
import requests
from utils import (
    get_portal_tile, grant_oidc_privileges, host_is_alive, keycloak_get_request, keycloak_post_request,
    keycloak_sessions_by_user, run_command,
)

from univention.testing.utils import get_ldap_connection


@pytest.mark.parametrize('protocol', ['saml', 'oidc'])
def test_session_sync(ucr, udm, portal_login_via_keycloak, portal_config, keycloak_config, protocol):
    """
    Test session sync between two keycloak servers.
    Configure system so that keycloak fqdn points to system one
    and login. Now configure system so that keycloak fqdn
    points to system two. Now check if browser session is still
    valid (SSO) in portal on system two.
    """
    ldap = get_ldap_connection()
    fqdn = ucr.get('keycloak/server/sso/fqdn', f"ucs-sso-ng.{ucr['domainname']}")
    addresses = [addr.address for addr in dns.resolver.query(fqdn, 'A')]
    # check if there are enough keycloak hosts
    # make sure there is at least one scenario in jenkins with two keycloak host
    if len(addresses) < 2:
        return
    login_ip = addresses.pop()
    check_ip = addresses.pop()
    login_host = ldap.search(f'(&(arecord={login_ip})(objectClass=univentionHost))', attr=['cn'])[0][1].get('cn')[0].decode('utf-8')
    check_host = ldap.search(f'(&(arecord={check_ip})(objectClass=univentionHost))', attr=['cn'])[0][1].get('cn')[0].decode('utf-8')
    login_url = f"https://{login_host}.{ucr['domainname']}"
    check_url = f"https://{check_host}.{ucr['domainname']}"

    print(f'login at {login_url}')
    print(f'check at {check_url}')
    # set ucs-sso-ng to login ip
    ucr.handler_set([f'hosts/static/{login_ip}={fqdn}'])
    assert socket.gethostbyname(fqdn) == login_ip
    # login on login_host
    username = udm.create_user()[1]
    print(f'login to {login_url} ({login_ip})')
    page = portal_login_via_keycloak(username, 'univention', url=login_url, protocol=protocol)
    # change ucs-sso-ng to check_ip
    ucr.handler_unset([f'hosts/static/{login_ip}'])
    ucr.handler_set([f'hosts/static/{check_ip}={fqdn}'])
    assert socket.gethostbyname(fqdn) == check_ip

    # check portal in check_url
    print(f'check session on {check_url} ({check_ip})')
    page.goto(check_url)
    login_tile = portal_config.sso_oidc_login_tile if protocol == 'oidc' else portal_config.sso_login_tile
    get_portal_tile(page, login_tile, portal_config).click()
    grant_oidc_privileges(page)
    page.click(f"[id='{portal_config.header_menu_id}']")
    a = page.locator(f'.{portal_config.portal_sidenavigation_username_class}').first
    assert a.inner_html() == username
    # check sessions
    sessions = keycloak_sessions_by_user(keycloak_config, username)[0]
    sso_protocol = 'oidc/' if protocol == 'oidc' else 'saml/metadata'
    assert f'{login_url}/univention/{sso_protocol}' in sessions['clients'].values()
    assert f'{check_url}/univention/{sso_protocol}' in sessions['clients'].values()


def test_every_umc_server_has_a_saml_client(ucr, keycloak_config):
    ldap = get_ldap_connection()
    umc_hosts = ldap.search('univentionService=Univention Management Console', attr=['cn'])
    umc_hosts = [f"{host[1]['cn'][0].decode('utf-8')}.{ucr['domainname']}" for host in umc_hosts]
    # check only hosts that are alive, we use pre-join templates in our test
    # that have more systems joined than we use in the tests, for these hosts
    # the saml client can't be created because they are not started
    umc_hosts = [host for host in umc_hosts if host_is_alive(host)]
    kc_clients = [client['clientId'] for client in keycloak_get_request(keycloak_config, 'realms/ucs/clients')]
    for host in umc_hosts:
        assert f'https://{host}/univention/saml/metadata' in kc_clients


def test_every_umc_server_has_a_oidc_client(ucr, keycloak_config):
    ldap = get_ldap_connection()
    umc_hosts = ldap.search('univentionService=Univention Management Console', attr=['cn'])
    umc_hosts = [f"{host[1]['cn'][0].decode('utf-8')}.{ucr['domainname']}" for host in umc_hosts]
    umc_hosts = [host for host in umc_hosts if host_is_alive(host)]
    kc_clients = [client['clientId'] for client in keycloak_get_request(keycloak_config, 'realms/ucs/clients')]
    for host in umc_hosts:
        assert f'https://{host}/univention/oidc/' in kc_clients


@pytest.mark.parametrize('realm', ['master', 'ucs'])
def test_rest_api_endpoints(keycloak_config, realm: str):
    """
    Test some of the REST endpoints

    In the past we made changes that broke the user list request,
    test some of the endpoints here to make sure they work

    See https://forge.univention.org/bugzilla/show_bug.cgi?id=57205
    """
    assert keycloak_get_request(keycloak_config, f'realms/{realm}')
    assert keycloak_get_request(keycloak_config, f'realms/{realm}/users/profile')
    assert keycloak_get_request(keycloak_config, f'realms/{realm}/users')
    users = keycloak_get_request(keycloak_config, f'realms/{realm}/ui-ext/brute-force-user')
    assert users
    some_user_id = users[0]['id']
    assert keycloak_get_request(keycloak_config, f'realms/{realm}/users/{some_user_id}?userProfileMetadata=true')
    assert keycloak_get_request(keycloak_config, f'realms/{realm}/clients')
    assert keycloak_get_request(keycloak_config, f'realms/{realm}/client-scopes')
    assert keycloak_get_request(keycloak_config, f'realms/{realm}/roles')
    keycloak_get_request(keycloak_config, f'realms/{realm}/groups')
    keycloak_post_request(keycloak_config, f'realms/{realm}/logout-all')
    keycloak_get_request(keycloak_config, f'realms/{realm}/ui-ext/sessions')
    keycloak_get_request(keycloak_config, f'realms/{realm}/admin-events')
    keycloak_get_request(keycloak_config, f'realms/{realm}/events')
    keycloak_get_request(keycloak_config, f'realms/{realm}/authentication/unregistered-required-actions')
    assert keycloak_get_request(keycloak_config, f'realms/{realm}/authentication/required-actions')
    assert keycloak_get_request(keycloak_config, f'realms/{realm}/authentication/flows')
    assert keycloak_get_request(keycloak_config, f'realms/{realm}/ui-ext/authentication-management/flows')
    assert keycloak_get_request(keycloak_config, f'realms/{realm}/components')


def test_master_realm_config(keycloak_config, ucr):
    # required actions master realm
    required_actions = keycloak_get_request(keycloak_config, 'realms/master/authentication/required-actions')
    required_actions = [ra['alias'] for ra in required_actions if ra['enabled']]
    assert 'UNIVENTION_SELF_SERVICE' not in required_actions
    assert 'UNIVENTION_UPDATE_PASSWORD' not in required_actions
    # ucs ldap federation and mapper
    ldap_federation = keycloak_get_request(keycloak_config, 'realms/master/components?type=org.keycloak.storage.UserStorageProvider')
    ldap_federation = next(lf for lf in ldap_federation if lf['name'] == 'ldap-master-admin')
    assert ldap_federation['providerId'] == 'ldap'
    assert ldap_federation['config']['enabled'] == ['true']
    assert ldap_federation['config']['editMode'] == ['READ_ONLY']
    components = keycloak_get_request(keycloak_config, f"realms/master/components?parent={ldap_federation['id']}")
    components = [c['name'] for c in components]
    assert set(components) == {
        'admin-role',
        'last name',
        'modify date',
        'email',
        'creation date',
        'username',
        'first name',
    }


def test_ucs_realm_config(keycloak_config, ucr):
    sso_fqdn = ucr.get('keycloak/server/sso/fqdn')
    kerberos_realm = ucr.get('kerberos/realm')

    # required actions ucs realm
    required_actions = keycloak_get_request(keycloak_config, 'realms/ucs/authentication/required-actions')
    required_actions = [ra['alias'] for ra in required_actions if ra['enabled']]
    assert 'UNIVENTION_SELF_SERVICE' in required_actions
    assert 'UNIVENTION_UPDATE_PASSWORD' in required_actions
    # ucs ldap federation and mapper
    ldap_federation = keycloak_get_request(keycloak_config, 'realms/ucs/components?type=org.keycloak.storage.UserStorageProvider')
    ldap_federation = next(lf for lf in ldap_federation if lf['name'] == 'ldap-provider')
    assert ldap_federation['providerId'] == 'ldap'
    assert ldap_federation['config']['enabled'] == ['true']
    assert ldap_federation['config']['editMode'] == ['READ_ONLY']
    assert ldap_federation['config']['allowKerberosAuthentication'] == ['true']
    assert ldap_federation['config']['kerberosRealm'] == [ucr.get('kerberos/realm')]
    if sso_fqdn:
        assert ldap_federation['config']['serverPrincipal'] == [f'HTTP/{sso_fqdn}@{kerberos_realm}']
    else:
        # not a keycloak server so sso_fqdn is not set. Check at least if it is set and the kerberos_realm is present
        assert kerberos_realm in ldap_federation['config']['serverPrincipal'][0]
    assert ldap_federation['config']['keyTab'] == ['/var/lib/univention-appcenter/apps/keycloak/conf/keycloak.keytab']
    components = keycloak_get_request(keycloak_config, f"realms/ucs/components?parent={ldap_federation['id']}")
    components = [c['name'] for c in components]
    assert set(components) == {
        'uid',
        'creation date',
        'username',
        'last name',
        'first name',
        'Univention ldap mapper',
        'email',
        'modify date',
        'displayName',
        'entryUUID',
    }


@pytest.mark.is_keycloak()
@pytest.mark.skipif(not os.path.isfile('/etc/keycloak.secret'), reason='fails on hosts without keycloak.secret')
def test_csp(keycloak_config, ucr):
    if not ucr.is_true('keycloak/server/sso/virtualhost'):
        pytest.skip('no virtual host config, therefore no special cookie header settings')
    response = requests.post(f'{keycloak_config.admin_url}/master/console', headers={'Accept': 'text/html'})
    assert response.headers['Content-Security-Policy']
    assert f"*.{ucr['domainname']}" in response.headers['Content-Security-Policy']
    if ucr['server/role'] != 'domaincontroller_master':
        pytest.skip('onyl on master, we have scenarios where keycloak/server/sso/fqdn points to a different server, but in this test we changed the local apache config.')
    try:
        # change app setting for csp
        ucr.handler_set(['keycloak/csp/frame-ancestors=https://*.external.com'])
        run_command(['systemctl', 'restart', 'apache2'])
        response = requests.post(f'{keycloak_config.admin_url}/master/console', headers={'Accept': 'text/html'})
        assert response.headers['Content-Security-Policy']
        assert f"frame-src 'self'; frame-ancestors 'self' https://*.{ucr['domainname']} https://login.microsoftonline.com https://*.external.com;  object-src 'none';" == response.headers['Content-Security-Policy']
    finally:
        run_command(['systemctl', 'restart', 'apache2'])


@pytest.mark.roles('domaincontroller_master')
def test_additional_ca_certifiates_issue_223():
    ca_dir = '/var/lib/univention-appcenter/apps/keycloak/conf/ca-certificates'
    src = '/etc/univention/ssl/ucsCA/CAcert.pem'
    dst = f'{ca_dir}/my-new-certificate.pem'
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copyfile(src, dst)
    run_command(['univention-app', 'configure', 'keycloak'])
    stdout = run_command(['docker', 'exec', '-u', 'root', 'keycloak', 'keytool', '-cacerts', '-list', '-storepass', 'changeit', '-noprompt'])
    assert 'my-new-certificate.pem' in stdout, f'certificate not found in {stdout}'
