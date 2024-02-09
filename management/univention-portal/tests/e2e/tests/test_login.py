# SPDX-License-Identifier: AGPL-3.0-only
# SPDX-FileCopyrightText: 2023-2024 Univention GmbH

import pytest
from playwright_pages_ucs_portal.home_page.logged_in import HomePageLoggedIn
from playwright_pages_ucs_portal.home_page.logged_out import HomePageLoggedOut
from playwright_pages_ucs_portal.login_page import LoginPage


def test_login(navigate_to_login_page, username, password):
    """Tests the plain UMC login in our devenv but the SAML login in the nightly deployment"""
    page = navigate_to_login_page
    login_page = LoginPage(page)
    login_page.login(username, password)

    home_page_logged_in = HomePageLoggedIn(page)
    home_page_logged_in.assert_logged_in()


def test_logout(navigate_to_login_page, username, password):
    """Tests the plain UMC logout in our devenv but the SAML login in the nightly deployment"""
    page = navigate_to_login_page
    login_page = LoginPage(page)
    login_page.login(username, password)
    home_page_logged_in = HomePageLoggedIn(page)

    home_page_logged_in.reveal_area(home_page_logged_in.right_side_menu, home_page_logged_in.header.hamburger_icon)
    home_page_logged_in.right_side_menu.click_logout_button()

    home_page_logged_out = HomePageLoggedOut(page)
    home_page_logged_out.assert_logged_out()


@pytest.mark.saml()
def test_saml_login(navigate_to_saml_login_page, username, password):
    page = navigate_to_saml_login_page
    login_page = LoginPage(page)
    login_page.login(username, password)

    home_page_logged_in = HomePageLoggedIn(page)
    home_page_logged_in.assert_logged_in()


@pytest.mark.saml()
def test_saml_logout(navigate_to_saml_login_page, username, password):
    page = navigate_to_saml_login_page
    login_page = LoginPage(page)
    login_page.login(username, password)
    home_page_logged_in = HomePageLoggedIn(page)
    home_page_logged_in.assert_logged_in()

    home_page_logged_in.reveal_area(home_page_logged_in.right_side_menu, home_page_logged_in.header.hamburger_icon)
    home_page_logged_in.right_side_menu.click_logout_button()

    home_page_logged_out = HomePageLoggedOut(page)
    home_page_logged_out.assert_logged_out()
