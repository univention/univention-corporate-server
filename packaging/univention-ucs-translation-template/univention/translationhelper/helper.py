#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2013-2019 Univention GmbH
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
import subprocess


def make_parent_dir(path):
	# type: (str) -> None
	"""
	Create parent directories for file.

	:param path: Path for a file.
	"""
	dir_path = os.path.dirname(path)
	try:
		os.makedirs(dir_path)
	except EnvironmentError:
		if not os.path.isdir(dir_path):
			raise


def call(*argv):
	# type: (*str) -> int
	"""
	Execute argv and wait.

	:param args: List of command and arguments.

	>>> call('true')
	0
	"""
	if os.environ.get('DH_VERBOSE', False):
		print('\t%s' % ' '.join(argv))
	return subprocess.call(argv)
