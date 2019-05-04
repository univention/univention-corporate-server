# vim: set fileencoding=utf-8 ft=python sw=4 ts=4 :
"""Format UCS Test results as Jenkins report."""
from __future__ import print_function
import sys
from univention.testing.data import TestFormatInterface
from xml.sax.saxutils import escape as escape_xml
from codecs import encode

__all__ = ['Jenkins']


class Jenkins(TestFormatInterface):

	"""
	Create Jenkins report.
	<https://wiki.jenkins-ci.org/display/JENKINS/Monitoring+external+jobs>
	"""

	def __init__(self, stream=sys.stdout):
		super(Jenkins, self).__init__(stream)

	def end_test(self, result):
		"""Called after each test."""
		print('<run>', file=self.stream)
		try:
			mime, content = result.artifacts['stdout']
		except KeyError:
			pass
		else:
			print('<log encoding="hexBinary">%s</log>' % \
				(encode(content, 'hex'),), file=self.stream)
		print('<result>%d</result>' % (result.result,), file=self.stream)
		print('<duration>%d</duration>' % \
			(result.duration or -1,), file=self.stream)
		print('<displayName>%s</displayName>' % \
			(escape_xml(result.case.uid),), file=self.stream)
		print('<description>%s</description>' % \
			(escape_xml(result.case.description or ''),), file=self.stream)
		print('</run>', file=self.stream)
		super(Jenkins, self).end_test(result)

	def format(self, result):
		"""
		>>> from univention.testing.data import TestCase, TestEnvironment, \
						TestResult
		>>> te = TestEnvironment()
		>>> tc = TestCase()
		>>> tc.uid = 'python/data.py'
		>>> tr = TestResult(tc, te)
		>>> tr.success()
		>>> Jenkins().format(tr)
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
