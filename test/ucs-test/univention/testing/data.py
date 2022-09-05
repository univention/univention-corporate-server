# vim: set fileencoding=utf-8 ft=python sw=4 ts=4 :
"""Test case, environment, result and related classes."""

# pylint: disable-msg=R0902,W0201,R0903,E1101,E0611

from __future__ import print_function

import errno
import logging
import os
import re
import select
import signal
import sys
from datetime import datetime
from functools import reduce
from operator import and_, or_
from subprocess import PIPE, Popen, call
from time import time
from typing import IO, Any, Dict, Iterable, Iterator, List, Optional, Sequence, Set, Tuple, TypeVar  # noqa: F401

import apt
import six
import yaml

from univention.config_registry import ConfigRegistry
from univention.testing.codes import TestCodes
from univention.testing.errors import TestError
from univention.testing.internal import UCSVersion
from univention.testing.pytest import PytestRunner

__all__ = ['TestEnvironment', 'TestCase', 'TestResult', 'TestFormatInterface']

T = TypeVar("T")

# <http://stackoverflow.com/questions/1707890/>
ILLEGAL_XML_UNICHR = (
	(0x00, 0x08), (0x0B, 0x1F), (0x7F, 0x84), (0x86, 0x9F),
	(0xD800, 0xDFFF), (0xFDD0, 0xFDDF), (0xFFFE, 0xFFFF),
	(0x1FFFE, 0x1FFFF), (0x2FFFE, 0x2FFFF), (0x3FFFE, 0x3FFFF),
	(0x4FFFE, 0x4FFFF), (0x5FFFE, 0x5FFFF), (0x6FFFE, 0x6FFFF),
	(0x7FFFE, 0x7FFFF), (0x8FFFE, 0x8FFFF), (0x9FFFE, 0x9FFFF),
	(0xAFFFE, 0xAFFFF), (0xBFFFE, 0xBFFFF), (0xCFFFE, 0xCFFFF),
	(0xDFFFE, 0xDFFFF), (0xEFFFE, 0xEFFFF), (0xFFFFE, 0xFFFFF),
	(0x10FFFE, 0x10FFFF),
)
RE_ILLEGAL_XML = re.compile(u'[%s]' % u''.join((u'%s-%s' % (six.unichr(low), six.unichr(high)) for (low, high) in ILLEGAL_XML_UNICHR if low < sys.maxunicode)))


def checked_set(values):  # type: (Optional[Iterable[T]]) -> Set[T]
	if not isinstance(values, (list, tuple, set, frozenset)):
		raise TypeError('"%r" not a list or tuple' % values)
	return set(values)


