# -*- coding: utf-8 -*-
"""Find unquoted usage of eval "$(ucr shell)"."""
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

reHashBang = re.compile('#!\s*/bin/(?:ba|da|z|c)?sh')


def containsHashBang(path):
	try:
		fp = open(path, 'r')
	except IOError:
		return False
	try:
		for line in fp:
			if reHashBang.search(line):
				return True
		return False
	finally:
		fp.close()


class UniventionPackageCheck(uub.UniventionPackageCheckDebian):

	def __init__(self):
		super(UniventionPackageCheck, self).__init__()
		self.tester = uub.UPCFileTester()
		self.tester.addTest(re.compile(r'eval\s+(`|[$][(])\s*(/usr/sbin/)?(ucr|univention-baseconfig|univention-config-registry)\s+shell\s*[^`)]*[`)]\s*'),
			'0017-1', 'unquoted call of eval "$(ucr shell)"', cntmax=0)
		self.tester.addTest(re.compile(r'\btr\s+(-[a-zA-Z]+\s+)*\['),
			'0017-2', 'unquoted argument for tr (e.g. "tr -d [a-z]")', cntmax=0)
		self.tester.addTest(re.compile(r'''\btr\s+(-[a-zA-Z]+\s+)*["']\[+[^\]]+\]+["']\s+\['''),
			'0017-2', 'unquoted argument for tr (e.g. "tr -d [a-z]")', cntmax=0)
		self.tester.addTest(re.compile(r'\bunivention-ldapsearch\b.*\s-[a-wyzA-Z]*x[a-wyzA-Z]*\b'),
			'0017-3', 'use of univention-ldapsearch -x', cntmax=0)
		self.tester.addTest(re.compile(r'\b(?:/sbin/)?ip6?tables\b +(?!--wait\b)'),
			'0017-4', 'iptables without --wait', cntmax=0)

	def getMsgIds(self):
		return {
			'0017-1': [uub.RESULT_WARN, 'script contains unquoted calls of eval "$(ucr shell)"'],
			'0017-2': [uub.RESULT_ERROR, 'script contains unquoted arguments of tr'],
			'0017-3': [uub.RESULT_WARN, 'LDAP simple bind is an internal detail of "univention-ldapsearch"'],
			'0017-4': [uub.RESULT_ERROR, 'ip[6]tables --wait must be used since UCS-4.2'],
		}

	def postinit(self, path):
		""" checks to be run before real check or to create precalculated data for several runs. Only called once! """

	def check(self, path):
		""" the real check """
		super(UniventionPackageCheck, self).check(path)

		#
		# search shell scripts and execute test
		#
		for fn in uub.FilteredDirWalkGenerator(path):
			if fn.endswith('.sh') or containsHashBang(fn):
				try:
					self.tester.open(fn)
					msglist = self.tester.runTests()
					self.msg.extend(msglist)
				except (IOError, OSError):
					continue
