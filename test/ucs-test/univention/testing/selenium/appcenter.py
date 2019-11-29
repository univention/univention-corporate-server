#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Selenium Tests
#
# Copyright 2017-2019 Univention GmbH
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
from time import sleep

from selenium.common.exceptions import TimeoutException, NoSuchElementException
from univention.appcenter.app_cache import Apps
from univention.testing.selenium.utils import expand_path

from univention.admin import localization

translator = localization.translation('ucs-test-framework')
_ = translator.translate


class InfiniteLoop(Exception):
	pass


class AppCenter(object):

	def __init__(self, selenium):
		self.selenium = selenium

	def install_app_with_checks(self, app_id):
		app = Apps().find(app_id)

		# TODO use backend function to get dependencies
		dependencies = set(app.required_apps).union(app.required_apps_in_domain)
		dependencies = [Apps().find(dep) for dep in dependencies]

		apps = [app]
		apps.extend(dependencies)

		# TODO: Make sure the license is activated!
		self.open_app(app_id)

		self.selenium.click_button(_('Install'))

		# AppPreInstallWizard
		self.selenium.wait_for_text(_('Installation of %s') % (app.name,))

		# TODO check if the ChooseHost page should be shown and then test against that instead of
		# try: except:
		try:
			self.selenium.wait_for_text(_('Host for installation of application'), timeout=2)
		except TimeoutException:
			pass
		else:
			self.selenium.click_button(_('Next'))

		if len(dependencies):
			if len(dependencies) == 1:
				self.selenium.wait_for_text(_('The following app is required to install %s') % (app.name,))
			else:
				self.selenium.wait_for_text(_('The following apps are required to install %s') % (app.name,))
			for _app in dependencies:
				self.selenium.wait_until_element_visible(expand_path('//div[@containsClass="appIconAndNameGrid"]//*[text() = "%s"]' % (_app.name)))
			self.selenium.click_button(_('Next'))

		# TODO check if docker warning should be shown
		try:
			self.selenium.wait_for_text(_('Do not show this message again'), timeout=2)
		except TimeoutException:
			pass
		else:
			self.selenium.click_button(_('Next'))

		# TODO since we wait for ChooseHost page and docker warning page the ChecksPage might already be over
		# if we check for ChooseHost page and docker warning explicitly we can remove the try block here
		try:
			self.selenium.wait_for_text(_('Performing pre-install checks'))
			self.selenium.wait_until_standby_animation_appears_and_disappears()
		except TimeoutException:
			pass

		# AppInstallWizard
		for _app in apps:
			if _app.license_agreement:
				self.selenium.wait_for_text(_('License agreement'))
				self.selenium.click_button(_('Accept license'))

			if _app.readme_install:
				self.selenium.wait_for_text(_('Install Information'))
				self.selenium.click_button(_('Next'))

			try:
				self.selenium.wait_until_element_visible(expand_path('//*[@containsClass="details_%s"]' % _app.id), timeout=2)
			except TimeoutException:
				pass
			else:
				self.selenium.click_button(_('Next'))

			# if len(_app.get_settings()): return settings that are not shown in the AppSettings form
				#  self.selenium.wait_until_element_visible(expand_path('//*[@containsClass="appSettings_%s"]' % _app.id))
				#  self.selenium.click_button(_('Next'))
			try:
				self.selenium.wait_until_element_visible(expand_path('//*[@containsClass="appSettings_%s"]' % _app.id), timeout=2)
			except TimeoutException:
				pass
			else:
				self.selenium.click_button(_('Next'))

		self.selenium.wait_for_text(_('Please confirm to install'))
		if len(dependencies):
			for _app in dependencies:
				self.selenium.wait_until_element_visible(expand_path('//div[@containsClass="appIconAndNameGrid"]//*[text() = "%s"]' % (_app.name)))
		if len(dependencies):
			self.selenium.click_button(_('Install apps'))
		else:
			self.selenium.click_button(_('Install app'))

		# TODO wait for installation (progressbar)

		# AppPostInstallWizard
		for _app in apps:
			if _app.readme_post_install:
				self.selenium.wait_for_text(_('Install information'))
				try:
					self.selenium.click_button(_('Next'), timeout=2)
				except TimeoutException:
					self.selenium.click_button(_('Finish'))

	def install_app(self, app_id):
		# TODO: Make sure the license is activated!
		self.open_app(app_id)

		self.selenium.click_button(_('Install'))

		# AppPreInstallWizard
		self.selenium.wait_for_text(_('Installation of'))

		try:
			self.selenium.wait_for_text(_('Host for installation of application'), timeout=2)
		except TimeoutException:
			pass
		else:
			self.selenium.click_button(_('Next'))

		try:
			self.selenium.wait_for_any_text_in_list([
				_('The following app is required to install'),
				_('The following apps are required to install')
			])
		except TimeoutException:
			print('App has no dependencies. Ignoring dependencies page')
			pass
		else:
			self.selenium.click_button(_('Next'))

		try:
			self.selenium.wait_for_text(_('Do not show this message again'), timeout=2)  # Docker warning
		except TimeoutException:
			print('App and possible dependencies do not use docker. Ignoring docker warning page')
			pass
		else:
			self.selenium.click_button(_('Next'))

		try:
			self.selenium.wait_for_text(_('Performing pre-install checks'))
			self.selenium.wait_until_standby_animation_appears_and_disappears()
		except TimeoutException:
			pass

		# AppInstallWizard
		def click_through_install_wizard_pages():
			try:
				self.selenium.wait_for_text(_('Please confirm to install'), timeout=2)
			except TimeoutException:
				print('Not on the last page of the AppInstallWizard yet. Going to skip pages')
				found_page = False
				try:
					self.selenium.wait_for_text(_('License agreement'), timeout=2)
				except TimeoutException:
					print('No License agreement page found. Ignoring')
					pass
				else:
					found_page = True
					self.selenium.click_button(_('Accept license'))

				try:
					self.selenium.wait_for_text(_('Install Information'), timeout=2)
				except TimeoutException:
					print('No Install information page found. Ignoring')
					pass
				else:
					found_page = True
					self.selenium.click_button(_('Next'))

				try:
					self.selenium.wait_until_any_element_visible('//*[contains(@class, "details_")]', timeout=2)
				except TimeoutException:
					print('No details page found. Ignoring')
					pass
				else:
					found_page = True
					self.selenium.click_button(_('Next'))

				try:
					self.selenium.wait_until_any_element_visible('//*[contains(@class, "appSettings_")]', timeout=2)
				except TimeoutException:
					print('No App settings page found. Ignoring')
					pass
				else:
					found_page = True
					self.selenium.click_button(_('Next'))
				if not found_page:
					raise InfiniteLoop('Cant find an AppInstallWizard page')
				else:
					click_through_install_wizard_pages()
			else:
				try:
					self.selenium.click_button(_('Install apps'), timeout=2)
				except TimeoutException:
					self.selenium.click_button(_('Install app'), timeout=2)
		click_through_install_wizard_pages()

		# TODO wait for installation (progressbar)

		# AppPostInstallWizard
		def click_through_post_install_wizard_pages():
			try:
				self.selenium.wait_for_text(_('Install information'), timeout=2)
			except TimeoutException:
				print('No readme postinstall page found. Post install wizard has finished')
				pass
			else:
				try:
					self.selenium.click_button(_('Next'), timeout=2)
				except TimeoutException:
					self.selenium.click_button(_('Finish'))
				click_through_post_install_wizard_pages()
		click_through_post_install_wizard_pages()

		self.selenium.wait_for_any_text_in_list([_('Uninstall'), _('Manage domain wide installations')], timeout=900)

	def uninstall_app(self, app):
		self.open_app(app)

		try:
			self.selenium.driver.find_element_by_xpath('//*[text() = "Manage domain wide installations"]')
		except NoSuchElementException:
			pass
		else:
			self.selenium.click_text(_('(this computer)'))
		self.selenium.click_button(_('Uninstall'))

		self.selenium.wait_for_text(_('Please confirm to uninstall the application'))
		self.selenium.wait_until_all_standby_animations_disappeared()
		sleep(2)  # there is still something in the way even with wait_until_all_standby_animations_disappeared
		self.selenium.click_button(_('Uninstall'))

		self.selenium.wait_for_text(_('Running tests'))
		self.selenium.wait_until_element_visible('//*[contains(concat(" ", normalize-space(@class), " "), " dijitButtonText ")][text() = "Install"]', timeout=900)
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

	def click_app_tile(self, appid):
		self.selenium.click_element('//div[contains(concat(" ", normalize-space(@class), " "), " umcGalleryWrapperItem ")][@moduleid="%s"]' % appid)

	def open(self, do_reload=True):
		# TODO: check if appcenter is already opened with the overview site
		self.selenium.open_module(_('App Center'), do_reload=do_reload, wait_for_standby=False)
		self.close_info_dialog_if_visisble()
		self.selenium.wait_until_standby_animation_appears_and_disappears()

	def open_app(self, app):
		# TODO: check if appcenter is already opened with the app page
		self.open()
		self.click_app_tile(app)
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
	a.install_app('dudle')
	a.uninstall_app('dudle')
