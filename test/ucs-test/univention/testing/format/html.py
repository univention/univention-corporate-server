# vim: set fileencoding=utf-8 ft=python sw=4 ts=4 :
"""Format UCS Test results as HTML."""
from __future__ import print_function
import sys
from univention.testing.codes import TestCodes
from xml.sax.saxutils import escape as escape_xml
from univention.testing.data import TestFormatInterface

__all__ = ['HTML']

URI_BUG = 'https://forge.univention.org/bugzilla/show_bug.cgi?id=%s'
URI_OTRS = 'https://gorm.knut.univention.de/otrs/index.pl?' + \
	'Action=AgentTicketSearch&Subaction=Search&TicketNumber=%s'


class HTML(TestFormatInterface):

	"""
	Create simple HTML report.
	"""

	def __init__(self, stream=sys.stdout):
		super(HTML, self).__init__(stream)

	def begin_run(self, environment, count=1):
		"""Called before first test."""
		super(HTML, self).begin_run(environment, count)
		print('<html>', file=self.stream)
		print('<head>', file=self.stream)
		print('<title>ucs-test</title>', file=self.stream)
		print('</head>', file=self.stream)
		print('<body>', file=self.stream)

	def begin_section(self, section):
		"""Called before each section."""
		super(HTML, self).begin_section(section)
		print('<h2>Section %s</h2>' % (escape_xml(section),), file=self.stream)
		print('<table>', file=self.stream)

	def end_test(self, result):
		"""Called after each test."""
		title = escape_xml(result.case.uid)
		if result.case.description:
			title = '<span title="%s">%s</span>' % \
				(title, escape_xml(result.case.description))
		if result.case.bugs or result.case.otrs:
			links = []
			links += [
				'<a href="%s">Bug #%d</a>' %
				(escape_xml(URI_BUG % bug), bug)
				for bug in result.case.bugs]
			links += [
				'<a href="%s">OTRS #%d</a>' %
				(escape_xml(URI_OTRS % tick), tick)
				for tick in result.case.otrs]
			title = '%s (%s)' % (title, ', '.join(links))
		msg = TestCodes.MESSAGE.get(result.reason, TestCodes.REASON_INTERNAL)
		colorname = TestCodes.COLOR.get(result.reason, 'BLACK')
		msg = '<span style="color:%s;">%s</span>' % \
			(colorname.lower(), escape_xml(msg))
		print('<tr><td>%s</td><td>%s</td></tr>' % (title, msg), file=self.stream)
		super(HTML, self).end_test(result)

	def end_section(self):
		"""Called after each section."""
		print('</table>', file=self.stream)
		super(HTML, self).end_section()

	def end_run(self):
		"""Called after all test."""
		print('</body>', file=self.stream)
		print('</html>', file=self.stream)
		super(HTML, self).end_run()

	def format(self, result):
		"""Format single test.

		>>> from univention.testing.data import TestCase, TestEnvironment, \
						TestResult
		>>> te = TestEnvironment()
		>>> tc = TestCase()
		>>> tc.uid = 'python/data.py'
		>>> tr = TestResult(tc, te)
		>>> tr.success()
		>>> HTML().format(tr)
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
