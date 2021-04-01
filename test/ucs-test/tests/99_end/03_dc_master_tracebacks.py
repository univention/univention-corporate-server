#!/usr/share/ucs-test/runner /usr/bin/py.test-3 -s
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
	with tempfile.NamedTemporaryFile() as fd:
		fd.write(password.encode())
		fd.flush()
		try:
			subprocess.check_output("""univention-ssh %s root@%s 'univention-install -y ucs-test-end'""" % (pipes.quote(fd.name), pipes.quote(ucr['ldap/master'])), shell=True)
		except subprocess.CalledProcessError as exc:
			raise Exception(exc.output)

		try:
			subprocess.check_call("""univention-ssh %s root@%s '/usr/share/ucs-test/99_end/%s -f'""" % (pipes.quote(fd.name), pipes.quote(ucr['ldap/master']), pipes.quote(testfile)), shell=True)
		except subprocess.CalledProcessError as exc:
			print(exc.output.decode('UTF-8', 'replace'))
			assert not exc.returncode, exc.returncode
		# TODO: detect skipped exit code
