# -*- coding: utf-8 -*-
# pylint: disable-msg=C0103
"""Find use of deprecated functions / programs / scripts."""
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
import os


class UniventionPackageCheck(uub.UniventionPackageCheckDebian):

	"""Find use of deprecated functions / programs / scripts."""

	def getMsgIds(self):  # pylint: disable-msg=R0201
		"""Return severity and description for message identifiers."""
		return {
			'0016-1': [uub.RESULT_WARN, 'failed to open file'],
			'0016-2': [uub.RESULT_WARN, 'Deprecated use of "univention-admin"'],
			'0016-3': [uub.RESULT_WARN, 'Use of deprecated "univention-baseconfig"'],
			'0016-4': [uub.RESULT_WARN, 'Use of deprecated "univention_baseconfig"'],
			'0016-5': [uub.RESULT_WARN, 'Use of deprecated "@%@BCWARNING=@%@"'],
			'0016-6': [uub.RESULT_WARN, 'Use of deprecated "debian/*.univention-baseconfig"'],
		}

	def postinit(self, path):
		"""checks to be run before real check or to create precalculated data
		for several runs. Only called once! """

	def check(self, path):
		""" the real check """
		super(UniventionPackageCheck, self).check(path)

		tester = uub.UPCFileTester()
		tester.addTest(
			re.compile('''(?:(?<=['" \t])|^)(?:/usr/sbin/)?univention-admin(?=['" \t]|$)'''),
			'0016-2', 'Use of deprecated "univention-admin"', cntmax=0)
		tester.addTest(
			re.compile('''(?:(?<=['" \t])|^)(?:/usr/sbin/)?univention-baseconfig(?=["' \t]|$)'''),
			'0016-3', 'Use of deprecated "univention-baseconfig"', cntmax=0)
		tester.addTest(
			re.compile(r'''\bfrom\b.+\bunivention_baseconfig\b.+\bimport\b|\bimport\b.+\bunivention_baseconfig\b'''),
			'0016-4', 'Use of deprecated "univention_baseconfig"', cntmax=0)
		tester.addTest(
			re.compile(r'''@%@BCWARNING=.+?@%@'''),
			'0016-5', 'Use of deprecated "@%@BCWARNING=@%@"', cntmax=0)

		ignore_suffixes = ('.1', '.2', '.3', '.4', '.5', '.6', '.7', '.8', '.txt'),
		ignore_files = ('changelog', 'README')
		for fn in uub.FilteredDirWalkGenerator(path, ignore_suffixes=ignore_suffixes, ignore_files=ignore_files):
			tester.open(fn)
			msglist = tester.runTests()
			self.msg.extend(msglist)

		for fn in uub.FilteredDirWalkGenerator(os.path.join(path, 'debian'), suffixes=('.univention-baseconfig',)):
			self.addmsg('0016-6', 'Use of deprecated "debian/*.univention-baseconfig"', fn)
