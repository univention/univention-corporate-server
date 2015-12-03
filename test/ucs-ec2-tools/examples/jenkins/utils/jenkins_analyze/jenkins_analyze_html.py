#!/usr/bin/python2.7

from __future__ import print_function
import argparse
import jenkinsapi.jenkins
from collections import defaultdict
import sys

# import requests
# import logging
# # these two lines enable debugging at httplib level (requests->urllib3->httplib)
# # you will see the REQUEST, including HEADERS and DATA, and RESPONSE with HEADERS but without DATA.
# # the only thing missing will be the response.body which is not logged.
# import httplib
# httplib.HTTPConnection.debuglevel = 1
# logging.basicConfig() # you need to initialize logging, otherwise you will not see anything from requests
# logging.getLogger().setLevel(logging.DEBUG)
# requests_log = logging.getLogger("requests.packages.urllib3")
# requests_log.setLevel(logging.DEBUG)
# requests_log.propagate = True

colors = defaultdict(lambda: 'black')
colors.update({
	'PASSED': '#339966',
	'FIXED': '#339966',
	'SKIPPED': '#ffff99',
	'FAILED': '#990000',
	'REGRESSION': '#990000',
})
base_url = 'http://jenkins.knut.univention.de:8080/job/UCS-4.1/job/UCS-4.1-0/'


def print_table_header(machines, spacing=4):
	print('<table class="table table-header-rotated">')
	print('<thead>')
	print('<tr>')
	print('<th></th>')
	for name in machines:
		print('<th class="rotate">')
		print('<div>')
		print('<span>')
		print(name.decode('utf-8').split(u'\u00bb')[-1].split('#')[0])
		print('</span>')
		print('</div>')
		print('</th>')
	print('</tr>')
	print('</thead>')


def strip_build_number(machine_name):
	return ''.join(machine_name.split()[:-1])


def append_status_to_line(line, status):
	line = line + '<td style="background-color: {}">'.format(colors[status]) + status[:4] + '</td>'
	return line


def main():
	desc = "console tool for analyzing jenkins builds"
	parser = argparse.ArgumentParser(description=desc)
#single test or single build?
	group = parser.add_mutually_exclusive_group(required=True)
	group.add_argument(
			'--build', '-b', help='get all results for a specific build')
	group.add_argument(
			'--test', '-t', help='get all results for a specific test')
#4.03-update or 4.1?
	version_group = parser.add_mutually_exclusive_group(required=True)
	version_group.add_argument(
			'--template03', '-3', help='updated 4.03 template',
			action ='store_false', dest='new')
	version_group.add_argument(
			'--template10', '-1', help='4.10 template',
			action ='store_true', dest='new')

	parser.add_argument(
			'--no-empty', '-n', help='do not show empty lines in build mode',
			action='store_true', default=False)
	args = vars(parser.parse_args())

	j = jenkinsapi.jenkins.Jenkins(base_url)
	if args['new']:
		job_name = 'Autotest MultiEnv (IPv6) 4.1 Generic'
	else:
		job_name = 'Autotest MultiEnv (IPv6) Update from 4.0'
	job = j.get_job(job_name)

	print('<html class="csstransforms"')
	print('<head>')
	print('<link rel="stylesheet" type="text/css" href="style.css">')
	print('</head>')
	print('<body>')

	if args['build']:
		single_build(job, args)

	if args['test']:
		single_test(job, args)

	print('</body>')
	print('</html>')


def single_build(job, args):
	build = job.get_build(int(args['build']))

	print('<h1>{}</h1>'.format(job.name))
	print('<h2>Build # {}</h2>'.format(args['build']))

	results = {run.name:
			run.get_resultset()
			for run in build.get_matrix_runs()
			if run.has_resultset()}

	test_names = set()

	#get all unique test names
	for resultset in results.values():
		test_names |= set(resultset.keys())

	test_names = sorted(list(test_names))

	print_table_header(results.keys(), spacing=36)

	print('<tbody>')
	for test_name in test_names:
		line = '<tr>'
		line += '<td style="text-align:left"> {} </td>'.format(test_name)
		for resultset in results.values():
			if test_name in resultset.keys():
				status = resultset[test_name].status
				line = append_status_to_line(line, status)
			else:
				line += '<td></td>'
		line +='</tr>'
		print(line)
	print('</tbody>')
	
	print('</table>')


def single_test(job, args):
	test_name = args['test']
	print('<h1>{}</h1>'.format(job.name))
	print('<h2>{}</h2>'.format(test_name))
	builds = job.get_build_ids()

	results = {}
	machines = set()

	for build_id in builds:
		build = job.get_build(build_id)
		build_results = {strip_build_number(run.name):
			run.get_resultset()
			for run in build.get_matrix_runs()
			if run.has_resultset()}
		results[build_id] = build_results
		machines |= set(strip_build_number(run.name)
				for run in build.get_matrix_runs())

	print_table_header(machines)

	for build_id, result in results.items():
		line = '<tr>'
		test_found = False
		line += '<td> {:03d} </td>'.format(build_id)
		for machine in machines:
			if machine in result.keys() and test_name in result[machine].keys():
				test_found = True
				status = result[machine][test_name].status
				line = append_status_to_line(line, status)
			else:
				line += '<td></td>'
		line += '</tr>'
		if test_found or not args['no_empty']:
			print(line)

	print('</table>')


if __name__ == '__main__':
	main()
