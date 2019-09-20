#!/usr/bin/python2.7

#
# Copyright 2011-2019 Univention GmbH
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

# This script was adjusted from the Tests for ntacls manipulation
# Copyright (C) Matthieu Patou <mat@matws.net> 2009-2010
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#

"""Set user_xattr option on ext3/ext4 filesystems, remount if necessary"""
from __future__ import print_function

from univention.lib import fstab
import subprocess


def _do_modify_extfs_option(fstab_partition, options=[], activate=True):
	fstab_modified = False
	for option in options:
		if activate:
			if option not in fstab_partition.options:
				fstab_partition.options.append(option)
				fstab_modified = True
			else:
				# operation successful: nothing to be done
				continue
		else:
			if option not in fstab_partition.options:
				continue
			else:
				fstab_partition.options.remove(option)
				fstab_modified = True
	return fstab_modified


def _modify_extfs_option(options=[], activate=True, devices=[]):
	fs = fstab.File()
	target_partitions = []
	if devices:
		for device in devices:
			fstab_partition = fs.find(spec=device)
			if fstab_partition and fstab_partition.type in ('ext3', 'ext4'):
				target_partitions.append(fstab_partition)
			else:
				print('Device could not be found: %s' % (device,))
	else:
		for fstype in ('ext3', 'ext4'):
			for fstab_partition in fs.get(fstype, ignore_root=False):
				target_partitions.append(fstab_partition)

	for fstab_partition in target_partitions:
		if _do_modify_extfs_option(fstab_partition, options, activate):
			fs.save()
			if subprocess.call(('mount', '-o', 'remount', fstab_partition.spec)):
				print('Remounting partition failed: %s' % (fstab_partition.spec,))


if __name__ == '__main__':
	_modify_extfs_option(['user_xattr'])
