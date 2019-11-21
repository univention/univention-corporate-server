"""Code coverage measurement for ucs-test"""

from __future__ import absolute_import
from __future__ import print_function

import os
import sys
import time
import signal
import atexit
import subprocess
import distutils.spawn
from distutils.version import LooseVersion


class Coverage(object):

	COVERAGE_PTH = '/usr/lib/python2.7/dist-packages/ucstest-coverage.pth'
	COVERAGE_PTH_CONTENT = '''import univention.testing.coverage; univention.testing.coverage.Coverage.startup()'''
	COVERAGE_DEBUG_PATH = '/tmp/ucs-test-coverage'
	COVERAGE_DEBUG = os.path.exists(COVERAGE_DEBUG_PATH)
	COVERAGE_MIN_VERSION = '4.3'

	coverage = None

	def __init__(self, options):
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

		if self.coverage:
			try:
				import coverage
				if LooseVersion(coverage.__version__) < LooseVersion(self.COVERAGE_MIN_VERSION):
					raise ImportError('Version {!r} of coverage to low, at least {!r} required.'.format(coverage.__version__, self.COVERAGE_MIN_VERSION))
			except ImportError as exc:
				print('Could not load coverage: %s' % (exc,), file=sys.stderr)
				print("Use: ucr set repository/online/unmaintained='yes'; univention-install -y --force-yes python-pip; pip install coverage", file=sys.stderr)
				print("Or download a 'python-coverage' package with version >= {} from 'packages.debian.org'".format(self.COVERAGE_MIN_VERSION), file=sys.stderr)
				print("and install with 'dpkg -i python-coverage_*.deb'.", file=sys.stderr)
				sys.exit(1)

		if self.coverage and options.coverage_debug:
			with open(self.COVERAGE_DEBUG_PATH, 'w'):
				self.COVERAGE_DEBUG = True

	def start(self):
		"""Start measuring of coverage. Only called by ucs-test-framework once. Sets up the configuration."""
		if not self.coverage:
			return
		self.write_config_file()
		os.environ['COVERAGE_PROCESS_START'] = self.coverage_config
		self.restart_python_services()

	def write_config_file(self):
		"""Write a python .pth file which is invoked before any python process"""
		with open(self.COVERAGE_PTH, 'wb') as fd:
			fd.write(self.COVERAGE_PTH_CONTENT)

		with open(self.coverage_config, 'wb') as fd:
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
		"""Restart currently running python services, so that they start/stop measuring code"""
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
		"""Stop coverage measuring. Only called by ucs-test-framework once. Stores the results."""
		if not self.coverage:
			return

		# stop all services, so that their atexit-handler/signal handler stores the result before evaluating the result
		self.restart_python_services()
		coverage_bin = distutils.spawn.find_executable("coverage")
		if not coverage_bin:
			coverage_bin = distutils.spawn.find_executable("python-coverage")
		subprocess.call([coverage_bin, '--version'])
		subprocess.call([coverage_bin, 'combine'])
		subprocess.call([coverage_bin, 'html'])
		subprocess.call([coverage_bin, 'report'])
		subprocess.call([coverage_bin, 'erase'])
		if os.path.exists(self.COVERAGE_PTH):
			os.remove(self.COVERAGE_PTH)
		if os.path.exists(self.coverage_config):
			os.remove(self.coverage_config)

	@classmethod
	def get_argument_group(cls, parser):
		"""The option group for ucs-test-framework"""
		coverage_group = parser.add_argument_group('Code coverage measurement options')
		coverage_group.add_argument("--with-coverage", dest="coverage", action='store_true', default=False)
		coverage_group.add_argument("--coverage-config", dest="coverage_config", default=os.path.abspath(os.path.expanduser('~/.coveragerc')))  # don't use this, doesn't work!
		coverage_group.add_argument("--branch-coverage", dest="branch_coverage", action='store_true', default=False)
		coverage_group.add_argument('--coverage-sources', dest='coverage_sources', action='append', default=[])
		coverage_group.add_argument("--coverage-debug", dest="coverage_debug", action='store_true', default=False)
		coverage_group.add_argument('--coverage-restart-service', dest='coverage_restart_services', action='append', default=[])
		coverage_group.add_argument('--coverage-show-missing', dest='coverage_show_missing', action='store_true', default=False)
		coverage_group.add_argument("--coverage-output-directory", dest="coverage_output_directory", default=os.path.abspath(os.path.expanduser('~/htmlcov')))
		return coverage_group

	@classmethod  # noqa: C901
	def startup(cls):
		"""Startup function which is invoked by every(!) python process during coverage measurement. If the process is relevant we start measuring coverage."""
		argv = open('/proc/%s/cmdline' % os.getpid()).read().split('\x00')
		if os.getuid() != 0 or not any('univention' in arg or 'udm' in arg or 'ucs' in arg or 'ucr' in arg for arg in argv):
			if argv != ['/usr/bin/python2.7', '']:
				cls.debug_message('skip non-ucs process', argv)
			return  # don't change non UCS-python scripts
		if any('listener' in arg or 'notifier' in arg for arg in argv[2:]):
			cls.debug_message('skip listener', argv)
			return  # we don't need to cover the listener currently. some tests failed, maybe because of measuring the listener?

		cls.debug_message('START', argv)
		atexit.register(lambda: cls.debug_message('STOP'))

		if not os.environ.get('COVERAGE_PROCESS_START'):
			os.environ["COVERAGE_PROCESS_START"] = os.path.abspath(os.path.expanduser('~/.coveragerc'))
			cls.debug_message('ENVIRON WAS CLEARED BY PARENT PROCESS', argv)

		import coverage
		cls.coverage = coverage.process_startup()
		if not cls.coverage:
			cls.debug_message('no coverage startup (already started?, environ cleared?)')
			return

		# FIXME: univention-cli-server calls os.fork() which causes the coverage measurement not to start in the forked process
		# https://bitbucket.org/ned/coveragepy/issues/310/coverage-fails-with-osfork-and-os_exit
		osfork = getattr(os, 'fork')

		def fork(*args, **kwargs):
			pid = osfork(*args, **kwargs)
			if pid == 0:
				cls.debug_message('FORK CHILD')
				cls.startup()
			else:
				cls.debug_message('FORK PARENT')
				cls.stop_measurement(True)
			return pid
		os.fork = fork

		# https://bitbucket.org/ned/coveragepy/issues/43/coverage-measurement-fails-on-code
		# if the process calls one of the process-replacement functions the coverage must be started in the new process
		for method in ['execl', 'execle', 'execlp', 'execlpe', 'execv', 'execve', 'execvp', 'execvpe', '_exit']:
			if isinstance(getattr(os, method), StopCoverageDecorator):
				continue  # restarted in the same process (e.g. os.fork())
			setattr(os, method, StopCoverageDecorator(getattr(os, method)))

		# There are test cases which e.g. kill the univention-cli-server.
		# The atexit-handler of coverage will not be called for SIGTERM, so we need to stop coverage manually
		def sigterm(sig, frame):
			cls.debug_message('signal handler', sig, argv)
			cls.stop_measurement()
			signal.signal(signal.SIGTERM, previous)
			os.kill(os.getpid(), sig)
		previous = signal.signal(signal.SIGTERM, sigterm)

	@classmethod
	def stop_measurement(cls, start=False):
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
		if not cls.COVERAGE_DEBUG:
			return
		try:
			with open(cls.COVERAGE_DEBUG_PATH, 'a') as fd:
				fd.write('%s : %s: %s\n' % (os.getpid(), time.time(), ' '.join(map(repr, messages)),))
		except EnvironmentError:
			pass


class StopCoverageDecorator(object):
	inDecorator = False

	def __init__(self, method):
		self.method = method

	def __call__(self, *args, **kw):
		if not StopCoverageDecorator.inDecorator:
			StopCoverageDecorator.inDecorator = True
			Coverage.debug_message('StopCoverageDecorator', self.method.__name__, open('/proc/%s/cmdline' % os.getpid()).read().split('\x00'))
			Coverage.stop_measurement(True)
		try:
			self.method(*args, **kw)
		finally:
			StopCoverageDecorator.inDecorator = False

	def __repr__(self):
		return '<StopCoverageDecorator %r>' % (self.method,)
