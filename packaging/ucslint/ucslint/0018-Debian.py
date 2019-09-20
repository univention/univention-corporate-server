# vim:set ts=4 sw=4 noet fileencoding=UTF-8 :
"""Find maintainer scripts using wrong header."""
#
# Copyright (C) 2016-2019 Univention GmbH
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
from os import listdir
from os.path import join, splitext


class UniventionPackageCheck(uub.UniventionPackageCheckDebian):

	def getMsgIds(self):
		return {
			'0018-1': [uub.RESULT_STYLE, 'wrong script name in comment'],
		}

	def check(self, path):
		SCRIPTS = frozenset(('preinst', 'postinst', 'prerm', 'postrm'))
		for filename in listdir(join(path, 'debian')):
			if '.' in filename:
				package, suffix = splitext(filename)
				suffix = suffix.lstrip('.')
			else:
				package, suffix = None, filename

			if suffix not in SCRIPTS:
				continue

			script_path = join(path, 'debian', filename)
			with open(script_path, 'r') as script_file:
				for nr, line in enumerate(script_file, start=1):
					if not line.startswith('#'):
						break
					for script_name in SCRIPTS - set((suffix,)):
						if script_name in line:
							self.addmsg(
								'0018-1',
								'wrong script name: %r' % (line.strip(),),
								filename=script_path,
								line=nr)
