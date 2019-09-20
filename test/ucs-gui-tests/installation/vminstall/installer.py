#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Python VNC automate
#
# Copyright 2016 Univention GmbH
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

import argparse
import time

from vncautomate import init_logger, VNCConnection
from vncautomate.cli import add_config_options_to_parser, get_config_from_args

import os
import vminstall.utils as utils
import vminstall.languages.german as german
import vminstall.languages.english as english
import vminstall.languages.french as french
from vminstall.vmconfig import Config as VmConfig


class Installer(object):

	def __init__(self, args=None, role='master', language='en'):
		init_logger('info')
		self.args = self.parse_args(args)
		self.ocr_config = self.__get_ocr_config()
		self.vm_config = VmConfig(
			ip=self.args.ip,
			role=role,
			language=language
		)

		host = self.__get_host()
		self.vnc_connection = VNCConnection(host)
		# Note: The second part of this initialisation is in __enter__().

	def __enter__(self):
		self.client = self.vnc_connection.__enter__()
		self.__set_language(self.vm_config.language)
		return self

	def __exit__(self, etype, exc, etraceback):
		self.vnc_connection.__exit__(etype, exc, etraceback)

	def parse_args(self, args=None):
		parser = argparse.ArgumentParser(description='VNC example test')
		parser.add_argument('host', metavar='vnc_host', help='Host with VNC port to connect to')
		parser.add_argument('--ip', dest='ip', required=True, help='The IP to assign to this virtual machine')
		add_config_options_to_parser(parser)
		args = parser.parse_args(args)
		return args

	def __get_ocr_config(self):
		config = get_config_from_args(self.args)
		return config

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

	def __get_host(self):
		return self.args.host

	def skip_boot_device_selection(self):
		self.__set_language('en')
		self.client.waitForText('start with default settings')
		self.client.keyPress('enter')

	def select_language(self):
		self.__set_language('en')
		language_english_name = utils.iso_639_1_to_english_name(self.vm_config.language)

		self.client.waitForText('select a language', timeout=30)
		self.client.mouseClickOnText('English')
		self.client.enterText(language_english_name)
		self.client.keyPress('enter')

		self.__set_language(self.vm_config.language)

	def set_country_and_keyboard_layout(self):
		self.client.waitForText(self.locale_strings['location_selection'], timeout=30)
		self.client.keyPress('enter')

		# Always using US keyboard layout here, because it's the only one
		# vncdotool fully supports.
		self.client.waitForText(self.locale_strings['configure_keyboard'], timeout=30)
		self.client.mouseClickOnText(self.locale_strings['default_keyboard_layout_of_current_language'])
		self.client.enterText(self.locale_strings['us_keyboard_layout'])
		self.client.keyPress('enter')

	def network_setup(self, has_multiple_network_devices=False):
		if has_multiple_network_devices:
			self.client.waitForText(self.locale_strings['multiple_network_devices'], timeout=120)
			self.client.keyPress('enter')

		self.client.waitForText(self.locale_strings['dhcp_configuration'], timeout=120)
		self.client.mouseClickOnText(self.locale_strings['cancel'])

		self.client.waitForText(self.locale_strings['not_using_dhcp'], timeout=30)
		self.client.keyPress('enter')

		self.client.waitForText(self.locale_strings['manual_network_config'], timeout=30)
		self.client.mouseClickOnText(self.locale_strings['manual_network_config'])
		self.client.keyPress('enter')
		self.client.waitForText(self.locale_strings['ip_address'], timeout=30)
		self.client.enterText(self.vm_config.ip)
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
		self.client.keyPress('enter')

	# Only some countries (e.g. USA) have a time zone selection dialog here.
	def set_time_zone(self):
		self.client.waitForText(self.locale_strings['time_zone'], timeout=60)
		self.client.keyPress('enter')

	def hdd_setup(self, hdd_empty=True):
		self.client.waitForText(self.locale_strings['partitioning_method'], timeout=60)
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
		self.client.keyPress('enter')

		self.client.waitForText(self.locale_strings['partitioning_commit'], timeout=30)
		self.client.keyPress('enter')

		self.client.waitForText(self.locale_strings['partitioning_warning3'], timeout=30)
		self.client.keyPress('down')
		self.client.keyPress('enter')
		self.client.waitForText(self.locale_strings['domain_setup'], timeout=1200, prevent_screen_saver=True)

	def setup_ucs(self, expect_login_screen=False):
		self.choose_system_role()
		self.set_domain_settings()
		self.select_software_components()
		self.confirm_config(expect_login_screen)

	def choose_system_role(self):
		if self.vm_config.role == "master":
			self.client.mouseClickOnText(self.locale_strings['setup_master'])
			self.client.mouseClickOnText(self.locale_strings['next'])
			self.client.waitForText(self.locale_strings['account_info'], timeout=30)
		elif self.vm_config.role == "backup" or self.vm_config.role == "slave" or self.vm_config.role == "member":
			self.client.mouseClickOnText(self.locale_strings['join_ucs'])
			self.client.mouseClickOnText(self.locale_strings['next'])
			self.client.waitForText(self.locale_strings['system_role'], timeout=30)
		elif self.vm_config.role == "basesystem":
			self.client.mouseClickOnText(self.locale_strings['no_domain'])
			self.client.mouseClickOnText(self.locale_strings['next'])
			self.client.waitForText(self.locale_strings['no_domain_warn'], timeout=30)

		if self.vm_config.role == "backup":
			self.client.mouseClickOnText(self.locale_strings['next'])
		if self.vm_config.role == "slave":
			self.client.keyPress('down')
			self.client.mouseClickOnText(self.locale_strings['next'])
		if self.vm_config.role == "member":
			self.client.keyPress('down')
			self.client.keyPress('down')
			self.client.mouseClickOnText(self.locale_strings['next'])

	def set_domain_settings(self):
		if self.vm_config.role == "master":
			self.client.enterText(self.locale_strings['company'])
			self.client.mouseClickOnText(self.locale_strings['next'])
			self.client.waitForText(self.locale_strings['host_settings'], timeout=30)

			self.client.mouseClickOnText(self.locale_strings['ldap_base'])
			self.client.enterText(self.vm_config.ldap_base)
			self.client.mouseClickOnText(self.locale_strings['next'])
			self.client.waitForText(self.locale_strings['software_config'], timeout=30)

		elif self.vm_config.role == "backup" or self.vm_config.role == "slave" or self.vm_config.role == "member":
			self.client.waitForText(self.locale_strings['domain_join'], timeout=30)
			self.client.mouseClickOnText(self.locale_strings['password_field'])
			self.client.enterText(self.vm_config.password)
			self.client.mouseClickOnText(self.locale_strings['next'])
			self.client.waitForText(self.locale_strings['host_settings'], timeout=30)
			self.client.mouseClickOnText(self.locale_strings['next'])
			self.client.waitForText(self.locale_strings['software_config'], timeout=30)

		elif self.vm_config.role == "basesystem":
			self.client.mouseClickOnText(self.locale_strings['next'])

			self.client.waitForText(self.locale_strings['host_settings'], timeout=30)
			self.client.mouseClickOnText(self.locale_strings['next'])

			self.client.waitForText(self.locale_strings['confirm_config'], timeout=30)

	def select_software_components(self):
		if self.vm_config.role != "basesystem":
			if self.vm_config.install_all_additional_components:
				self.client.mouseMove(320, 215)
				self.client.mousePress(1)
			self.client.mouseClickOnText(self.locale_strings['next'])
			self.client.waitForText(self.locale_strings['confirm_config'], timeout=30)

	def confirm_config(self, expect_login_screen):
		if not self.vm_config.update_ucs_after_install:
			# The tab is needed to take away the focus from the text, because
			# when focused the text is surrounded by a frame, which irritates
			# tesseract-ocr, sometimes.
			self.client.keyPress('tab')
			# Pressing page down is needed, because the checkbox is off screen
			# when the software components list is long.
			time.sleep(3)
			self.client.keyPress('pgdn')
			self.client.mouseClickOnText(self.locale_strings['do_update'])
		self.client.keyPress('enter')

		# The setup will probably take at least 20min, so this sleep reduces the
		# load while waiting. This sleep is also needed to add to the timeout
		# of the following waitForText(), where the maximum timeout is 3600s,
		# due to limitations of vncdotool.
		time.sleep(20 * 60)
		self.client.waitForText(self.locale_strings['setup_successful'], timeout=3550, prevent_screen_saver=True)
		self.client.mouseClickOnText(self.locale_strings['finish'])

		if self.vm_config.role == "basesystem":
			self.client.waitForText('login:', timeout=360)
		elif expect_login_screen:
			this_dir, _ = os.path.split(__file__)
			self.client.findSubimage(os.path.join(this_dir, 'expected_welcome_screen_with_kde.png'), timeout=360)
		else:
			self.client.waitForText(self.locale_strings['welcome'], timeout=360)
