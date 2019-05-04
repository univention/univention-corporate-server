# vim: set fileencoding=utf-8 ft=python sw=4 ts=4 :
"""Format UCS Test results as Test Anything Protocol report."""
from __future__ import print_function
import sys
from univention.testing.data import TestFormatInterface
from univention.testing.codes import TestCodes

__all__ = ['TAP']


class TAP(TestFormatInterface):

	"""
	Create simple Test-Anything-Protocol report.
	<http://testanything.org/wiki/index.php/Main_Page>
	"""

	def __init__(self, stream=sys.stdout):
		super(TAP, self).__init__(stream)

	def begin_run(self, environment, count=1):
		"""Called before first test."""
		super(TAP, self).begin_run(environment, count)
		print("1..%d" % (count,))

	def end_test(self, result):
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

	def format(self, result):
		"""
		>>> from univention.testing.data import TestCase, TestEnvironment, \
						TestResult
		>>> te = TestEnvironment()
		>>> tc = TestCase()
		>>> tc.uid = 'python/data.py'
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
