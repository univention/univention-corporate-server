#!/usr/share/ucs-test/runner pytest-3 -s
## desc: Run all diagnostic checks
## exposure: safe
## tags: [basic, apptest]
## packages: [univention-management-console-module-diagnostic]

import re
import subprocess
import tempfile

import pytest

from univention.config_registry import ucr
from univention.testing import utils
from univention.testing.umc import Client


DIAGNOSTIC_RE = re.compile(r'(?:^ran ([\d\w]*) successfully.$)|(?:#+ Start ([\d\w]*) #+)\n(.*)\n(?:#+ End (?:\2) #+)', flags=re.M | re.S)
# One would need a strong argument to skip any tests here, as it masks reals problems (See bug #50021)
PREFIX = "diagnostic/check/disable/"
SKIPPED_TESTS = {
}
SKIPPED_TESTS.update({
    k[len(PREFIX):]: PREFIX
    for k, v in ucr.items()
    if k.startswith(PREFIX) and ucr.is_true(value=v)
})


def pytest_generate_tests(metafunc):
    client = Client.get_test_connection()
    plugins = [plugin['id'] for plugin in client.umc_command('diagnostic/query', print_response=False, print_request_data=False).result]
    plugins = [
        pytest.param(plugin, marks=pytest.mark.xfail(reason=SKIPPED_TESTS[plugin])) if plugin in SKIPPED_TESTS else plugin
        for plugin in plugins
    ]
    metafunc.parametrize('plugin', plugins)


@pytest.fixture(scope='session')
def diagnostic_results():
    account = utils.UCSTestDomainAdminCredentials()
    with tempfile.NamedTemporaryFile() as fd:
        fd.write(account.bindpw.encode('UTF-8'))
        fd.flush()
        args = ['/usr/bin/univention-run-diagnostic-checks', '--username', account.username, '--bindpwdfile', fd.name]
        proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        stdout, _ = proc.communicate()
    params = {
        success or failed: {
            'success': bool(success and not failed),
            'error_message': error_message,
        } for success, failed, error_message in DIAGNOSTIC_RE.findall(stdout.decode('UTF-8', 'replace'))
    }
    if not proc.returncode:
        assert all(item['success'] for plugin, item in params.items())
    return params


def test_run_diagnostic_checks(plugin, diagnostic_results):
    plugin_data = diagnostic_results.get(plugin)
    print(plugin)
    assert plugin_data
    print(plugin_data['error_message'])
    assert plugin_data['success'], plugin_data['error_message']
