# vim: set fileencoding=utf-8 ft=python sw=4 ts=4 :
"""Format UCS Test results as JUnit report."""

from __future__ import print_function

import errno
import os
import shutil
import sys
from codecs import encode as _encode
from datetime import datetime
from typing import IO, Any  # noqa: F401
from xml.sax.saxutils import XMLGenerator

import six

from univention.testing.codes import TestCodes
from univention.testing.data import TestCase, TestFormatInterface, TestResult  # noqa: F401
from univention.testing.format.text import Raw

__all__ = ['Junit']


def encode(string, *args):  # type: (str, *Any) -> str
	if six.PY2:
		return _encode(string, *args)
	return string


class Junit(TestFormatInterface):

	"""
	Create Junit report.
	<http://windyroad.org/dl/Open%20Source/JUnit.xsd>
	"""

	def __init__(self, stream=sys.stdout):  # type: (IO[str]) -> None
		super(Junit, self).__init__(stream)
		self.outdir = "test-reports"
		self.now = datetime.today()
		self.raw = Raw(stream)

	def begin_test(self, case, prefix=''):  # type: (TestCase, str) -> None
		"""Called before each test."""
		super(Junit, self).begin_test(case, prefix)
		self.now = datetime.today().replace(microsecond=0)
		print('\r', end='', file=self.stream)
		self.raw.begin_test(case, prefix)
		self.stream.flush()

	def end_run(self):
		print('')  # clear \r
		self.stream.flush()

	def end_test(self, result):  # type: (TestResult) -> None
		"""Called after each test."""
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
		classname = encode(result.case.uid.replace("/", "."))
		if classname.endswith('.py'):
			classname = classname[:-3]

		filename = os.path.join(self.outdir, '%s.xml' % (result.case.uid,))
		if result.case.is_pytest and os.path.exists(filename):
			return  # pytest itself already writes the junit file! create one if pytest did not

		dirname = os.path.dirname(filename)
		try:
			os.makedirs(dirname)
		except OSError as ex:
			if ex.errno != errno.EEXIST:
				raise

		if result.case.external_junit and os.path.exists(result.case.external_junit):
			shutil.copyfile(result.case.external_junit, filename)
			return

		with open(filename, 'w') as f_report:
			xml = XMLGenerator(f_report, encoding='utf-8')
			xml.startDocument()
			xml.startElement('testsuite', {
				'name': classname,
				'tests': '%d' % (1,),
				'failures': '%d' % (failures,),
				'errors': '%d' % (errors,),
				'time': '%0.3f' % (result.duration / 1000.0,),
				'disabled': '%d' % (disabled,),
				'skipped': '%d' % (skipped,),
				'timestamp': self.now.isoformat(),
				'hostname': os.uname()[1],
			})

			xml.startElement('properties', {})
			xml.startElement('property', {
				'name': 'hostname',
				'value': result.environment.hostname,
			})
			xml.endElement('property')
			xml.startElement('property', {
				'name': 'architecture',
				'value': result.environment.architecture,
			})
			xml.endElement('property')
			xml.startElement('property', {
				'name': 'role',
				'value': result.environment.role,
			})
			xml.endElement('property')
			xml.startElement('property', {
				'name': 'version',
				'value': '%s' % (result.environment.ucs_version,),
			})
			xml.endElement('property')
			if result.case.description:
				xml.startElement('property', {
					'name': 'description',
					'value': encode(result.case.description or result.case.uid),
				})
				xml.endElement('property')
			xml.endElement('properties')

			xml.startElement('testcase', {
				'name': result.environment.hostname,
				# 'assertions': '%d' % (0,),
				'time': '%0.3f' % (result.duration / 1000.0,),
				'classname': classname,
				# 'status': '???',
			})

			if skipped:
				try:
					mime, content = result.artifacts['check']
				except KeyError:
					msg = ''
				else:
					msg = '\n'.join(['%s' % (c,) for c in content])
				xml.startElement('skipped', {
					'message': msg,
				})
				xml.endElement('skipped')
			elif errors:
				xml.startElement('error', {
					'type': 'TestError',
					'message': '%s' % (result.result,),
				})
				xml.endElement('error')
			elif failures:
				msg = TestCodes.MESSAGE.get(result.reason, '')
				xml.startElement('failure', {
					'type': 'TestFailure',
					'message': '{} ({})'.format(msg, result.case.description or result.case.uid),
				})
				xml.endElement('failure')

			try:
				mime, content = result.artifacts['stdout']
			except KeyError:
				pass
			else:
				xml.startElement('system-out', {})
				xml.characters(self.utf8(content))
				xml.endElement('system-out')

			try:
				mime, content = result.artifacts['stderr']
			except KeyError:
				pass
			else:
				xml.startElement('system-err', {})
				xml.characters(self.utf8(content))
				xml.endElement('system-err')

			xml.endElement('testcase')
			xml.endElement('testsuite')
			xml.endDocument()
		super(Junit, self).end_test(result)

	def utf8(self, data):  # type: (Any) -> str
		if isinstance(data, six.text_type):
			data = data.encode('utf-8', 'replace').decode('utf-8')
		elif isinstance(data, bytes):
			data = data.decode('utf-8', 'replace').encode('utf-8')
		return data

	def format(self, result):  # type: (TestResult) -> None
		"""
		>>> from univention.testing.data import TestEnvironment
		>>> te = TestEnvironment()
		>>> tc = TestCase('python/data.py')
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
