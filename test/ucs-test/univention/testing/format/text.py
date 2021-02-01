# vim: set fileencoding=utf-8 ft=python sw=4 ts=4 :
"""Format UCS Test results as simple text report."""

from __future__ import print_function

import curses
import time
import subprocess
import re
import sys
from weakref import WeakValueDictionary
try:
	from typing import IO  # noqa F401
except ImportError:
	pass

import univention.config_registry

from univention.testing.data import TestFormatInterface, TestCodes, TestCase, TestEnvironment, TestResult  # noqa F401

__all__ = ['Text', 'Raw']


class _Term(object):  # pylint: disable-msg=R0903

	"""Handle terminal formatting."""
	__ANSICOLORS = "BLACK RED GREEN YELLOW BLUE MAGENTA CYAN WHITE".split()
	# vt100.sgr0 contains a delay in the form of '$<2>'
	__RE_DELAY = re.compile(r'\$<\d+>[/*]?'.encode('utf-8'))

	def __init__(self, term_stream=sys.stdout):  # type: (IO[str]) -> None
		self.COLS = 80  # pylint: disable-msg=C0103
		self.LINES = 25  # pylint: disable-msg=C0103
		self.NORMAL = ''  # pylint: disable-msg=C0103
		for color in self.__ANSICOLORS:
			setattr(self, color, '')
		if not term_stream.isatty():
			return
		try:
			curses.setupterm()
		except TypeError:
			return
		self.COLS = curses.tigetnum('cols') or 80
		self.LINES = curses.tigetnum('lines') or 25
		self.NORMAL = _Term.__RE_DELAY.sub(b'', curses.tigetstr('sgr0') or b'')
		set_fg_ansi = curses.tigetstr('setaf')
		for color in self.__ANSICOLORS:
			i = getattr(curses, 'COLOR_%s' % color)
			val = set_fg_ansi and curses.tparm(set_fg_ansi, i) or ''
			setattr(self, color, val)


class Text(TestFormatInterface):

	"""
	Create simple text report.
	"""
	__term = WeakValueDictionary()

	def __init__(self, stream=sys.stdout):  # type: (IO[str]) -> None
		super(Text, self).__init__(stream)
		try:
			self.term = Text.__term[self.stream]
		except KeyError:
			self.term = Text.__term[self.stream] = _Term(self.stream)

	def begin_run(self, environment, count=1):  # type: (TestEnvironment, int) -> None
		"""Called before first test."""
		super(Text, self).begin_run(environment, count)
		now = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
		print("Starting %s ucs-test at %s to %s" %
			(count, now, environment.log.name), file=self.stream)
		try:
			ucs_test_version = subprocess.check_output(['/usr/bin/dpkg-query', '--showformat=${Version}', '--show', 'ucs-test-framework'])
		except subprocess.CalledProcessError:
			ucs_test_version = 'not installed'
		ucr = univention.config_registry.ConfigRegistry()
		ucr.load()
		print("UCS %s-%s-e%s ucs-test %s" % (ucr.get('version/version'), ucr.get('version/patchlevel'), ucr.get('version/erratalevel'), ucs_test_version), file=self.stream)

	def begin_section(self, section):  # type: (str) -> None
		"""Called before each section."""
		super(Text, self).begin_section(section)
		if section:
			header = " Section '%s' " % (section,)
			line = header.center(self.term.COLS, '=')
			print(line, file=self.stream)

	def begin_test(self, case, prefix=''):  # type: (TestCase, str) -> None
		"""Called before each test."""
		super(Text, self).begin_test(case, prefix)
		title = case.description or case.uid
		title = prefix + title.splitlines()[0]

		cols = self.term.COLS - TestCodes.MAX_MESSAGE_LEN - 1
		if cols < 1:
			cols = self.term.COLS
		while len(title) > cols:
			print(title[:cols], file=self.stream)
			title = title[cols:]
		ruler = '.' * (cols - len(title))
		print('%s%s' % (title, ruler), end=' ', file=self.stream)
		self.stream.flush()

	def end_test(self, result):  # type: (TestResult) -> None
		"""Called after each test."""
		reason = result.reason
		msg = TestCodes.MESSAGE.get(reason, reason)

		colorname = TestCodes.COLOR.get(result.reason, 'BLACK')
		color = getattr(self.term, colorname.upper(), '')

		print('%s%s%s' % (color, msg, self.term.NORMAL), file=self.stream)
		super(Text, self).end_test(result)

	def end_section(self):  # type: () -> None
		"""Called after each section."""
		if self.section:
			print(file=self.stream)
		super(Text, self).end_section()

	def format(self, result):  # type: (TestResult) -> None
		"""
		>>> te = TestEnvironment()
		>>> tc = TestCase('python/data.py')
		>>> tr = TestResult(tc, te)
		>>> tr.success()
		>>> Text().format(tr)
		"""
		self.begin_run(result.environment)
		self.begin_section('')
		self.begin_test(result.case)
		self.end_test(result)
		self.end_section()
		self.end_run()


class Raw(Text):
	"""
	Create simple text report with raw file names.
	"""

	def begin_test(self, case, prefix=''):  # type: (TestCase, str) -> None
		"""Called before each test."""
		super(Text, self).begin_test(case, prefix)
		title = prefix + case.uid

		cols = self.term.COLS - TestCodes.MAX_MESSAGE_LEN - 2
		if cols < 1:
			cols = self.term.COLS
		while len(title) > cols:
			print(title[:cols], file=self.stream)
			title = title[cols:]
		ruler = '.' * (cols - len(title))
		print('%s %s' % (title, ruler), end=' ', file=self.stream)
		self.stream.flush()


if __name__ == '__main__':
	import doctest
	doctest.testmod()
