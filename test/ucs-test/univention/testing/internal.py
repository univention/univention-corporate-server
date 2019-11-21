"""
Internal functions for test finding and setup.
"""
from __future__ import print_function
# Copyright 2013-2019 Univention GmbH
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

import sys
import re
import os
import operator
import logging
import six
import subprocess

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
LISTENER_INIT_SCRIPT = '/etc/init.d/univention-directory-listener'


def package_installed(package):
	sys.stdout.flush()
	with open('/dev/null', 'w') as null:
		return (subprocess.call(['dpkg-query', '-W', package], stderr=null) == 0)


def fail(log_message=None, returncode=1):
	print('### FAIL ###')
	if log_message:
		print('%s\n###      ###' % log_message)
	sys.exit(returncode)


def setup_environment():
	"""Setup runtime environment."""
	os.environ['TESTLIBPATH'] = '/usr/share/ucs-test/lib'
	os.environ['PYTHONUNBUFFERED'] = '1'


def setup_debug(level):
	"""Setup Python logging."""
	level = setup_debug.TAB.get(level, logging.DEBUG)
	FORMAT = '%(asctime)-15s ' + logging.BASIC_FORMAT
	logging.basicConfig(stream=sys.stderr, level=level, format=FORMAT)


setup_debug.TAB = {  # pylint: disable-msg=W0612
	None: logging.WARNING,
	0: logging.WARNING,
	1: logging.INFO,
	2: logging.DEBUG,
}


def strip_indent(text):
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


def get_sections():
	"""
	Return dictionary section-name -> section-directory.
	"""
	section_dirs = os.listdir(TEST_BASE)
	sections = dict([(dirname[3:], TEST_BASE + os.path.sep + dirname) for dirname in section_dirs if RE_SECTION.match(dirname)])
	return sections


def get_tests(sections):
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
	"""
	RE_VERSION = re.compile("^(<|<<|<=|=|==|>=|>|>>)?([1-9][0-9]*)\.([0-9]+)(?:-([0-9]*)(?:-([0-9]+))?)?$")
	_CONVERTER = {
		None: lambda _: None,
		'': lambda _: None,
	}

	@classmethod
	def _parse(cls, ver, default_op='='):
		"""
		Parse UCS-version range and return two-tuple (operator, version)
		>>> UCSVersion._parse('11.22')
		(<built-in function eq>, (11, 22, None, None))
		>>> UCSVersion._parse('11.22-33')
		(<built-in function eq>, (11, 22, 33, None))
		>>> UCSVersion._parse('11.22-33-44')
		(<built-in function eq>, (11, 22, 33, 44))
		>>> UCSVersion._parse('<1.2-3')
		(<built-in function lt>, (1, 2, 3, None))
		>>> UCSVersion._parse('<<1.2-3')
		(<built-in function lt>, (1, 2, 3, None))
		>>> UCSVersion._parse('<=1.2-3')
		(<built-in function le>, (1, 2, 3, None))
		>>> UCSVersion._parse('=1.2-3')
		(<built-in function eq>, (1, 2, 3, None))
		>>> UCSVersion._parse('==1.2-3')
		(<built-in function eq>, (1, 2, 3, None))
		>>> UCSVersion._parse('>=1.2-3')
		(<built-in function ge>, (1, 2, 3, None))
		>>> UCSVersion._parse('>>1.2-3')
		(<built-in function gt>, (1, 2, 3, None))
		>>> UCSVersion._parse('>1.2-3')
		(<built-in function gt>, (1, 2, 3, None))
		"""
		match = cls.RE_VERSION.match(ver)
		if not match:
			raise ValueError('Version does not match: "%s"' % (ver,))
		rel = match.group(1) or default_op
		parts = tuple([UCSVersion._CONVERTER.get(_, int)(_) for _ in match.groups()[1:]])
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

	def __init__(self, ver):
		if isinstance(ver, six.string_types):
			self.rel, self.ver = self._parse(ver)
		else:
			self.rel = operator.eq
			self.ver = ver

	def __str__(self):
		rel = {
			operator.lt: '<',
			operator.le: '<=',
			operator.eq: '=',
			operator.ge: '>=',
			operator.gt: '>',
		}[self.rel]
		ver = '%d.%d' % self.ver[0:2]
		skipped = 0
		for part in self.ver[2:]:
			skipped += 1
			if part is not None:
				ver += '%s%d' % ('-' * skipped, part)
				skipped = 0
		return '%s%s' % (rel, ver)

	def __repr__(self):
		return '%s(%r)' % (self.__class__.__name__, self.__str__(),)

	def __cmp__(self, other):
		return cmp(self.ver, other.ver)  # noqa: F821

	def __eq__(self, other):
		return self.ver == other.ver

	def __ne__(self, other):
		return self.ver != other.ver

	def __lt__(self, other):
		return self.ver < other.ver

	def __le__(self, other):
		return self.ver <= other.ver

	def __gt__(self, other):
		return self.ver > other.ver

	def __ge__(self, other):
		return self.ver >= other.ver

	def match(self, other):
		"""
		Check if other matches the criterion.
		>>> UCSVersion('>1.2-3').match(UCSVersion('1.2-4'))
		True
		>>> UCSVersion('>1.2-3').match(UCSVersion('1.2-3-4'))
		False
		>>> UCSVersion('>1.2-3-5').match(UCSVersion('1.2-3-4'))
		False
		"""
		parts = [
			(other_ver, self_ver)
			for self_ver, other_ver in zip(self.ver, other.ver)
			if self_ver is not None and other_ver is not None]
		return self.rel(*zip(*parts))  # pylint: disable-msg=W0142


if __name__ == '__main__':
	import doctest
	doctest.testmod()

# vim: set fileencoding=utf-8 ft=python sw=4 ts=4 :
