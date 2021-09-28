#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Selenium Tests
#
# Copyright 2013-2021 Univention GmbH
#
# https://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <https://www.gnu.org/licenses/>.

from __future__ import absolute_import

import datetime
import json
import logging
import os
import subprocess
import time
from types import TracebackType  # noqa F401
from typing import Optional, Type  # noqa F401

import selenium.common.exceptions as selenium_exceptions
from PIL import Image
from selenium import webdriver
from selenium.webdriver.support import expected_conditions

import univention.testing.ucr as ucr_test
import univention.testing.utils as utils
from univention.admin import localization
from univention.config_registry import handler_set
from univention.testing.selenium.checks_and_waits import ChecksAndWaits
from univention.testing.selenium.interactions import Interactions
from univention.testing.selenium.utils import expand_path

logger = logging.getLogger(__name__)

translator = localization.translation('ucs-test-framework')
_ = translator.translate


class UMCSeleniumTest(ChecksAndWaits, Interactions):
	"""
	This class provides selenium test for web UI tests.
	Default browser is Firefox. Set local variable UCSTEST_SELENIUM_BROWSER to 'chrome' or 'ie' to switch browser.
	Tests run on selenium grid server. To run tests locally use local variable UCSTEST_SELENIUM=local.
	Root privileges are required, also root needs the privilege to display the browser.
	"""

	BROWSERS = {
		'ie': 'internet explorer',
		'firefox': 'firefox',
		'chrome': 'chrome',
		'chromium': 'chrome',
		'ff': 'firefox',
	}

	def __init__(self, language='en', host="", suppress_notifications=True):
		# type: (str, str, bool, bool) -> None
		self._ucr = ucr_test.UCSTestConfigRegistry()
		self._ucr.load()
		self.browser = self.BROWSERS[os.environ.get('UCSTEST_SELENIUM_BROWSER', 'firefox')]
		self.selenium_grid = os.environ.get('UCSTEST_SELENIUM') != 'local'
		self.language = language
		self.base_url = 'https://%s/' % (host or '%(hostname)s.%(domainname)s' % self._ucr)
		self.screenshot_path = os.path.abspath('selenium/')
		self.suppress_notifications = suppress_notifications
		translator.set_language(self.language)
		logging.basicConfig(level=logging.INFO)

	def __enter__(self):
		# type: () -> UMCSeleniumTest
		self.restart_umc()
		self._ucr.__enter__()
		if self.selenium_grid:
			self.driver = webdriver.Remote(
				command_executor=os.environ.get('SELENIUM_HUB', 'http://jenkins.knut.univention.de:4444/wd/hub'),
				desired_capabilities={
					'browserName': self.browser
				})
		else:
			if self.browser == 'chrome':
				chrome_options = webdriver.ChromeOptions()
				chrome_options.add_argument('--no-sandbox')  # chrome complains about being executed as root
				chrome_options.add_argument('ignore-certificate-errors')
				self.driver = webdriver.Chrome(options=chrome_options)
			else:
				self.driver = webdriver.Firefox()

		self.ldap_base = self._ucr.get('ldap/base')
		if self.suppress_notifications:
			handler_set(['umc/web/hooks/suppress_notifications=suppress_notifications'])

		self.account = utils.UCSTestDomainAdminCredentials()
		self.umcLoginUsername = self.account.username
		self.umcLoginPassword = self.account.bindpw

		if not os.path.exists(self.screenshot_path):
			os.makedirs(self.screenshot_path)

		self.driver.get(self.base_url + 'univention/login/?lang=%s' % (self.language,))
		# FIXME: Workaround for Bug #44718.
		try:
			self.driver.execute_script('document.cookie = "UMCLang=%s; path=/univention/"' % (self.language,))
		except selenium_exceptions.WebDriverException as exc:
			logger.warn('Setting language cookie failed: %s' % (exc,))

		self.set_viewport_size(1200, 800)
		return self

	def __exit__(self, exc_type, exc_value, traceback):
		# type: (Optional[Type[BaseException]], Optional[BaseException], Optional[TracebackType]) -> None
		try:
			if exc_type:
				logger.error('Exception: %s %s' % (exc_type, exc_value))
				self.save_screenshot(hide_notifications=False, append_timestamp=True)
				self.save_browser_log()
			self.driver.quit()
		finally:
			self._ucr.__exit__(exc_type, exc_value, traceback)

	def restart_umc(self):
		# type: () -> None
		subprocess.call(['systemctl', 'restart', 'univention-management-console-server'], close_fds=True)

	def set_viewport_size(self, width, height):
		# type: (int, int) -> None
		self.driver.set_window_size(width, height)

		measured = self.driver.execute_script("return {width: window.innerWidth, height: window.innerHeight};")
		width_delta = width - measured['width']
		height_delta = height - measured['height']

		self.driver.set_window_size(width + width_delta, height + height_delta)

	def save_screenshot(self, name='error', hide_notifications=True, xpath='/html/body', append_timestamp=False):
		# type: (str, bool, str, bool) -> None
		# FIXME: This is needed, because sometimes it takes some time until
		# some texts are really visible (even if elem.is_displayed() is already
		# true).
		time.sleep(2)

		if hide_notifications:
			self.show_notifications(False)

		self.open_traceback()

		timestamp = ''
		if append_timestamp:
			timestamp = '_%s' % (datetime.datetime.now().strftime("%Y%m%d%H%M%S"),)

		filename = '%s/%s_%s%s.png' % (self.screenshot_path, name, self.language, timestamp)
		logger.warning('Saving screenshot %r', filename)
		if os.environ.get('JENKINS_WS'):
			logger.warning('Screenshot URL: %sws/test/selenium/selenium/%s' % (os.environ['JENKINS_WS'], os.path.basename(filename)))

		self.driver.save_screenshot(filename)
		screenshot = self.crop_screenshot_to_element(filename, xpath)
		screenshot.save(filename)

		if hide_notifications:
			try:
				self.show_notifications(True)
			except selenium_exceptions.TimeoutException:
				pass

	def open_traceback(self):
		# type: () -> None
		try:
			self.wait_for_text(_('Show server error message'), timeout=1)
			self.click_text(_('Show server error message'))
		except selenium_exceptions.TimeoutException:
			pass

	def crop_screenshot_to_element(self, image_filename, xpath):
		# type: (str, str) -> Image
		elem = self.driver.find_element_by_xpath(xpath)
		location = elem.location
		size = elem.size
		top, left = int(location['y']), int(location['x'])
		bottom, right = int(location['y'] + size['height']), int(location['x'] + size['width'])

		screenshot = Image.open(image_filename)
		return screenshot.crop((left, top, right, bottom))

	def save_browser_log(self, name='error', append_timestamp=True):
		# type: (str, bool) -> None
		timestamp = ''
		if append_timestamp:
			timestamp = '_%s' % (datetime.datetime.now().strftime("%Y%m%d%H%M%S"),)

		filename = '%s/%s_%s_browserlog%s.txt' % (self.screenshot_path, name, self.language, timestamp)
		logger.info('Saving browser log %r', filename)
		if os.environ.get('JENKINS_WS'):
			logger.info('Browser Log URL: %sws/test/selenium/selenium/%s' % (os.environ['JENKINS_WS'], os.path.basename(filename)))
		with open(filename, 'w') as f:
			for entry in self.driver.get_log('browser'):
				f.write('%s\n' % (json.dumps(entry),))

	def show_notifications(self, show_notifications=True):
		# type: (bool) -> None
		if show_notifications:
			if not self.notifications_visible():
				self.press_notifications_button()
		else:
			if self.notifications_visible():
				self.press_notifications_button()

	def notifications_visible(self):
		# type: () -> bool
		return not self.elements_invisible('//*[contains(concat(" ", normalize-space(@class), " "), " umcNotificationDropDownButtonOpened ")]')

	def press_notifications_button(self):
		# type: () -> None
		self.click_element('//*[contains(concat(" ", normalize-space(@class), " "), " umcNotificationDropDownButton ")]')
		# Wait for the animation to run.
		time.sleep(1)

	def do_login(self, username=None, password=None, without_navigation=False, language=None, check_successful_login=True):
		# type: (Optional[str], Optional[str], bool, Optional[str]) -> None
		if username is None:
			username = self.umcLoginUsername
		if password is None:
			password = self.umcLoginPassword

		# FIXME: selenium.common.exceptions.InvalidCookieDomainException: Message: invalid cookie domain
		# for year in set([2020, datetime.date.today().year, datetime.date.today().year + 1, datetime.date.today().year - 1]):
		# 	self.driver.add_cookie({'name': 'hideSummit%sDialog' % (year,), 'value': 'true'})
		# 	self.driver.add_cookie({'name': 'hideSummit%sNotification' % (year,), 'value': 'true'})
		if not without_navigation:
			self.driver.get(self.base_url + 'univention/login/?lang=%s' % (self.language if not language else language,))

		self.wait_until(
			expected_conditions.presence_of_element_located(
				(webdriver.common.by.By.ID, "umcLoginUsername")
			)
		)
		self.enter_input('username', username)
		self.enter_input('password', password)
		self.submit_input('password')

		# for testing 'change password on next login'
		# don't check for available modules etc.
		if not check_successful_login:
			return

		self.wait_for_any_text_in_list([
			_('Users'),
			_('Devices'),
			_('Domain'),
			_('System'),
			_('Software'),
			_('Installed Applications'),
			_('no module available')
		])
		try:
			self.wait_for_text(_('no module available'), timeout=1)
			self.click_button(_('Ok'))
			self.wait_until_all_dialogues_closed()
		except selenium_exceptions.TimeoutException:
			pass
		self.show_notifications(False)
		logger.info('Successful login')

	def end_umc_session(self):
		# type: () -> None
		"""
		Log out the logged in user.
		"""
		self.driver.get(self.base_url + 'univention/logout')

	def open_module(self, name, wait_for_standby=True, do_reload=True):
		# type: (str, bool, bool) -> None
		self.search_module(name, do_reload)
		self.click_tile(name)
		if wait_for_standby:
			self.wait_until_standby_animation_appears_and_disappears()
			if name == 'System diagnostic':
				self.wait_until_progress_bar_finishes()

	def search_module(self, name, do_reload=True):
		# type: (str, bool) -> None
		if do_reload:
			self.driver.get(self.base_url + 'univention/management/?lang=%s' % (self.language,))

		input_field = self.wait_for_element_by_css_selector('.umcModuleSearch input.dijitInputInner')
		if not input_field.is_displayed():
			self.click_element(expand_path('//*[@containsClass="umcModuleSearchToggleButton"]'))
		limit = 60
		while limit > 0:
			try:
				input_field.clear()
				break
			except selenium_exceptions.ElementNotInteractableException:
				if limit > 1:
					logger.info("Item was not interactable, retrying after one second")
					time.sleep(1)
					limit -= 1
				else:
					logger.info("Item was not interactable after 60 seconds.")
					raise
		input_field.send_keys(name)
		self.wait_for_text(_('Search query'))

	# def check_checkbox_by_name(self, inputname, checked=True):
	# 	"""
	# 	This method finds html input tags by name attribute and selects and returns first element with location on screen (visible region).
	# 	"""
	# 	elems = self.driver.find_elements_by_name(inputname)
	# 	elem = self.find_visible_element_from_list(elems)
	# 	if not elem:
	# 		elem = self.find_visible_checkbox_from_list(elems)
	# 	# workaround for selenium grid firefox the 'disabled' checkbox needs to be clicked three times to be selected
	# 	for i in range(0, 3):
	# 		if elem.is_selected() is not checked:
	# 			elem.click()
	# 	return elem

	# def check_wizard_checkbox_by_name(self, inputname, checked=True):
	# 	elem = self.driver.find_element_by_xpath("//div[starts-with(@id,'umc_modules_udm_wizards_')]//input[@name= %s ]" % json.dumps(inputname))
	# 	for i in range(0, 3):
	# 		if elem.is_selected() is not checked:
	# 			elem.click()
	# 	return elem

	# def find_combobox_by_name(self, inputname):
	# 	return self.driver.find_element_by_xpath("//input[@name = %s]/parent::div/input[starts-with(@id,'umc_widgets_ComboBox')]" % json.dumps(inputname))

	# @staticmethod
	# def find_visible_element_from_list(elements):
	# 	"""
	# 	returns first visible element from list
	# 	"""
	# 	for elem in elements:
	# 		if elem.is_displayed():
	# 			return elem
	# 	return None

	# @staticmethod
	# def find_visible_checkbox_from_list(elements):
	# 	for elem in elements:
	# 		if elem.location['x'] > 0 or elem.location['y'] > 0 and elem.get_attribute("type") == "checkbox" and "dijitCheckBoxInput" in elem.get_attribute("class"):
	# 			return elem
	# 	return None

	# def find_error_symbol_for_inputfield(self, inputfield):
	# 	logger.info('check error symbol', inputfield)
	# 	elems = self.driver.find_elements_by_xpath("//input[@name= %s ]/parent::div/parent::div/div[contains(@class,'dijitValidationContainer')]" % json.dumps(inputfield))
	# 	elem = self.find_visible_element_from_list(elems)
	# 	if elem:
	# 		return True
	# 	return False

	# def error_symbol_displayed(self, inputfield, displayed=True):
	# 	if displayed:
	# 		if not self.find_error_symbol_for_inputfield(inputfield):
	# 			logger.error('Missing error symbol', inputfield)
	# 			raise ValueError()
	# 	else:
	# 		if self.find_error_symbol_for_inputfield(inputfield):
	# 			logger.error('Error symbol %r should not be displayed.', inputfield)
	# 			raise ValueError()

	# def select_table_item_by_name(self, itemname):
	# 	elem = self.driver.find_element_by_xpath("//div[contains(text(), %s )]/parent::td" % json.dumps(itemname))
	# 	#TODO if not elem search itemname
	# 	elem.click()
