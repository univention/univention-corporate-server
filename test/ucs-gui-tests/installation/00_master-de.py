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


class GermanMasterInstaller(Installer):
	def __init__(self):
		super(GermanMasterInstaller, self).__init__()
		self.vm_config.language = "de"
		self.vm_config.update_ucs_after_install = False

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
