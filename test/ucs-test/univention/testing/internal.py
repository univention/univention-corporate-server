"""
Internal functions for test finding and setup.
"""
# Copyright 2013-2022 Univention GmbH
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

import logging
import operator
import os
import re
import sys
from typing import Any, Callable, Dict, Iterable, List, NoReturn, Optional, Tuple, Union  # noqa: F401

import six

__all__ = [
	'TEST_BASE', 'LOG_BASE', 'setup_environment', 'setup_debug',
	'strip_indent', 'get_sections', 'get_tests', 'UCSVersion',
]

TEST_BASE = os.environ.get('UCS_TESTS', '/usr/share/ucs-test')
RE_SECTION = re.compile(r'^[0-9]{2}_(.+)$')
RE_PREFIX = re.compile(r'^[0-9]{2,3}_?(.+)')
RE_SUFFIX = re.compile(r'(?:~|\.(?:lib|sh|py[co]|bak|mo|po|png|jpg|jpeg|xml|csv|inst|uinst))$')
LOG_BASE = '/var/log/univention/test_%d.log'
S4CONNECTOR_INIT_SCRIPT = '/etc/init.d/univention-s4-connector'
INF = sys.maxsize


def setup_environment():  # type: () -> None
	"""Setup runtime environment."""
	os.environ['TESTLIBPATH'] = '/usr/share/ucs-test/lib'
	os.environ['PYTHONUNBUFFERED'] = '1'


def setup_debug(level):  # type: (int) -> None
	"""Setup Python logging."""
	level = _TAB.get(level, logging.DEBUG)
	FORMAT = '%(asctime)-15s ' + logging.BASIC_FORMAT
	logging.basicConfig(stream=sys.stderr, level=level, format=FORMAT)


_TAB = {  # pylint: disable-msg=W0612
	None: logging.WARNING,
	0: logging.WARNING,
	1: logging.INFO,
	2: logging.DEBUG,
}


def strip_indent(text):  # type: (str) -> str
	"""
	Strip common indent.
	"""
	lines = text.splitlines()
	while lines and not lines[0].strip():
		del lines[0]
	while lines and not lines[-1].strip():
		del lines[-1]
	indent = min((len(l) - len(l.lstrip()) for l in lines if l.lstrip()))
	return '\n'.join((l[indent:] for l in lines))


def get_sections():  # type: () -> Dict[str, str]
	"""
	Return dictionary section-name -> section-directory.
	"""
	section_dirs = os.listdir(TEST_BASE)
	sections = {dirname[3:]: TEST_BASE + os.path.sep + dirname for dirname in section_dirs if RE_SECTION.match(dirname)}
	return sections


def get_tests(sections):  # type: (Iterable[str]) -> Dict[str, List[str]]
	"""
	Return dictionary of section -> [filenames].
	"""
	result = {}
	logger = logging.getLogger('test.find')

	all_sections = get_sections()

	for section in sections:
		dirname = all_sections[section]
		logger.debug('Processing directory %s' % (dirname,))
		tests = []

		files = os.listdir(dirname)
		for filename in sorted(files):
			fname = os.path.join(dirname, filename)
			if not RE_PREFIX.match(filename):
				logger.debug('Skipped file %s' % (fname,))
				continue
			if RE_SUFFIX.search(filename):
				logger.debug('Skipped file %s' % (fname,))
				continue
			logger.debug('Adding file %s' % (fname,))
			tests.append(fname)

		if tests:
			result[section] = tests
	return result


