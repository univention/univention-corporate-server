import sys
from univention.testing.data import TestResult
import curses
import time
from weakref import WeakValueDictionary
from re import compile

__all__ = ['Text']

class _Term(object):
	__ANSICOLORS = "BLACK RED GREEN YELLOW BLUE MAGENTA CYAN WHITE".split()

	def __init__(self, term_stream=sys.stdout):
		self.COLS = 80
		self.LINES = 25
		self.NORMAL = ''
		for color in self.__ANSICOLORS:
			setattr(self, color, '')
		if not term_stream.isatty():
			return
		try:
			curses.setupterm()
		except TypeError, e:
			return
		RE = compile(r'\$<\d+>[/*]?') # vt100.sgr0 contains a delay in the form of '$<2>'
		self.COLS = curses.tigetnum('cols') or 80
		self.LINES = curses.tigetnum('lines') or 25
		self.NORMAL = RE.sub('', curses.tigetstr('sgr0') or '')
		set_fg_ansi = curses.tigetstr('setaf')
		for color in self.__ANSICOLORS:
			i = getattr(curses, 'COLOR_%s' % color)
			val = set_fg_ansi and curses.tparm(set_fg_ansi, i) or ''
			setattr(self, color, val)

class Text(object):
	"""
	Create simple text report.
	"""
	__term = WeakValueDictionary()

	def __init__(self, stream=sys.stdout):
		self.stream = stream
		try:
			self.term = Text.__term[self.stream]
		except KeyError, e:
			self.term = Text.__term[self.stream] = _Term(self.stream)

	def begin_run(self, environment, count=1):
		now = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
		print >>self.stream, "Starting %s ucs-test at %s to %s" % (count, now, environment.log.name)

	def begin_section(self, section):
		self.section = section
		if section:
			header = " Section '%s' " % (section,)
			line = header.center(self.term.COLS, '=')
			print >>self.stream, line

	def begin_test(self, case, prefix=''):
		title = case.description or case.id
		title = prefix + title.splitlines()[0]

		cols = self.term.COLS - TestResult.MAX_MESSAGE_LEN - 1
		if cols < 1:
			cols = self.term.COLS
		while len(title) > cols:
			print >>self.stream, title[:cols]
			title = title[cols:]
		ruler = '.' * (cols - len(title))
		print >>self.stream, '%s%s' % (title, ruler),
		self.stream.flush()

	def end_test(self, result):
		reason = result.reason
		msg = TestResult.MESSAGE.get(reason, reason)

		colorname = TestResult.COLOR.get(result.reason, 'BLACK')
		color = getattr(self.term, colorname.upper(), '')

		print >>self.stream, '%s%s%s' % (color, msg, self.term.NORMAL)

	def end_section(self):
		if self.section:
			print >>self.stream
		del self.section

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
		>>> Text().format(tr)
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
