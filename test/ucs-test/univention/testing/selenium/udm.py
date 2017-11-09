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

import time

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys

from univention.admin import localization
import univention.testing.strings as uts

translator = localization.translation('ucs-test-framework')
_ = translator.translate


class UDMBase(object):

	def __init__(self, selenium):
		self.selenium = selenium

	def exists(self, objectname):
		# This method will work with *most* UDM modules.
		self.search(objectname)
		time.sleep(5)
		self.selenium.wait_until_all_standby_animations_disappeared()
		try:
			self.selenium.wait_for_text(objectname, timeout=1)
			return True
		except TimeoutException:
			pass
		return False

	def open_details(self, objectname):
		# This method will work with *most* UDM modules.
		self.search(objectname)
		self.selenium.click_grid_entry(objectname)
		self.selenium.wait_for_text(_('Basic settings'))

	def close_details(self):
		self.selenium.click_button(_('Back'))
		self.wait_for_main_grid_load()

	def save_details(self):
		self.selenium.click_button(_('Save'))
		self.wait_for_main_grid_load()

	def delete(self, objectname):
		# This method will work with *most* UDM modules.
		self.search(objectname)

		self.selenium.click_checkbox_of_grid_entry(objectname)
		self.selenium.click_button(_('Delete'))
		self.selenium.wait_for_text(_("Please confirm the removal"))
		self.selenium.click_element(
			'//div[contains(concat(" ", normalize-space(@class), " "), " dijitDialog ")]'
			'//*[contains(concat(" ", normalize-space(@class), " "), " dijitButtonText ")]'
			'[text() = "%s"]' % (_("Delete"),)
		)
		self.wait_for_main_grid_load()

	def wait_for_main_grid_load(self, timeout=60):
		time.sleep(5)
		xpaths = ['//div[contains(concat(" ", normalize-space(@class), " "), " dgrid-row ")]']
		webdriver.support.ui.WebDriverWait(xpaths, timeout).until(
			self.selenium.get_all_visible_elements, 'wait %s for grid load' % (timeout,)
		)
		self.selenium.wait_until_all_standby_animations_disappeared()

	def search(self, objectname):
		# This method will work with *most* UDM modules.
		xpath = '//input[@name="objectPropertyValue"]'
		elems = webdriver.support.ui.WebDriverWait(xpath, 60).until(
			self.selenium.get_all_enabled_elements
		)
		elems[0].clear()
		elems[0].send_keys(objectname)
		elems[0].send_keys(Keys.RETURN)
		time.sleep(5)
		self.selenium.wait_until_all_standby_animations_disappeared()
		elems[0].clear()


class Computers(UDMBase):
	name = _('Computers')

	def add(self, computername=None):
		if computername is None:
			computername = uts.random_string()

		self.selenium.click_button(_('Add'))
		self.selenium.wait_for_text(_("Container"))
		self.selenium.click_button(_('Next'))
		self.selenium.enter_input("name", computername)
		self.selenium.click_button(_("Create computer"))
		self.selenium.wait_for_text(_('has been created'))
		self.selenium.click_button(_('Cancel'))
		self.selenium.wait_until_all_dialogues_closed()

		return computername


class Groups(UDMBase):
	name = _("Groups")

	def add(self, groupname=None):
		if groupname is None:
			groupname = uts.random_string()

		self.selenium.click_button(_('Add'))
		self.selenium.wait_for_text(_("Members of this group"))
		self.selenium.enter_input("name", groupname)
		self.selenium.click_button(_("Create group"))
		self.wait_for_main_grid_load()

		return groupname


class Policies(UDMBase):
	name = _('Policies')

	def add(self, policyname=None):
		if policyname is None:
			policyname = uts.random_string()

		self.selenium.click_button(_('Add'))
		self.selenium.wait_for_text(_("Container"))
		self.selenium.click_button(_('Next'))
		self.selenium.enter_input("name", policyname)
		self.selenium.click_button(_("Create policy"))
		self.wait_for_main_grid_load()

		return policyname

	def open_details(self, objectname):
		self.search(objectname)
		self.selenium.click_grid_entry(objectname)
		self.selenium.wait_for_text(_('Advanced settings'))


class Users(UDMBase):
	name = _("Users")

	def get_description(self):
		xpath = '//input[@name="description"]'
		elems = webdriver.support.ui.WebDriverWait(xpath, 60).until(
			self.selenium.get_all_enabled_elements
		)
		return elems[0].get_attribute('value')

	def get_primary_mail(self):
		xpath = '//input[@name="mailPrimaryAddress"]'
		elems = webdriver.support.ui.WebDriverWait(xpath, 60).until(
			self.selenium.get_all_enabled_elements
		)
		return elems[0].get_attribute('value')

	def add(
		self,
		template=None,
		firstname='',
		lastname=None,
		username=None,
		password='univention'
	):
		if username is None:
			username = uts.random_string()
		if lastname is None:
			lastname = uts.random_string()

		self.selenium.click_button(_('Add'))

		if template is not None:
			self.selenium.wait_for_text(_("User template"))
			template_selection_dropdown_button = self.selenium.driver.find_element_by_xpath(
				'//input[@name="objectTemplate"]/../..//input[contains(concat(" ", normalize-space(@class), " "), " dijitArrowButtonInner ")]'
			)
			template_selection_dropdown_button.click()
			self.selenium.click_text(template)
			self.selenium.click_button(_("Next"))

		self.selenium.wait_for_text(_("First name"))
		self.selenium.enter_input("firstname", firstname)
		self.selenium.enter_input("lastname", lastname)
		self.selenium.enter_input("username", username)

		self.selenium.click_button(_("Next"))
		self.selenium.wait_for_text(_("Password *"))
		self.selenium.enter_input("password_1", password)
		self.selenium.enter_input("password_2", password)
		self.selenium.click_button(_("Create user"))
		self.selenium.wait_for_text(_('has been created'))
		self.selenium.click_button(_('Cancel'))
		self.selenium.wait_until_all_dialogues_closed()

		return username
