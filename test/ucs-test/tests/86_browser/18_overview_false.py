#!/usr/share/ucs-test/runner /usr/share/ucs-test/playwright
## desc: check behaviour of ?overview=false query parameter
## tags: [umc]
## roles: [domaincontroller_master]
## bugs: [53906]
## exposure: dangerous
## packages:
## - univention-management-console-module-udm

from playwright.sync_api import expect

import univention.testing.strings as uts
from univention.lib.i18n import Translation
from univention.testing.browser.generic_udm_module import UserModule
from univention.testing.browser.lib import UMCBrowserTest


_ = Translation('ucs-test-browser').translate


def test_correct_number_of_tabs_displayed(umc_browser_test: UMCBrowserTest, udm):
    page = umc_browser_test.page

    name = uts.random_name()
    _dn, username = udm.create_user(username=name, displayName=name)

    user_module = UserModule(umc_browser_test)
    umc_browser_test.login('Administrator', 'univention', '/univention/management/?overview=false#module=udm:users/user')

    details = user_module.open_details(username)
    details.open_tab(_('Policies'))
    users_tab = page.get_by_role('tab', name=_('Users'))
    # tab should not be visible as long as only one tab is open
    expect(users_tab).to_be_hidden()

    details.click_button(_('Policy: Desktop'))
    details.click_button(_('Create new policy'))

    # When a second tab opened the first tab should be visible
    expect(users_tab).to_be_visible()
    # this is very ugly but as far as I can see the only way to get to the close buttons
    # the first close button here is the one from the first tab and the second one from the second
    close_buttons = umc_browser_test.page.locator('#umc_widgets_TabController_0').filter(has_text='Users').locator('div').get_by_title('Close')

    # the first tabs close button should not be visible
    expect(close_buttons.first).to_be_hidden()

    policies_tab = page.get_by_role('tab', name=_('Policies'))

    # the second tab should be visible
    expect(policies_tab).to_be_visible()

    # the policies tab close button should be visible
    expect(close_buttons.last).to_be_visible()

    page.get_by_role('button', name=_('Cancel')).click()

    # the user tab should be hidden again
    expect(users_tab).to_be_hidden()
