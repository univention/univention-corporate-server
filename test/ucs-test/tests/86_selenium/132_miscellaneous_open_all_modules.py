#!/usr/share/ucs-test/runner /usr/share/ucs-test/selenium
# -*- coding: utf-8 -*-
## desc: |
##  Test if all available modules can be opened and closed without a problem.
## roles-not:
##  - basesystem
## tags:
##  - skip_admember
## join: true
## exposure: dangerous

import logging

from selenium.webdriver.common.by import By

from univention.lib.i18n import Translation
from univention.testing import selenium
from univention.testing.selenium.appcenter import AppCenter


logger = logging.getLogger(__name__)

_ = Translation('ucs-test-selenium').translate


class UMCTester(object):

    def test_umc(self):
        self.selenium.do_login()
        self.open_and_close_all_modules()

    def open_and_close_all_modules(self):
        available_modules = self.get_available_modules()
        self.selenium.show_notifications(False)
        for module in available_modules:
            logger.info('opening module: %s' % (module,))
            if module == _('App Center'):
                AppCenter(self.selenium).open()
            else:
                self.selenium.open_module(module, True, False)
            self.selenium.click_button(_('Close'))

    def get_available_modules(self):
        self.selenium.search_module('*')
        tile_headings = self.selenium.driver.find_elements(By.CSS_SELECTOR, '.umcGalleryName')
        return [tile_heading.get_attribute("title") if tile_heading.get_attribute("title") else tile_heading.text for tile_heading in tile_headings]


if __name__ == '__main__':
    with selenium.UMCSeleniumTest() as s:
        umc_tester = UMCTester()
        umc_tester.selenium = s
        umc_tester.appcenter = AppCenter(umc_tester.selenium)

        umc_tester.test_umc()
