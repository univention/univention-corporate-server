#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
"""
Univention common Python library for shell scripts.
"""
# Copyright 2010-2022 Univention GmbH
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

import subprocess
import pipes
import re

import six


def escape_value(value):
	# type: (str) -> str
	"""
	Escape a value for shell usage with double quotes.

	:param str value: The string to escape.
	:returns: The escaped string.
	:rtype: str

	.. deprecated:: 4.4
		use pipes.quote() instead

	>>> escape_value('eins zwei')
	'"eins zwei"'
	>>> escape_value('''"'$\`''')
	'"\\\\"\\'\\\\$\\\\\\\\\\\\`"'
	"""
	escapes = {
		'"': '\\"',
		'$': '\\$',
		'\\': '\\\\',
		'`': '\\`',
	}
	return '"%s"' % ''.join(escapes.get(c, c) for c in value)


_RE_AT_JOB = re.compile('^job ([1-9][0-9]*) at .*')


def create_at_job(script, time=None, date=None):
	# type: (Union[List[str], Tuple[str], str], Optional[str], Optional[str]) -> Any
	"""
	Create an :program:`at` job.

	:param script: The shell command to execute.
	:type script: List[str] or Tuple[str] or str
	:param str time: The time of day when the command is to be executed. If `None` is given, `now` is used.
	:param str date: The date when the command is to be executed.
	:returns: an `AtJob` object with the named attributes `.returncode`, `.job`, `.stdout` and `.stderr`.

	>>> r = create_at_job('''echo "42"''')
	>>> r = create_at_job(['echo', 'noon'], '12:00')
	>>> r = create_at_job(['echo', 'new year'], '24:00', '31.12.2030')
	>>> (r.returncode, r.job, r.stdout, r.stderr) # doctest:+ELLIPSIS
	(0, ..., '', '...job ... at Wed Jan  1 00:00:00 2031\\n')

	.. deprecated:: 4.4

	See :py:mod:`univention.atjobs` for an alternative implementation.
	"""
	# if script is a sequence, shell escape it
	if isinstance(script, (list, tuple)):
		script = ' '.join(pipes.quote(val) for val in script)
	# build at command
	cmd = ['at']
	if time:
		cmd.append('%s' % time)
		if date:
			cmd.append('%s' % date)
	else:
		cmd.append('now')
	env = {'LC_ALL': 'C'}

	p = subprocess.Popen(cmd, shell=False, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)

	class AtJob(object):
		stdout, stderr = p.communicate(script.encode('UTF-8'))
		if six.PY3:
			stdout, stderr = stdout.decode('UTF-8', 'replace'), stderr.decode('UTF-8', 'replace')
		returncode = p.returncode
		if returncode == 0:
			job = int(_RE_AT_JOB.match(stderr.splitlines()[-1]).groups()[0])
		else:
			job = None
	return AtJob


if __name__ == '__main__':
	import doctest
	doctest.testmod()
