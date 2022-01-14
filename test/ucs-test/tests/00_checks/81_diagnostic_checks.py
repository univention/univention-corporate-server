#!/usr/share/ucs-test/runner /usr/bin/py.test -s
## desc: Run all diagnostic checks
## exposure: safe
## tags: [basic, apptest]
## packages: [univention-management-console-module-diagnostic]

from __future__ import print_function

import subprocess
import tempfile
from univention.testing.umc import Client
from univention.testing import utils
from univention.testing.utils import package_installed

# One would neeed a strong argument to skip any tests here, as it masks reals problems (See bug #50021)
SKIPPED_TESTS = []
# notifier protocol version only needs to be set if notifier is installed
if not package_installed('univention-directory_notifier'):
	SKIPPED_TESTS.append("61_notifier_protocol_version")


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
