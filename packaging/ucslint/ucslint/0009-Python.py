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


class UniventionPackageCheck(uub.UniventionPackageCheckDebian):

	"""Python specific checks."""

	def getMsgIds(self):
		return {
			'0009-1': [uub.RESULT_WARN, 'failed to open file'],
			'0009-2': [uub.RESULT_ERROR, 'python file does not specify python version in hashbang'],
			'0009-3': [uub.RESULT_ERROR, 'python file specifies wrong python version in hashbang'],
			'0009-4': [uub.RESULT_WARN, 'python file contains whitespace and maybe arguments after python command'],
			'0009-5': [uub.RESULT_WARN, 'dict.has_key is deprecated in python3 - please use "if key in dict:"'],
			'0009-6': [uub.RESULT_WARN, 'raise "text" is deprecated in python3'],
			'0009-7': [uub.RESULT_STYLE, 'fragile comparison with None'],
			'0009-8': [uub.RESULT_STYLE, 'use ucr.is_true() or .is_false()'],
			'0009-9': [uub.RESULT_ERROR, 'hashbang contains more than one option'],
		}

	def postinit(self, path):
		""" checks to be run before real check or to create precalculated data for several runs. Only called once! """

	RE_HASHBANG = re.compile(r'''^#!\s*/usr/bin/python(?:([0-9.]+))?(?:(\s+)(?:(\S+)(\s.*)?)?)?$''')

	def check(self, path):
		""" the real check """
		super(UniventionPackageCheck, self).check(path)

		py_files = []
		for fn in uub.FilteredDirWalkGenerator(path):
			if fn.endswith('.py'):  # add all files to list that end with ".py"
				py_files.append(fn)
				continue

			try:
				content = open(fn, 'r').read(100)  # add all files that contain a hashbang in first line
			except (IOError, OSError):
				self.debug('Failed to read 100 bytes from %r' % (fn,))
			else:
				if content.startswith('#!'):
					py_files.append(fn)

		tester = uub.UPCFileTester()
		tester.addTest(re.compile('.has_key\s*\('), '0009-5', 'dict.has_key is deprecated in python3 - please use "if key in dict:"', cntmax=0)
		tester.addTest(re.compile(r'''\braise\s*(?:'[^']+'|"[^"]+")'''), '0009-6', 'raise "text" is deprecated in python3', cntmax=0)
		tester.addTest(re.compile(r"""\b(?:if|while)\b.*(?:(?:!=|<>|==)\s*None\b|\bNone\s*(?:!=|<>|==)).*:"""), '0009-7', 'fragile comparison with None', cntmax=0)
		tester.addTest(re.compile(
			r'''(?:baseConfig|configRegistry|ucr)(?:\[.+\]|\.get\(.+\)).*\bin\s*
			[[(]
			(?:\s*(['"])(?:yes|no|1|0|true|false|on|off|enabled?|disabled?)\1\s*,?\s*){3,}
			[])]''', re.VERBOSE | re.IGNORECASE),
			'0009-8', 'use ucr.is_true() or .is_false()', cntmax=0)
		for fn in py_files:
			try:
				content = open(fn, 'r').read(100)
			except (IOError, OSError):
				self.addmsg('0009-1', 'failed to open and read file', filename=fn)
				continue
			self.debug('testing %s' % fn)

			if not content:
				continue

			tester.open(fn)
			msglist = tester.runTests()
			self.msg.extend(msglist)

			firstline = content.splitlines()[0]
			match = UniventionPackageCheck.RE_HASHBANG.match(firstline)
			if match:
				version, space, option, tail = match.groups()
				if not version:
					self.addmsg('0009-2', 'file does not specify python version in hashbang', filename=fn)
				elif version != '2.7':
					self.addmsg('0009-3', 'file specifies wrong python version in hashbang', filename=fn)
				if space and not option:
					self.addmsg('0009-4', 'file contains whitespace after python command', filename=fn)
				if tail:
					self.addmsg('0009-9', 'hashbang contains more than one option', filename=fn)
