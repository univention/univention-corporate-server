#!/usr/share/ucs-test/runner /usr/bin/py.test -s
## desc: Run all diagnostic checks
## exposure: safe
## packages: [univention-management-console-module-diagnostic]

from univention.testing.umc import Client

SKIPPED_TESTS = ['40_samba_tool_dbcheck', '46_kerberos_ddns_update']


def test_run_diagnostic_checks():
	client = Client.get_test_connection()
	plugins = client.umc_command('diagnostic/query').result
	failures = []
	for plugin in plugins:
		if plugin['id'] in SKIPPED_TESTS:
			print 'SKIP %s' % plugin['id']
			continue
		result = client.umc_command('diagnostic/run', {'plugin': plugin['id']}).result
		if result['type'] != 'success':
			failures.append(result)
	error = ''.join('###############\n%s\n%s###############\n\n' % (x['title'], x['description']) for x in failures)
	if failures:
		raise Exception(error)
