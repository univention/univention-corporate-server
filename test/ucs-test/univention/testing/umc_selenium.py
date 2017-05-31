"""
Common functions used by tests.
"""
# Copyright 2013-2016 Univention GmbH
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
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.keys import Keys
import univention.testing.utils as utils
import univention.testing.ucr as ucr_test
import datetime
import logging
import os
import time
import json

logger = logging.getLogger(__name__)


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


class UMCSeleniumTest(object):
	"""
	This class provides selenium test for web ui tests.
	Default browser is Firefox. Set local variable UCSTEST_SELENIUM_BROWSER to 'chrome' or 'ie' to switch browser.
	Tests run on selenium grid server. To run tests locally use lacal varibable UCSTEST_SELENIUM=local.
	Root privileges are required, also root needs the privilege to display the browser.
	"""
	def __init__(self, login=True):

		self.login = login
		self.max_exceptions = 3
		self.browser = 'firefox'
		self.selenium_grid = False

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
		self.driver.implicitly_wait(2)

		ucr = ucr_test.UCSTestConfigRegistry()
		ucr.load()
		self.ldap_base = ucr.get('ldap/base')
		self.ip = ucr.get('interfaces/eth0/address')
		self.base_url = 'https://' + self.ip + '/'

		self.account = utils.UCSTestDomainAdminCredentials()
		self.umcLoginUsername = self.account.username
		self.umcLoginPassword = self.account.bindpw

		self.screenshot_path = '/test_selenium_screenshots/'
		if not os.path.exists(self.screenshot_path):
			os.makedirs(self.screenshot_path)

		self.driver.get(self.base_url + 'univention/login/?lang=en-US')
		if self.login:
			self.do_login()

		self.set_viewport_size(1200, 800)
		return self

	def __exit__(self, exc_type, exc_value, traceback):
		if exc_type:
			logger.error('Exception: %s %s' % (exc_type, exc_value))
			self.save_screenshot()
		self.driver.quit()

	def set_viewport_size(self, width, height):
		self.driver.set_window_size(width, height)

		measured = self.driver.execute_script("return {width: window.innerWidth, height: window.innerHeight};")
		width_delta = width - measured['width']
		height_delta = height - measured['height']

		self.driver.set_window_size(width + width_delta, height + height_delta)

	def do_login(self):
		elem = self.driver.find_element_by_id("umcLoginUsername")
		elem.clear()
		elem.send_keys(self.umcLoginUsername)
		elem = self.driver.find_element_by_id("umcLoginPassword")
		elem.clear()
		elem.send_keys(self.umcLoginPassword)
		elem.send_keys(Keys.RETURN)
		assert self.umcLoginUsername in self.driver.page_source
		logger.info('Successful login')

	def save_screenshot(self, name='error', hide_notifications=True, element_xpath='/html/body', append_timestamp=False):
		# FIXME: This is needed, because sometimes it takes some time until
		# some texts are really visible (even if elem.is_displayed() is already
		# true).
		time.sleep(1)

		if hide_notifications:
			self.driver.execute_script('dojo.style(dojo.byId("umc_widgets_ContainerWidget_0"), "display", "none")')

		if append_timestamp:
			timestamp = '_' + datetime.datetime.now().strftime("%Y%m%d%H%M%S")
		else:
			timestamp = ''

		filename = self.screenshot_path + name + timestamp + '.png'
		logger.info('Saving screenshot %r', filename)
		self.driver.find_element_by_xpath(element_xpath).screenshot(filename)

		self.driver.execute_script('dojo.style(dojo.byId("umc_widgets_ContainerWidget_0"), "display", "")')

	def open_module(self, name):
		self.driver.get(self.base_url + 'univention/management/?lang=en-US')

		search_field = self.driver.find_element_by_xpath('//*[@id="umc_widgets_LiveSearch_0"]')
		search_field.click()
		search_field.send_keys(name)
		search_field.send_keys(Keys.RETURN)

		self.click_tile(name)

	def check_checkbox_by_name(self, inputname, checked=True):
		"""
		This method finds html input tags by name attribute and selects and returns first element with location on screen (visible region).
		"""
		elems = self.driver.find_elements_by_name(inputname)
		elem = self.find_visible_element_from_list(elems)
		if not elem:
			elem = self.find_visible_checkbox_from_list(elems)
		# workaround for selenium grid firefox the 'disabled' checkbox needs to be clicked three times to be selected
		for i in range(0, 3):
			if elem.is_selected() is not checked:
				elem.click()
		return elem

	def check_wizard_checkbox_by_name(self, inputname, checked=True):
		elem = self.driver.find_element_by_xpath("//div[starts-with(@id,'umc_modules_udm_wizards_')]//input[@name= %s ]" % json.dumps(inputname))
		for i in range(0, 3):
			if elem.is_selected() is not checked:
				elem.click()
		return elem

	def find_combobox_by_name(self, inputname):
		return self.driver.find_element_by_xpath("//input[@name = %s]/parent::div/input[starts-with(@id,'umc_widgets_ComboBox')]" % json.dumps(inputname))

	def wait_for_text(self, text, timeout=30):
		logger.info("Waiting for text: %r", text)

		xpath = '//*[contains(text(), "%s")]' % (text,)
		elem = webdriver.support.ui.WebDriverWait(self.driver, timeout).until(
			expected_conditions.presence_of_element_located(
				(webdriver.common.by.By.XPATH, xpath)
			)
		)
		return elem

	def click_button(self, buttonname):
		logger.info("Clicking the button %r", buttonname)
		self.click_element(buttonname, '.dijitButtonText')

	def click_tile(self, tilename):
		logger.info("Clicking the tile %r", tilename)
		self.click_element(tilename, '.umcGalleryName')

	def click_grid_entry(self, name):
		logger.info("Clicking the grid entry %r", name)
		elems = self.driver.execute_script("""
			return dojo.query('.umcGridDefaultAction').filter(function(node) { return node.offsetParent !== null });""")
		# Only check if name is contained, because innerHTML is "polluted" in
		# grids.
		elem = filter(lambda elem: name in elem.get_attribute("innerHTML"), elems)[0]
		elem.click()

	def click_element(self, name, css_class):
		"""
		Click on an element with innerHTML=name and CCS2-selector=css_class.

		Only use with caution when there are multiple elements with that name.
		Also looks for hover texts, if no visible element is found.
		User must be logged in.
		"""

		elem = self.driver.execute_script("""
			return dojo.query(%s).filter(function(node) { return node.offsetParent !== null && node.innerHTML == %s }).pop();
			""" % (json.dumps(css_class), json.dumps(name)))
		if not elem:
			elem = self.driver.execute_script("""
				return dojo.query(%s).filter(function(node) { return node.innerHTML == %s })[0].parentNode;
				""" % (json.dumps(css_class), json.dumps(name)))
		elem.click()

	@staticmethod
	def find_visible_element_from_list(elements):
		"""
		returns first visible element from list
		"""
		for elem in elements:
			if elem.is_displayed():
				return elem
		return None

	@staticmethod
	def find_visible_checkbox_from_list(elements):
		for elem in elements:
			if elem.location['x'] > 0 or elem.location['y'] > 0 and elem.get_attribute("type") == "checkbox" and "dijitCheckBoxInput" in elem.get_attribute("class"):
				return elem
		return None

	def find_error_symbol_for_inputfield(self, inputfield):
		logger.info('check error symbol', inputfield)
		elems = self.driver.find_elements_by_xpath("//input[@name= %s ]/parent::div/parent::div/div[contains(@class,'dijitValidationContainer')]" % json.dumps(inputfield))
		elem = self.find_visible_element_from_list(elems)
		if elem:
			return True
		return False

	def error_symbol_displayed(self, inputfield, displayed=True):
		if displayed:
			if not self.find_error_symbol_for_inputfield(inputfield):
				logger.error('Missing error symbol', inputfield)
				raise SeleniumErrorSymbolException
		else:
			if self.find_error_symbol_for_inputfield(inputfield):
				logger.error('Error symbol %r should not be displayed.', inputfield)
				raise SeleniumErrorSymbolException

	def enter_input(self, inputname, inputvalue):
		"""
		Parameter inputname is the name of input tag, parameter inputvalue is the value to enter in input tag
		"""
		logger.info('enter', inputname, inputvalue)
		elem = self.driver.execute_script("""
			return dojo.query('input').filter(function(node) { return node.name == %s && node.offsetParent !== null })[0];
			""" % json.dumps(inputname))
		elem.send_keys(inputvalue)
		return elem

	def end_umc_session(self):
		"""
		Log out the logged in user.
		"""
		self.driver.get(self.base_url + 'univention/logout')

	def select_table_item_by_name(self, itemname):
		elem = self.driver.find_element_by_xpath("//div[contains(text(), %s )]/parent::td" % json.dumps(itemname))
		#TODO if not elem search itemname
		elem.click()
