#!/usr/share/ucs-test/runner /usr/bin/py.test -s
## desc: Run all diagnostic checks
## exposure: safe
## packages: [univention-management-console-module-diagnostic]

from univention.testing.umc import Client


def test_run_diagnostic_checks():
	client = Client.get_test_connection()
	plugins = client.umc_command('diagnostic/query').result
	failures = []
	for plugin in plugins:
		result = client.umc_command('diagnostic/run', {'plugin': plugin['id']}).result
		if result['type'] != 'success':
			failures.append(result)
	error = ''.join('###############\n%s\n%s###############\n\n' % (x['title'], x['description']) for x in failures)
	if failures:
		raise Exception(error)
