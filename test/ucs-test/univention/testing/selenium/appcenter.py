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
from time import sleep

from selenium.common.exceptions import TimeoutException

from univention.admin import localization

translator = localization.translation('ucs-test-framework')
_ = translator.translate


class AppCenter(object):

	def __init__(self, selenium):
		self.selenium = selenium

	def install_app(self, app):
		# TODO: Make sure the license is activated!
		self.open_app(app)

		self.selenium.click_button(_('Install'))

		try:
			self.selenium.wait_for_text(_('In order to proceed with the installation'), timeout=15)
			self.selenium.click_button(_('Next'))
		except TimeoutException:
			pass

		self.close_info_dialog_if_visisble()

		self.selenium.wait_for_text(_('Please confirm to install the application'))
		self.self.wait_until_progress_bar_finishes()
		self.selenium.click_button(_('Install'))

		self.selenium.wait_for_text(_('Installing %s') % (app,))
		self.self.wait_until_progress_bar_finishes()

		self.selenium.wait_for_text(_('Installed'), timeout=900)
		self.selenium.wait_until_all_standby_animations_disappeared()

	def uninstall_app(self, app):
		self.open_app(app)

		self.selenium.click_text(_('(this computer)'))
		self.selenium.click_button(_('Uninstall'))

		self.selenium.wait_for_text(_('Please confirm to uninstall the application'))
		self.selenium.click_button(_('Uninstall'))

		self.selenium.wait_for_text(_('Running tests'))
		self.selenium.wait_for_text(_('More information'), timeout=900)
		self.selenium.wait_until_all_standby_animations_disappeared()

	def upgrade_app(self, app):
		self.open_app(app)

		self.selenium.click_text(_('(this computer)'))
		self.selenium.click_button(_('Upgrade'))

		try:
			self.selenium.wait_for_text(_('Upgrade Information'), timeout=5)
		except TimeoutException:
			pass
		else:
			self.selenium.click_element('//div[contains(concat(" ", normalize-space(@class), " "), " umcConfirmDialog ")]//*[contains(concat(" ", normalize-space(@class), " "), " dijitButtonText ")][text() = "%s"]' % (_('Upgrade'),))

		self.selenium.wait_until_progress_bar_finishes()
		self.selenium.wait_for_text(_('Upgrade of %s') % (app,))
		self.selenium.click_button(_('Upgrade'))
		self.selenium.wait_until_progress_bar_finishes(timeout=900)
		self.selenium.wait_for_text(_('More information'), timeout=900)

	def search_for_apps(self, text, category=None):
		self.open()

		category = category or _('All')
		self.select_search_category(category)

		search_field = self.selenium.driver.find_element_by_xpath(
			'//*[contains(text(), "%s")]/../input' % ('Search applications...',)
		)
		search_field.send_keys(text)
		sleep(2)

		return self.selenium.get_gallery_items()

	def select_search_category(self, category):
		self.selenium.show_notifications(False)
		self.selenium.click_element(
			'//div[contains(concat(" ", normalize-space(@class), " "), " dropDownMenu ")]//input[contains(concat(" ", normalize-space(@class), " "), " dijitArrowButtonInner ")]'
		)
		self.selenium.click_element(
			'//*[contains(concat(" ", normalize-space(@class), " "), " dijitMenuItem ")][@role="option"]//*[contains(text(), "%s")]'
			% (category,)
		)
		sleep(2)

	def open(self):
		# TODO: check if appcenter is already opened with the overview site
		self.selenium.search_module(_('App Center'))
		self.selenium.click_tile(_('App Center'))
		self.close_info_dialog_if_visisble()
		self.selenium.wait_until_all_standby_animations_disappeared()

	def open_app(self, app):
		# TODO: check if appcenter is already opened with the app page
		self.open()
		self.selenium.click_text(app)
		self.selenium.wait_for_text(_('More information'))
		self.selenium.wait_until_all_standby_animations_disappeared()

	def close_info_dialog_if_visisble(self):
		try:
			self.selenium.wait_for_text(_('Do not show this message again'), timeout=5)
			self.selenium.click_button(_('Continue'))
		except TimeoutException:
			pass
		self.selenium.wait_until_all_standby_animations_disappeared()


if __name__ == '__main__':
	import univention.testing.selenium
	s = univention.testing.selenium.UMCSeleniumTest()
	s.__enter__()
	s.do_login()
	a = AppCenter(s)
	a.install_app('Dudle')
	a.uninstall_app('Dudle')
