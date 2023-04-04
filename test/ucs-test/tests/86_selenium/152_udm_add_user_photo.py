#!/usr/share/ucs-test/runner /usr/share/ucs-test/selenium
# -*- coding: utf-8 -*-
## desc: Test adding, changing and removing a photo for a user
## packages:
##  - univention-management-console-module-udm
## roles:
##  - domaincontroller_master
##  - domaincontroller_backup
## tags:
##  - skip_admember
## join: true
## exposure: dangerous

from selenium.common.exceptions import NoSuchElementException

import univention.testing.selenium as selenium
import univention.testing.selenium.udm as selenium_udm
import univention.testing.udm as udm_test
from univention.admin import localization
from univention.testing.utils import get_ldap_connection


translator = localization.translation('ucs-test-selenium')
_ = translator.translate


class UmcUdmError(Exception):
	pass


class UMCTester(object):

	def setup(self):
		self.create_test_user()
		self.login_and_open_module()

	def create_test_user(self):
		self.users = selenium_udm.Users(self.selenium)
		userdn = self.udm.create_user()[0]
		lo = get_ldap_connection()
		user_object = lo.get(userdn)
		user = {}
		user['username'] = user_object['uid'][0].decode('utf-8')
		user['lastname'] = user_object['sn'][0].decode('utf-8')
		self.user = user

	def login_and_open_module(self):
		self.selenium.do_login()
		self.selenium.open_module(self.users.name)
		self.users.wait_for_main_grid_load()

	def test_umc(self):
		self.setup()

		uploaded_src_initial = self.test_upload_image(self.user, '/tmp/initial.png')
		uploaded_src_changed = self.test_upload_image(self.user, '/tmp/changed.png')
		if uploaded_src_changed == uploaded_src_initial:
			raise UmcUdmError('The src in the img tag did not change after a new image has been uploaded')
		self.test_clear_image(self.user)

	def test_upload_image(self, user, img_path):
		self.users.open_details(user)
		self.selenium.driver.save_screenshot(img_path)
		self.selenium.upload_image(img_path, button_label='Upload profile image')

		if not self.get_uploaded_src():
			raise UmcUdmError('There is no img tag in the Image widget after an image has been uploaded')
		self.users.save_details()
		self.users.open_details(user)
		uploaded_src = self.get_uploaded_src()
		if not uploaded_src:
			raise UmcUdmError('There is no img tag in the Image widget after uploading a image, saving and opening the detailspage again')
		self.users.close_details()

		return uploaded_src

	def test_clear_image(self, user):
		self.users.open_details(user)
		self.selenium.click_button('Remove', xpath_prefix='//*[@containsClass="umcUDMUsersModule__jpegPhoto"]')
		if self.get_uploaded_src():
			raise UmcUdmError('There is still an img tag in the Image widget after "Remove" has been pressed')
		self.users.save_details()
		self.users.open_details(user)
		if self.get_uploaded_src():
			raise UmcUdmError('There is still an img tag in the Image widget after clearing the image, saving and opening the detailspage again')

	def get_uploaded_src(self):
		try:
			img = self.selenium.driver.find_element_by_css_selector('.umcUDMUsersModule__jpegPhoto .umcImage__img')
		except NoSuchElementException:
			return None
		else:
			return img.get_attribute('src')


if __name__ == '__main__':
	with udm_test.UCSTestUDM() as udm, selenium.UMCSeleniumTest() as s:
		umc_tester = UMCTester()
		umc_tester.udm = udm
		umc_tester.selenium = s

		umc_tester.test_umc()
