#!/usr/share/ucs-test/runner /usr/bin/py.test -s
## desc: Run all diagnostic checks
## exposure: safe
## packages: [univention-management-console-module-diagnostic]

import subprocess
import tempfile
from univention.testing.umc import Client
from univention.testing import utils

SKIPPED_TESTS = ['11_nameserver', '31_file_permissions', '40_samba_tool_dbcheck']


def test_run_diagnostic_checks():
	client = Client.get_test_connection()
	plugins = [plugin['id'] for plugin in client.umc_command('diagnostic/query').result if plugin['id'] not in SKIPPED_TESTS]

	account = utils.UCSTestDomainAdminCredentials()
	with tempfile.NamedTemporaryFile() as fd:
		fd.write(account.bindpw)
		fd.flush()
		args = ['/usr/bin/univention-run-diagnostic-checks', '--username', account.username, '--bindpwdfile', fd.name, '-t'] + plugins
		print(args)
		returncode = subprocess.call(args)
		assert 0 == returncode, 'Exit code != 0: %d' % (returncode,)
