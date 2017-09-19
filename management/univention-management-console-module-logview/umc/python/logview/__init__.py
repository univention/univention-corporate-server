#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Management Console module:
#   View logfiles
#
# Copyright 2016-2017 Univention GmbH
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
import subprocess

from univention.lib.i18n import Translation
from univention.management.console.base import Base, MODULE
from univention.management.console.modules.decorators import sanitize, simple_response
from univention.management.console.modules.sanitizers import (
	IntegerSanitizer,
	PatternSanitizer,
	SearchSanitizer,
	StringSanitizer,
)

_ = Translation('univention-management-console-module-logview').translate


LOGFILE_BASEDIR = '/var/log/univention/'
LOGFILE_EXTENSION = '.log'


class _FilenameSanitizer(StringSanitizer):
	"""Checks if a filename starts with a specified base directory and ends with a specified extension"""

	def __init__(self, basedir, extension, **kwargs):
		super(_FilenameSanitizer, self).__init__(**kwargs)
		self._basedir = basedir
		self._extension = extension

	def _sanitize(self, value, name, further_arguments):
		value = super(_FilenameSanitizer, self)._sanitize(value, name, further_arguments)
		value = os.path.abspath(value)  # strip ../ and resolve symlinks
		if not os.path.exists(value) or not value.startswith(self._basedir) or not value.endswith(self._extension):
			self.raise_validation_error(
				_('Only a file in directory "%s" with extension "%s" can be requested.')
				% (self._basedir, self._extension)
			)
		return value


class Instance(Base):

	@sanitize(
		logfile=PatternSanitizer(default='.*'),
		pattern=PatternSanitizer(default='.*', add_asterisks=True),
	)
	@simple_response
	def query(self, logfile, pattern):
		"""Searches for logfiles in /var/log/univention/"""
		result = []
		filenames = [
			os.path.join(LOGFILE_BASEDIR, file_)
			for file_ in os.listdir(LOGFILE_BASEDIR)
			if file_.endswith(LOGFILE_EXTENSION) and logfile.search(file_)
		]
		for filename in filenames:
			try:
				filesize = os.stat(filename).st_size
			except EnvironmentError as exc:
				MODULE.warn('Could not stat file %r: %s' % (filename, exc,))
				continue

			if not filesize:
				continue

			with open(filename, 'r') as fd:
				strings = fd.readlines()
				lines = len(strings)
				match = bool(pattern.search(''.join(strings)))
				if match:
					result += [{
						'filename': filename,
						'lines': lines,
						'filesize': filesize,
					}]
		return result

	@sanitize(
		logfile=_FilenameSanitizer(basedir=LOGFILE_BASEDIR, extension=LOGFILE_EXTENSION),
		offset=IntegerSanitizer(default=0),
		buffer=IntegerSanitizer(default=100),
	)
	@simple_response
	def load_text(self, logfile, offset, buffer):
		"""Returns part of the content of a file"""
		lines = []
		with open(logfile, 'r') as fd:
			for _ in range(offset):
				fd.readline()
			for _ in range(buffer):
				lines += [fd.readline()]
		return ''.join(lines)

	@sanitize(
		logfile=_FilenameSanitizer(basedir=LOGFILE_BASEDIR, extension=LOGFILE_EXTENSION),
		pattern=SearchSanitizer(default='.*', add_asterisks=False),
		radius=IntegerSanitizer(default=10),
	)
	@simple_response
	def search_pattern(self, logfile, pattern, radius):
		"""Searches for a pattern in a logfile and returns filtered text"""
		process = subprocess.Popen(
			['grep', '-inC', '%d' % (radius,), pattern, logfile],
			stdout=subprocess.PIPE,
		)
		return process.communicate()[0]
