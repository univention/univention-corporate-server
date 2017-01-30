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
#

import argparse

from vncautomate import init_logger, VNCConnection
from vncautomate.cli import add_config_options_to_parser, get_config_from_args


class Installer(object):
	def __init__(self, vm_config):
		init_logger('info')
		self.args = self.parse_args()
		self.ocr_config = self.get_ocr_config()
		self.vm_config = vm_config
		# TODO: Ask Alex if self.host could be removed. It is needed only
		# here and once again, when the vnc-connection is refreshed. Maybe
		# the refreshing could be done differently...
		self.host = self.get_host()
		# Note: The second part of this initialisation is in __enter__().
		self.vnc_connection = VNCConnection(self.host)

	def __enter__(self):
		self.client = self.vnc_connection.__enter__()
		self.client.updateOCRConfig(self.ocr_config)
		return self

	def __exit__(self, etype, exc, etraceback):
		self.vnc_connection.__exit__(etype, exc, etraceback)

	def parse_args(self):
		parser = argparse.ArgumentParser(description='VNC example test')
		parser.add_argument('host', metavar='vnc_host', help='Host with VNC port to connect to')
		add_config_options_to_parser(parser)
		args = parser.parse_args()
		return args

	def get_ocr_config(self):
		config = get_config_from_args(self.args)
		return config

	def set_ocr_lang(self, language):
		self.ocr_config.update(lang=language)
		self.client.updateOCRConfig(self.ocr_config)

	def get_host(self):
		return self.args.host

	def skip_boot_device_selection(self):
		self.client.waitForText('start with default settings')
		self.client.keyPress('enter')
