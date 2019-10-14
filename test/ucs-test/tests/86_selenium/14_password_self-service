#!/usr/share/ucs-test/runner /usr/share/ucs-test/selenium
# -*- coding: utf-8 -*-
## desc: test password reset via self service app
## packages:
##  - univention-mail-server
##  - univention-self-service
##  - univention-self-service-master
##  - univention-self-service-passwordreset-umc
## roles-not:
##  - memberserver
##  - basesystem
## tags:
##  - skip_admember
##  - SKIP
## join: true
## exposure: dangerous

from essential.mail import file_search_mail
from selenium import webdriver
from univention.admin import localization
from univention.testing.udm import UCSTestUDM_CreateUDMObjectFailed
import time
import univention.testing.strings as uts
import univention.testing.ucr as ucr_test
import univention.testing.udm as udm_test
from univention.testing import selenium

translator = localization.translation('ucs-test-selenium')
_ = translator.translate


MAIL_RECEIVE_TIMEOUT = 120
# TODO: Find out why the message is always in English.
TOKEN_PW_RESET = "To change your password please follow this link"


class UmcPasswordSelfServiceError(Exception):
	pass


class User(object):

	def __init__(self, username, password='univention', mail=None):
		self.name = username
		self.password = password
		self.mail = mail


class UMCTester(object):

	def test_umc(self):
		self.enable_mail_receiving()

		testuser = self.create_user_with_mail()

		self.setup_recovery_mail(testuser)
		self.test_password_change(testuser)
		self.test_password_reset(testuser)

	def enable_mail_receiving(self):
		name = self.ucr.get('domainname')
		position = 'cn=domain,cn=mail,%s' % (self.ucr.get('ldap/base'),)
		try:
			self.udm.create_object('mail/domain', name=name, position=position)
		except UCSTestUDM_CreateUDMObjectFailed:
			# Assuming this error occurred, because the object exists already,
			# which is ok.
			pass

	def create_user_with_mail(self):
		domain = self.ucr.get('domainname')
		mail = '%s@%s' % (uts.random_string(), domain)
		password = 'univention'
		userdn, username = self.udm.create_user(
			set={
				'mailHomeServer': '%s.%s' % (self.ucr.get('hostname'), domain),
				'mailPrimaryAddress': mail,
				'password': password
			}
		)
		return User(username, password=password, mail=mail)

	def setup_recovery_mail(self, user):
		self.selenium.driver.get(self.selenium.base_url + 'univention/portal')
		self.selenium.click_text(_('Change password'))
		self.selenium.click_text(_('Protect account'))

		self.enter_input_into_xpath(user.name, '//input[starts-with(@id, "selfservice_password_TextBox_")]')
		self.enter_input_into_xpath(user.password, '//input[starts-with(@id, "selfservice_password_PasswordBox_")]')

		self.selenium.click_button(_('Next'))
		time.sleep(2)

		self.enter_input_into_xpath(user.mail, '//input[@id="email_check"]')
		self.enter_input_into_xpath(user.mail, '//input[@id="email"]')

		self.selenium.click_button(_('Save'))
		self.selenium.wait_for_text(_('Univention Portal'))

	def test_password_change(self, user):
		self.selenium.driver.get(self.selenium.base_url + 'univention/portal')
		self.selenium.click_text(_('Change password'))
		self.selenium.click_text(_('Password change'))
		self.selenium.wait_for_text(_('Change your (expired) password.'))

		self.enter_input_into_xpath(user.name, '//ol[@id="PasswordChangeSteps"]//div[./text()="Username"]/..//input[starts-with(@id,"selfservice_password_")]')
		self.enter_input_into_xpath(user.password, '//ol[@id="PasswordChangeSteps"]//div[./text()="Old Password"]/..//input[starts-with(@id,"selfservice_password_")]')
		user.password = uts.random_string()
		self.enter_input_into_xpath(user.password, '//ol[@id="PasswordChangeSteps"]//div[./text()="New Password"]/..//input[starts-with(@id,"selfservice_password_")]')
		self.enter_input_into_xpath(user.password, '//ol[@id="PasswordChangeSteps"]//div[./text()="New Password (retype)"]/..//input[starts-with(@id,"selfservice_password_")]')

		self.selenium.click_button(_('Change password'))
		self.selenium.wait_for_text(_('Univention Portal'))

		self.selenium.do_login(username=user.name, password=user.password)
		self.selenium.end_umc_session()

	def test_password_reset(self, user):
		self.request_password_reset(user.name)
		self.wait_for_mail_to_arrive(user.mail, token=TOKEN_PW_RESET)
		# TODO: Follow both links from the mail, once Bug #45041 is fixed.
		# self.selenium.do_login(username=user.name, password=user.password)
		# self.selenium.end_umc_session()

	def request_password_reset(self, username):
		self.selenium.driver.get(self.selenium.base_url + 'univention/portal')
		self.selenium.click_text(_('Change password'))
		self.selenium.click_text(_('Password forgotten'))
		self.selenium.wait_for_text(_('Forgot your password'))
		self.enter_input_into_xpath(username, '//input[contains(concat(" ", normalize-space(@class), " "), " dijitInputInner ")]')
		self.selenium.click_button(_('Next'))
		self.selenium.wait_for_text(_('Please choose an option'))
		self.selenium.click_button(_('Next'))

	def wait_for_mail_to_arrive(self, mail, token):
		for timeout in range(MAIL_RECEIVE_TIMEOUT, 0, -1):
			count_found_mails = file_search_mail(tokenlist=[TOKEN_PW_RESET], mail_address=mail)
			if count_found_mails == 0:
				time.sleep(1)
			else:
				return
		raise UmcPasswordSelfServiceError('No mail has been received.')

	def enter_input_into_xpath(self, text, xpath):
		elem = self.wait_for_and_get_element_by_xpath(xpath)
		elem.clear()
		elem.send_keys(text)

	def wait_for_and_get_element_by_xpath(self, xpath):
		elems = webdriver.support.ui.WebDriverWait(xpath, 60).until(
			self.selenium.get_all_enabled_elements
		)
		return elems[0]


if __name__ == '__main__':
	with ucr_test.UCSTestConfigRegistry() as ucr, udm_test.UCSTestUDM() as udm, selenium.UMCSeleniumTest() as s:
		umc_tester = UMCTester()
		umc_tester.ucr = ucr
		umc_tester.udm = udm
		umc_tester.selenium = s

		umc_tester.test_umc()
