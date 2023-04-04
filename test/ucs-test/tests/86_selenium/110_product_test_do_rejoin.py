#!/usr/share/ucs-test/runner /usr/share/ucs-test/selenium
## desc: (Re)join a domain controller.
## packages:
##  - univention-management-console-module-join
## roles-not:
##  - domaincontroller_master
##  - basesystem
## tags: [SKIP, umc-producttest]
## exposure: dangerous

from shutil import copyfile
from univention.admin import localization
from univention.testing import selenium
import os

translator = localization.translation('ucs-test-selenium')
_ = translator.translate


class PasswordChangeError(Exception):
	pass


class UMCTester(object):

	def test_umc(self):
		self.save_status_file()

		self.selenium.do_login(username='root')
		self.join_domain()
		self.test_if_login_works()

		self.restore_status_file()

	def save_status_file(self):
		copyfile('/var/univention-join/status', '/var/univention-join/status.bak')

	def restore_status_file(self):
		os.rename('/var/univention-join/status.bak', '/var/univention-join/status')

	def join_domain(self):
		self.selenium.open_module(_('Domain join'))
		self.selenium.wait_for_text(_('This page shows the status of'))
		self.selenium.click_button(_('Rejoin'))

		self.selenium.wait_for_text(_('Confirmation'))
		self.selenium.enter_input('username', self.selenium.umcLoginUsername)
		self.selenium.enter_input('password', self.selenium.umcLoginPassword)
		self.selenium.click_button(_('Rejoin system'))

		self.selenium.wait_for_text(_('A reboot of the server is recommended'), timeout=600)
		self.selenium.click_button(_('Cancel'))

	def test_if_login_works(self):
		self.selenium.do_login()


if __name__ == '__main__':
	with selenium.UMCSeleniumTest() as s:
		umc_tester = UMCTester()
		umc_tester.selenium = s

		umc_tester.test_umc()
