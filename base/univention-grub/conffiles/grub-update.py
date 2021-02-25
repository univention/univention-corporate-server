# -*- coding: utf-8 -*-
#
# Univention Grub
#  baseconfig module for the grub update
#
# Copyright 2007-2021 Univention GmbH
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

import os
import shutil
import hashlib


def is_conf_compatible():
	# This is a workaround to avoid syntax errors
	# during the UCS 4.4 to UCS 5.0 upgrade, it can be removed with UCS 5.1
	conf_file = '/etc/grub.d/05_debian_theme'
	broken_md5 = '1b68d93d4dd2dacf7b62a7d0937baa74'
	if os.path.isfile(conf_file) and os.path.isfile(conf_file + '.dpkg-new'):
		with open(conf_file, 'rb') as conf_file_fd:
			return hashlib.md5(conf_file_fd.read()).hexdigest() == broken_md5
	return True


def postinst(configRegistry, changes):
	light_theme = configRegistry.get('bootsplash/theme') in ['ucs-light', 'ucs-appliance-light']
	backgroundimage_target = '/boot/grub/uniboot.png'
	backgroundimage_source = os.path.join('/usr/share/univention-grub/', 'light-background.png' if light_theme else 'dark-background.png')
	if configRegistry.get('grub/backgroundimage') == backgroundimage_target:
		try:
			os.makedirs(os.path.dirname(backgroundimage_target), mode=0o755)
		except OSError:
			pass
		shutil.copy(backgroundimage_source, backgroundimage_target)
	if is_conf_compatible():
		os.system('update-grub')
