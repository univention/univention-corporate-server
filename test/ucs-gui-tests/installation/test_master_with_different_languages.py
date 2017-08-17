#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Python VNC automate
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

import os
import subprocess

from vminstall.installer import Installer
from vminstall.virtual_machine import VirtualMachine


def test_master_with_different_languages(language, server, ip_address, iso_image):
	# TODO: move to some more general point
	if not os.path.exists('screen_dumps'):
		os.makedirs('screen_dumps')

	# TODO: the name parameter should be automatically generated
	with VirtualMachine(name='installer_test_master_multi-language_%s' % (language,), server=server, iso_image=iso_image) as vm, Installer(args=['--ip', ip_address, '--dump-dir', 'screen_dumps', vm.vnc_host], language=language) as installer:
		installer.vm_config.update_ucs_after_install = False
		installer.skip_boot_device_selection()
		installer.select_language()
		installer.set_country_and_keyboard_layout()
		installer.network_setup()
		installer.account_setup()
		installer.hdd_setup()
		installer.setup_ucs_master()

	# TODO: move to some more general point
	subprocess.call(['tar', '--remove-files', '-zcf', 'screen_dumps.tar.gz', 'screen_dumps'])
