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
import subprocess

RE_BASHISM = re.compile(r'^.*?\s+line\s+(\d+)\s+[(](.*?)[)][:]\n([^\n]+)$')
RE_LOCAL = re.compile(
    r'''
    \blocal\b
    \s+
    \w+
    =
    (?:\$(?![?$!#\s'"]
           |\{[?$!#]\}
           |$)
      |`
    )
    ''',  # noqa: E101
	re.VERBOSE
)


class UniventionPackageCheck(uub.UniventionPackageCheckDebian):

	def getMsgIds(self):
		return {
			'0013-1': [uub.RESULT_WARN, 'failed to open file'],
			'0013-2': [uub.RESULT_ERROR, 'possible bashism found'],
			'0013-3': [uub.RESULT_WARN, 'cannot parse output of "checkbashism"'],
			'0013-4': [uub.RESULT_WARN, 'unquoted local variable'],
		}

	def postinit(self, path):
		""" checks to be run before real check or to create precalculated data for several runs. Only called once! """

	def check(self, path):
		""" the real check """
		super(UniventionPackageCheck, self).check(path)

		for fn in uub.FilteredDirWalkGenerator(
			path,
			ignore_suffixes=['.po'],
			reHashBang=re.compile('^#![ \t]*/bin/(?:d?a)?sh')
		):
			self.debug('Testing file %s' % fn)
			self.check_bashism(fn)
			self.check_unquoted_local(fn)

	def check_bashism(self, fn):
			p = subprocess.Popen(['checkbashisms', fn], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			stdout, stderr = p.communicate()
			# 2 = file is no shell script or file is already bash script
			# 1 = bashism found
			# 0 = everything is posix compliant
			if p.returncode == 1:
				for item in stderr.split('possible bashism in '):
					item = item.strip()
					if not item:
						continue

					match = RE_BASHISM.search(item)
					if not match:
						self.addmsg('0013-3', 'cannot parse checkbashism output:\n"%s"' % item.replace('\n', '\\n').replace('\r', '\\r'), filename=fn)
						continue

					line = int(match.group(1))
					msg = match.group(2)
					code = match.group(3)

					self.addmsg('0013-2', 'possible bashism (%s):\n%s' % (msg, code), filename=fn, line=line)

	def check_unquoted_local(self, fn):
		with open(fn, 'r') as fd:
			for nr, line in enumerate(fd, start=1):
				line = line.strip()
				match = RE_LOCAL.search(line)
				if not match:
					continue

				self.addmsg('0013-4', 'unquoted local variable: %s' % (line,), filename=fn, line=nr)
