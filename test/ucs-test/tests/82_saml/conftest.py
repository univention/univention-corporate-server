import subprocess
from pathlib import Path

import pytest

from univention.config_registry import ucr

import samltest


@pytest.fixture()
def kerberos_ticket(ucr, account) -> None:
    ucr.handler_set(['kerberos/defaults/rdns=false', 'saml/idp/authsource=univention-negotiate'])
    subprocess.call(['kdestroy'])
    subprocess.check_call(['kinit', '--password-file=%s' % (account.pwdfile,), account.username])  # get kerberos ticket
    yield
    subprocess.call(['kdestroy'])


@pytest.fixture()
def saml_session(account):
    return samltest.SamlTest(account.username, account.bindpw)


@pytest.fixture()
def saml_session_kerberos():
    return samltest.SamlTest('', '', use_kerberos=True)


def set_umc_idp_server(saml_endpoint: str):
    if ucr["umc/saml/idp-server"] == saml_endpoint:
        return
    subprocess.run(["ucr", "set", f"umc/saml/idp-server={saml_endpoint}"], check=True)
    subprocess.run(["systemctl", "restart", "slapd"], check=True)


@pytest.fixture()
def is_keycloak_installed() -> bool:
    filename = "/run/UCS_TEST_KEYCLOAK_INSTALLED"
    try:
        with open(filename) as f:
            return f.read() == 'True'
    except FileNotFoundError:
        pass

    keycloak_installed = subprocess.run(["univention-keycloak", "get-keycloak-base-url"], check=False).returncode == 0
    Path(filename).write_text(str(keycloak_installed))

    return keycloak_installed


@pytest.fixture(params=["keycloak", "simplesamlphp"])
def configure_sso(request: pytest.FixtureRequest, is_keycloak_installed: bool):
    # can't use the UCR fixture here since it seems to not like us calling UCR via the CLI
    domainname = ucr["domainname"]
    server_role = ucr["server/role"]
    if request.param == "keycloak":
        if not is_keycloak_installed:
            pytest.skip("Keycloak is not installed")
        if server_role != "domaincontroller_master":
            pytest.skip("SAML Keycloak test only run on primary")
        set_umc_idp_server(f"https://ucs-sso-ng.{domainname}/realms/ucs/protocol/saml/descriptor")
        yield
        set_umc_idp_server(f"https://ucs-sso.{domainname}/simplesamlphp/saml2/idp/metadata.php")
    elif request.param == "simplesamlphp":
        set_umc_idp_server(f"https://ucs-sso.{domainname}/simplesamlphp/saml2/idp/metadata.php")
        yield
