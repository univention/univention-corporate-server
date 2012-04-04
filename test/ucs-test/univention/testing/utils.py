import sys
from os import listdir, environ
from re import compile
import os.path
import operator
import logging

__all__ = ['TEST_BASE', 'LOG_BASE', 'setup_environment', 'setup_debug', 'strip_indent', 'get_sections', 'get_tests', 'UCSVersion']

TEST_BASE = '/usr/share/ucs-test'
RE_SECTION = compile(r'^[0-9]{2}_(.+)$')
RE_PREFIX = compile(r'^[0-9]{2}(.+)')
RE_SUFFIX = compile(r'\.lib$|\.sh$|\.py[co]?$|\.bak$|~$')
LOG_BASE = '/var/log/univention/test_%d.log'

def setup_environment():
	"""Setup runtime environemnt."""
	os.environ['TESTLIBPATH'] = '/usr/share/ucs-test/lib'

def setup_debug(level):
	"""Setup Python logging."""
	level = setup_debug.TAB.get(level, logging.DEBUG)
	logging.basicConfig(stream=sys.stderr, level=level)
setup_debug.TAB = {
		None: logging.WARNING,
		0: logging.WARNING,
		1: logging.INFO,
		2: logging.DEBUG,
		}

def strip_indent(s):
	"""
	Strip common indent.
	"""
	lines = s.splitlines()
	while lines and not lines[0].strip():
		del lines[0]
	while lines and not lines[-1].strip():
		del lines[-1]
	indent = min((len(l) - len(l.lstrip()) for l in lines if l.lstrip()))
	return '\n'.join((l[indent:] for l in lines))

def get_sections():
	"""
	Return dictionary section-name -> section-directory.
	"""
	section_dirs = listdir(TEST_BASE)
	sections = dict([(dir[3:], TEST_BASE + os.path.sep + dir) for dir in section_dirs if RE_SECTION.match(dir)])
	return sections

def get_tests(sections):
	"""
	Return dictionary of section -> [filenames].
	"""
	result = {}
	logger = logging.getLogger('test.find')

	all_sections = get_sections()

	for section in sections:
		dir = all_sections[section]
		logger.debug('Processing directory %s' % (dir,))
		tests = []

		files = listdir(dir)
		for filename in sorted(files):
			fname = dir + os.path.sep + filename
			if not RE_PREFIX.match(filename):
				logger.debug('Skipped file %s' % (fname,))
				continue
			if RE_SUFFIX.match(filename):
				logger.debug('Skipped file %s' % (fname,))
				continue
			logger.debug('Adding file %s' % (fname,))
			tests.append(fname)

		if tests:
			result[section] = tests
	return result

class UCSVersion(object):
	"""
	UCS version.
	"""
	RE_VERSION = compile("^(<|<<|<=|=|==|>=|>|>>)?([1-9][0-9]*)\.([0-9]+)(?:-([0-9]*)(?:-([0-9]+))?)?$")

	@classmethod
	def _parse(cls, v, default_op='='):
		"""
		Parse UCS-version range and return two-tuple (operator, version)
		>>> UCSVersion._parse('11.22')
		(<built-in function eq>, (11, 22, None, None))
		>>> UCSVersion._parse('11.22-33')
		(<built-in function eq>, (11, 22, 33, None))
		>>> UCSVersion._parse('11.22-33-44')
		(<built-in function eq>, (11, 22, 33, 44))
		>>> UCSVersion._parse('<1.2-3')
		(<built-in function lt>, (1, 2, 3, None))
		>>> UCSVersion._parse('<<1.2-3')
		(<built-in function lt>, (1, 2, 3, None))
		>>> UCSVersion._parse('<=1.2-3')
		(<built-in function le>, (1, 2, 3, None))
		>>> UCSVersion._parse('=1.2-3')
		(<built-in function eq>, (1, 2, 3, None))
		>>> UCSVersion._parse('==1.2-3')
		(<built-in function eq>, (1, 2, 3, None))
		>>> UCSVersion._parse('>=1.2-3')
		(<built-in function ge>, (1, 2, 3, None))
		>>> UCSVersion._parse('>>1.2-3')
		(<built-in function gt>, (1, 2, 3, None))
		>>> UCSVersion._parse('>1.2-3')
		(<built-in function gt>, (1, 2, 3, None))
		"""
		m = cls.RE_VERSION.match(v)
		if not m:
			raise ValueError('Version does not match: "%s"' % (v,))
		op = m.group(1) or default_op
		ver = tuple(map(lambda v: {None:lambda n:None, '':lambda n:None}.get(v, int)(v), m.groups()[1:]))
		if op in ('<', '<<'):
			return (operator.lt, ver)
		if op in ('<=',):
			return (operator.le, ver)
		if op in ('=', '=='):
			return (operator.eq, ver)
		if op in ('>=',):
			return (operator.ge, ver)
		if op in ('>', '>>'):
			return (operator.gt, ver)
		raise ValueError('Unknown version match: "%s"' % (v,))

	def __init__(self, v):
		if isinstance(v, basestring):
			self.op, self.ver = self._parse(v)
		else:
			self.op = operator.eq
			self.ver = v

	def __str__(self):
		op = {
				operator.lt: '<',
				operator.le: '<=',
				operator.eq: '=',
				operator.ge: '>=',
				operator.gt: '>',
				}[self.op]
		ver = '%d.%d' % self.ver[0:2]
		d = 0
		for v in self.ver[2:]:
			d +=1
			if v is not None:
				ver += '%s%d' % ('-' * d, v)
				d = 0
		return '%s%s' % (op, ver)

	def __repr__(self):
		return '%s(%r)' % (self.__class__.__name__, self.__str__(),)

	def __cmp__(self, other):
		return cmp(self.ver, other.ver)

	def match(self, other):
		"""
		Check if other matches the criterion.
		>>> UCSVersion('>1.2-3').match(UCSVersion('1.2-4'))
		True
		>>> UCSVersion('>1.2-3').match(UCSVersion('1.2-3-4'))
		False
		>>> UCSVersion('>1.2-3-5').match(UCSVersion('1.2-3-4'))
		False
		"""
		l = [(o, s) for s, o in zip(self.ver, other.ver) if s is not None and o is not None]
		return self.op(*zip(*l))

if __name__ == '__main__':
	import doctest
	doctest.testmod()
