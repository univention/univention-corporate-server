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

		if self.login:
			self.do_login()

		# FIXME: For some reason I need to do set_window_size() once before it
		# works correctly.
		self.driver.set_window_size(1200, 800)
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
		self.driver.get(self.base_url + 'univention/login/?lang=en-US')

		elem = self.driver.find_element_by_id("umcLoginUsername")
		elem.clear()
		elem.send_keys(self.umcLoginUsername)
		elem = self.driver.find_element_by_id("umcLoginPassword")
		elem.clear()
		elem.send_keys(self.umcLoginPassword)
		elem.send_keys(Keys.RETURN)
		assert self.umcLoginUsername in self.driver.page_source
		logger.info('Successful login')

	def save_screenshot(self, name='error', hide_notifications=True):
		old_viewport_width = self.driver.execute_script("return window.innerWidth")
		old_viewport_height = self.driver.execute_script("return window.innerHeight")
		document_height = self.driver.execute_script("return document.body.clientHeight")
		if old_viewport_height < document_height:
			logger.info(
				'Increasing viewport height temporarily from %spx to %spx to '
				'fit the whole document into a screenshot.'
				% (old_viewport_height, document_height)
			)
			self.set_viewport_size(old_viewport_width, document_height)

		if hide_notifications:
			self.driver.execute_script('dojo.style(dojo.byId("umc_widgets_ContainerWidget_0"), "display", "none")')

		filename = self.screenshot_path + name + '_' + datetime.datetime.now().strftime("%Y%m%d%H%M%S") + '.png'
		logger.info('Saving screenshot %s' % filename)
		self.driver.save_screenshot(filename)

		self.driver.execute_script('dojo.style(dojo.byId("umc_widgets_ContainerWidget_0"), "display", "")')
		self.set_viewport_size(old_viewport_width, old_viewport_height)

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

	def find_element_by_text(self, text):
		return self.driver.find_element_by_xpath('//*[contains(text(), "%s")]' % text)

	def click_button(self, buttonname):
		self.click_element(buttonname, '.dijitButtonText')

	def click_tile(self, tilename):
		self.click_element(tilename, '.umcGalleryName')

	def click_grid_entry(self, name):
		elems = self.driver.execute_script("""
			return dojo.query('.umcGridDefaultAction').filter(function(node) { return node.offsetParent !== null });""")
		# Only check if name is contained, because innerHTML is "polluted" in
		# grids.
		elem = filter(lambda elem: name in elem.get_attribute("innerHTML"), elems)[0]
		elem.click()
		self.wait_for_pageload()

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
		self.wait_for_pageload()

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
				logger.error('Error symbol %s should not be displayed.' % inputfield)
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

	def wait_for_pageload(self, timeout=30):
		"""
		Waits until page is loaded. Can only be used if a user is signed in. Parameter 'timeout' gives maximum time to wait in seconds.
		"""
		deadline = time.time() + timeout
		while time.time() < deadline:
			time.sleep(0.2)
			if self.driver.execute_script("""
					try {
						var tools = require('umc/tools');
						var app = require('umc/app');
						var load = false;
						var page = app._tabContainer.selectedChildWidget;
						require(['dojo/ready'], function (ready) {
							ready(function () {
								load =  document.readyState == "complete" && tools.status('setupGui') && !page.$isDummy$;
							});
						});
						return load;
					}
					catch (err) {
						return;
					}"""):
						break
		else:
			logger.error('Timeout reached - page still not loaded completely')
			raise SeleniumTimeoutPageload

	def end_umc_session(self):
		"""
		Log out the logged in user.
		"""
		self.driver.get('https://' + self.ip + '/univention/logout')

	def select_table_item_by_name(self, itemname):
		elem = self.driver.find_element_by_xpath("//div[contains(text(), %s )]/parent::td" % json.dumps(itemname))
		#TODO if not elem search itemname
		elem.click()
