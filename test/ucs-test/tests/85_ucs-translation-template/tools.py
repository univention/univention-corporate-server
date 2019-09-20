#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2016-2019 Univention GmbH
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
import subprocess
import fnmatch
import os


class InvalidCommandError(Exception):
	pass


def get_matching_file_paths(path, pattern):
	matched_files_paths = list()
	for dirname, dns, fnames in os.walk(path):
		for fn in fnames:
			matched_files_paths.append(os.path.join(dirname, fn))
	return fnmatch.filter(matched_files_paths, pattern)


def call(*command_parts):
	if not command_parts:
		raise InvalidCommandError()
	try:
		subprocess.check_call([part for part in command_parts])
	except subprocess.CalledProcessError as exc:
		print('Error: Subprocess exited unsuccessfully. Attempted command:')
		print(' '.join(exc.cmd))
		raise InvalidCommandError()
	except AttributeError as exc:
		print('Command must be a string like object.')
		raise InvalidCommandError()
	except OSError as exc:
		print('Error: Command exited unsuccessfully. Operating System error during command execution.')
		print('Error: {}'.format(exc.strerror))
		raise InvalidCommandError()