class TestEnvironment(object):

	"""Test environment for running test cases.

	Handels system data, requirements checks, test output.
	"""

	logger = logging.getLogger('test.env')

	def __init__(self, interactive=True, logfile=None):  # type: (bool, Optional[str]) -> None
		self.exposure = 'safe'
		self.interactive = interactive
		self.timeout = 0

		self._load_host()
		self._load_ucr()
		self._load_join()
		self._load_apt()

		if interactive:
			self.tags_required = None  # type: Optional[Set[str]]
			self.tags_prohibited = None  # type: Optional[Set[str]]
		else:
			self.tags_required = set()
			self.tags_prohibited = {'SKIP', 'WIP'}

		self.log = open(logfile or os.path.devnull, 'a')

	def _load_host(self):  # type: () -> None
		"""Load host system information."""
		(_sysname, nodename, _release, _version, machine) = os.uname()
		self.hostname = nodename
		self.architecture = machine

	def _load_ucr(self):  # type: () -> None
		"""Load Univention Config Registry information."""
		self.ucr = ConfigRegistry()
		self.ucr.load()
		self.role = self.ucr.get('server/role', '')
		TestEnvironment.logger.debug('Role=%r' % self.role)

		version = self.ucr.get('version/version', '0.0').split('.', 1)
		major, minor = int(version[0]), int(version[1])
		patchlevel = int(self.ucr.get('version/patchlevel', 0))
		if (major, minor) < (3, 0):
			securitylevel = int(self.ucr.get('version/security-patchlevel', 0))
			self.ucs_version = UCSVersion((major, minor, patchlevel, securitylevel))
		else:
			erratalevel = int(self.ucr.get('version/erratalevel', 0))
			self.ucs_version = UCSVersion((major, minor, patchlevel, erratalevel))
		TestEnvironment.logger.debug('Version=%r' % self.ucs_version)

	def _load_join(self):  # type: () -> None
		"""Load join status."""
		with open(os.path.devnull, 'w+') as devnull:
			try:
				ret = call(
					('/usr/sbin/univention-check-join-status',),
					stdin=devnull, stdout=devnull, stderr=devnull)
				self.joined = ret == 0
			except OSError:
				self.joined = False
		TestEnvironment.logger.debug('Join=%r' % self.joined)

	def _load_apt(self):  # type: () -> None
		"""Load package information."""
		self.apt = apt.Cache()

	def dump(self, stream=sys.stdout):  # type: (IO[str]) -> None
		"""Dump environment information."""
		print('hostname: %s' % (self.hostname,), file=stream)
		print('architecture: %s' % (self.architecture,), file=stream)
		print('version: %s' % (self.ucs_version,), file=stream)
		print('role: %s' % (self.role,), file=stream)
		print('joined: %s' % (self.joined,), file=stream)
		print('tags_required: %s' % (' '.join(self.tags_required or set()) or '-',), file=stream)
		print('tags_prohibited: %s' % (' '.join(self.tags_prohibited or set()) or '-',), file=stream)
		print('timeout: %d' % (self.timeout,), file=stream)

	def tag(self, require=set(), ignore=set(), prohibit=set()):  # type: (Set[str], Set[str], Set[str]) -> None
		"""Update required, ignored, prohibited tags."""
		if self.tags_required is not None:
			self.tags_required -= set(ignore)
			self.tags_required |= set(require)
		if self.tags_prohibited is not None:
			self.tags_prohibited -= set(ignore)
			self.tags_prohibited |= set(prohibit)
		TestEnvironment.logger.debug('tags_required=%r tags_prohibited=%r' % (self.tags_required, self.tags_prohibited))

	def set_exposure(self, exposure):  # type: (str) -> None
		"""Set maximum allowed exposure level."""
		self.exposure = exposure

	def set_timeout(self, timeout):  # type: (int) -> None
		"""Set maximum allowed time for single test."""
		self.timeout = timeout


class _TestReader(object):  # pylint: disable-msg=R0903

	"""
	Read test case header lines starting with ##.
	"""

	def __init__(self, stream):  # type: (IO[bytes]) -> None
		self.stream = stream

	def read(self, size=-1):  # type: (int) -> bytes
		"""Read next line prefixed by '## '."""
		while True:
			line = self.stream.readline(size)
			if not line:
				return b''  # EOF
			if line.startswith(b'## '):
				return line[3:]
			if not line.startswith(b'#'):
				while line:
					line = self.stream.readline(size)


class Verdict(object):

	"""
	Result of a test, either successful or failed.
	"""

	INFO = 0  # Successful check, continue
	WARNING = 1  # Non-critical condition, may continue
	ERROR = 2  # Critical contion, abort

	logger = logging.getLogger('test.cond')

	def __init__(self, level, message, reason=None):  # type: (int, str, Optional[Any]) -> None
		self.level = level
		self.message = message
		self.reason = reason
		Verdict.logger.debug(self)

	def __bool__(self):  # type: () -> bool
		return self.level < Verdict.ERROR
	__nonzero__ = __bool__

	def __str__(self):  # type: () -> str
		return '%s: %s' % ('IWE'[self.level], self.message)

	def __repr__(self):  # type: () -> str
		return '%s(level=%r, message=%r)' % (self.__class__.__name__, self.level, self.message)


class Check(object):

	"""
	Abstract check.
	"""

	def check(self, environment):  # type: (TestEnvironment) -> Iterator[Verdict]
		"""Check if precondition to run test is met."""
		raise NotImplementedError()

	def pytest_args(self, environment):  # type: (TestEnvironment) -> List[str]
		return []


