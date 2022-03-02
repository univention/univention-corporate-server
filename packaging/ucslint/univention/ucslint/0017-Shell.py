# -*- coding: utf-8 -*-
"""Find unquoted usage of eval "$(ucr shell)"."""
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

import univention.ucslint.base as uub
from univention.ucslint.common import RE_HASHBANG_SHELL


class UniventionPackageCheck(uub.UniventionPackageCheckDebian):

	def __init__(self) -> None:
		super(UniventionPackageCheck, self).__init__()
		self.tester = uub.UPCFileTester()
		self.tester.addTest(
			re.compile(r'eval\s+(`|[$][(])\s*(/usr/sbin/)?(ucr|univention-baseconfig|univention-config-registry)\s+shell\s*[^`)]*[`)]\s*'),
			'0017-1', 'unquoted call of eval "$(ucr shell)"', cntmax=0)
		self.tester.addTest(re.compile(
			r'\b tr \s+ (-[a-zA-Z]+\s+)* \[', re.VERBOSE),
			'0017-2', 'unquoted argument for tr (e.g. "tr -d [a-z]")', cntmax=0)
		self.tester.addTest(re.compile(
			r'''\b tr \s+ (-[a-zA-Z]+\s+)* ["']\[+[^\]]+\]+["']\s+\[''', re.VERBOSE),
			'0017-2', 'unquoted argument for tr (e.g. "tr -d [a-z]")', cntmax=0)
		self.tester.addTest(re.compile(
			r'\b univention-ldapsearch \b .* \s-[a-wyzA-Z]*x[a-wyzA-Z]* \b', re.VERBOSE),
			'0017-3', 'use of univention-ldapsearch -x', cntmax=0)
		self.tester.addTest(
			re.compile(r'\b (?:/sbin/)? ip6?tables \b \s+ (?!--wait \b)', re.VERBOSE),
			'0017-4', 'iptables without --wait', cntmax=0)
		self.tester.addTest(
			re.compile(r'\b sed \s+ .* s (.) .* \\\(\.\*\\\) \$? \1 \\1 \1', re.VERBOSE),
			'0017-5', 'Use `sed -n "s/^prefix: //p"`', cntmax=0)
		self.tester.addTest(
			re.compile(r'\b sed (?: \s+ -[bnsuz]*[Er][bnsuze]* \b )+ .* s (.) .* \(\.\*\) \$? \1 \\1 \1', re.VERBOSE),
			'0017-5', 'Use `sed -n "s/^prefix: //p"`', cntmax=0)
		self.tester.addTest(
			re.compile(r'\b ldapsearch \b .+ \b ldapsearch-wrapper \b', re.VERBOSE),
			'0017-6', 'Use `ldapsearch -o ldif-wrap=no`', cntmax=0)
		self.tester.addTest(
			re.compile(r'\b (\w+) \[ \${\#\1\[[@*]\]} \]=', re.VERBOSE),
			'0017-7', 'Use `array+=(val)`', cntmax=0)
		self.tester.addTest(
			re.compile(r'''\b (?:cat|more) \s+ (?:'[^']*'|"[^"]*"|[^"'*? |])+ \s* \|(?!\|)''', re.VERBOSE),
			'0017-8', "Useless use of `cat`; redirect STDIN instead", cntmax=0)
		self.tester.addTest(
			re.compile(r'\b grep \b .* \|(?!\|) .* \b (?:awk|perl|sed) \b', re.VERBOSE),
			'0017-9', "Useless use of `grep`; use /PATTERN/s instead", cntmax=0)
		self.tester.addTest(
			re.compile(r'\b echo \s+ (?:-[ne]+ \s+)* (")? \$\( [^<][^)]* \) \1 \s* (?:$|[|&]|\d*[<>])', re.VERBOSE),
			'0017-10', "Useless use of `echo $(...)` for single argument", cntmax=0)

	def getMsgIds(self) -> uub.MsgIds:
		return {
			'0017-1': (uub.RESULT_WARN, 'script contains unquoted calls of eval "$(ucr shell)"'),
			'0017-2': (uub.RESULT_ERROR, 'script contains unquoted arguments of tr'),
			'0017-3': (uub.RESULT_WARN, 'LDAP simple bind is an internal detail of "univention-ldapsearch"'),
			'0017-4': (uub.RESULT_ERROR, 'ip[6]tables --wait must be used since UCS-4.2'),
			'0017-5': (uub.RESULT_STYLE, 'Use `sed -n "s/^prefix: //p"`'),
			'0017-6': (uub.RESULT_STYLE, 'Use `ldapsearch -LLLo ldif-wrap=no`'),
			'0017-7': (uub.RESULT_STYLE, 'Use `array+=(val)`'),
			'0017-8': (uub.RESULT_STYLE, "Useless use of `cat`; redirect STDIN instead"),
			'0017-9': (uub.RESULT_STYLE, "Useless use of `grep`; use /PATTERN/s instead"),
			'0017-10': (uub.RESULT_STYLE, "Useless use of `echo $(...)` for single argument"),
		}

	def check(self, path: str) -> None:
		""" the real check """
		super(UniventionPackageCheck, self).check(path)

		#
		# search shell scripts and execute test
		#
		for fn in uub.FilteredDirWalkGenerator(path, suffixes=['.sh'], reHashBang=RE_HASHBANG_SHELL):
			try:
				self.tester.open(fn)
			except EnvironmentError:
				continue
			else:
				msglist = self.tester.runTests()
				self.msg.extend(msglist)
