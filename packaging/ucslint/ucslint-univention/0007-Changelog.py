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
import os

REticket = re.compile(r'''
	(Bug:?[ ]\#[0-9]{1,6} # Bugzilla
	|Issue:?[ ]\#[0-9]{1,6} # Redmine
	|Ticket(\#:[ ]|:?[ ]\#)2[0-9]{3}(0[1-9]|1[0-2])(0[1-9]|[12][0-9]|3[01])(?:1[0-9]{7}|21[0-9]{6})) # OTRS
	(?![0-9]) # not followed by additional digits
	''', re.VERBOSE)


class UniventionPackageCheck(uub.UniventionPackageCheckDebian):

	def getMsgIds(self):
		return {
			'0007-1': [uub.RESULT_WARN, 'failed to open file'],
			'0007-2': [uub.RESULT_WARN, 'changelog does not contain ticket/bug/issue number'],
		}

	def postinit(self, path):
		""" checks to be run before real check or to create precalculated data for several runs. Only called once! """

	def check(self, path):
		""" the real check """
		super(UniventionPackageCheck, self).check(path)

		fn = os.path.join(path, 'debian', 'changelog')
		try:
			content = open(fn, 'r').read()
		except IOError:
			self.addmsg('0007-1', 'failed to open and read file', fn)
			return

		REchangelog = re.compile('^ -- [^<]+ <[^>]+>', re.M)

		firstEntry = REchangelog.split(content)[0]
		match = REticket.search(firstEntry)
		if not match:
			self.addmsg('0007-2', 'latest changelog entry does not contain bug/ticket/issue number', fn)
