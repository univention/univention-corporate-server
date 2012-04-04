import sys
from univention.testing.data import TestResult
from univention.testing.codes import TestCodes

__all__ = ['TAP']

class TAP(object):
	"""
	Create simple Test-Anything-Protocol report.
	<http://testanything.org/wiki/index.php/Main_Page>
	"""
	def __init__(self, stream=sys.stdout):
		self.stream = stream

	def begin_run(self, environment, count=1):
		print "1..%d" % (count,)

	def begin_section(self, section):
		pass

	def begin_test(self, case, prefix=''):
		pass

	def end_test(self, result):
		if result.result == TestCodes.RESULT_OKAY:
			prefix = 'ok'
			suffix = ''
		elif result.result == TestCodes.RESULT_SKIP:
			prefix = 'not ok'
			suffix = ' # skip'
		else:
			prefix = 'not ok'
			suffix = ''
		print >>self.stream, '%s %s%s' % (prefix, result.case.id, suffix)

	def end_section(self):
		pass

	def end_run(self):
		pass

	def format(self, result):
		"""
		>>> from univention.testing.data import TestCase, TestEnvironment
		>>> te = TestEnvironment()
		>>> tc = TestCase()
		>>> tc.id = 'python/data.py'
		>>> tr = TestResult(tc, te)
		>>> tr.success()
		>>> TAP().format(tr)
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
