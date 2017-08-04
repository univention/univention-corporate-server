#!/usr/share/ucs-test/runner /usr/bin/py.test -s
## desc: Run all diagnostic checks
## exposure: dangerous
## packages: [univention-management-console-module-diagnostic]


def test_run_diagnostic_checks(Client):
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
