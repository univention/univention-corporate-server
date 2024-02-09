# SPDX-License-Identifier: AGPL-3.0-only
# SPDX-FileCopyrightText: 2023-2024 Univention GmbH

from playwright_pages_base import expect
from playwright_pages_ucs_portal.home_page.logged_in import HomePageLoggedIn
from playwright_pages_ucs_portal.users.users_page import UsersPage


def test_admin_user_can_view_users_page(navigate_to_home_page_logged_in):
    """This test should be run using an admin user. Otherwise, it will fail."""
    page = navigate_to_home_page_logged_in
    home_page_logged_in = HomePageLoggedIn(page)
    # TODO: We don't yet have a concept for popups in our POM.
    with page.expect_popup() as tab_admin:
        home_page_logged_in.click_users_tile()
    users_page = UsersPage(tab_admin.value)
    # TODO: The user list takes unnaturally long to appear. We are using a locator timeout
    # to handle that. Replace this with an increased global timeout as soon as we figure out how.
    expect(users_page.add_user_button).to_be_visible(timeout=10000)
    expect(users_page.column_header_name).to_be_visible()
    expect(users_page.column_header_type).to_be_visible()
    expect(users_page.column_header_path).to_be_visible()