class CheckExecutable(Check):

	"""
	Check language.
	"""

	def __init__(self, filename):  # type: (str) -> None
		super(CheckExecutable, self).__init__()
		self.filename = filename

	def check(self, _environment):  # type: (TestEnvironment) -> Iterator[Verdict]
		"""Check environment for required executable."""
		if not os.path.isabs(self.filename):
			if self.filename.startswith('python') or self.filename.startswith('pytest') or self.filename.startswith('py.test'):
				self.filename = '/usr/bin/' + self.filename
			elif self.filename.endswith('sh'):
				self.filename = '/bin/' + self.filename
			else:
				yield Verdict(Verdict.ERROR, 'Unknown executable: %s' % (self.filename,), TestCodes.REASON_INSTALL)
				return
		if os.path.isfile(self.filename):
			yield Verdict(Verdict.INFO, 'Executable: %s' % (self.filename,))
		else:
			yield Verdict(Verdict.ERROR, 'Missing executable: %s' % (self.filename,), TestCodes.REASON_INSTALL)

	def __str__(self):  # type: () -> str
		return self.filename


class CheckVersion(Check):

	"""
	Check expected result of test for version.
	"""

	STATES = frozenset(('found', 'fixed', 'skip', 'run'))

	def __init__(self, versions):  # type: (Dict[str, str]) -> None
		super(CheckVersion, self).__init__()
		self.versions = versions
		self.state = 'run'

	def check(self, environment):  # type: (TestEnvironment) -> Iterator[Verdict]
		"""Check environment for expected version."""
		versions = []
		for version, state in self.versions.items():
			ucs_version = UCSVersion(version)
			if state not in CheckVersion.STATES:
				yield Verdict(Verdict.WARNING, 'Unknown state "%s" for version "%s"' % (state, version))
				continue
			versions.append((ucs_version, state))
		versions.sort()
		for (ucs_version, state) in versions:
			if ucs_version <= environment.ucs_version:
				self.state = state
		if self.state == 'skip':
			yield Verdict(Verdict.ERROR, 'Skipped for version %s' % (environment.ucs_version,), TestCodes.REASON_VERSION_MISMATCH)


class CheckTags(Check):

	"""
	Check for required / prohibited tags.
	"""

	def __init__(self, tags):  # type: (Iterable[str]) -> None
		super(CheckTags, self).__init__()
		self.tags = checked_set(tags)

	def check(self, environment):  # type: (TestEnvironment) -> Iterator[Verdict]
		"""Check environment for required / prohibited tags."""
		if environment.tags_required is None or environment.tags_prohibited is None:
			yield Verdict(Verdict.INFO, 'Tags disabled')
			return
		prohibited = self.tags & environment.tags_prohibited
		if prohibited:
			yield Verdict(Verdict.ERROR, 'De-selected by tag: %s' % (' '.join(prohibited),), TestCodes.REASON_ROLE_MISMATCH)
		elif environment.tags_required:
			required = self.tags & environment.tags_required
			if required:
				yield Verdict(Verdict.INFO, 'Selected by tag: %s' % (' '.join(required),))
			else:
				yield Verdict(Verdict.ERROR, 'De-selected by tag: %s' % (' '.join(environment.tags_required),), TestCodes.REASON_ROLE_MISMATCH)

	def pytest_args(self, environment):  # type: (TestEnvironment) -> List[str]
		args = []
		for tag in self.tags:
			args.extend(['--ucs-test-default-tags', tag])
		for tag in (environment.tags_required or []):
			if tag in ('SKIP', 'WIP'):
				continue
			args.extend(['--ucs-test-tags-required', tag])
		for tag in (environment.tags_prohibited or []):
			if tag in ('SKIP', 'WIP'):
				continue
			args.extend(['--ucs-test-tags-prohibited', tag])
		return args


class CheckRoles(Check):

	"""
	Check server role.
	"""

	ROLES = frozenset((
		'domaincontroller_master',
		'domaincontroller_backup',
		'domaincontroller_slave',
		'memberserver',
		'basesystem',
	))

	def __init__(self, roles_required=(), roles_prohibited=()):  # type: (Iterable[str], Iterable[str]) -> None
		super(CheckRoles, self).__init__()
		self.roles_required = checked_set(roles_required)
		self.roles_prohibited = checked_set(roles_prohibited)

	def check(self, environment):  # type: (TestEnvironment) -> Iterator[Verdict]
		"""Check environment for required / prohibited server role."""
		overlap = self.roles_required & self.roles_prohibited
		if overlap:
			yield Verdict(Verdict.WARNING, 'Overlapping roles: %s' % (' '.join(overlap),))
			roles = self.roles_required - self.roles_prohibited
		elif self.roles_required:
			roles = set(self.roles_required)
		else:
			roles = set(CheckRoles.ROLES) - set(self.roles_prohibited)

		unknown_roles = roles - CheckRoles.ROLES
		if unknown_roles:
			yield Verdict(Verdict.WARNING, 'Unknown roles: %s' % (' '.join(unknown_roles),))

		if environment.role not in roles:
			yield Verdict(Verdict.ERROR, 'Wrong role: %s not in (%s)' % (environment.role, ','.join(roles)), TestCodes.REASON_ROLE_MISMATCH)


