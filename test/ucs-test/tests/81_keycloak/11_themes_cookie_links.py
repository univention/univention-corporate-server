#!/usr/share/ucs-test/runner /usr/share/ucs-test/playwright
## desc: Test univention-keycloak
## tags: [keycloak]
## roles: [domaincontroller_master, domaincontroller_backup]
## exposure: dangerous

import os
import shutil
import tempfile
import time
from itertools import product
from subprocess import CalledProcessError

import pytest
import requests
from playwright.sync_api import expect
from utils import _, run_command


LINK_COUNT = 12


def cleanup_cookies(context):
    context.clear_cookies()


@pytest.fixture()
def login_links(lang: str, link_count: int) -> tuple[str, int]:
    try:
        for i in range(1, link_count + 1):
            run_command(['univention-keycloak', 'login-links', 'set', lang, str(i), f'href{i}', f'desc{i}'])
        yield lang, link_count
    finally:
        for i in range(1, link_count + 1):
            try:
                run_command(['univention-keycloak', 'login-links', 'delete', lang, str(i)])
            except CalledProcessError:
                pass


def test_get_webresources(keycloak_config):
    resources = [
        '/univention/theme.css',
        '/univention/login/css/custom.css',
        '/favicon.ico',
        '/univention/meta.json',
        '/univention/js/dijit/themes/umc/images/login_logo.svg',
    ]
    for resource in resources:
        url = f'https://{keycloak_config.server}/{resource}'
        resp = requests.get(url)
        assert resp.status_code == 200, f'{resp.status_code} {url}'


@pytest.mark.skipif(not os.path.isfile('/etc/keycloak.secret'), reason='fails without keycloak locally installed')
@pytest.mark.parametrize(
    'settings',
    [['dark', 'rgb(255, 255, 255)'], ['light', 'rgb(30, 30, 29)']],
    ids=['dark', 'light'],
)
def test_theme_switch(ucr, keycloak_adm_login, admin_account, settings, is_keycloak):
    theme = settings[0]
    color = settings[1]
    ucr.handler_set([f'ucs/web/theme={theme}'])
    page = keycloak_adm_login(admin_account.username, admin_account.bindpw, no_login=True)
    element = page.locator('.login-pf-header')
    assert element.evaluate("el => getComputedStyle(el).color") == color


@pytest.mark.skipif(not os.path.isfile('/etc/keycloak.secret'), reason='fails without keycloak locally installed')
def test_custom_theme(keycloak_adm_login, admin_account, is_keycloak):
    custom_css = '/var/www/univention/login/css/custom.css'
    color_css = 'rgb(131, 20, 20)'
    with tempfile.NamedTemporaryFile(dir='/tmp', delete=False) as tmpfile:
        temp_file = tmpfile.name
    shutil.move(custom_css, temp_file)
    try:
        with open(custom_css, 'w') as fh:
            fh.write(':root { --bgc-content-body: #831414; }')
        page = keycloak_adm_login(admin_account.username, admin_account.bindpw, no_login=True)
        element = page.get_by_label(_('Username or email'))
        assert element.evaluate("el => getComputedStyle(el).backgroundColor") == color_css
    finally:
        shutil.move(temp_file, custom_css)


@pytest.mark.skipif(not os.path.isfile('/etc/keycloak.secret'), reason='fails without keycloak locally installed')
def test_cookie_banner(keycloak_adm_login, admin_account, ucr, keycloak_config, is_keycloak):
    ucr.handler_set(
        [
            'umc/cookie-banner/cookie=TESTCOOKIE',
            'umc/cookie-banner/show=true',
            'umc/cookie-banner/text/de=de-DE text',
            'umc/cookie-banner/title/de=de-DE title',
            'umc/cookie-banner/text/en=en-US text',
            'umc/cookie-banner/title/en=en-US title',
        ],
    )
    # check the popup
    page = keycloak_adm_login(admin_account.username, admin_account.bindpw, no_login=True)
    time.sleep(1)
    assert page.locator("[id='cookie-text']").inner_text() == _('en-US text')
    assert page.locator("[id='cookie-title']").inner_text() == _('en-US title')
    button = page.get_by_role("button", name=_('ACCEPT'))
    # accept the popup and check the cookie
    assert button.inner_text() == _('ACCEPT')
    button.click()
    cookies = page.context.cookies()
    for cookie in cookies:
        if cookie['name'] == 'TESTCOOKIE':
            assert cookie['value'] == 'do-not-change-me'
            assert cookie['domain'] == keycloak_config.server.lower()
            break
    else:
        raise Exception(f'cookie TESTCOOKIE not found: {cookies}')
    # just to test if this is interactable")
    page.click(f"[id='{keycloak_config.login_id}']")


