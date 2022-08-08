# -*- coding: utf-8 -*-
#
# Univention Grub
#  baseconfig module for the grub update
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2007-2022 Univention GmbH
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
	os.system('update-grub')
