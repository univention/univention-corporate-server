# Copyright 2013-2017 Univention GmbH
#
# http://www.univention.de/
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
# <http://www.gnu.org/licenses/>.

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions
from univention.admin import localization
from univention.testing.umc_selenium.checks_and_waits import ChecksAndWaits
from univention.testing.umc_selenium.interactions import Interactions
import datetime
import logging
import os
import selenium.common.exceptions as selenium_exceptions
import time
import univention.testing.ucr as ucr_test
import univention.testing.utils as utils

logger = logging.getLogger(__name__)

translator = localization.translation('univention-ucs-test_umc-screenshots')
_ = translator.translate


class SeleniumError(Exception):
	pass


class SeleniumTimeoutPageload(SeleniumError):
	pass


class SeleniumCheckTestcaseError(SeleniumError):
	pass


class SeleniumErrorSymbolException(SeleniumError):
	pass


class SeleniumSeeErrorDescriptionBehindFailingTestcase(SeleniumError):
	pass


class UMCSeleniumTest(ChecksAndWaits, Interactions):
	"""
	This class provides selenium test for web ui tests.
	Default browser is Firefox. Set local variable UCSTEST_SELENIUM_BROWSER to 'chrome' or 'ie' to switch browser.
	Tests run on selenium grid server. To run tests locally use lacal varibable UCSTEST_SELENIUM=local.
	Root privileges are required, also root needs the privilege to display the browser.
	"""
	def __init__(self, language='en', host='localhost'):
		self.max_exceptions = 3
		self.browser = 'firefox'
		self.selenium_grid = False
		self.language = language
		self.base_url = 'https://' + host + '/'
		translator.set_language(self.language)
		logging.basicConfig(level=logging.INFO)

	def __enter__(self):
		if 'UCSTEST_SELENIUM_BROWSER' in os.environ:
			self.browser = os.environ['UCSTEST_SELENIUM_BROWSER']
		if 'UCSTEST_SELENIUM' in os.environ and os.environ['UCSTEST_SELENIUM'] == 'local':
			self.selenium_grid = False
		if self.selenium_grid:
			if self.browser == 'ie':
				self.browser = 'internet explorer'
			self.driver = webdriver.Remote(
				command_executor='http://jenkins.knut.univention.de:4444/wd/hub',
				desired_capabilities={
					'browserName': self.browser
				})
		else:
			if self.browser == 'chrome':
				self.driver = webdriver.Chrome()
			else:
				self.driver = webdriver.Firefox()

		ucr = ucr_test.UCSTestConfigRegistry()
		ucr.load()
		self.ldap_base = ucr.get('ldap/base')

		self.account = utils.UCSTestDomainAdminCredentials()
		self.umcLoginUsername = self.account.username
		self.umcLoginPassword = self.account.bindpw

		self.screenshot_path = '/test_selenium_screenshots/'
		if not os.path.exists(self.screenshot_path):
			os.makedirs(self.screenshot_path)

		self.driver.get(self.base_url + 'univention/login/?lang=%s' % (self.language,))
		# FIXME: Workaround for Bug #44718.
		self.driver.execute_script('document.cookie = "UMCLang=%s; path=/univention/"' % (self.language,))

		self.set_viewport_size(1200, 800)
		return self

	def __exit__(self, exc_type, exc_value, traceback):
		if exc_type:
			logger.error('Exception: %s %s' % (exc_type, exc_value))
			self.save_screenshot(hide_notifications=False, append_timestamp=True)
		self.driver.quit()

	def set_viewport_size(self, width, height):
		self.driver.set_window_size(width, height)

		measured = self.driver.execute_script("return {width: window.innerWidth, height: window.innerHeight};")
		width_delta = width - measured['width']
		height_delta = height - measured['height']

		self.driver.set_window_size(width + width_delta, height + height_delta)

	def save_screenshot(self, name='error', hide_notifications=True, xpath='/html/body', append_timestamp=False):
		# FIXME: This is needed, because sometimes it takes some time until
		# some texts are really visible (even if elem.is_displayed() is already
		# true).
		time.sleep(2)

		if hide_notifications:
			try:
				notifications_container = self.driver.find_element_by_xpath(
					'//*[contains(concat(" ", normalize-space(@class), " "), " umcNotificationContainer ")]'
				)
				self.driver.execute_script('arguments[0].style.display="None"', notifications_container)
			except selenium_exceptions.NoSuchElementException:
				hide_notifications = False

		if append_timestamp:
			timestamp = '_' + datetime.datetime.now().strftime("%Y%m%d%H%M%S")
		else:
			timestamp = ''

		filename = self.screenshot_path + name + '_' + self.language + timestamp + '.png'
		logger.info('Saving screenshot %r', filename)
		self.driver.find_element_by_xpath(xpath).screenshot(filename)

		if hide_notifications:
			self.driver.execute_script('arguments[0].style.display=""', notifications_container)

	def do_login(self, username=None, password=None):
		if username is None:
			username = self.umcLoginUsername
		if password is None:
			password = self.umcLoginPassword

		self.driver.get(self.base_url + 'univention/login/?lang=%s' % (self.language,))

		self.wait_until(
			expected_conditions.presence_of_element_located(
				(webdriver.common.by.By.ID, "umcLoginUsername")
			)
		)
		self.enter_input('username', username)
		self.enter_input('password', password)
		self.submit_input('password')
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
		logger.info('Successful login')

	def end_umc_session(self):
		"""
		Log out the logged in user.
		"""
		self.driver.get(self.base_url + 'univention/logout')

	def open_module(self, name):
		self.driver.get(self.base_url + 'univention/management/?lang=%s' % (self.language,))

		xpath = '//*[contains(concat(" ", normalize-space(@class), " "), " umcLiveSearch ")]'
		self.wait_until(
			expected_conditions.presence_of_element_located(
				(webdriver.common.by.By.XPATH, xpath)
			)
		)
		search_field = self.driver.find_element_by_xpath(xpath)
		search_field.click()
		search_field.send_keys(name)
		search_field.send_keys(Keys.RETURN)

		self.click_tile(name)

	#def check_checkbox_by_name(self, inputname, checked=True):
	#	"""
	#	This method finds html input tags by name attribute and selects and returns first element with location on screen (visible region).
	#	"""
	#	elems = self.driver.find_elements_by_name(inputname)
	#	elem = self.find_visible_element_from_list(elems)
	#	if not elem:
	#		elem = self.find_visible_checkbox_from_list(elems)
	#	# workaround for selenium grid firefox the 'disabled' checkbox needs to be clicked three times to be selected
	#	for i in range(0, 3):
	#		if elem.is_selected() is not checked:
	#			elem.click()
	#	return elem

	#def check_wizard_checkbox_by_name(self, inputname, checked=True):
	#	elem = self.driver.find_element_by_xpath("//div[starts-with(@id,'umc_modules_udm_wizards_')]//input[@name= %s ]" % json.dumps(inputname))
	#	for i in range(0, 3):
	#		if elem.is_selected() is not checked:
	#			elem.click()
	#	return elem

	#def find_combobox_by_name(self, inputname):
	#	return self.driver.find_element_by_xpath("//input[@name = %s]/parent::div/input[starts-with(@id,'umc_widgets_ComboBox')]" % json.dumps(inputname))

	#@staticmethod
	#def find_visible_element_from_list(elements):
	#	"""
	#	returns first visible element from list
	#	"""
	#	for elem in elements:
	#		if elem.is_displayed():
	#			return elem
	#	return None

	#@staticmethod
	#def find_visible_checkbox_from_list(elements):
	#	for elem in elements:
	#		if elem.location['x'] > 0 or elem.location['y'] > 0 and elem.get_attribute("type") == "checkbox" and "dijitCheckBoxInput" in elem.get_attribute("class"):
	#			return elem
	#	return None

	#def find_error_symbol_for_inputfield(self, inputfield):
	#	logger.info('check error symbol', inputfield)
	#	elems = self.driver.find_elements_by_xpath("//input[@name= %s ]/parent::div/parent::div/div[contains(@class,'dijitValidationContainer')]" % json.dumps(inputfield))
	#	elem = self.find_visible_element_from_list(elems)
	#	if elem:
	#		return True
	#	return False

	#def error_symbol_displayed(self, inputfield, displayed=True):
	#	if displayed:
	#		if not self.find_error_symbol_for_inputfield(inputfield):
	#			logger.error('Missing error symbol', inputfield)
	#			raise SeleniumErrorSymbolException
	#	else:
	#		if self.find_error_symbol_for_inputfield(inputfield):
	#			logger.error('Error symbol %r should not be displayed.', inputfield)
	#			raise SeleniumErrorSymbolException

	#def select_table_item_by_name(self, itemname):
	#	elem = self.driver.find_element_by_xpath("//div[contains(text(), %s )]/parent::td" % json.dumps(itemname))
	#	#TODO if not elem search itemname
	#	elem.click()
