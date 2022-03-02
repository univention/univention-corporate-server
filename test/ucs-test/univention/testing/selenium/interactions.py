#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Selenium Tests
#
# Copyright 2017-2022 Univention GmbH
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

import json
import logging
import time
from typing import Any, List, Union  # noqa F401

import selenium.common.exceptions as selenium_exceptions
import six
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

from univention.testing.selenium.utils import expand_path

logger = logging.getLogger(__name__)


class Interactions(object):

	def click_text(self, text, **kwargs):
		# type: (str, **Any) -> None
		logger.info("Clicking the text %r", text)
		self.click_element('//*[contains(text(), "%s")]' % (text,), **kwargs)

	def click_checkbox_of_grid_entry(self, name, **kwargs):
		# type: (str, **Any) -> None
		logger.info("Clicking the checkbox of the grid entry  %r", name)
		self.click_element(
			'//*[contains(concat(" ", normalize-space(@class), " "), " dgrid-cell ")][@role="gridcell"]/descendant-or-self::node()[contains(text(), "%s")]/../..//input[@type="checkbox"]/..'
			% (name,),
			**kwargs
		)

	def click_checkbox_of_dojox_grid_entry(self, name, **kwargs):
		# type: (str, **Any) -> None
		logger.info("Clicking the checkbox of the dojox grid entry  %r", name)
		self.click_element(
			expand_path('//*[@containsClass="dojoxGridCell"][@role="gridcell"][contains(text(), "%s")]/preceding-sibling::*[1]')
			% (name,),
			**kwargs
		)

	def click_grid_entry(self, name, **kwargs):
		# type: (str, **Any) -> None
		logger.info("Clicking the grid entry %r", name)
		self.click_element(
			'//*[contains(concat(" ", normalize-space(@class), " "), " dgrid-cell ")][@role="gridcell"]/descendant-or-self::node()[contains(text(), "%s")]'
			% (name,),
			**kwargs
		)

	def click_tree_entry(self, name, **kwargs):
		# type: (str, **Any) -> None
		logger.info("Clicking the tree entry %r", name)
		self.click_element(
			'//*[contains(concat(" ", normalize-space(@class), " "), " dgrid-column-label ")][contains(text(), "%s")]'
			% (name,),
			**kwargs
		)

	def click_button(self, button_text, xpath_prefix='', **kwargs):
		# type: (str, str, **Any) -> None
		logger.info("Clicking the button %r", button_text)
		xpath = '//*[@containsClass="dijitButtonText"][text() = "%s"]' % (button_text,)
		xpath = expand_path(xpath_prefix + xpath)
		self.click_element(
			xpath,
			**kwargs
		)

	def click_buttons(self, button_name_list, xpath_prefix='', **kwargs):
		for i, button in enumerate(button_name_list):
			try:
				self.click_button(button, xpath_prefix=xpath_prefix, **kwargs)
			except selenium_exceptions.TimeoutException:
				if i == len(button_name_list) - 1:
					raise
			else:
				break

	def click_search_button(self):
		# type: () -> None
		logger.info("Clicking the search button")
		self.click_element('//form//div[contains(concat(" ", normalize-space(@class), " "), " umcSearchIcon ")]')

	def click_tile(self, tilename, **kwargs):
		# type: (str, **Any) -> None
		logger.info("Clicking the tile %r", tilename)
		try:
			self.click_element(
				'//*[contains(concat(" ", normalize-space(@class), " "), " umcGalleryName ")][text() = "%s"]'
				% (tilename,),
				**kwargs
			)
		except selenium_exceptions.TimeoutException:
			self.click_element(
				'//*[contains(concat(" ", normalize-space(@class), " "), " umcGalleryName ")][@title = "%s"]'
				% (tilename,),
				**kwargs
			)

	def click_tile_menu_icon(self, tilename, **kwargs):
		# type: (str, **Any) -> None
		logger.info("Clicking the menu icon of tile %r", tilename)
		self.click_element(
			'//*[contains(concat(" ", normalize-space(@class), " "), " umcGalleryName ")][text() = "%s"]/../*[contains(concat(" ", normalize-space(@class), " "), " umcGalleryContextIcon ")]'
			% (tilename,),
			**kwargs
		)

	def click_tab(self, tabname, **kwargs):
		# type: (str, **Any) -> None
		logger.info("Clicking the tab %r", tabname)
		self.click_element(
			'//*[contains(concat(" ", normalize-space(@class), " "), " tabLabel ")][text() = "%s"]'
			% (tabname,),
			**kwargs
		)

	def open_side_menu(self):
		# type: () -> None
		self.click_element(expand_path('//*[@containsClass="umcMenuButton"]'))
		time.sleep(0.5)

	def close_side_menu(self):
		# type: () -> None
		self.click_element(expand_path('//*[@containsClass="umcMenuButton"]'))
		time.sleep(0.5)

	def click_side_menu_entry(self, text):
		# type: (str) -> None
		self.click_element(expand_path('//*[@containsClass="mobileMenu"]//*[@containsClass="menuItem"][contains(text(), "%s")]') % text)
		time.sleep(0.5)

	def click_side_menu_back(self):
		# type: () -> None
		self.click_element(expand_path('//*[@containsClass="mobileMenu"]//*[@containsClass="menuSlideHeader"]'))
		time.sleep(0.5)

	def click_element(self, xpath, scroll_into_view=False, timeout=60, right_click=False):
		# type: (str, bool, float, bool) -> None
		"""
		Click on the element which is found by the given xpath.

		Only use with caution when there are multiple elements with that xpath.
		Waits for the element to be clickable before attempting to click.
		"""
		elems = webdriver.support.ui.WebDriverWait(xpath, timeout).until(
			self.get_all_enabled_elements, 'click_element(%r, scroll_into_view=%r, timeout=%r, right_click=%r)' % (xpath, scroll_into_view, timeout, right_click)
		)

		if len(elems) != 1:
			logger.warn(
				"Found %d clickable elements instead of 1. Trying to click on "
				"the first one." % (len(elems),)
			)

		if scroll_into_view:
			self.driver.execute_script("arguments[0].scrollIntoView();", elems[0])
		limit = timeout
		if right_click:
			# context_click will always work since it triggers the browser context menu
			# instead of throwing ElementClickInterceptedException.
			# So we do not need to put it in the loop below
			ActionChains(self.driver).context_click(elems[0]).perform()
		else:
			while True:
				try:
					elems[0].click()
					break
				except selenium_exceptions.ElementClickInterceptedException:
					limit -= 1
					if limit == 0:
						raise
					time.sleep(1)

	def enter_input(self, inputname, inputvalue):
		# type: (str, str) -> None
		"""
		Enter inputvalue into an input-element with the tag inputname.
		"""
		logger.info('Entering %r into the input-field %r.', inputvalue, inputname)
		elem = self.get_input(inputname)
		# Retry up to 30 times if expected value does not match actual input field value.
		# This problem may arise, if the focus changes suddenly during send_keys()
		# (e.g. due to the autofocus feature of Dojo).
		for i in range(30):
			elem.clear()
			elem.send_keys(inputvalue)
			if elem.get_property('value') == inputvalue:
				break
		else:
			raise ValueError('value of input {!r} does not contain previously entered value ({!r} != {!r})'.format(inputname, inputvalue, elem.get_property('value')))

	def enter_input_combobox(self, inputname, inputvalue, with_click=True):
		# type: (str, str, bool) -> None
		xpath = "//*[@role='combobox' and .//input[@name='{}']]//input[@role='textbox']".format(inputname)
		elems = webdriver.support.ui.WebDriverWait(xpath, 60).until(
			self.get_all_enabled_elements
		)
		if len(elems) != 1:
			logger.warn("Found {!d} input elements instead of one. Try using the first one".format(len(elems)))
		elems[0].clear()
		elems[0].send_keys(inputvalue)
		if with_click:
			xpath = expand_path('//*[@containsClass="dijitMenuItem"]/descendant-or-self::node()[contains(text(), "%s")]' % (inputvalue))
			self.wait_until_element_visible(xpath)
			self.click_element(xpath)

	def enter_input_date(self, inputname, inputvalue):  # type: (str, str) -> None
		xpath = "//*[@role='combobox' and .//input[@name='{}']]//input[@role='textbox']".format(inputname)
		elems = webdriver.support.ui.WebDriverWait(xpath, 60).until(
			self.get_all_enabled_elements
		)
		if len(elems) != 1:
			logger.warn("Found {:d} input elements instead of one. Try using the first one".format(len(elems)))
		elems[0].clear()
		elems[0].send_keys(inputvalue)

	def submit_input(self, inputname):
		# type: (str) -> None
		"""
		Submit the input in an input-element with the tag inputname.
		"""
		logger.info('Submitting input field %r.' % (inputname,))
		elem = self.get_input(inputname)
		# elem.submit() -> This doesn't work, when there is an html element
		# named 'submit'.
		elem.send_keys(Keys.RETURN)

	def get_input(self, inputname):
		# type: (str) -> None
		"""
		Get an input-element with the tag inputname.
		"""
		xpath = '//input[@name= %s ]' % (json.dumps(inputname),)
		elems = webdriver.support.ui.WebDriverWait(xpath, 60).until(
			self.get_all_enabled_elements
		)

		if len(elems) != 1:
			logger.warn(
				"Found %d input elements instead of 1. Trying to use the first "
				"one." % (len(elems),)
			)
		return elems[0]

	def get_all_enabled_elements(self, xpath):
		# type: (str) -> List[Any]
		elems = self.driver.find_elements_by_xpath(xpath)
		try:
			return [
				elem
				for elem in elems
				if elem.is_enabled() and elem.is_displayed()
			]
		except selenium_exceptions.StaleElementReferenceException:
			pass
		return []

	def upload_image(self, img_path, button_label='Upload', timeout=60, xpath_prefix=''):
		# type: (str, str, int, str) -> None
		"""
		Get an ImageUploader widget on screen and upload the given img_path.
		Which ImageUploader widget is found can be isolated by specifying 'xpath_prefix'
		which would be an xpath pointing to a specific container/section etc.
		"""
		uploader_button_xpath = '//*[contains(@id, "_ImageUploader_")]//*[text()="%s"]' % (button_label,)
		self.wait_until_element_visible(xpath_prefix + uploader_button_xpath)
		uploader_xpath = '//*[contains(@id, "_ImageUploader_")]//input[@type="file"]'
		logger.info("Getting the uploader with xpath: %s" % xpath_prefix + uploader_xpath)
		uploader = self.driver.find_element_by_xpath(xpath_prefix + uploader_xpath)
		logger.info("Uploading the image: %s" % img_path)
		uploader.send_keys(img_path)
		logger.info("Waiting for upload to finish")
		time.sleep(1)  # wait_for_text('Uploading...') is too inconsistent
		self.wait_until_element_visible(xpath_prefix + uploader_button_xpath)

	def drag_and_drop(self, source, target, find_by='xpath'):
		# type: (Union[Any, str], Union[Any, str], str) -> None
		"""
		Wrapper for selenium.webdriver.common.action_chains.drag_and_drop
		"""
		if isinstance(source, six.string_types):
			source = getattr(self.driver, 'find_element_by_%s' % find_by)(source)
		if isinstance(target, six.string_types):
			target = getattr(self.driver, 'find_element_by_%s' % find_by)(target)
		ActionChains(self.driver).drag_and_drop(source, target).perform()

	def drag_and_drop_by_offset(self, source, xoffset, yoffset, find_by='xpath'):
		# type: (Union[Any, str], int, int, str) -> None
		"""
		Wrapper for selenium.webdriver.common.action_chains.drag_and_drop_by_offset
		"""
		if isinstance(source, six.string_types):
			source = getattr(self.driver, 'find_element_by_%s' % find_by)(source)
		ActionChains(self.driver).drag_and_drop_by_offset(source, xoffset, yoffset).perform()
