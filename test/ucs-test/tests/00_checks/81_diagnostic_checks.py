#!/usr/share/ucs-test/runner pytest-3 -s
## desc: Run all diagnostic checks
## exposure: safe
## tags: [basic, apptest]
## packages: [univention-management-console-module-diagnostic]

import subprocess
import tempfile

from univention.testing import utils
from univention.testing.umc import Client

# One would neeed a strong argument to skip any tests here, as it masks reals problems (See bug #50021)
SKIPPED_TESTS = []


def test_run_diagnostic_checks():
	client = Client.get_test_connection()
	plugins = [plugin['id'] for plugin in client.umc_command('diagnostic/query').result if plugin['id'] not in SKIPPED_TESTS]

	account = utils.UCSTestDomainAdminCredentials()
	with tempfile.NamedTemporaryFile() as fd:
		fd.write(account.bindpw.encode('UTF-8'))
		fd.flush()
		args = ['/usr/bin/univention-run-diagnostic-checks', '--username', account.username, '--bindpwdfile', fd.name, '-t'] + plugins
		print(args)
		returncode = subprocess.call(args)
		assert 0 == returncode, 'Exit code != 0: %d' % (returncode,)
