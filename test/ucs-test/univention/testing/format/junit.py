import sys
from univention.testing.data import TestResult
from univention.testing.codes import TestCodes
from xml.sax.saxutils import escape as escape_xml, XMLGenerator
from codecs import encode
from datetime import datetime
import os
import errno

__all__ = ['Junit']

class Junit(object):
	"""
	Create Junit report.
	<http://windyroad.org/dl/Open%20Source/JUnit.xsd>
	"""
	def __init__(self, stream=sys.stdout):
		self.outdir = "test-reports"
		self.section = ''
		self.now = 0

	def begin_run(self, environment, count=1):
		pass

	def begin_section(self, section):
		self.section = section

	def begin_test(self, case, prefix=''):
		self.now = datetime.today()

	def end_test(self, result):
		failures = errors = skipped = disabled = 0
		if result.eofs == 'O':
			pass
		elif result.eofs == 'S':
			skipped = 1
		elif result.eofs == 'F':
			failures = 1
		elif result.eofs == 'E':
			errors = 1
		else:
			errors = 1

		fn = os.path.join(self.outdir, '%s.xml' % (result.case.id,))
		dirname = os.path.dirname(fn)
		try:
			os.makedirs(dirname)
		except OSError, e:
			if e.errno != errno.EEXIST:
				raise
		f = open(fn, 'w')
		try:
			w = XMLGenerator(f, encoding='utf-8')
			w.startDocument()
			w.startElement('testsuite', {
				'name': encode(result.case.description or result.case.id),
				'tests': '%d' % (1,),
				'failures': '%d' % (failures,),
				'errors': '%d' % (errors,),
				'time': '%0.3f' % (result.duration / 1000.0,),
				'disabled': '%d' % (disabled,),
				'skipped': '%d' % (skipped,),
				'timestamp': self.now.isoformat(),
				'hostname': os.uname()[1],
				'id': result.case.id,
				'package': self.section,
				})

			w.startElement('properties', {})
			w.startElement('property', {
				'name': 'hostname',
				'value': result.environment.hostname,
				})
			w.endElement('property')
			w.startElement('property', {
				'name': 'architecture',
				'value': result.environment.architecture,
				})
			w.endElement('property')
			w.startElement('property', {
				'name': 'role',
				'value': result.environment.role,
				})
			w.endElement('property')
			w.startElement('property', {
				'name': 'version',
				'value': '%s' % (result.environment.ucs_version,),
				})
			w.endElement('property')
			w.endElement('properties')

			w.startElement('testcase', {
				'name': encode(result.case.description or result.case.id),
				#'assertions': '%d' % (0,),
				'time': '%0.3f' % (result.duration / 1000.0,),
				'classname': result.case.id,
				#'status': 'FIXME',
				})

			if skipped:
				w.startElement('skipped', {})
				try:
					mime, content = result.artifacts['check']
					msg = '\n'.join(['%s' % (c,) for c in content])
					w.characters(msg)
				except KeyError, e:
					pass
				w.endElement('skipped')
			elif errors:
				w.startElement('error', {
					'type': 'TestError',
					'message': '%s' % (result.result,),
					})
				w.endElement('error')
			elif failures:
				msg = TestResult.MESSAGE.get(result.reason, '')
				w.startElement('failure', {
					'type': 'TestFailure',
					'message': msg,
					})
				w.endElement('failure')

			try:
				mime, content = result.artifacts['stdout']
				w.startElement('system-out', {})
				w.characters(content)
				w.endElement('system-out')
			except KeyError, e:
				pass

			try:
				mime, content = result.artifacts['stderr']
				w.startElement('system-err', {})
				w.characters(content)
				w.endElement('system-err')
			except KeyError, e:
				pass

			w.endElement('testcase')
			w.endElement('testsuite')
			w.endDocument()
		finally:
			f.close()

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
		>>> Junit().format(tr)
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
