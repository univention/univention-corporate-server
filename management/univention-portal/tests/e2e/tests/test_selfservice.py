# SPDX-License-Identifier: AGPL-3.0-only
# SPDX-FileCopyrightText: 2023-2024 Univention GmbH

import random

import pytest
from playwright.sync_api import Page
from playwright_pages_base import expect
from playwright_pages_ucs_portal.home_page.logged_in import HomePageLoggedIn
from playwright_pages_ucs_portal.home_page.logged_out import HomePageLoggedOut
from playwright_pages_ucs_portal.selfservice.change_password import ChangePasswordDialogPage
from playwright_pages_ucs_portal.users.users_page import UCSUsersPage


DUMMY_USER_NAME = f"dummy_{random.randint(1000, 9999)}"  # noqa: S311
DUMMY_USER_PASSWORD_1 = "firstpass"
DUMMY_USER_PASSWORD_2 = "secondpass"


@pytest.fixture()
def dummy_user_home(navigate_to_home_page_logged_in: Page, username, password) -> Page:
    page = navigate_to_home_page_logged_in
    home_page_logged_in = HomePageLoggedIn(page)
    home_page_logged_out = HomePageLoggedOut(page)

    # TODO: This step is necessary, because when using a UCS VM vs. a SouvAP env,
    # the start page after login is not /umc.
    home_page_logged_in.page.goto("/umc")
    home_page_logged_in.click_users_tile()
    users_page = UCSUsersPage(page)
    users_page.add_user(DUMMY_USER_NAME, DUMMY_USER_PASSWORD_1)

    home_page_logged_out.navigate()

    yield page

    dummy_user_home_logged_out = HomePageLoggedOut(page)
    dummy_user_home_logged_out.navigate()

    home_page_logged_in.navigate(username, password)

    home_page_logged_in.page.goto("/umc")
    home_page_logged_in.click_users_tile()
    users_page.remove_user(DUMMY_USER_NAME)

    home_page_logged_out.navigate()


def test_non_admin_can_change_password(dummy_user_home: Page):
    # TODO: this test is currently implemented to work with a UCS VM only.
    # It is not validated against the SouvAP environment!
    change_password_page = ChangePasswordDialogPage(dummy_user_home)
    change_password_page.navigate(DUMMY_USER_NAME, DUMMY_USER_PASSWORD_1)
    change_password_page.change_password(DUMMY_USER_PASSWORD_1, DUMMY_USER_PASSWORD_2)

    dummy_user_home_logged_out = HomePageLoggedOut(dummy_user_home)
    dummy_user_home_logged_out.navigate()

    dummy_user_home_logged_in = HomePageLoggedIn(dummy_user_home)
    dummy_user_home_logged_in.navigate(DUMMY_USER_NAME, DUMMY_USER_PASSWORD_2)
    dummy_user_home_logged_in.reveal_area(
        dummy_user_home_logged_in.right_side_menu,
        dummy_user_home_logged_in.header.hamburger_icon,
    )
    expect(dummy_user_home_logged_in.right_side_menu.logout_button).to_be_visible()
