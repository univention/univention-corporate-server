#!/usr/share/ucs-test/runner /usr/share/ucs-test/playwright
## desc: Test portal OIDC login via keycloak with multiple UMC processes
## tags: [keycloak]
## roles: [domaincontroller_master, domaincontroller_backup]
## exposure: dangerous

import time

import pytest
from playwright.sync_api import expect
from utils import run_command

from univention.lib.i18n import Translation


_ = Translation('ucs-test-browser').translate


@pytest.fixture()
def umc_multi_processes(ucr):
    old_value = ucr.get("umc/http/processes", 1)
    ucr.handler_set(["umc/http/processes=8"])
    try:
        run_command(['univention-management-console-settings', 'set', '-u', 'sqlite:////var/cache/univention-management-console/session_db'])
        run_command(["systemctl", "restart", "apache2"])
        run_command(["systemctl", "restart", "univention-management-console-*"])
        time.sleep(10)
        yield
    finally:
        ucr.handler_set(["umc/http/processes=%s" % old_value])
        run_command(['univention-management-console-settings', 'set', '-u'])
        run_command(["systemctl", "restart", "apache2"])
        run_command(["systemctl", "restart", "univention-management-console-*"])
        time.sleep(10)


@pytest.mark.usefixtures("umc_multi_processes")
@pytest.mark.usefixtures('oidc_client_logout_meachanism')
@pytest.mark.parametrize('oidc_client_logout_meachanism', ['backchannel'], indirect=True)
def test_login(udm, portal_login_via_keycloak_custom_page, portal_config, keycloak_config, multi_tab_context):
    username = udm.create_user()[1]

    portal_hostname = portal_config.fqdn
    multi_tab_context.add_cookies([{
        "name": "UMCWEB_ROUTEID",
        "value": ".2",
        "domain": portal_hostname,
        "path": "/",
    }])
    login_page, logout_page = multi_tab_context.new_page(), multi_tab_context.new_page()
    portal_login_via_keycloak_custom_page(login_page, username, "univention", protocol="oidc")
    logout_page.goto(keycloak_config.logout_url)
    logout_page.get_by_role('button', name='Logout').click()
    time.sleep(3)
    login_page.reload()
    expect(login_page.get_by_role('link', name=_('Login Same tab'), exact=True), message='Tab not logged out').to_be_visible()
