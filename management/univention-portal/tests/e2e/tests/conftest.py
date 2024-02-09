# SPDX-License-Identifier: AGPL-3.0-only
# SPDX-FileCopyrightText: 2023-2024 Univention GmbH

import pytest
from playwright_pages_ucs_portal.home_page.logged_in import HomePageLoggedIn
from playwright_pages_ucs_portal.home_page.logged_out import HomePageLoggedOut
from playwright_pages_ucs_portal.login_page import LoginPage


def pytest_addoption(parser):
    parser.addoption("--username", default="Administrator",
                     help="Portal login username",
                     )
    parser.addoption("--password", default="univention",
                     help="Portal login password",
                     )
    parser.addoption("--notifications-api-base-url",
                     default="http://localhost:8000/univention/portal/notifications-api/",
                     help="Base URL of the notification API",
                     )
    parser.addoption("--portal-base-url", default="http://localhost:8000",
                     help="Base URL of the univention portal",
                     )


@pytest.fixture()
def username(pytestconfig):
    return pytestconfig.option.username


@pytest.fixture()
def password(pytestconfig):
    return pytestconfig.option.password


@pytest.fixture()
def notifications_api_base_url(pytestconfig):
    return pytestconfig.getoption("--notifications-api-base-url")


@pytest.fixture()
def browser_context_args(browser_context_args, pytestconfig):
    browser_context_args["base_url"] = pytestconfig.getoption("--portal-base-url")
    return browser_context_args


@pytest.fixture()
def navigate_to_home_page_logged_out(page):
    home_page_logged_out = HomePageLoggedOut(page)
    home_page_logged_out.navigate()
    return page


@pytest.fixture()
def navigate_to_login_page(page):
    login_page = LoginPage(page)
    login_page.navigate()
    return page


@pytest.fixture()
def navigate_to_saml_login_page(page):
    login_page = LoginPage(page)
    login_page.navigate_saml()
    return page


@pytest.fixture()
def navigate_to_home_page_logged_in(page, username, password):
    home_page_logged_in = HomePageLoggedIn(page)
    home_page_logged_in.navigate(username, password)
    return page