class UCSVersion(object):  # pylint: disable-msg=R0903

	"""
	UCS version.

	>>> UCSVersion("1.0") < UCSVersion("2.0")
	True
	>>> UCSVersion("1.0") < UCSVersion("1.0")
	False
	>>> UCSVersion("1.0") <= UCSVersion("1.0")
	True
	>>> UCSVersion("2.0") <= UCSVersion("1.0")
	False
	>>> UCSVersion("1.0") == UCSVersion("1.0")
	True
	>>> UCSVersion("1.0") == UCSVersion("2.0")
	False
	>>> UCSVersion("1.0") != UCSVersion("2.0")
	True
	>>> UCSVersion("1.0") != UCSVersion("1.0")
	False
	>>> UCSVersion("1.0") >= UCSVersion("1.0")
	True
	>>> UCSVersion("1.0") >= UCSVersion("2.0")
	False
	>>> UCSVersion("2.0") > UCSVersion("1.0")
	True
	>>> UCSVersion("1.0") > UCSVersion("1.0")
	False
	>>> UCSVersion("1.0") == UCSVersion((1, 0, INF, INF))
	True
	>>> UCSVersion("1.0-0-0") == UCSVersion((1, 0, 0, 0))
	True
	>>> UCSVersion("")
	Traceback (most recent call last):
		...
	ValueError: Version does not match: ""
	>>> UCSVersion("0")
	Traceback (most recent call last):
		...
	ValueError: Version does not match: "0"
	>>> UCSVersion("1")
	Traceback (most recent call last):
		...
	ValueError: Version does not match: "1"
	>>> UCSVersion("1.2")
	UCSVersion('=1.2')
	>>> UCSVersion("1.2-3")
	UCSVersion('=1.2-3')
	>>> UCSVersion("1.2-3-4")
	UCSVersion('=1.2-3-4')
	>>> UCSVersion("1.2-3-4-5")
	Traceback (most recent call last):
		...
	ValueError: Version does not match: "1.2-3-4-5"
	>>> UCSVersion(None)
	Traceback (most recent call last):
		...
	TypeError: None
	>>> UCSVersion(1)
	Traceback (most recent call last):
		...
	TypeError: 1
	>>> UCSVersion(1.5)
	Traceback (most recent call last):
		...
	TypeError: 1.5
	"""
	RE_VERSION = re.compile(r"^(<|<<|<=|=|==|>=|>|>>)?([1-9][0-9]*)\.([0-9]+)(?:-([0-9]*)(?:-([0-9]+))?)?$")

	@classmethod
	def _parse(cls, ver, default_op='='):  # type: (str, str) -> Tuple[Callable[[Any, Any], Any], Tuple[int, int, int, int]]
		"""
		Parse UCS-version range and return two-tuple (operator, version)
		>>> UCSVersion._parse('11.22')  # doctest: +ELLIPSIS
		(<built-in function eq>, (11, 22, ..., ...))
		>>> UCSVersion._parse('11.22-33')  # doctest: +ELLIPSIS
		(<built-in function eq>, (11, 22, 33, ...))
		>>> UCSVersion._parse('11.22-33-44')
		(<built-in function eq>, (11, 22, 33, 44))
		>>> UCSVersion._parse('<1.2-3')  # doctest: +ELLIPSIS
		(<built-in function lt>, (1, 2, 3, ...))
		>>> UCSVersion._parse('<<1.2-3')  # doctest: +ELLIPSIS
		(<built-in function lt>, (1, 2, 3, ...))
		>>> UCSVersion._parse('<=1.2-3')  # doctest: +ELLIPSIS
		(<built-in function le>, (1, 2, 3, ...))
		>>> UCSVersion._parse('=1.2-3')  # doctest: +ELLIPSIS
		(<built-in function eq>, (1, 2, 3, ...))
		>>> UCSVersion._parse('==1.2-3')  # doctest: +ELLIPSIS
		(<built-in function eq>, (1, 2, 3, ...))
		>>> UCSVersion._parse('>=1.2-3')  # doctest: +ELLIPSIS
		(<built-in function ge>, (1, 2, 3, ...))
		>>> UCSVersion._parse('>>1.2-3')  # doctest: +ELLIPSIS
		(<built-in function gt>, (1, 2, 3, ...))
		>>> UCSVersion._parse('>1.2-3')  # doctest: +ELLIPSIS
		(<built-in function gt>, (1, 2, 3, ...))
		"""
		match = cls.RE_VERSION.match(ver)
		if not match:
			raise ValueError('Version does not match: "%s"' % (ver,))
		rel = match.group(1) or default_op
		parts = tuple([int(_) if _ else INF for _ in match.groups()[1:]])  # type: Tuple[int, int, int, int] # type: ignore
		if rel in ('<', '<<'):
			return (operator.lt, parts)
		if rel in ('<=',):
			return (operator.le, parts)
		if rel in ('=', '=='):
			return (operator.eq, parts)
		if rel in ('>=',):
			return (operator.ge, parts)
		if rel in ('>', '>>'):
			return (operator.gt, parts)
		raise ValueError('Unknown version match: "%s"' % (ver,))

	def __init__(self, ver):  # type: (Union[str, Tuple[int, int, int, int]]) -> None
		if isinstance(ver, six.string_types):
			self.rel, self.ver = self._parse(ver)
		elif isinstance(ver, tuple):
			self.rel = operator.eq
			assert all(isinstance(_, int) for _ in ver)
			self.ver = ver
		else:
			raise TypeError(ver)

	def __str__(self):  # type: () -> str
		rel = {
			operator.lt: '<',
			operator.le: '<=',
			operator.eq: '=',
			operator.ge: '>=',
			operator.gt: '>',
		}[self.rel]
		ver = '%d.%d' % self.ver[0:2]  # type: ignore
		skipped = 0
		for part in self.ver[2:]:
			skipped += 1
			if part != INF:
				ver += '%s%d' % ('-' * skipped, part)
				skipped = 0
		return '%s%s' % (rel, ver)

	def __repr__(self):  # type: () -> str
		return '%s(%r)' % (self.__class__.__name__, self.__str__(),)

	def __lt__(self, other):  # type: (Any) -> object
		return self.ver < other.ver if isinstance(other, UCSVersion) else NotImplemented

	def __le__(self, other):  # type: (Any) -> object
		return self.ver <= other.ver if isinstance(other, UCSVersion) else NotImplemented

	def __eq__(self, other):  # type: (Any) -> bool
		return self.ver == other.ver if isinstance(other, UCSVersion) else False

	def __ne__(self, other):  # type: (Any) -> bool
		return self.ver != other.ver if isinstance(other, UCSVersion) else False

	def __ge__(self, other):  # type: (Any) -> object
		return self.ver >= other.ver if isinstance(other, UCSVersion) else NotImplemented

	def __gt__(self, other):  # type: (Any) -> object
		return self.ver > other.ver if isinstance(other, UCSVersion) else NotImplemented

	def match(self, other):  # type: (UCSVersion) -> bool
		"""
		Check if other matches the criterion.
		>>> UCSVersion('>1.2-3').match(UCSVersion('1.2-4'))
		True
		>>> UCSVersion('>1.2-3').match(UCSVersion('1.2-3-4'))
		False
		>>> UCSVersion('>1.2-3-5').match(UCSVersion('1.2-3-4'))
		False
		>>> UCSVersion('>=1.2-3').match(UCSVersion('1.2-3-4'))
		True
		"""
		parts = [
			(other_ver, self_ver)
			for self_ver, other_ver in zip(self.ver, other.ver)
			if self_ver != INF and other_ver != INF
		]
		return self.rel(*zip(*parts))  # pylint: disable-msg=W0142


if __name__ == '__main__':
	import doctest
	doctest.testmod()

# vim: set fileencoding=utf-8 ft=python sw=4 ts=4 :
