#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Python VNC automate
#
# Copyright 2016 Univention GmbH
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

from vminstall.installer import Installer
import time
import vminstall.languages.english as english
import vminstall.languages.french as french
import vminstall.languages.german as german
import vminstall.utils as utils


class GermanMasterInstaller(Installer):
	def __init__(self):
		super(GermanMasterInstaller, self).__init__()
		self.vm_config.language = "de"
		self.vm_config.update_ucs_after_install = False

	def __set_language(self, language):
		self.locale_strings = self.__get_strings(language)
		self.__set_ocr_language(language)

	def __get_strings(self, language):
		if language == 'en':
			return english.strings
		elif language == 'de':
			return german.strings
		elif language == 'fr':
			return french.strings

	def __set_ocr_language(self, language):
		language_iso_639_2 = utils.iso_639_1_to_iso_639_2(language)
		self.ocr_config.update(lang=language_iso_639_2)
		self.client.updateOCRConfig(self.ocr_config)

	def skip_boot_device_selection(self):
		self.__set_language('en')
		self.client.waitForText('start with default settings')
		self.client.saveScreenshot('installer-isolinux.png')
		self.client.keyPress('enter')

	def select_language(self):
		self.__set_language('en')
		language_english_name = utils.iso_639_1_to_english_name(self.vm_config.language)

		self.client.waitForText('select a language', timeout=30)
		self.client.saveScreenshot('installer-language.png')
		self.client.mouseClickOnText('English')
		self.client.enterText(language_english_name)
		self.client.keyPress('enter')

		self.__set_language(self.vm_config.language)

	def set_country_and_keyboard_layout(self):
		self.client.waitForText(self.locale_strings['location_selection'], timeout=30)
		self.client.saveScreenshot('installer-location_de.png')
		self.client.keyPress('enter')

		# Always using US keyboard layout here, because it's the only one
		# vncdotool fully supports.
		self.client.waitForText(self.locale_strings['configure_keyboard'], timeout=30)
		self.client.saveScreenshot('installer-keyboardselection_de.png')
		self.client.mouseClickOnText(self.locale_strings['default_keyboard_layout_of_current_language'])
		self.client.enterText(self.locale_strings['us_keyboard_layout'])
		self.client.keyPress('enter')

	def network_setup(self):
		self.client.waitForText(self.locale_strings['dhcp_configuration'], timeout=120)
		self.client.saveScreenshot('installer-netcfg-dhcp_de.png')
		self.client.mouseClickOnText(self.locale_strings['cancel'])

		self.client.waitForText(self.locale_strings['not_using_dhcp'], timeout=30)
		self.client.keyPress('enter')

		self.client.waitForText(self.locale_strings['manual_network_config'], timeout=30)
		self.client.mouseClickOnText(self.locale_strings['manual_network_config'])
		self.client.saveScreenshot('installer-netcfg-static_de.png')
		self.client.keyPress('enter')
		self.client.waitForText(self.locale_strings['ip_address'], timeout=30)
		self.client.enterText(self.vm_config.ip)
		self.client.saveScreenshot('installer-netcfg-ip_de.png')
		self.client.keyPress('enter')

		self.client.waitForText(self.locale_strings['netmask'], timeout=30)
		self.client.keyPress('enter')

		self.client.waitForText(self.locale_strings['gateway'], timeout=30)
		self.client.keyPress('enter')

		self.client.waitForText(self.locale_strings['name_server'], timeout=30)
		self.client.enterText(self.vm_config.dns_server_ip)
		self.client.keyPress('enter')

	def account_setup(self):
		self.client.waitForText(self.locale_strings['user_and_password'], timeout=30)
		self.client.enterText(self.vm_config.password)
		self.client.keyPress('tab')
		self.client.enterText(self.vm_config.password)
		self.client.saveScreenshot('installer-password_de.png')
		self.client.keyPress('enter')

	# Only some countries (e.g. USA) have a time zone selection dialog here.
	def set_time_zone(self):
		self.client.waitForText(self.locale_strings['time_zone'], timeout=60)
		self.client.keyPress('enter')

	def hdd_setup(self, hdd_empty=True):
		self.client.waitForText(self.locale_strings['partitioning_method'], timeout=60)
		self.client.saveScreenshot('installer-partman-selectguided_de.png')
		self.client.keyPress('enter')
		self.client.waitForText(self.locale_strings['partitioning_device'], timeout=30)
		self.client.keyPress('enter')
		self.client.waitForText(self.locale_strings['partitioning_structure'], timeout=30)
		if self.vm_config.use_multiple_partitions:
			self.client.mouseClickOnText(self.locale_strings['multiple_partitions'])
		self.client.keyPress('enter')

		# This dialog only appears when the HDD is not empty.
		if not hdd_empty:
			self.client.waitForText(self.locale_strings['partitioning_warning1'], timeout=30)
			self.client.keyPress('down')
			self.client.keyPress('enter')

		self.client.waitForText(self.locale_strings['partitioning_warning2'], timeout=30)
		self.client.keyPress('down')
		# The installer needs some time to react here.
		time.sleep(2)
		self.client.saveScreenshot('installer-partman-writelvm_de.png')
		self.client.keyPress('enter')

		self.client.waitForText(self.locale_strings['partitioning_commit'], timeout=30)
		self.client.keyPress('enter')

		self.client.waitForText(self.locale_strings['partitioning_warning3'], timeout=30)
		self.client.keyPress('down')
		self.client.keyPress('enter')
		self.client.waitForText(self.locale_strings['domain_setup'], timeout=1200, prevent_screen_saver=True)

	def setup_ucs_master(self):
		self.client.mouseClickOnText(self.locale_strings['setup_master'])
		self.client.saveScreenshot('installer-domainrole_de.png')
		self.client.mouseClickOnText(self.locale_strings['next'])

		self.client.waitForText(self.locale_strings['account_info'], timeout=30)
		self.client.enterText(self.locale_strings['company'])
		self.client.mouseClickOnText(self.locale_strings['next'])

		self.client.waitForText(self.locale_strings['host_settings'], timeout=30)
		self.client.saveScreenshot('installer-hostname_de.png')
		self.client.mouseClickOnText(self.locale_strings['ldap_base'])
		self.client.enterText(self.vm_config.ldap_base)
		self.client.mouseClickOnText(self.locale_strings['next'])

		self.client.waitForText(self.locale_strings['software_config'], timeout=30)
		self.client.saveScreenshot('installer-softwareselection_de.png')
		self.client.mouseClickOnText(self.locale_strings['next'])
		self.client.waitForText(self.locale_strings['confirm_config'], timeout=30)
		self.client.saveScreenshot('installer-overview_de.png')

	def install(self):
		self.skip_boot_device_selection()
		self.select_language()
		self.set_country_and_keyboard_layout()
		self.network_setup()
		self.account_setup()
		self.hdd_setup()
		self.setup_ucs_master()


def main():
	with GermanMasterInstaller() as installer:
		installer.install()

if __name__ == '__main__':
	main()
