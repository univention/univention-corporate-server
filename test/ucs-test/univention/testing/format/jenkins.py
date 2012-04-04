import sys
from univention.testing.data import TestResult
from xml.sax.saxutils import escape as escape_xml
from codecs import encode

__all__ = ['Jenkins']

class Jenkins(object):
	"""
	Create Jenkins report.
	<https://wiki.jenkins-ci.org/display/JENKINS/Monitoring+external+jobs>
	"""
	def __init__(self, stream=sys.stdout):
		self.stream = stream

	def begin_run(self, environment, count=1):
		pass

	def begin_section(self, section):
		pass

	def begin_test(self, case, prefix=''):
		pass

	def end_test(self, result):
		print >>self.stream, '<run>'
		if 'stdout' in result.artifacts:
			print >>self.stream, '<log encoding="hexBinary">%s</log>' % (encode(result.artifacts['stdout'], 'hex'),)
		print >>self.stream, '<result>%d</result>' % (result.result,)
		print >>self.stream, '<duration>%d</duration>' % (result.duration or -1,)
		print >>self.stream, '<displayName>%s</displayName>' % (escape_xml(result.case.id),)
		print >>self.stream, '<description>%s</description>' % (escape_xml(result.case.description or ''),)
		print >>self.stream, '</run>'

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
