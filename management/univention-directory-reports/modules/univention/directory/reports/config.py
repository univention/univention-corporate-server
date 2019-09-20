# -*- coding: utf-8 -*-
#
# Univention Directory Reports
#  write an interpreted token structure to a file
#
# Copyright 2007-2019 Univention GmbH
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

import ConfigParser
import shlex
import locale
import os.path


class Config(ConfigParser.ConfigParser):

	def __init__(self, filename='/etc/univention/directory/reports/config.ini'):
		ConfigParser.ConfigParser.__init__(self)
		self._filename = filename
		self.read(filename)
		defaults = self.defaults()
		self._oldHeader = defaults.get('header', None)
		self._oldFooter = defaults.get('footer', None)
		self.default_report_name = defaults.get('report', None)
		self._reports = {}

		# get the language, defaults to English if nothing is set
		self._lang = locale.getlocale(locale.LC_MESSAGES)[0]
		if not self._lang:
			self._lang = "en_US"

		for key, value in self.items('reports'):
			# Entries are expected to have the form (see also config.ini):
			#   <module> <name> <directoryPath> <templateFile>
			# For compatibility reasons, we need also to accept the deprecated format:
			#   <module> <name> <templateFilePath>
			# make sure that the entries match this format
			module, name, dir, filename = [''] * 4
			tmpList = shlex.split(value)
			if len(tmpList) == 3:
				# old format, insert empty string for 'directory'
				tmpList.insert(2, '')
			if not len(tmpList) == 4:
				# wrong format
				continue
			module, name, dir, filename = tmpList

			# save the entry to our internal list
			if module in self._reports:
				self._reports[module].append((name, dir, filename))
			else:
				self._reports[module] = [(name, dir, filename)]

	def _get_report_entry(self, module, name=None):
		"""Find the correct internal report entry for a given a module and a report name."""
		# return None for non-existent module
		if module not in self._reports:
			return None
		# return first report if only the module name is given
		if not name:
			return self._reports[module][0]
		# if module name and report name are given, try to find the correct entry
		for report in self._reports[module]:
			if report[0] == name:
				return report
		# if anything fails, return None
		return None

	def _guess_path(self, directory, fileName, alternativePath=''):
		"""Guess the correct path for a given template file. Possible paths:
		(1) directory/<language>/fileName
		(2) directory/fileName
		(3) alternativePath"""
		# guess the header/footer path in order to support the old format
		guessedPaths = []

		# if the directory path is non-empty, this is how it should be, our first guess
		if directory:
			guessedPaths.append(os.path.join(directory, self._lang, fileName))
		# in case there is no language directory, our second guess
		# (works also for empty directory)
		guessedPaths.append(os.path.join(directory, fileName))
		# if given, our last guess is the alternative path
		if alternativePath:
			guessedPaths.append(alternativePath)

		# get the first valid path
		while len(guessedPaths):
			path = guessedPaths.pop(0)
			if os.path.exists(path):
				return path
		return None

	def get_header(self, module, name=None, suffix='.tex'):
		report = self._get_report_entry(module, name)
		if not report:
			return None
		return self._guess_path(report[1], 'header%s' % (suffix,), self._oldHeader)

	def get_footer(self, module, name=None, suffix='.tex'):
		report = self._get_report_entry(module, name)
		if not report:
			return None
		return self._guess_path(report[1], 'footer%s' % (suffix,), self._oldFooter)

	def get_report_names(self, module):
		reports = self._reports.get(module, [])
		return [item[0] for item in reports]

	def get_report(self, module, name=None):
		report = self._get_report_entry(module, name)
		if not report:
			return None
		return self._guess_path(report[1], report[2])
