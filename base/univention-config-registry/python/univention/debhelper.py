# -*- coding: utf-8 -*-
#
# Univention Configuration Registry
"""Debhelper compatible routines."""
#
# Copyright 2010-2019 Univention GmbH
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
from __future__ import print_function
import os
import subprocess
try:
	from typing import Dict, List  # noqa F401
except ImportError:
	pass


def doIt(*argv):
	# type: (*str) -> int
	"""
	Execute argv and wait.

	:param args: List of command and arguments.

	>>> doIt('true')
	0
	"""
	if os.environ.get('DH_VERBOSE', False):
		print('\t%s' % ' '.join(argv))
	return subprocess.call(argv)


def binary_packages():
	# type: () -> List[str]
	"""
	Get list of binary packages from debian/control file.

	>>> binary_packages() #doctest: +ELLIPSIS
	[...]
	"""
	_prefix = 'Package: '
	packages = []
	f = open('debian/control', 'r')
	try:
		for line in f:
			if not line.startswith(_prefix):
				continue
			packages.append(line[len(_prefix): -1])
	finally:
		f.close()
	return packages


def parseRfc822(f):
	# type: (str) -> List[Dict[str, List[str]]]
	r"""
	Parses string `f` as a :rfc:`822` conforming file and returns list of sections, each a dict mapping keys to lists of values.
	Splits file into multiple sections separated by blank line.

	:param f: The messate to parse.
	:returns: A list of dictionaries.

	.. note::
		For real Debian files, use the :py:mod:`debian.deb822` module from the `python-debian` package.

	>>> res = parseRfc822('Type: file\nFile: /etc/fstab\n\nType: Script\nScript: /bin/false\n')
	>>> res == [{'Type': ['file'], 'File': ['/etc/fstab']}, {'Type': ['Script'], 'Script': ['/bin/false']}]
	True
	>>> parseRfc822('')
	[]
	>>> parseRfc822('\n')
	[]
	>>> parseRfc822('\n\n')
	[]
	"""
	res = []  # type: List[Dict[str, List[str]]]
	ent = {}  # type: Dict[str, List[str]]
	for line in f.splitlines():
		if line:
			try:
				key, value = line.split(': ', 1)
			except ValueError:
				pass
			else:
				ent.setdefault(key, []).append(value)
		elif ent:
			res.append(ent)
			ent = {}
	if ent:
		res.append(ent)
	return res


if __name__ == '__main__':
	import doctest
	doctest.testmod()