class CheckJoin(Check):

	"""
	Check join status.
	"""

	def __init__(self, joined):  # type: (Optional[bool]) -> None
		super(CheckJoin, self).__init__()
		self.joined = joined

	def check(self, environment):  # type: (TestEnvironment) -> Iterator[Verdict]
		"""Check environment for join status."""
		if self.joined is None:
			yield Verdict(Verdict.INFO, 'No required join status')
		elif self.joined and not environment.joined:
			yield Verdict(Verdict.ERROR, 'Test requires system to be joined', TestCodes.REASON_JOIN)
		elif not self.joined and environment.joined:
			yield Verdict(Verdict.ERROR, 'Test requires system to be not joined', TestCodes.REASON_JOINED)
		else:
			yield Verdict(Verdict.INFO, 'Joined: %s' % (environment.joined,))


class CheckComponents(Check):

	"""
	Check for required / prohibited components.
	"""

	def __init__(self, components):  # type: (Dict[str, str]) -> None
		super(CheckComponents, self).__init__()
		self.components = components

	def check(self, environment):  # type: (TestEnvironment) -> Iterator[Verdict]
		"""Check environment for required / prohibited components."""
		for component, required in self.components.items():
			key = 'repository/online/component/%s' % (component,)
			active = environment.ucr.is_true(key, False)
			if required:
				if active:
					yield Verdict(Verdict.INFO, 'Required component %s active' % (component,))
				else:
					yield Verdict(Verdict.ERROR, 'Required component %s missing' % (component,), TestCodes.REASON_INSTALL)
			else:  # not required
				if active:
					yield Verdict(Verdict.ERROR, 'Prohibited component %s active' % (component,), TestCodes.REASON_INSTALLED)
				else:
					yield Verdict(Verdict.INFO, 'Prohibited component %s not active' % (component,))


class CheckPackages(Check):

	"""
	Check for required packages.
	"""

	def __init__(self, packages, packages_not):  # type: (Sequence[str], Sequence[str]) -> None
		super(CheckPackages, self).__init__()
		self.packages = packages
		self.packages_not = packages_not

	def check(self, environment):  # type: (TestEnvironment) -> Iterator[Verdict]
		"""Check environment for required / prohibited packages."""
		def check_disjunction(conjunction):
			"""Check is any of the alternative packages is installed."""
			for name, dep_version, dep_op in conjunction:
				try:
					pkg = environment.apt[name]
				except KeyError:
					yield Verdict(Verdict.ERROR, 'Package %s not found' % (name,), TestCodes.REASON_INSTALL)
					continue
				ver = pkg.installed
				if ver is None:
					yield Verdict(Verdict.ERROR, 'Package %s not installed' % (name,), TestCodes.REASON_INSTALL)
					continue
				if dep_version and not apt.apt_pkg.check_dep(ver.version, dep_op, dep_version):
					yield Verdict(Verdict.ERROR, 'Package %s version mismatch' % (name,), TestCodes.REASON_INSTALL)
					continue
				yield Verdict(Verdict.INFO, 'Package %s installed' % (name,))
				break

		for dependency in self.packages:
			deps = apt.apt_pkg.parse_depends(dependency)
			for conjunction in deps:
				conditions = list(check_disjunction(conjunction))
				success = reduce(or_, (bool(_) for _ in conditions), False)
				if success:
					for condition in conditions:
						if condition.level < Verdict.ERROR:
							yield condition
				else:
					for condition in conditions:
						yield condition

		for pkg in self.packages_not:
			try:
				p = environment.apt[pkg]
			except KeyError:
				continue
			if p.installed:
				yield Verdict(Verdict.ERROR, 'Package %s is installed, but should not be' % (pkg,), TestCodes.REASON_INSTALLED)
				break


