#!/usr/share/ucs-test/runner /usr/bin/py.test-3 -s --tb=native
## desc: "Find traceback on the DC Master"
## exposure: dangerous
## roles-not: [domaincontroller_master]

import univention.testing.utils
import subprocess
import tempfile
import pipes
import pytest


@pytest.mark.parametrize('testfile', [
	'01_var_log_tracebacks',
	'02_var_log_tracebacks_gz',
])
def test_fetch_logfiles_on_dc_master(testfile, ucr):
	password = univention.testing.utils.UCSTestDomainAdminCredentials().bindpw
	testpath = '/usr/share/ucs-test/99_end/%s' % (testfile,)
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
			raise Exception(exc.output)

		try:
			cmd_test = """univention-ssh %s root@%s '%s -f'""" % (pipes.quote(fd.name), pipes.quote(ucr['ldap/master']), pipes.quote(pipes.quote(testpath)))  # somehow does not work, because no TTY?!
			cmd_test = """univention-ssh %s root@%s 'ucs-test -s end -r %s -E dangerous -l /tmp/%s -H; rc=$?; cat /tmp/%s; exit "$rc"'""" % (
				pipes.quote(fd.name),
				pipes.quote(ucr['ldap/master']),
				pipes.quote(pipes.quote(testfile)),
				pipes.quote(pipes.quote(testfile)),
				pipes.quote(pipes.quote(testfile)),
			)
			subprocess.check_call(cmd_test, shell=True)
		except subprocess.CalledProcessError as exc:
			print(cmd_test)
			if exc.output:
				print(exc.output.decode('UTF-8', 'replace'))
			assert not exc.returncode, (cmd_test, exc.returncode)
		# TODO: detect skipped exit code
