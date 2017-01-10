"""Code coverage measurement for ucs-test"""

from __future__ import absolute_import

import os
import sys
import signal
import subprocess
from optparse import OptionGroup


class Coverage(object):

	COVERAGE_PTH = '/usr/lib/python2.7/dist-packages/ucstest-coverage.pth'
	COVERAGE_PTH_CONTENT = '''import univention.testing.coverage; univention.testing.coverage.Coverage.startup()'''

	def __init__(self, options):
		self.coverage_config = options.coverage_config
		self.branch_coverage = options.branch_coverage
		self.coverage = options.coverage
		self.coverage_sources = options.coverage_sources
		if self.coverage:
			try:
				__import__('coverage')
			except ImportError as exc:
				print >> sys.stderr, 'Could not load coverage: %s' % (exc,)
				print >> sys.stderr, "use: ucr set repository/online/unmaintained='yes'; univention-install -y --force-yes python-pip; pip install coverage"
				self.coverage = False

	def start(self):
		if not self.coverage:
			return
		self.write_config_file()
		os.environ['COVERAGE_PROCESS_START'] = self.coverage_config
		self.restart_python_services()

	def write_config_file(self):
		with open(self.COVERAGE_PTH, 'wb') as fd:
			fd.write(self.COVERAGE_PTH_CONTENT)

		with open(self.coverage_config, 'wb') as fd:
			fd.write('[run]\ndata_file = %s\nbranch = %s\nparallel = True\nsource = %s\n' % (
				os.path.join(os.path.dirname(self.coverage_config), '.coverage'),
				repr(self.branch_coverage),
				'\n\t'.join(self.coverage_sources)
			))

	def restart_python_services(self):
		for service in ['/etc/init.d/univention-management-console-server', '/etc/init.d/univention-management-console-web-server']:
			try:
				subprocess.call([service, 'restart'])
			except EnvironmentError:
				pass
		try:
			subprocess.call(['pkill', '-f', 'python.*univention-cli-server'])
		except EnvironmentError:
			pass

	def stop(self):
		if not self.coverage:
			return
		self.restart_python_services()
		subprocess.call(['coverage', '--version'])
		subprocess.call(['coverage', 'combine'])
		subprocess.call(['coverage', 'html'])
		subprocess.call(['coverage', 'report'])
		if os.path.exists(self.COVERAGE_PTH):
			os.remove(self.COVERAGE_PTH)
		if os.path.exists(self.coverage_config):
			os.remove(self.coverage_config)

	@classmethod
	def get_option_group(cls, parser):
		coverage_group = OptionGroup(parser, 'Code coverage measurement options')
		coverage_group.add_option("--with-coverage", dest="coverage", action='store_true', default=False)
		coverage_group.add_option("--coverage-config", dest="coverage_config", default=os.path.abspath(os.path.expanduser('~/.coveragerc')))
		coverage_group.add_option("--branch-coverage", dest="branch_coverage", action='store_true', default=False)
		coverage_group.add_option('--coverage-sources', dest='coverage_sources', action='append', default=['univention'])
		return coverage_group

	@classmethod
	def startup(cls):
		argv = open('/proc/%s/cmdline' % os.getpid()).read().split('\x00')
		if os.getuid() != 0 or not any('univention' in arg or 'udm' in arg or 'ucs' in arg for arg in argv[2:]):
			return  # don't change non UCS-python scripts
		if any('listener' in arg or 'notifier' in arg for arg in argv[2:]):
			return  # we don't need to cover the listener currently. some tests failed, maybe because of measuring the listener?

		if not os.environ.get('COVERAGE_PROCESS_START'):
			print >> sys.stderr, 'COVERAGE NOT MEASURED. ENVIRON WAS CLEARED BY PARENT PROCESS.'

		import coverage
		# FIXME: univention-cli-server calls os.fork() which destroys all information
		cov = coverage.process_startup()
		for method in ['execl', 'execle', 'execlp', 'execlpe', 'execv', 'execve', 'execvp', 'execvpe']:  # , 'fork', '_exit']:
			setattr(os, method, StopCoverageDecorator(cov, getattr(os, method)))

		def sigterm(sig, frame):
			cov.stop()
			cov.save()
			signal.signal(signal.SIGTERM, previous)
			os.kill(os.getpid(), sig)
		previous = signal.signal(signal.SIGTERM, sigterm)


class StopCoverageDecorator:  # https://bitbucket.org/ned/coveragepy/issues/43/coverage-measurement-fails-on-code
	inDecorator = False

	def __init__(self, cov, method):
		self.cov = cov
		self.method = method

	def __call__(self, *args, **kw):
		if not StopCoverageDecorator.inDecorator:
			StopCoverageDecorator.inDecorator = True
			if self.cov:
				self.cov.stop()
				self.cov.save()
				self.cov.start()
		self.method(*args, **kw)
		StopCoverageDecorator.inDecorator = False