class CheckExposure(Check):

	"""
	Check for signed exposure.
	"""

	STATES = ['safe', 'careful', 'dangerous']

	def __init__(self, exposure):  # type: (str) -> None
		super(CheckExposure, self).__init__()
		self.exposure = exposure

	def check(self, environment):  # type: (TestEnvironment) -> Iterator[Verdict]
		"""Check environment for permitted exposure level."""
		if self.exposure not in CheckExposure.STATES:
			yield Verdict(Verdict.WARNING, 'Unknown exposure: %s' % (self.exposure,))
			return
		if CheckExposure.STATES.index(self.exposure) > CheckExposure.STATES.index(environment.exposure):
			yield Verdict(Verdict.ERROR, 'Too dangerous: %s > %s' % (self.exposure, environment.exposure), TestCodes.REASON_DANGER)
		else:
			yield Verdict(Verdict.INFO, 'Safe enough: %s <= %s' % (self.exposure, environment.exposure))

	def pytest_args(self, environment):  # type: (TestEnvironment) -> List[str]
		args = []
		args.extend(['--ucs-test-exposure', environment.exposure.lower()])
		if self.exposure:
			args.extend(['--ucs-test-default-exposure', self.exposure.lower()])
		return args


class TestCase(object):

	"""Test case."""

	logger = logging.getLogger('test.case')
	RE_NL = re.compile(r'[\r\n]+'.encode('utf-8'))

	def __init__(self, filename):  # type: (str) -> None
		self.filename = os.path.abspath(filename)
		self.uid = os.path.sep.join(filename.rsplit(os.path.sep, 2)[-2:])

		self.exe = None  # type: Optional[CheckExecutable]
		self.args = []  # type: List[str]
		self.description = None  # type: Optional[str]
		self.bugs = set()  # type: Set[str]
		self.otrs = set()  # type: Set[str]
		self.timeout = None  # type: Optional[int]
		self.signaled = None  # type: Optional[int]
		self.is_pytest = False  # type: bool
		self.external_junit = None  # type: Optional[str]

	def load(self):  # type: () -> TestCase
		"""
		Load test case from stream.
		"""
		try:
			header = self.load_meta()
		except EnvironmentError as ex:
			TestCase.logger.critical(
				'Failed to read "%s": %s',
				self.filename, ex)
			raise TestError('Failed to open file')

		self.parse_meta(header)

		return self

	def load_meta(self):  # type: () -> Dict[str, Any]
		TestCase.logger.info('Loading test %s', self.filename)

		with open(self.filename, 'rb') as tc_file:
			firstline = tc_file.readline()
			if not firstline.startswith(b'#!'):
				raise TestError('Missing hash-bang')
			args = firstline.decode('utf-8').split(None)
			try:
				lang = args[1]
			except IndexError:
				lang = u''
			self.exe = CheckExecutable(lang)
			self.args = args[2:]

			reader = _TestReader(tc_file)
			try:
				header = yaml.safe_load(reader) or {}
			except yaml.scanner.ScannerError as ex:
				TestCase.logger.critical(
					'Failed to read "%s": %s',
					self.filename, ex,
					exc_info=True)
				raise TestError('Invalid test YAML data')

		return header

	def parse_meta(self, header):  # type: (Dict[str, Any]) -> None
		try:
			self.description = header.get('desc', '').strip()
			self.bugs = checked_set(header.get('bugs', []))
			self.otrs = checked_set(header.get('otrs', []))
			self.versions = CheckVersion(header.get('versions', {}))
			self.tags = CheckTags(header.get('tags', []))
			self.roles = CheckRoles(
				header.get('roles', []),
				header.get('roles-not', []))
			self.join = CheckJoin(header.get('join', None))
			self.components = CheckComponents(header.get('components', {}))
			self.packages = CheckPackages(header.get('packages', []), header.get('packages-not', []))
			self.exposure = CheckExposure(header.get('exposure', 'dangerous'))
			self.external_junit = header.get('external-junit', '').strip()
			try:
				self.timeout = int(header['timeout'])
			except LookupError:
				pass
		except (TypeError, ValueError) as ex:
			TestCase.logger.critical(
				'Tag error in "%s": %s',
				self.filename, ex,
				exc_info=True)
			raise TestError(ex)

		self.is_pytest = PytestRunner.is_pytest(self)

	def check(self, environment):  # type: (TestEnvironment) -> List[Check]
		"""
		Check if the test case should run.
		"""
		TestCase.logger.info('Checking test %s' % (self.filename,))
		if self.timeout is None:
			self.timeout = environment.timeout
		conditions = []
		conditions += list(self.exe.check(environment))
		conditions += list(self.versions.check(environment))
		conditions += list(self.tags.check(environment))
		conditions += list(self.roles.check(environment))
		conditions += list(self.components.check(environment))
		conditions += list(self.packages.check(environment))
		conditions += list(self.exposure.check(environment))
		return conditions

	def pytest_check(self, environment):  # type: (TestEnvironment) -> List[str]
		args = []
		args += self.exe.pytest_args(environment)
		args += self.versions.pytest_args(environment)
		args += self.tags.pytest_args(environment)
		args += self.roles.pytest_args(environment)
		args += self.components.pytest_args(environment)
		args += self.packages.pytest_args(environment)
		args += self.exposure.pytest_args(environment)
		return args

	def _run_tee(self, proc, result, stdout=sys.stdout, stderr=sys.stderr):
		# type: (Popen, TestResult, IO[str], IO[str]) -> None
		"""Run test collecting and passing through stdout, stderr:"""
		assert proc.stdout
		assert proc.stderr
		channels = {
			proc.stdout.fileno(): (proc.stdout, [], u'stdout', stdout, b'[]', bytearray()),
			proc.stderr.fileno(): (proc.stderr, [], u'stderr', stderr, b'()', bytearray()),
		}  # type: Dict[int, Tuple[IO[str], List, str, IO[str], bytes, bytearray]]
		combined = []
		next_kill = next_read = 0.0
		shutdown = False
		kill_sequence = self._terminate_proc(proc)
		while channels:
			current = time()
			if self.signaled == signal.SIGALRM:
				if next_kill <= current:
					try:
						next_kill = current + next(kill_sequence)
					except StopIteration:
						shutdown = True
						next_kill = current + 1.0
			elif self.signaled == signal.SIGCHLD:
				shutdown = True
				next_kill = current + 1.0

			delays = [max(0.0, t - current) for t in (next_kill, next_read) if t > 0.0]
			try:
				rlist, _wlist, _elist = select.select(list(channels), [], [], min(delays) if delays else None)
			except select.error as ex:
				if ex.args[0] == errno.EINTR:
					TestCase.logger.debug('select() interrupted by SIG%d rc=%r', self.signaled, proc.poll())
					continue
				raise

			next_read = 0.0
			for fd in rlist or list(channels):
				stream, log, name, out, paren, buf = channels[fd]

				if fd in rlist:
					data = os.read(fd, 1024)
					if six.PY3:
						out.buffer.write(data)  # type: ignore
					else:
						out.write(data)
					buf += data
					eof = data == b''
				else:
					data = b''
					eof = shutdown

				while buf:
					if eof:
						line = buf
						buf = bytearray()
					else:
						match = TestCase.RE_NL.search(buf)
						if not match:
							break
						line = buf[0:match.start()]
						del buf[0:match.end()]

					now = datetime.now().isoformat(' ')
					entry = b'%s %s\n' % (u'{1[0]}{0}{1[1]}'.format(now, paren).encode('ascii'), line.rstrip(b'\r\n'))
					log.append(entry)
					combined.append(entry)

				if eof:
					stream.close()
					del channels[fd]
					TestCase._attach(result, name, log)

				if buf and data:
					next_read = current + 0.1

		TestCase._attach(result, 'stdout', combined)

	@staticmethod
	def _terminate_proc(proc):
		try:
			for i in range(8):  # 2^8 * 100ms = 25.5s
				TestCase.logger.info('Sending %d. SIGTERM to %d', i + 1, proc.pid)
				rc = os.killpg(proc.pid, signal.SIGTERM)
				TestCase.logger.debug('rc=%s', rc)
				rc = proc.poll()
				TestCase.logger.debug('rc=%s', rc)
				if rc is not None:
					return
				yield (1 << i) / 10.0
			TestCase.logger.info('Sending SIGKILL to %d', proc.pid)
			os.killpg(proc.pid, signal.SIGKILL)
		except OSError as ex:
			if ex.errno != errno.ESRCH:
				TestCase.logger.warn(
					'Failed to kill process %d: %s', proc.pid, ex,
					exc_info=True)

	@staticmethod
	def _attach(result, part, content):
		"""Attach content."""
		text = b''.join(content)
		dirty = text.decode(sys.getfilesystemencoding(), 'replace')
		clean = RE_ILLEGAL_XML.sub(u'\uFFFD', dirty)
		result.attach(part, 'text/plain', clean)

	def _translate_result(self, result):  # type: (TestResult) -> None
		"""Translate exit code into result."""
		if result.result == TestCodes.RESULT_OKAY:
			result.reason = {
				'fixed': TestCodes.REASON_FIXED_EXPECTED,
				'found': TestCodes.REASON_FIXED_UNEXPECTED,
				'run': TestCodes.REASON_OKAY,
			}.get(self.versions.state, result.result)
		elif result.result == TestCodes.RESULT_SKIP:
			result.reason = TestCodes.REASON_SKIP
		else:
			if result.result in TestCodes.MESSAGE:
				result.reason = result.result
			else:
				result.reason = {
					'fixed': TestCodes.REASON_FAIL_UNEXPECTED,
					'found': TestCodes.REASON_FAIL_EXPECTED,
					'run': TestCodes.REASON_FAIL,
				}.get(self.versions.state, result.result)
		result.eofs = TestCodes.EOFS.get(result.reason, 'E')

	def run(self, result):  # type: (TestResult) -> None
		"""Run the test case and fill in result."""
		base = os.path.basename(self.filename)
		dirname = os.path.dirname(self.filename)
		cmd = [self.exe.filename, base] + self.args

		if self.is_pytest:
			cmd = PytestRunner.extend_command(self, cmd)
			cmd.extend(self.pytest_check(result.environment))

		time_start = datetime.now()

		print('\n*** BEGIN *** %r ***' % (
			cmd,), file=result.environment.log)
		print('*** %s *** %s ***' % (
			self.uid, self.description,), file=result.environment.log)
		print('*** START TIME: %s ***' % (
			time_start.strftime("%Y-%m-%d %H:%M:%S")), file=result.environment.log)
		result.environment.log.flush()

		# Protect wrapper from Ctrl-C as long as test case is running
		def handle_int(_signal, _frame):  # type: (int, Any) -> None
			"""Handle Ctrl-C signal."""
			result.result = TestCodes.RESULT_SKIP
			result.reason = TestCodes.REASON_ABORT
		old_sig_int = signal.signal(signal.SIGINT, handle_int)
		old_sig_alrm = signal.getsignal(signal.SIGALRM)

		def prepare_child():  # type: () -> None
			"""Setup child process."""
			os.setsid()
			signal.signal(signal.SIGINT, signal.SIG_IGN)

		try:
			TestCase.logger.debug('Running %r using %s in %s', cmd, self.exe, dirname)
			try:
				if result.environment.interactive:
					proc = Popen(
						cmd, executable=self.exe.filename,
						shell=False, stdout=PIPE, stderr=PIPE,
						close_fds=True, cwd=dirname,
						preexec_fn=os.setsid
					)
					to_stdout, to_stderr = sys.stdout, sys.stderr
				else:
					with open(os.path.devnull, 'rb') as devnull:
						proc = Popen(
							cmd, executable=self.exe.filename,
							shell=False, stdin=devnull,
							stdout=PIPE, stderr=PIPE, close_fds=True,
							cwd=dirname, preexec_fn=prepare_child
						)
					to_stdout = to_stderr = result.environment.log

				signal.signal(signal.SIGCHLD, self.handle_shutdown)
				if self.timeout:
					old_sig_alrm = signal.signal(signal.SIGALRM, self.handle_shutdown)
					signal.alarm(self.timeout)

				self._run_tee(proc, result, to_stdout, to_stderr)

				result.result = proc.wait()
			except OSError:
				TestCase.logger.error('Failed to execute %r using %s in %s', cmd, self.exe, dirname)
				raise
		finally:
			signal.alarm(0)
			signal.signal(signal.SIGALRM, old_sig_alrm)
			signal.signal(signal.SIGINT, old_sig_int)
			if result.reason == TestCodes.REASON_ABORT:
				raise KeyboardInterrupt()  # pylint: disable-msg=W1010

		time_end = datetime.now()
		time_delta = time_end - time_start

		print('*** END TIME: %s ***' % (
			time_end.strftime("%Y-%m-%d %H:%M:%S")), file=result.environment.log)
		print('*** TEST DURATION (H:MM:SS.ms): %s ***' % (
			time_delta), file=result.environment.log)
		print('*** END *** %d ***' % (
			result.result,), file=result.environment.log)
		result.environment.log.flush()

		result.duration = time_delta.total_seconds() * 1000
		TestCase.logger.info('Test %r using %s in %s returned %s in %s ms', cmd, self.exe, dirname, result.result, result.duration)

		self._translate_result(result)

	def handle_shutdown(self, signal, _frame):  # type: (int, Any) -> None
		TestCase.logger.debug('Received SIG%d', signal)
		self.signaled = signal


