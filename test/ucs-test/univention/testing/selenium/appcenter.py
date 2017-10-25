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

from selenium.common.exceptions import TimeoutException

from univention.admin import localization

translator = localization.translation('ucs-test-framework')
_ = translator.translate


class AppCenter(object):

	def __init__(self, selenium):
		self.selenium = selenium

	def install_app(self, app):
		# TODO: Make sure the license is activated!

		self.selenium.open_module(_('App Center'))
		self.close_info_dialog_if_visisble()
		self.selenium.wait_until_all_standby_animations_disappeared()

		self.selenium.click_text(app)
		self.selenium.wait_for_text(_('More information'))
		self.selenium.wait_until_all_standby_animations_disappeared()

		self.selenium.click_button(_('Install'))

		try:
			self.selenium.wait_for_text(_('In order to proceed with the installation'), timeout=15)
			self.selenium.click_button(_('Next'))
		except TimeoutException:
			pass

		self.close_info_dialog_if_visisble()

		self.selenium.wait_for_text(_('Please confirm to install the application'))
		# TODO: Maybe implement a wait_until_all_loading_animations_disappeared
		# method and use it here.
		self.selenium.click_button(_('Install'))

		self.selenium.wait_for_text(_('Installed'), timeout=900)
		# TODO: Maybe implement a wait_until_all_loading_animations_disappeared
		# method and use it here.
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
