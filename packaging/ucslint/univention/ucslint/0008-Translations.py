# -*- coding: utf-8 -*-
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright (C) 2008-2022 Univention GmbH
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

import re
from typing import Iterable

import univention.ucslint.base as uub
from univention.ucslint.python import MATCHED_LENIENT as MATCHED_STRING
from univention.ucslint.python import _or, python_files

# 1) check if translation strings are correct; detect something like  _('foo %s bar' % var)  ==> _('foo %s bar') % var
# 2) check if all translation strings are translated in de.po file


RE_FUZZY = re.compile(r'^\#,[ ] .*? \b fuzzy \b', re.MULTILINE | re.VERBOSE)
RE_EMPTY = re.compile(r'msgstr ""\n\n', re.DOTALL)
RE_CHARSET = re.compile(r'"Content-Type: text/plain; charset=(.*?)\\n"', re.DOTALL)

NON_STRING = r"""[^'"#\n]"""
CONTEXT = _or(NON_STRING, MATCHED_STRING)
SEPARATOR = r"[([{\s,:]"
TRANSLATION = r"(_\(\s*" + MATCHED_STRING + r"\s*%\s*(?:[^\n]+\))?)"
RE_TRANSLATION = re.compile(CONTEXT + SEPARATOR + TRANSLATION, re.DOTALL | re.MULTILINE | re.VERBOSE)


class UniventionPackageCheck(uub.UniventionPackageCheckDebian):

	def getMsgIds(self) -> uub.MsgIds:
		return {
			'0008-1': (uub.RESULT_ERROR, 'substitutes before translation'),
			'0008-2': (uub.RESULT_WARN, 'failed to open file'),
			'0008-3': (uub.RESULT_ERROR, 'po-file contains "fuzzy" string'),
			'0008-4': (uub.RESULT_WARN, 'po-file contains empty msg string'),
			'0008-5': (uub.RESULT_ERROR, 'po-file contains no character set definition'),
			'0008-6': (uub.RESULT_ERROR, 'po-file contains invalid character set definition'),
			'0008-7': (uub.RESULT_WARN, 'found well-known LDAP object but no custom_*name()'),
		}

	def check(self, path: str) -> None:
		""" the real check """
		super(UniventionPackageCheck, self).check(path)

		self.check_py(python_files(path))
		self.check_po(uub.FilteredDirWalkGenerator(path, suffixes=('.po',)))
		self.check_names(uub.FilteredDirWalkGenerator(
			path,
			ignore_suffixes=uub.FilteredDirWalkGenerator.BINARY_SUFFIXES | uub.FilteredDirWalkGenerator.DOCUMENTATION_SUFFIXES,
		))

	def check_py(self, py_files: Iterable[str]) -> None:
		"""Check Python files."""
		for fn in py_files:
			try:
				content = open(fn, 'r').read()
			except EnvironmentError:
				self.addmsg('0008-2', 'failed to open and read file', fn)
				continue

			self.debug('testing %s' % fn)
			for row, col, match in uub.line_regexp(content, RE_TRANSLATION):
				self.addmsg('0008-1', 'substitutes before translation: %s' % match.group(1), fn, row, col)

	def check_po(self, po_files: Iterable[str]) -> None:
		"""Check Portable Object files."""
		for fn in po_files:
			try:
				content = open(fn, 'r').read()
			except EnvironmentError:
				self.addmsg('0008-2', 'failed to open and read file', fn)
				continue

			match = RE_CHARSET.search(content)
			if not match:
				self.addmsg('0008-5', 'cannot find charset definition', fn)
			elif not match.group(1).lower() in ('utf-8'):
				self.addmsg('0008-6', 'invalid charset (%s) defined' % (match.group(1)), fn)

			self.debug('testing %s' % fn)
			for regex, errid, errtxt in [
				(RE_FUZZY, '0008-3', 'contains "fuzzy"'),
				(RE_EMPTY, '0008-4', 'contains empty msgstr')
			]:
				for row, col, match in uub.line_regexp(content, regex):
					self.addmsg(errid, errtxt, fn, row, col)

	def check_names(self, files: Iterable[str]) -> None:
		tester = uub.UPCFileTester()
		tester.addTest(
			re.compile(
				r'''
				(?<!custom_groupname[( ])
				(?<!custom_username[( ])
				(['"]) \b
				(?:Domain\ Users|Domain\ Admins|Administrator|Windows\ Hosts)
				\b \1
				''', re.VERBOSE),
			'0008-7', 'found well-known LDAP object but no custom_*name()', cntmax=0)

		for fn in files:
			try:
				tester.open(fn)
			except EnvironmentError:
				self.addmsg('0002-1', 'failed to open and read file', fn)
				continue
			else:
				self.msg += tester.runTests()