class TestResult(object):

	"""Test result from running a test case."""

	def __init__(self, case, environment=None):
		self.case = case
		self.environment = environment
		self.result = -1
		self.reason = None
		self.duration = 0
		self.artifacts = {}
		self.condition = None
		self.eofs = None
		self.is_pytest = False

	def dump(self, stream=sys.stdout):
		"""Dump test result data."""
		print('Case: %s' % (self.case.uid,), file=stream)
		print('Environment: %s' % (self.environment.hostname,), file=stream)
		print('Result: %d %s' % (self.result, self.eofs), file=stream)
		print('Reason: %s (%s)' % (self.reason, TestCodes.MESSAGE.get(self.reason, '')), file=stream)
		print('Duration: %d' % (self.duration or 0,), file=stream)
		for (key, (mime, content)) in self.artifacts.items():
			print('Artifact[%s]: %s %r' % (key, mime, content))

	def attach(self, key, mime, content):
		"""Attach artifact 'content' of mime-type 'mime'."""
		self.artifacts[key] = (mime, content)

	def success(self, reason=TestCodes.REASON_OKAY):
		"""Mark result as successful."""
		self.result = TestCodes.RESULT_OKAY
		self.reason = reason
		self.eofs = 'O'

	def fail(self, reason=TestCodes.REASON_FAIL):
		"""Mark result as failed."""
		self.result = TestCodes.RESULT_FAIL
		self.reason = reason
		self.eofs = 'F'

	def skip(self, reason=TestCodes.REASON_INTERNAL):
		"""Mark result as skipped."""
		self.result = TestCodes.RESULT_SKIP
		self.reason = self.reason or reason
		self.eofs = 'S'

	def check(self):
		"""Test conditions to run test."""
		conditions = self.case.check(self.environment)
		self.attach('check', 'python', conditions)
		self.condition = reduce(and_, (bool(_) for _ in conditions), True)
		reasons = [c.reason for c in conditions if c.reason is not None]
		if reasons:
			self.reason = reasons[0]
		else:
			self.reason = None
		return self.condition

	def run(self):
		"""Return test."""
		if self.condition is None:
			self.check()
		if self.condition:
			self.case.run(self)
		else:
			self.skip()
		return self


