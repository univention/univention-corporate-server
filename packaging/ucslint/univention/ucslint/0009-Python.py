# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2020 Univention GmbH
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

import univention.ucslint.base as uub
from univention.ucslint.python import python_files, Python33 as PythonVer, RE_LENIENT
import re


class UniventionPackageCheck(uub.UniventionPackageCheckDebian):

	"""Python specific checks."""

	def getMsgIds(self):
		return {
			'0009-1': (uub.RESULT_WARN, 'failed to open file'),
			'0009-2': (uub.RESULT_ERROR, 'python file does not specify python version in hashbang'),
			'0009-3': (uub.RESULT_ERROR, 'python file specifies wrong python version in hashbang'),
			'0009-4': (uub.RESULT_WARN, 'python file contains whitespace and maybe arguments after python command'),
			'0009-5': (uub.RESULT_WARN, 'dict.has_key is deprecated in python3 - please use "if key in dict:"'),
			'0009-6': (uub.RESULT_WARN, 'raise "text" is deprecated in python3'),
			'0009-7': (uub.RESULT_STYLE, 'fragile comparison with None'),
			'0009-8': (uub.RESULT_STYLE, 'use ucr.is_true() or .is_false()'),
			'0009-9': (uub.RESULT_ERROR, 'hashbang contains more than one option'),
			'0009-10': (uub.RESULT_WARN, 'invalid Python string literal escape sequence'),
			'0009-11': (uub.RESULT_STYLE, 'Use uldap.searchDN() instead of uldap.search(attr=["dn"])'),
		}

	RE_HASHBANG = re.compile(r'''^#!\s*/usr/bin/python(?:([0-9.]+))?(?:(\s+)(?:(\S+)(\s.*)?)?)?$''')
	RE_STRING = PythonVer.matcher()

	def check(self, path):
		""" the real check """
		super(UniventionPackageCheck, self).check(path)

		tester = uub.UPCFileTester()
		tester.addTest(re.compile(r'\.has_key\s*\('), '0009-5', 'dict.has_key is deprecated in python3 - please use "if key in dict:"', cntmax=0)
		tester.addTest(re.compile(r'''\braise\s*(?:'[^']+'|"[^"]+")'''), '0009-6', 'raise "text" is deprecated in python3', cntmax=0)
		tester.addTest(re.compile(r"""\b(?:if|while)\b.*(?:(?:!=|<>|==)\s*None\b|\bNone\s*(?:!=|<>|==)).*:"""), '0009-7', 'fragile comparison with None', cntmax=0)
		tester.addTest(re.compile(
			r'''(?:baseConfig|configRegistry|ucr)(?:\[.+\]|\.get\(.+\)).*\bin\s*
			[\[\(]
			(?:\s*(['"])(?:yes|no|1|0|true|false|on|off|enabled?|disabled?)\1\s*,?\s*){3,}
			[\]\)]''', re.VERBOSE | re.IGNORECASE),
			'0009-8', 'use ucr.is_true() or .is_false()', cntmax=0)
		tester.addTest(re.compile(
			r'''\.search\s*\(
			.*?\b
			attr
			\s*=\s*
			(?:(?P<list>\[)|(?P<tuple>\())
			\s*
			(?P<str>["'])
			dn
			(?P=str)
			\s*
			(?(list)\])(?(tuple)\))
			''', re.VERBOSE),
			'0009-11', 'Use uldap.searchDN() instead of uldap.search(attr=["dn"])', cntmax=0)

		for fn in python_files(path):
			tester.open(fn)
			if not tester.raw:
				continue
			msglist = tester.runTests()
			self.msg.extend(msglist)

			match = self.RE_HASHBANG.match(tester.lines[0])
			if match:
				version, space, option, tail = match.groups()
				if not version:
					self.addmsg('0009-2', 'file does not specify python version in hashbang', filename=fn)
				elif version not in ('3', '2.7'):
					self.addmsg('0009-3', 'file specifies wrong python version in hashbang', filename=fn)
				if space and not option:
					self.addmsg('0009-4', 'file contains whitespace after python command', filename=fn)
				if tail:
					self.addmsg('0009-9', 'hashbang contains more than one option', filename=fn)

			line = 1
			col = 1
			pos = 0
			for m in RE_LENIENT.finditer(tester.raw):
				txt = m.group("str")
				if not txt:
					continue
				if self.RE_STRING.match(txt):
					continue
				start, end = m.span()
				while pos < start:
					if tester.raw[pos] == "\n":
						col = 1
						line += 1
					else:
						col += 1
					pos += 1

				self.addmsg('0009-10', 'invalid Python string literal: %s' % (txt,), filename=fn, line=line, pos=col)
