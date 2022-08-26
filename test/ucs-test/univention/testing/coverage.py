"""Code coverage measurement for ucs-test"""

from __future__ import absolute_import, print_function

import atexit
import distutils.spawn
import os
import signal
import subprocess
import time
from argparse import ArgumentParser, Namespace, _ArgumentGroup  # noqa: F401
from typing import Any, Callable, List  # noqa: F401

import six


class MissingCoverage(Exception):
	pass


class Coverage(object):

	COVERAGE_PTH = '/usr/lib/python2.7/dist-packages/ucstest-coverage.pth' if six.PY2 else '/usr/lib/python3/dist-packages/ucstest-coverage.pth'
	COVERAGE_PTH_CONTENT = '''import univention.testing.coverage; univention.testing.coverage.Coverage.startup()'''
	COVERAGE_DEBUG_PATH = '/tmp/ucs-test-coverage'
	COVERAGE_DEBUG = os.path.exists(COVERAGE_DEBUG_PATH)

	coverage = None

	def __init__(self, options):
		# type: (Namespace) -> None
		self.coverage_config = options.coverage_config
		self.branch_coverage = options.branch_coverage
		self.coverage = options.coverage
		self.coverage_sources = options.coverage_sources or ['univention']
		self.services = options.coverage_restart_services or [
			'univention-management-console-server',
			'univention-management-console-web-server',
			'univention-s4-connector',
			'univention-directory-listener',
			'univention-portal-server',
			'univention-directory-manager-rest',
		]
		self.show_missing = options.coverage_show_missing
		self.output_directory = options.coverage_output_directory

		try:
			subprocess.check_call(
				["dpkg", "-l", "python-ucs-school"],
				stderr=open("/dev/null", "a"),
				stdout=open("/dev/null", "a")
			)
			self.coverage_sources.append('ucsschool')

			subprocess.check_call(
				["dpkg", "-l", "ucs-school-import-http-api"],
				stderr=open("/dev/null", "a"),
				stdout=open("/dev/null", "a")
			)
			self.services.extend([
				'celery-worker-ucsschool-import',
				'ucs-school-import-http-api',
			])
		except subprocess.CalledProcessError:
			pass

		if self.coverage and options.coverage_debug:
			with open(self.COVERAGE_DEBUG_PATH, 'w'):
				self.COVERAGE_DEBUG = True

	def start(self):
		# type: () -> None
		"""Start measuring of coverage. Only called by ucs-test-framework once. Sets up the configuration."""
		if not self.coverage:
			return
		self.write_config_file()
		os.environ['COVERAGE_PROCESS_START'] = self.coverage_config
		self.restart_python_services()

	def write_config_file(self):
		# type: () -> None
		"""Write a Python .pth file which is invoked before any Python process"""
		with open(self.COVERAGE_PTH, 'w') as fd:
			fd.write(self.COVERAGE_PTH_CONTENT)

		with open(self.coverage_config, 'w') as fd:
			fd.write('''[run]
data_file = {data_file}
branch = {branch}
parallel = True
source = {source}
[report]
ignore_errors = True
show_missing = {show_missing}
omit = handlers/ucstest
	syntax.d/*
	hooks.d/*
[html]
directory = {directory}
'''.format(
				data_file=os.path.join(os.path.dirname(self.coverage_config), '.coverage'),
				branch=repr(self.branch_coverage),
				source='\n\t'.join(self.coverage_sources),
				show_missing=self.show_missing,
				directory=self.output_directory,
			))

	def restart_python_services(self):
		# type: () -> None
		"""Restart currently running Python services, so that they start/stop measuring code"""
		for service in self.services:
			try:
				subprocess.call(['/usr/sbin/service', service, 'restart'])
			except EnvironmentError:
				pass
		try:
			subprocess.call(['pkill', '-f', 'python.*univention-cli-server'])
		except EnvironmentError:
			pass

	def stop(self):
		# type: () -> None
		"""Stop coverage measuring. Only called by ucs-test-framework once. Stores the results."""
		if not self.coverage:
			return

		# stop all services, so that their atexit-handler/signal handler stores the result before evaluating the result
		if os.path.exists(self.COVERAGE_PTH):
			os.remove(self.COVERAGE_PTH)
		self.restart_python_services()

		for exe in ("coverage", "python3-coverage", "python-coverage"):
			coverage_bin = distutils.spawn.find_executable(exe)
			if coverage_bin:
				break
		else:
			raise MissingCoverage()
		subprocess.call([coverage_bin, '--version'])
		subprocess.call([coverage_bin, 'combine'])
		subprocess.call([coverage_bin, 'html'])
		subprocess.call([coverage_bin, 'report'])
		subprocess.call([coverage_bin, 'erase'])
		if os.path.exists(self.coverage_config):
			os.remove(self.coverage_config)

	@classmethod
	def get_argument_group(cls, parser):
		# type: (ArgumentParser) -> _ArgumentGroup
		"""The option group for ucs-test-framework"""
		coverage_group = parser.add_argument_group('Code coverage measurement options')
		coverage_group.add_argument("--with-coverage", dest="coverage", action='store_true')
		coverage_group.add_argument("--coverage-config", default=os.path.abspath(os.path.expanduser('~/.coveragerc')))  # don't use this, doesn't work!
		coverage_group.add_argument("--branch-coverage", action='store_true')
		coverage_group.add_argument('--coverage-sources', action='append', default=[])
		coverage_group.add_argument("--coverage-debug", action='store_true')
		coverage_group.add_argument('--coverage-restart-services', action='append', default=[])
		coverage_group.add_argument('--coverage-show-missing', action='store_true')
		coverage_group.add_argument("--coverage-output-directory", default=os.path.abspath(os.path.expanduser('~/htmlcov')))
		return coverage_group

	@classmethod
	def is_candidate(cls, argv):
		# type: (List[str]) -> bool
		if os.getuid():
			return False
		exe = os.path.basename(argv[0])
		if exe not in {'python', 'python2', 'python2.7', 'python3', 'python3.5', 'python3.7'}:
			return False
		if not any(s in arg for arg in argv for s in {'univention', 'udm', 'ucs', 'ucr'}):
			cls.debug_message('skip non-ucs process', argv)
			return False
		if any(s in arg for arg in argv[2:] for s in {'listener', 'notifier'}):
			# we don't need to cover the listener currently. some tests failed, maybe because of measuring the listener?
			cls.debug_message('skip UDL/UDN', argv)
			return False
		return True

	@classmethod  # noqa: C901
	def startup(cls):
		# type: () -> None
		"""Startup function which is invoked by every(!) Python process during coverage measurement. If the process is relevant we start measuring coverage."""
		argv = open('/proc/%s/cmdline' % os.getpid()).read().split('\x00')
		if not cls.is_candidate(argv):
			return

		cls.debug_message('START', argv)
		atexit.register(lambda: cls.debug_message('STOP'))

		if not os.environ.get('COVERAGE_PROCESS_START'):
			os.environ["COVERAGE_PROCESS_START"] = os.path.abspath(os.path.expanduser('~/.coveragerc'))
			cls.debug_message('ENVIRON WAS CLEARED BY PARENT PROCESS', argv)

		import coverage
		cov = coverage.process_startup()
		if not cov:
			cls.debug_message('no coverage startup (already started?, environ cleared?): %r' % (os.environ.get('COVERAGE_PROCESS_START'),))
			return

		cls.coverage = cov

		# FIXME: univention-cli-server calls os.fork() which causes the coverage measurement not to start in the forked process
		# https://github.com/nedbat/coveragepy/issues/310  # Coverage fails with os.fork and os._exit
		osfork = getattr(os, 'fork')

		def fork(*args, **kwargs):
			# type: (*Any, **Any) -> int
			pid = osfork(*args, **kwargs)
			if pid == 0:
				cls.debug_message('FORK CHILD')
				cls.startup()
			else:
				cls.debug_message('FORK PARENT')
				cls.stop_measurement(True)
			return pid
		os.fork = fork

		# https://github.com/nedbat/coveragepy/issues/43  # Coverage measurement fails on code containing os.exec* methods
		# if the process calls one of the process-replacement functions the coverage must be started in the new process
		for method in ['execl', 'execle', 'execlp', 'execlpe', 'execv', 'execve', 'execvp', 'execvpe', '_exit']:
			if isinstance(getattr(os, method), StopCoverageDecorator):
				continue  # restarted in the same process (e.g. os.fork())
			setattr(os, method, StopCoverageDecorator(getattr(os, method)))

		# There are test cases which e.g. kill the univention-cli-server.
		# The atexit-handler of coverage will not be called for SIGTERM, so we need to stop coverage manually
		def sigterm(sig, frame):
			# type: (int, Any) -> None
			cls.debug_message('signal handler', sig, argv)
			cls.stop_measurement()
			signal.signal(signal.SIGTERM, previous)
			os.kill(os.getpid(), sig)
		previous = signal.signal(signal.SIGTERM, sigterm)

	@classmethod
	def stop_measurement(cls, start=False):
		# type: (bool) -> None
		cover = cls.coverage
		cls.debug_message('STOP MEASURE', bool(cover))
		if not cover:
			return
		cover.stop()
		cover.save()
		if start:
			cover.start()

	@classmethod
	def debug_message(cls, *messages):
		# type: (object) -> None
		if not cls.COVERAGE_DEBUG:
			return
		try:
			with open(cls.COVERAGE_DEBUG_PATH, 'a') as fd:
				fd.write('%s : %s: %s\n' % (os.getpid(), time.time(), ' '.join(repr(m) for m in messages),))
		except EnvironmentError:
			pass


class StopCoverageDecorator(object):
	inDecorator = False

	def __init__(self, method):
		# type: (Callable[..., Any]) -> None
		self.method = method

	def __call__(self, *args, **kw):
		# type: (*Any, **Any) -> None
		if not StopCoverageDecorator.inDecorator:
			StopCoverageDecorator.inDecorator = True
			Coverage.debug_message('StopCoverageDecorator', self.method.__name__, open('/proc/%s/cmdline' % os.getpid()).read().split('\x00'))
			Coverage.stop_measurement(True)
		try:
			self.method(*args, **kw)
		finally:
			StopCoverageDecorator.inDecorator = False

	def __repr__(self):
		# type: () -> str
		return '<StopCoverageDecorator %r>' % (self.method,)
