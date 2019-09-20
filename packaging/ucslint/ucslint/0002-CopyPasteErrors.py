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
import os

# 1) check if strings like "dc=univention,dc=qa" appear in debian/* and conffiles/*
# 2) check if strings like "univention.qa" appear in debian/* and conffiles/*


class UniventionPackageCheck(uub.UniventionPackageCheckDebian):

	def getMsgIds(self):
		return {
			'0002-1': [uub.RESULT_WARN, 'cannot open file'],
			'0002-2': [uub.RESULT_ERROR, 'found basedn used in QA'],
			'0002-3': [uub.RESULT_ERROR, 'found domainname used in QA'],
		}

	def postinit(self, path):
		""" checks to be run before real check or to create precalculated data for several runs. Only called once! """

	def check(self, path):
		""" the real check """
		super(UniventionPackageCheck, self).check(path)

		files = []
		# scan directory only
		for dir in ['debian']:
			for fn in os.listdir(os.path.join(path, dir)):
				self.debug(os.path.join(path, dir, fn))
				if not os.path.isdir(os.path.join(path, dir, fn)):
					files.append(os.path.join(path, dir, fn))

		# scan directory recursively
		for dir in ['conffiles']:
			for fn in uub.FilteredDirWalkGenerator(os.path.join(path, dir)):
				files.append(fn)

		for fn in files:
			try:
				content = open(fn, 'r').read()
			except (OSError, IOError):
				self.addmsg('0002-1', 'failed to open and read file', fn)
				continue

			for txt in ['dc=univention,dc=local', 'dc=univention,dc=qa', 'dc=univention,dc=test']:
				for line in self._searchString(content, txt):
					self.addmsg('0002-2', 'contains invalid basedn', fn, line)

			for txt in ['univention.local', 'univention.qa', 'univention.test']:
				for line in self._searchString(content, txt):
					self.addmsg('0002-3', 'contains invalid domainname', fn, line)

	def _searchString(self, content, txt):
		result = []
		pos = 0
		while True:
			fpos = content.find(txt, pos)
			if fpos < 0:
				break
			else:
				line = content.count('\n', 0, fpos) + 1
				pos = fpos + len(txt) - 1
				result.append(line)
		return result
