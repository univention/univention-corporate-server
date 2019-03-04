# -*- coding: utf-8 -*-
#
# Copyright 2018-2019 Univention GmbH
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
# <http://www.gnu.org/licenses/>.

from __future__ import absolute_import, unicode_literals
import sys
import univention.debug


is_interactive = bool(getattr(sys, 'ps1', sys.flags.interactive))


class UDebug(object):
	""":py:mod:`univention.debug` convenience wrapper"""
	target = univention.debug.ADMIN
	level2str = {
		univention.debug.ALL: 'DEBUG',
		univention.debug.ERROR: 'ERROR',
		univention.debug.INFO: 'INFO',
		univention.debug.PROCESS: 'INFO',
		univention.debug.WARN: 'WARN',
	}

	@classmethod
	def all(cls, msg):
		"""Write a debug message with level ALL (as in DEBUG)"""
		cls._log(univention.debug.ALL, msg)

	debug = all

	@classmethod
	def error(cls, msg):
		"""Write a debug message with level ERROR"""
		cls._log(univention.debug.ERROR, msg)

	@classmethod
	def info(cls, msg):
		"""Write a debug message with level INFO"""
		cls._log(univention.debug.INFO, msg)

	@classmethod
	def process(cls, msg):
		"""Write a debug message with level PROCESS"""
		cls._log(univention.debug.PROCESS, msg)

	@classmethod
	def warn(cls, msg):
		"""Write a debug message with level WARN"""
		cls._log(univention.debug.WARN, msg)

	warning = warn

	@classmethod
	def _log(cls, level, msg):
		univention.debug.debug(cls.target, level, msg)
		if is_interactive and level <= univention.debug.INFO:
			print('{}: {}'.format(cls.level2str[level], msg))
