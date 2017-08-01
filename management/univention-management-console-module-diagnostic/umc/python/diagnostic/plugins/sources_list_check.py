#!/usr/bin/python2.7
# coding: utf-8
#
# Univention Management Console module:
#  System Diagnosis UMC module
#
# Copyright 2017 Univention GmbH
#
# http://www.univention.de/
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
# <http://www.gnu.org/licenses/>.

import re
import glob

from univention.management.console.modules.diagnostic import Warning

from univention.lib.i18n import Translation
_ = Translation('univention-management-console-module-diagnostic').translate

title = _('Check errors in sources.list files')
description = _('All files ok.')


TRACEBACK_REGEX = re.compile((
	'(?P<start>#\s+)Traceback \(most recent call last\):\n'  # start of exception
	'(?:(?P=start).*\n)+?'                                   # irrelevant lines of detail
	'(?P=start)(?P<exception>[^\s].*)\n'))                   # extract exception


class TracebackFound(Exception):
	def __init__(self, path, exception):
		super(TracebackFound, self).__init__(path, exception)
		self.path = path
		self.exception = exception

	def __str__(self):
		msg = _('Found exception in {path!r}: {exception}')
		return msg.format(path=self.path, exception=self.exception)


def find_tracebacks(path):
	with open(path) as fob:
		content = fob.read()
		for match in TRACEBACK_REGEX.finditer(content):
			yield match.group('exception')


def check_for_tracebacks():
	for path in glob.iglob('/etc/apt/sources.list.d/*'):
		for exception in find_tracebacks(path):
			yield TracebackFound(path, exception)


def run(_umc_instance):
	error_descriptions = [str(exc) for exc in check_for_tracebacks()]
	if error_descriptions:
		error_descriptions.append(_('Please check the files for more details.'))
		raise Warning(description='\n'.join(error_descriptions))


if __name__ == '__main__':
	from univention.management.console.modules.diagnostic import main
	main()
