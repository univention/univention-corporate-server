#!/usr/share/ucs-test/runner /usr/share/ucs-test/selenium
# -*- coding: utf-8 -*-
## desc: Reboot the server! Must be skipped!
## roles-not:
##  - basesystem
## tags:
##  - SKIP
##  - skip_admember
## exposure: dangerous

from univention.testing import selenium
from univention.admin import localization

translator = localization.translation('ucs-test-selenium')
_ = translator.translate


class UMCTester(object):

	def test_umc(self):
		self.selenium.do_login()
		self.selenium.open_side_menu()
		self.selenium.click_side_menu_entry(_('Server'))
		self.selenium.wait_for_text(_('Reboot server'))
		self.selenium.click_side_menu_entry(_('Reboot server'))
		self.selenium.wait_for_text(_('Please confirm to reboot this server.'))
		self.selenium.click_button(_('Reboot'))


if __name__ == '__main__':
	with selenium.UMCSeleniumTest() as s:
		umc_tester = UMCTester()
		umc_tester.selenium = s

		umc_tester.test_umc()
