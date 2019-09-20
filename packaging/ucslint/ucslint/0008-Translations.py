# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2019 Univention GmbH
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

try:
	import univention.ucslint.base as uub
except ImportError:
	import ucslint.base as uub
import re

# 1) check if translation strings are correct; detect something like  _('foo %s bar' % var)  ==> _('foo %s bar') % var
# 2) check if all translation strings are translated in de.po file


class UniventionPackageCheck(uub.UniventionPackageCheckDebian):

	def getMsgIds(self):
		return {
			'0008-1': [uub.RESULT_ERROR, 'substitutes before translation'],
			'0008-2': [uub.RESULT_WARN, 'failed to open file'],
			'0008-3': [uub.RESULT_ERROR, 'po-file contains "fuzzy" string'],
			'0008-4': [uub.RESULT_WARN, 'po-file contains empty msg string'],
			'0008-5': [uub.RESULT_ERROR, 'po-file contains no character set definition'],
			'0008-6': [uub.RESULT_ERROR, 'po-file contains invalid character set definition'],
		}

	def postinit(self, path):
		""" checks to be run before real check or to create precalculated data for several runs. Only called once! """

	def check(self, path):
		""" the real check """
		super(UniventionPackageCheck, self).check(path)

		py_files = []
		po_files = []
		for fn in uub.FilteredDirWalkGenerator(path, suffixes=('.py', '.po')):
			if fn.endswith('.py'):
				py_files.append(fn)
			if fn.endswith('.po'):
				po_files.append(fn)

		self.check_py(py_files)
		self.check_po(po_files)

	def check_py(self, py_files):
		"""Check Python files."""
		def _or(*disjunct):
			return r'(?:%s)' % ('|'.join(disjunct))

		matched_string = '%s?%s' % (
			_or('[Rr]', '[Uu]', '[Uu][Rr]'),
			_or(
				r"'''(?:[^'\\]|\\.|'[^']|''[^'])*?'''",
				r'"""(?:[^"\\]|\\.|"[^"]|""[^"])*?"""',
				r"'(?:[^'\\\n]|\\.)*?'",
				r'"(?:[^"\\\n]|\\.)*?"',
			)
		)
		non_string = r"""[^'"#\n]"""
		context = _or(non_string, matched_string)
		separator = r"[([{\s,:]"
		translation = r"(_\(\s*" + matched_string + r"\s*%\s*(?:[^\n]+\))?)"
		regEx1 = re.compile(context + separator + translation,
			re.DOTALL | re.MULTILINE | re.VERBOSE)

		for fn in py_files:
			try:
				content = open(fn, 'r').read()
			except (OSError, IOError):
				self.addmsg('0008-2', 'failed to open and read file', filename=fn)
				continue
			self.debug('testing %s' % fn)
			for regex in (regEx1,):
				pos = 0
				while True:
					match = regex.search(content, pos)
					if not match:
						break
					else:
						line = content.count('\n', 0, match.start()) + 1
						pos = match.end()
						self.addmsg('0008-1', 'substitutes before translation: %s' % match.group(1), fn, line)

	def check_po(self, po_files):
		"""Check Portable Object files."""
		regEx1 = re.compile('\n#.*?fuzzy')
		regEx2 = re.compile('msgstr ""\n\n', re.DOTALL)
		regExCharset = re.compile('"Content-Type: text/plain; charset=(.*?)\\\\n"', re.DOTALL)

		for fn in po_files:
			try:
				content = open(fn, 'r').read()
			except (OSError, IOError):
				self.addmsg('0008-2', 'failed to open and read file', fn)
				continue

			match = regExCharset.search(content)
			if not match:
				self.addmsg('0008-5', 'cannot find charset definition', fn)
			elif not match.group(1).lower() in ('utf-8'):
				self.addmsg('0008-6', 'invalid charset (%s) defined' % (match.group(1)), fn)

			self.debug('testing %s' % fn)
			for regex, errid, errtxt in [(regEx1, '0008-3', 'contains "fuzzy"'),
					(regEx2, '0008-4', 'contains empty msgstr')]:
				pos = 0
				while True:
					match = regex.search(content, pos)
					if not match:
						break
					else:
						# match.start() + 1 ==> avoid wrong line numbers because regEx1 starts with \n
						line = content.count('\n', 0, match.start() + 1) + 1
						pos = match.end()
						self.addmsg(errid, errtxt, fn, line)
