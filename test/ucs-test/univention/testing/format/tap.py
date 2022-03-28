# vim: set fileencoding=utf-8 ft=python sw=4 ts=4 :
"""Format UCS Test results as Test Anything Protocol report."""

from __future__ import print_function

import sys
from typing import IO, Any  # noqa: F401

from univention.testing.codes import TestCodes
from univention.testing.data import TestEnvironment, TestFormatInterface, TestResult  # noqa: F401

__all__ = ['TAP']


class TAP(TestFormatInterface):

	"""
	Create simple Test-Anything-Protocol report.
	<http://testanything.org/wiki/index.php/Main_Page>
	"""

	def __init__(self, stream=sys.stdout):  # type: (IO[str]) -> None
		super(TAP, self).__init__(stream)

	def begin_run(self, environment, count=1):  # type: (TestEnvironment, int) -> None
		"""Called before first test."""
		super(TAP, self).begin_run(environment, count)
		print("1..%d" % (count,))

	def end_test(self, result):  # type: (TestResult) -> None
		"""Called after each test."""
		if result.result == TestCodes.RESULT_OKAY:
			prefix = 'ok'
			suffix = ''
		elif result.result == TestCodes.RESULT_SKIP:
			prefix = 'not ok'
			suffix = ' # skip'
		else:
			prefix = 'not ok'
			suffix = ''
		print('%s %s%s' % (prefix, result.case.uid, suffix), file=self.stream)
		super(TAP, self).end_test(result)

	def format(self, result):  # type: (TestResult) -> None
		"""
		>>> from univention.testing.data import TestCase
		>>> te = TestEnvironment()
		>>> tc = TestCase('python/data.py')
		>>> tr = TestResult(tc, te)
		>>> tr.success()
		>>> TAP().format(tr)
		1..1
		"""
		self.begin_run(result.environment)
		self.begin_section('')
		self.begin_test(result.case)
		self.end_test(result)
		self.end_section()
		self.end_run()


if __name__ == '__main__':
	import doctest
	doctest.testmod()
