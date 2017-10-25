#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Selenium Tests
#
# Copyright 2017 Univention GmbH
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

from __future__ import absolute_import

import json
import logging

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import selenium.common.exceptions as selenium_exceptions

logger = logging.getLogger(__name__)


class Interactions(object):

	def click_text(self, text, **kwargs):
		logger.info("Clicking the text %r", text)
		self.click_element('//*[contains(text(), "%s")]' % (text,), **kwargs)

	def click_checkbox_of_grid_entry(self, name, **kwargs):
		logger.info("Clicking the checkbox of the grid entry  %r", name)
		self.click_element(
			'//*[contains(concat(" ", normalize-space(@class), " "), " dgrid-cell ")][@role="gridcell"]//*[contains(text(), "%s")]/../..//input[@type="checkbox"]/..'
			% (name,),
			**kwargs
		)

	def click_grid_entry(self, name, **kwargs):
		logger.info("Clicking the grid entry %r", name)
		self.click_element(
			'//*[contains(concat(" ", normalize-space(@class), " "), " dgrid-cell ")][@role="gridcell"]/descendant-or-self::node()[contains(text(), "%s")]'
			% (name,),
			**kwargs
		)

	def click_tree_entry(self, name, **kwargs):
		logger.info("Clicking the tree entry %r", name)
		self.click_element(
			'//*[contains(concat(" ", normalize-space(@class), " "), " dgrid-column-label ")][contains(text(), "%s")]'
			% (name,),
			**kwargs
		)

	def click_button(self, buttonname, **kwargs):
		logger.info("Clicking the button %r", buttonname)
		self.click_element(
			'//*[contains(concat(" ", normalize-space(@class), " "), " dijitButtonText ")][text() = "%s"]'
			% (buttonname,),
			**kwargs
		)

	def click_search_button(self):
		logger.info("Clicking the search button")
		self.click_element('//form//div[contains(concat(" ", normalize-space(@class), " "), " umcSearchIcon ")]')

	def click_tile(self, tilename, **kwargs):
		logger.info("Clicking the tile %r", tilename)
		self.click_element(
			'//*[contains(concat(" ", normalize-space(@class), " "), " umcGalleryName ")][text() = "%s"]'
			% (tilename,),
			**kwargs
		)

	def click_tab(self, tabname, **kwargs):
		logger.info("Clicking the tab %r", tabname)
		self.click_element(
			'//*[contains(concat(" ", normalize-space(@class), " "), " tabLabel ")][text() = "%s"]'
			% (tabname,),
			**kwargs
		)

	def open_side_menu(self):
		self.click_element('//*[@class="umcMobileMenuToggleButton"]')

	def click_element(self, xpath, scroll_into_view=False):
		"""
		Click on the element which is found by the given xpath.

		Only use with caution when there are multiple elements with that xpath.
		Waits for the element to be clickable before attempting to click.
		"""
		elems = webdriver.support.ui.WebDriverWait(xpath, 60).until(
			self.get_all_enabled_elements
		)

		if len(elems) != 1:
			logger.warn(
				"Found %d clickable elements instead of 1. Trying to click on "
				"the first one." % (len(elems),)
			)

		if scroll_into_view:
			self.driver.execute_script("arguments[0].scrollIntoView();", elems[0])

		elems[0].click()

	def enter_input(self, inputname, inputvalue):
		"""
		Enter inputvalue into an input-element with the tag inputname.
		"""
		logger.info('Entering %r into the input-field %r.', inputvalue, inputname)
		elem = self.get_input(inputname)
		elem.clear()
		elem.send_keys(inputvalue)

	def submit_input(self, inputname):
		"""
		Submit the input in an input-element with the tag inputname.
		"""
		logger.info('Submitting input field %r.' % (inputname,))
		elem = self.get_input(inputname)
		# elem.submit() -> This doesn't work, when there is an html element
		# named 'submit'.
		elem.send_keys(Keys.RETURN)

	def force_full_grid_load(self):
		elem = self.driver.find_element_by_xpath(
			'//*[contains(concat(" ", normalize-space(@class), " "), '
			'" dgrid-grid ")]'
		)
		self.driver.execute_script(
			'arguments[0].style.maxHeight=""; '
			'dijit.byNode(arguments[0]).resize()',
			elem
		)

	def get_input(self, inputname):
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
		elems = self.driver.find_elements_by_xpath(xpath)
		try:
			clickable_elems = [elem for elem in elems if elem.is_enabled() and elem.is_displayed()]
			if clickable_elems:
				return clickable_elems
		except selenium_exceptions.StaleElementReferenceException:
			pass
		return False
