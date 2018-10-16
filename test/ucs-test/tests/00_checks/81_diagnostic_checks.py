#!/usr/share/ucs-test/runner python
## desc: Run all diagnostic checks
## exposure: safe
## packages: [univention-management-console-module-diagnostic]

import argparse
from univention.testing.umc import Client
SKIPPED_TESTS = []

def test_run_diagnostic_checks(client,plugins):
	failures = []

	for plugin in plugins:
		if plugin['id'] in SKIPPED_TESTS:
			print 'SKIP %s' % plugin['id']
			continue
		result = client.umc_command('diagnostic/run', {'plugin': plugin['id']}).result
		if result['type'] != 'success':
			failures.extend([
				'############################',
				'## Check failed: %s - %s' % (plugin['id'], result['title']),
				result['description'],
				'########### End #############',
			])
	if failures:
		raise Exception('\n'.join(failures))

#returns a list of the plugins whose names did not match any plugin
#returns a list of the plugins that should be run
def choose_tests(tests,plugins):
	chosen_tests = []
	unused_tests = []
	for plugin in plugins:
		for x in range(len(tests)):
			if plugin['id'] == tests[x]:
				chosen_tests.append(plugin)
				tests[x] = ''
	for x in tests:
		if x != '':
			unused_tests.append(x)
	return unused_tests, chosen_tests


def parsing():
	parser = argparse.ArgumentParser(description='Executes the diagnostic module checks')
	parser.add_argument("-t",type = str, help = 'You have to choose tests to run by using "{-t <testname>}" or write "-t all" to execute all tests', action = 'append')
	args = parser.parse_args()
	return args.t

def main():
	argst = parsing()
	valid_input = True
	
	for x in argst:
		if x.find(".") != -1:
			print 'Please enter the test names again, but without file endings'
			valid_input = False
	
	if valid_input:
		if argst is None:
			raise Exception('You have to choose tests to run by using "{-t <testname>}" or write "-t all" to execute all tests')
		
		client = Client.get_test_connection()
		plugins = client.umc_command('diagnostic/query').result
		
		if 'all' in argst:
			test_run_diagnostic_checks(client,plugins)
		else:
			unused_tests, chosen_tests = choose_tests(argst, plugins)
			for x in unused_tests:
				print 'Could not find a test named %s Please check for spelling mistakes' %x
			test_run_diagnostic_checks(client,chosen_tests)

if __name__ == '__main__':
	main()
