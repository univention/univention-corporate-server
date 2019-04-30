# -*- coding: utf-8 -*-
#
# Copyright 2018-2019 Univention GmbH
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
# you and Univention.
#
# This program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <https://www.gnu.org/licenses/>.

from __future__ import absolute_import, unicode_literals
from __future__ import print_function
import sys
import univention.debug as ud


is_interactive = bool(getattr(sys, 'ps1', sys.flags.interactive))


class UDebug(object):
	""":py:mod:`univention.debug` convenience wrapper"""
	target = ud.ADMIN
	level2str = {
		ud.ALL: 'DEBUG',
		ud.ERROR: 'ERROR',
		ud.INFO: 'INFO',
		ud.PROCESS: 'INFO',
		ud.WARN: 'WARN',
	}

	@classmethod
	def all(cls, msg):
		"""Write a debug message with level ALL (as in DEBUG)"""
		cls._log(ud.ALL, msg)

	debug = all

	@classmethod
	def error(cls, msg):
		"""Write a debug message with level ERROR"""
		cls._log(ud.ERROR, msg)

	@classmethod
	def info(cls, msg):
		"""Write a debug message with level INFO"""
		cls._log(ud.INFO, msg)

	@classmethod
	def process(cls, msg):
		"""Write a debug message with level PROCESS"""
		cls._log(ud.PROCESS, msg)

	@classmethod
	def warn(cls, msg):
		"""Write a debug message with level WARN"""
		cls._log(ud.WARN, msg)

	warning = warn

	@classmethod
	def _log(cls, level, msg):
		ud.debug(cls.target, level, msg)
		if is_interactive and level <= ud.INFO:
			print('{}: {}'.format(cls.level2str[level], msg))
