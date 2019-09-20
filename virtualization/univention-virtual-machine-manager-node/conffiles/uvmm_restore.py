#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# UCS Virtual Machine Manager Node Common
#  script to link restore documentation in backup directory
#
# Copyright 2010-2019 Univention GmbH
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
import errno

README = '/usr/share/doc/univention-virtual-machine-manager-node-common/README.restore'


def handler(ucr, changes):
	try:
		old, new = changes['uvmm/backup/directory']
	except:
		old = None
		new = changes['uvmm/backup/directory']
	if old and os.path.isdir(old):
		old_symlink = os.path.join(old, 'README.restore')
		if os.path.exists(old_symlink):
			os.unlink(old_symlink)
	new_symlink = os.path.join(new, 'README.restore')
	if new and os.path.isdir(new) and not os.path.exists(new_symlink) and os.path.exists(README):
		try:
			os.symlink(README, new_symlink)
		except OSError as e:
			if e.errno != errno.EEXIST:
				raise