class TestFormatInterface(object):  # pylint: disable-msg=R0921

	"""Format UCS Test result."""

	def __init__(self, stream=sys.stdout):  # type: (IO[str]) -> None
		self.stream = stream  # type: IO[str]
		self.environment = None  # type: Optional[TestEnvironment]
		self.count = 0
		self.section = ''
		self.case = None  # type: Optional[TestCase]
		self.prefix = ''

	def begin_run(self, environment, count=1):  # type: (TestEnvironment, int) -> None
		"""Called before first test."""
		self.environment = environment
		self.count = count

	def begin_section(self, section):  # type: (str) -> None
		"""Called before each section."""
		self.section = section

	def begin_test(self, case, prefix=''):  # type: (TestCase, str) -> None
		"""Called before each test."""
		self.case = case
		self.prefix = prefix

	def end_test(self, result):  # type: (TestResult) -> None
		"""Called after each test."""
		self.case = None
		self.prefix = ''

	def end_section(self):  # type: () -> None
		"""Called after each section."""
		self.section = ''

	def end_run(self):  # type: () -> None
		"""Called after all test."""
		self.environment = None
		self.count = 0

	def format(self, result):  # type: (TestResult) -> None
		"""Format single test."""
		raise NotImplementedError()


def __run_test(filename):  # type: (str) -> None
	"""Run local test."""
	test_env = TestEnvironment()
	# test_env.dump()
	test_case = TestCase().load(filename)
	# try:
	# 	test_case.check(te)
	# except TestConditionError, ex:
	# 	for msg in ex:
	# 		print msg
	test_result = TestResult(test_case, test_env)
	test_result.dump()


if __name__ == '__main__':
	import doctest
	doctest.testmod()
	# __run_test('tst3')
