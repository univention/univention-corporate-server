#!/usr/share/ucs-test/runner /usr/bin/py.test -s
## desc: "Find traceback on the DC Master"
## exposure: dangerous
## roles-not: [domaincontroller_master]
## tags: [SKIP]

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
		fd.write(password)
		fd.flush()
		subprocess.check_call("""univention-ssh %s root@%s 'univention-install -y --force-yes ucs-test-end'""" % (pipes.quote(fd.name), pipes.quote(ucr['ldap/master'])), shell=True)
		assert not subprocess.call("""univention-ssh %s root@%s '/usr/share/ucs-test/99_end/%s -f'""" % (pipes.quote(fd.name), pipes.quote(ucr['ldap/master']), pipes.quote(testfile)))
		# TODO: detect skipped exit code
