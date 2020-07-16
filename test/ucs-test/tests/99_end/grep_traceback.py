#!/usr/bin/python2.7
#
# Copyright 2019-2020 Univention GmbH
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
"""Grep python tracebacks in logfiles"""

from __future__ import print_function

import re
import gzip
import sys


class Set(set):
	pass


def main(filenames, ignore_exceptions=(), ignore_tracebacks=()):
	tracebacks = {}
	for filename in filenames:
		opener = gzip.open if filename.endswith('.gz') else open
		with opener(filename) as fd:
			line = True
			while line:
				line = fd.readline()
				if line.endswith('Traceback (most recent call last):\n'):
					lines = []
					line = ' '
					while line.startswith(' '):
						line = fd.readline()
						lines.append(line)
					d = Set()
					d.occurred = 1
					tb = tracebacks.setdefault(''.join(lines[:-1]), d)
					tb.add(lines[-1])
					tb.occurred += 1

	print(len(tracebacks))
	found = False
	for traceback, exceptions in tracebacks.items():
		ignored_exc = (ignore for exc in exceptions for ignore in ignore_exceptions if ignore.search(exc))
		ignored_tracebacks = (ignore for exc in exceptions for ignore in ignore_tracebacks if ignore.search(exc))
		try:
			print('\nIgnoring %s\n' % ((next(ignored_exc) or next(ignored_tracebacks)).pattern,))
			continue
		except StopIteration:
			pass
		found = True
		print('%d times:' % (exceptions.occurred,))
		print('Traceback (most recent call last):')
		print(traceback, end='')
		for exc in exceptions:
			print(exc, end=' ')
		print()
	return not found


if __name__ == '__main__':
	import argparse
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument('--ignore-exception', '-i', default='^$')
	parser.add_argument('filename', nargs='+')
	args = parser.parse_args()
	sys.exit(int(not main(args.filename, ignore_exceptions=[re.compile(args.ignore_exception)])))
