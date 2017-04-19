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

import argparse

from vncautomate import init_logger, VNCConnection
from vncautomate.cli import add_config_options_to_parser, get_config_from_args

import vminstall.utils as utils
import vminstall.languages.german as german
import vminstall.languages.english as english
from vminstall.vmconfig import Config as VmConfig


class Installer(object):
	def __init__(self):
		init_logger('info')
		self.args = self.__parse_args()
		self.ocr_config = self.__get_ocr_config()
		self.vm_config = VmConfig(
			ip=self.args.ip,
			language="en",
		)

		host = self.__get_host()
		self.vnc_connection = VNCConnection(host)
		# Note: The second part of this initialisation is in __enter__().

	def __enter__(self):
		self.client = self.vnc_connection.__enter__()
		self.__set_language('en')
		return self

	def __exit__(self, etype, exc, etraceback):
		self.vnc_connection.__exit__(etype, exc, etraceback)

	def __parse_args(self):
		parser = argparse.ArgumentParser(description='VNC example test')
		parser.add_argument('host', metavar='vnc_host', help='Host with VNC port to connect to')
		parser.add_argument('--ip', dest='ip', required=True, help='The IP to assign to this virtual machine')
		add_config_options_to_parser(parser)
		args = parser.parse_args()
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

	def __set_ocr_language(self, language):
		language_iso_639_2 = utils.iso_639_1_to_iso_639_2(language)
		self.ocr_config.update(lang=language_iso_639_2)
		self.client.updateOCRConfig(self.ocr_config)

	def __get_host(self):
		return self.args.host

	def skip_boot_device_selection(self):
		self.client.waitForText('start with default settings')
		self.client.keyPress('enter')

	def select_language(self):
		language_english_name = utils.iso_639_1_to_english_name(self.vm_config.language)

		self.client.waitForText('select a language', timeout=30)
		self.client.mouseClickOnText('English')
		self.client.enterText(language_english_name)
		self.client.keyPress('enter')

		self.__set_language(self.vm_config.language)

	def set_country_and_keyboard_layout(self):
		self.client.waitForText(self.locale_strings['location_selection'], timeout=30)
		self.client.keyPress('enter')

		self.client.waitForText(self.locale_strings['configure_keyboard'], timeout=30)
		self.client.keyPress('enter')

	def network_setup(self):
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
		self.client.keyPress('enter')

	def account_setup(self):
		self.client.waitForText(self.locale_strings['user_and_password'], timeout=30)
		self.client.enterText(self.locale_strings['password'])
		self.client.keyPress('tab')
		self.client.enterText(self.locale_strings['password'])
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

	def setup_ucs_master(self):
		self.client.waitForText(self.locale_strings['domain_setup'], timeout=1200, prevent_screen_saver=True)
		self.client.mouseClickOnText(self.locale_strings['setup_master'])
		self.client.mouseClickOnText(self.locale_strings['next'])

		self.client.waitForText(self.locale_strings['account_info'], timeout=30)
		self.client.enterText(self.locale_strings['company'])
		self.client.mouseClickOnText(self.locale_strings['next'])

		self.client.waitForText(self.locale_strings['host_settings'], timeout=30)
		self.client.mouseClickOnText(self.locale_strings['next'])

		self.client.waitForText(self.locale_strings['software_config'], timeout=30)
		self.client.mouseClickOnText(self.locale_strings['next'])
		self.client.waitForText(self.locale_strings['confirm_config'], timeout=30)
		if not self.vm_config.update_ucs_after_install:
			self.client.mouseClickOnText(self.locale_strings['do_update'])
		self.client.keyPress('enter')

		self.client.waitForText(self.locale_strings['setup_successful'], timeout=2400, prevent_screen_saver=True)    # FIXME: Screen saver still active!?
		self.client.mouseClickOnText(self.locale_strings['finish'])

		self.client.waitForText(self.locale_strings['welcome'], timeout=360)