@pytest.mark.skipif(not os.path.isfile('/etc/keycloak.secret'), reason='fails without keycloak locally installed')
def test_cookie_banner_no_banner_with_cookie_domains(keycloak_adm_login, admin_account, ucr, is_keycloak):
    # no banner if umc/cookie-banner/domains does not match
    # the current domain
    ucr.handler_set(
        [
            'umc/cookie-banner/cookie=TESTCOOKIE',
            'umc/cookie-banner/show=true',
            'umc/cookie-banner/text/de=de-DE text',
            'umc/cookie-banner/title/de=de-DE title',
            'umc/cookie-banner/text/en=en-US text',
            'umc/cookie-banner/title/en=en-US title',
            'umc/cookie-banner/domains=does.not.exists',
        ],
    )
    keycloak_adm_login(admin_account.username, admin_account.bindpw)


@pytest.mark.skipif(not os.path.isfile('/etc/keycloak.secret'), reason='fails without keycloak locally installed')
def test_cookie_banner_domains(keycloak_adm_login, admin_account, ucr, keycloak_config, is_keycloak):
    # check if cookie domain is set to umc/cookie-banner/domains
    domain = keycloak_config.server.split('.', 1)[1]
    ucr.handler_set(
        [
            'umc/cookie-banner/cookie=TESTCOOKIE',
            'umc/cookie-banner/show=true',
            'umc/cookie-banner/text/de=de-DE text',
            'umc/cookie-banner/title/de=de-DE title',
            'umc/cookie-banner/text/en=en-US text',
            'umc/cookie-banner/title/en=en-US title',
            f'umc/cookie-banner/domains=does.not.exist,{domain.lower()}',
        ],
    )
    page = keycloak_adm_login(admin_account.username, admin_account.bindpw, no_login=True)
    page.click(".cookie-banner-button")
    cookies = page.context.cookies()
    for cookie in cookies:
        if cookie['name'] == 'TESTCOOKIE':
            assert cookie['domain'] == f'.{domain.lower()}'
            break
    else:
        raise Exception(f'cookie TESTCOOKIE not found: {cookies}')


@pytest.mark.skipif(not os.path.isfile('/etc/keycloak.secret'), reason='fails without keycloak locally installed')
def test_login_page_with_cookie_banner_no_element_is_tabbable(keycloak_adm_login, admin_account, ucr, is_keycloak):
    # only the accept button is tabbable
    ucr.handler_set(
        [
            'umc/cookie-banner/cookie=TESTCOOKIE',
            'umc/cookie-banner/show=true',
            'umc/cookie-banner/text/de=de-DE text',
            'umc/cookie-banner/title/de=de-DE title',
            'umc/cookie-banner/text/en=en-US text',
            'umc/cookie-banner/title/en=en-US title',
        ],
    )
    page = keycloak_adm_login(admin_account.username, admin_account.bindpw, no_login=True)
    print(page.content())
    page.focus(f'text={_("Accept")}')
    assert page.evaluate("() => document.activeElement.textContent").replace("\n", "").strip() == _('Accept')
    assert page.is_visible(f'text={_("Accept")}')
    # some browser fields
    page.keyboard.press("Tab")
    page.keyboard.press("Tab")
    page.keyboard.press("Tab")
    page.keyboard.press("Tab")
    # and back to the beginning
    assert page.evaluate("() => document.activeElement.textContent").replace("\n", "").strip() == _('Accept')


@pytest.mark.skipif(not os.path.isfile('/etc/keycloak.secret'), reason='fails without keycloak locally installed')
def test_login_page_all_elements_are_tabbable(portal_login_via_keycloak, keycloak_adm_login, admin_account):
    page = portal_login_via_keycloak(admin_account.username, admin_account.bindpw, no_login=True)
    assert page.evaluate("() => document.activeElement.name") == 'username'
    page.keyboard.press("Tab")
    assert page.evaluate("() => document.activeElement.name") == 'password'
    page.keyboard.press("Tab")
    assert page.evaluate("() => document.activeElement.name") == 'login'
    # some browser fields
    page.keyboard.press("Tab")
    page.keyboard.press("Tab")
    page.keyboard.press("Tab")
    # and back to the beginning
    assert page.evaluate("() => document.activeElement.name") == 'username'


@pytest.mark.skipif(not os.path.isfile('/etc/keycloak.secret'), reason='fails without keycloak locally installed')
@pytest.mark.parametrize('lang, link_count', list(product(['en'], [0, LINK_COUNT + 1])))
def test_invalid_link_count(lang: str, link_count: int):
    with pytest.raises(CalledProcessError):
        run_command(['univention-keycloak', 'login-links', 'set', lang, str(link_count), 'href', 'desc'])


@pytest.mark.skipif(not os.path.isfile('/etc/keycloak.secret'), reason='fails without keycloak locally installed')
@pytest.mark.parametrize('lang, link_count', list(product(['en'], [1, 5, 12])))
def test_login_links(lang, link_count, login_links, portal_login_via_keycloak, admin_account):
    page = portal_login_via_keycloak(admin_account.username, admin_account.bindpw, no_login=True)
    login_links_parent = page.locator("[id='umcLoginLinks']")
    links_found = login_links_parent.locator("a")
    expect(links_found).to_have_count(link_count)
    for i in range(link_count):
        link = links_found.nth(i)
        assert link.inner_text().startswith('href')
        assert link.is_visible()
