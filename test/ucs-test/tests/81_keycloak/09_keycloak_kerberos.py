#!/usr/share/ucs-test/runner /usr/share/ucs-test/playwright
## desc: Test keycloak kerberos login
## tags: [keycloak]
## roles: [domaincontroller_master, domaincontroller_backup]
## exposure: dangerous

import pytest
from utils import kerberos_auth


@pytest.mark.parametrize('protocol', ['saml', 'oidc'])
def test_kerberos_authentication(portal_login_via_keycloak, ucr, protocol, portal_config):
    kerberos_auth(portal_login_via_keycloak, ucr, protocol, portal_config)
