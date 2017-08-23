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
import sys
import subprocess

from vminstall.installer import Installer
from vminstall.virtual_machine import VirtualMachine


def configure_it(installer):
	installer.vm_config.update_ucs_after_install = False
	installer.skip_boot_device_selection()
	installer.select_language()
	installer.set_country_and_keyboard_layout()
	installer.network_setup()
	installer.account_setup()
	installer.hdd_setup()


def test_installing_all_roles(language, server, ip_address, iso_image):
	# TODO: move to some more general point
	if not os.path.exists('screen_dumps'):
		os.makedirs('screen_dumps')

	# TODO: the name parameter should be automatically generated
	with VirtualMachine(name='installer_test_multi_roles-master-%s' % (language,), server=server, iso_image=iso_image) as vm, Installer(args=['--ip', ip_address, '--dump-dir', 'screen_dumps', vm.vnc_host], role='master', language=language) as installer:
		configure_it(installer)
		installer.setup_ucs()

		contexts = []
		i = 20

		def configure(role):
			global i
			if not os.path.exists('screen_dumps/%s' % (role,)):
				os.makedirs('screen_dumps/%s' % (role,))

			role_ip_address = '%s.%s' % (ip_address.rsplit('.', 1)[0], int(ip_address.rsplit('.', 1)[1]) + i)
			i += 1

			role_vm = VirtualMachine(name='installer_test_multi_roles-%s-%s' % (role, language,), server=server, iso_image=iso_image)
			contexts.append(role_vm)
			role_vm.__enter__()
			role_installer = Installer(args=['--ip', role_ip_address, '--dump-dir', 'screen_dumps/%s' % (role,), '--dns-server', ip_address, role_vm.vnc_host], role=role, language=language)
			contexts.append(role_installer)
			role_installer.__enter__()

			configure_it(role_installer)
			role_installer.setup_ucs()

		try:
			for role in ('slave', 'backup', 'member'):
				configure(role)
		finally:
			exc_info = sys.exc_info()
			for context in contexts:
				try:
					contexts.__exit__(*exc_info)
				except:
					pass

	# TODO: move to some more general point
	subprocess.call(['tar', '--remove-files', '-zcf', 'screen_dumps.tar.gz', 'screen_dumps'])
