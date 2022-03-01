#!/usr/share/ucs-test/runner /usr/bin/pytest-3 -s --tb=native
## desc: "Find traceback in /var/log/univention/ logfiles"
## exposure: safe
## tags: [apptest]

import argparse
import glob
import os
import pipes
import subprocess
import tempfile

import psutil
import pytest

import univention.testing.utils

import grep_traceback


@pytest.mark.exposure('safe')
def test_ucs_test_logfile():
	"""Find traceback in ucs-test logfile"""
	parser = argparse.ArgumentParser()
	parser.add_argument('-l', '--logfile')

	ucs_test = psutil.Process(os.getppid())
	args = parser.parse_known_args(ucs_test.cmdline())[0]

	if not args.logfile:
		for pfile in ucs_test.open_files():
			if pfile.path.startswith('/var/log/univention/test') and pfile.path.endswith('.log'):
				args.logfile = pfile.path
				break
	else:
		args.logfile = os.path.join(ucs_test.cwd(), args.logfile)

	if args.logfile and os.path.isfile(args.logfile):
		not_found = grep_traceback.main([args.logfile], ignore_exceptions=grep_traceback.COMMON_EXCEPTIONS)
		assert not_found, 'ucs-test logfile contains tracebacks'


@pytest.mark.exposure('safe')
def test_var_log_tracebacks():
	not_found = grep_traceback.main(glob.glob('/var/log/univention/*.log'), ignore_exceptions=grep_traceback.COMMON_EXCEPTIONS)
	assert not_found, 'logfiles contain tracebacks'


@pytest.mark.exposure('safe')
def test_var_log_subdirectory_tracebacks():
	not_found = grep_traceback.main(glob.glob('/var/log/univention/*/*.log'), ignore_exceptions=grep_traceback.COMMON_EXCEPTIONS)
	assert not_found, 'logfiles contain tracebacks'


@pytest.mark.exposure('safe')
def test_var_log_tracebacks_gz():
	not_found = grep_traceback.main(glob.glob('/var/log/univention/*.log.*.gz'), ignore_exceptions=grep_traceback.COMMON_EXCEPTIONS)
	assert not_found, 'logfiles *.gz contain tracebacks'


@pytest.mark.exposure('safe')
def test_journallog_tracebacks():
	proc = subprocess.Popen(['journalctl', '-o', 'cat'], stdout=subprocess.PIPE, text=True)
	not_found = grep_traceback.main([proc.stdout], ignore_exceptions=grep_traceback.COMMON_EXCEPTIONS)
	assert proc.wait() == 0
	assert not_found, 'logfiles journalctl contain tracebacks'


@pytest.mark.roles_not('domaincontroller_master')
@pytest.mark.exposure('dangerous')
# @pytest.mark.parametrize('testcase', [
# 	'test_var_log_tracebacks',
# 	'test_var_log_tracebacks_gz',
# ])  # FIXME: skip test_ucs_test_logfile
def test_fetch_logfiles_on_dc_master(ucr, testcase=None):
	"""Find traceback on the DC Master"""
	password = univention.testing.utils.UCSTestDomainAdminCredentials().bindpw
	testpath = '/usr/share/ucs-test/99_end/01_var_log_tracebacks.py'
	with tempfile.NamedTemporaryFile() as fd:
		fd.write(password.encode('UTF-8'))
		fd.flush()
		try:
			cmd_install = """univention-ssh %s root@%s '[ -e %s ] || univention-install -y ucs-test-end'""" % (pipes.quote(fd.name), pipes.quote(ucr['ldap/master']), pipes.quote(pipes.quote(testpath)))
			subprocess.check_output(cmd_install, shell=True)
		except subprocess.CalledProcessError as exc:
			print(cmd_install)
			if exc.output:
				print(exc.output.decode('UTF-8', 'replace'))
			assert False, (cmd_install, exc.output.decode('UTF-8', 'replace'))

		try:
			cmd_test = """univention-ssh %s root@%s '%s -i -f'""" % (pipes.quote(fd.name), pipes.quote(ucr['ldap/master']), pipes.quote(pipes.quote(testpath)))
			subprocess.check_call(cmd_test, shell=True)
		except subprocess.CalledProcessError as exc:
			print(cmd_test)
			if exc.output:
				print(exc.output.decode('UTF-8', 'replace'))
			assert not exc.returncode, (cmd_test, exc.returncode)
		# TODO: detect skipped exit code
