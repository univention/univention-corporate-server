#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

from __future__ import print_function
import argparse
import jenkinsapi.jenkins
import urllib
from collections import defaultdict
from collections import OrderedDict
from yattag import Doc

colors = defaultdict(lambda: 'black')
colors.update({
	'PASSED': '#339966',
	'FIXED': '#339966',
	'SKIPPED': '#ffff99',
	'FAILED': '#990000',
	'REGRESSION': '#990000',
})

stylesheet = '''
body {
  padding: 50px;
}

a {
  color: #000099;
}

table {
  border-collapse: collapse;
  border: none;
  width:100%;
}

/* for rotated table headers */

.table-header-rotated {
  border-collapse: collapse;
}
.csstransforms .table-header-rotated td {
  width: 30px;
}
.no-csstransforms .table-header-rotated th {
  padding: 5px 10px;
}
.table-header-rotated td {
  text-align: center;
  padding: 10px 5px;
  /* border: 1px solid #ccc; */
}
.csstransforms .table-header-rotated th.rotate {
  height: 140px;
  white-space: nowrap;
}
.csstransforms .table-header-rotated th.rotate > div {
  -webkit-transform: translate(25px, 51px) rotate(315deg);
      -ms-transform: translate(25px, 51px) rotate(315deg);
          transform: translate(25px, 51px) rotate(315deg);
  width: 30px;
}
.csstransforms .table-header-rotated th.rotate > div > span {
  border-bottom: 1px solid #ccc;
  padding: 5px 10px;
}
.table-header-rotated th.row-header {
  padding: 0 10px;
  border-bottom: 1px solid #ccc;
}

tbody tr {
	min-height:1.2em;
	border-bottom: 1px solid black;
}

td {
  padding: 2px;
  font-size: 12px;
}

tbody:before {
    content: "-";
    display: block;
    line-height: .5em;
    color: transparent;
}

.hiddentd {
  text-align: left;
  font-weight: bold;
  width: 20%;
}

.section_header {
  font-weight: bold;
  background-color: #00BFFF;
}

.section_header td{
  text-align: left;
}

.child {
  display: none;
}

.first_column {
  width: 20%;
}
'''  # noqa: E101

mouseover_scripts = '''
var lastSibling = function (node){
	var tempObj=node.parentNode.lastChild;
	while(tempObj.nodeType!=1 && tempObj.previousSibling!=null){
		tempObj=tempObj.previousSibling;
	}
	return (tempObj.nodeType==1)?tempObj:false;
};

var mk_mouseover = function (machine_name){
	var el = lastSibling(this);
	el.innerHTML = machine_name;
	el.style.visibility = "visible";
};

var mk_mouseout = function () {
	var el = lastSibling(this);
	el.innerHTML = "";
	el.style.visibility = "hidden";
};

/* see here http://stackoverflow.com/questions/4866229/can-you-check-an-objects-css-display-with-javascript */
var getDisplay = function (element) {
	return element.currentStyle ? element.currentStyle.display :
		getComputedStyle(element, null).display;
}

/* collapse/expand a section. This function expects 'this' to be bound to the
header <tr> element. If no parameter is passed, the function will toggle the
current state. Otherwise,
if newval is truthy, the section will be collapsed,
if newval is falsy,  the section will be expanded   */

var togglecollapse = function(newval) {
	var td = this.firstElementChild;
	if (arguments.length === 0) {
		if (this.getAttribute('collapsed') === 'true') {
			td.innerHTML = td.innerHTML.slice(0,-3) + "[+]";
			this.setAttribute('collapsed','false');
		}
		else {
			td.innerHTML = td.innerHTML.slice(0,-3) + "[-]";
			this.setAttribute('collapsed','true');
		}
	} else {
		if (newval) {
			td.innerHTML = td.innerHTML.slice(0,-3) + "[+]";
			this.setAttribute('collapsed','true');
		} else {
			td.innerHTML = td.innerHTML.slice(0,-3) + "[-]";
			this.setAttribute('collapsed','false');
		}
	}
	var next = this.nextSibling;
	while (next && next.nodeType != 1) {
		next = next.nextSibling;
	}

	while (next) {
		if (arguments.length === 0) {
			if (this.getAttribute('collapsed') === 'true') {
				next.style.display = 'none';
			} else {
				next.style.display = 'table-row';
			}
		} else {
			if (newval) {
				next.style.display = 'none';
			} else {
				next.style.display = 'table-row';
			}
		}

		next = next.nextSibling;
		while (next && next.nodeType != 1) {
			next = next.nextSibling;
		}
		if (!next || next===undefined || !next.className || next.className !== 'child') {
			break
		}
	}
};

var collapseall = function() {
	var allHeaders = document.getElementsByClassName('section_header');
	for (var i=0; i<allHeaders.length; i++){
		header = allHeaders[i];
		togglecollapse.bind(header)(true);
	}
}

var expandall = function() {
	var allHeaders = document.getElementsByClassName('section_header');
	for (var i=0; i<allHeaders.length; i++){
		header = allHeaders[i];
		togglecollapse.bind(header)(false);
	}
}

/* after loading the document, set all headers to collapsed. */
window.onload = function(){
	var allHeaders = document.getElementsByClassName('section_header');
	for (var i=0; i<allHeaders.length; i++){
		header = allHeaders[i];
		header.setAttribute('collapsed','true')
	}
};
'''  # noqa: E101

doc, tag, text = Doc().tagtext()


def main():
	global doc, tag, text
	desc = "console tool for analyzing jenkins builds"
	parser = argparse.ArgumentParser(description=desc)
	parser.add_argument(
		'--url', '-u',
		help='the url of a jenkins matrix project. case sensitive.',
		required=True)
	parser.add_argument(
		'--output', '-o', help='output file.'
	)
	group = parser.add_mutually_exclusive_group(required=True)
	group.add_argument(
		'--latest', '-l', help='get all results for the latest build',
		action='store_true')
	group.add_argument(
		'--build', '-b', help='get all results for a specific build')
	group.add_argument(
		'--test', '-t', help='get all results for a specific test')
	args = vars(parser.parse_args())
	# split the url into server url and job name.
	# remove trailing slashes (if any)
	url = args['url']
	if url[-1] == '/':
		url = url[:-1]
	job_name = urllib.unquote(url.split('/')[-1])
	server_url = '/'.join(url.split('/')[:-2])
	j = jenkinsapi.jenkins.Jenkins(server_url)
	job = j.get_job(job_name)
	with tag('html', klass='csstransforms'):
		with tag('head'):
			with tag('style'):
				doc.asis(stylesheet)
		with tag('body'):
			with tag('script'):
				doc.asis(mouseover_scripts)
			if args['build'] or args['latest']:
				single_build(job, args)
			if args['test']:
				single_test(job, args)

	if args['output']:
		with open(args['output'], 'w') as f:
			f.write(doc.getvalue())
	else:
		print(doc.getvalue())


def table_header(machines):
	global doc, tag, text
	with tag('thead'):
		with tag('tr'):
			with tag('th', klass="first_column"):
				text('')
			for name in machines:
				with tag('th', klass='rotate'):
					with tag('div'):
						with tag('span'):
							text(name)
			with tag('th', klass="hiddentd"):
				text('')


# jenkins uses funky unicode characters to display the machine name.
# this is a cleaned up representation
def pretty_machine_name(name):
	return name.decode('utf-8').split(u'\u00bb')[-1].split('#')[0]


def strip_build_number(machine_name):
	return ''.join(machine_name.split()[:-1])


def td_status(status, url):
	global doc, tag, text
	with tag('td', style='background-color: {}'.format(colors[status])):
		if url:
			with tag('a', href=url):
				text(status[:4])
		else:
			text(status[:4])


def single_build(job, args):
	global doc, tag, text
	if args['latest']:
		args['build'] = job.get_last_buildnumber()
	build = job.get_build(int(args['build']))

	with tag('h1'):
		text(job.name)
	with tag('h2'):
		text('Build # {}'.format(args['build']))
	with tag('button', onclick='expandall()'):
		text('expand all')
	with tag('button', onclick='collapseall()'):
		text('collapse all')
	doc.asis('<br />')
	results = {
		run.name: run.get_resultset()
		for run in build.get_matrix_runs()
		if run.has_resultset()
	}

	# OrderedDict for safe iteration order
	results = OrderedDict(sorted(results.items(), key=lambda t: t[0]))
	pretty_names = map(pretty_machine_name, results.keys())

	test_names = set()
	# get all unique test names
	for resultset in results.values():
		test_names |= set(resultset.keys())
	test_names = sorted(list(test_names))

	# turn the test names into a dictionary, containing the section names as keys
	sections = OrderedDict()
	for test_name in test_names:
		section_name = test_name.split('.')[0]
		if section_name in sections:
			sections[section_name] += [test_name]
		else:
			sections[section_name] = [test_name]

	with tag('table', klass='table table-header-rotated'):
		table_header(pretty_names)
		with tag('tbody'):
			for section, test_names in sections.iteritems():
				with tag('tr', onclick='togglecollapse.bind(this)();', klass='section_header'):
					with tag('td', colspan=len(pretty_names) + 2):
						text(section + "[+]")
				for test_num, test_name in enumerate(test_names):
					with tag('tr', klass='child'):
						with tag('td', style='text-align:left'):
							text(test_name)
						for pretty_name, resultset in zip(pretty_names, results.values()):
							if test_name in resultset.keys():
								test = resultset[test_name]
								js_mouseover = 'mk_mouseover.bind(this)( "{}");'.format(pretty_name)
								js_mouseout = 'mk_mouseout.bind(this)() '
								with tag('td', style='background-color: {}'.format(colors[test.status]), onmouseover=js_mouseover, onmouseout=js_mouseout):
									if test.stdout or test.stderr:
										url = '/'.join(resultset.baseurl.split('/')[:-2]) + \
											'/' + test.identifier().replace('.', '/')
										with tag('a', href=url):
											text(test.status[:4])
									else:
										text(test.status[:4])
							else:
								with tag('td'):
									text('')
						with tag('td', klass='hiddentd'):
							pass


def single_test(job, args):
	global doc, tag, text
	test_name = args['test']
	with tag('h1'):
		text(job.name)
	with tag('h2'):
		text(test_name)
	builds = job.get_build_ids()
	results = {}
	machines = set()
	for build_id in builds:
		build = job.get_build(build_id)
		build_results = {
			strip_build_number(run.name): run.get_resultset()
			for run in build.get_matrix_runs()
			if run.has_resultset()}
		results[build_id] = build_results
		machines |= set(strip_build_number(run.name) for run in build.get_matrix_runs())
	machines = sorted(list(machines))
	pretty_names = map(pretty_machine_name, machines)
	with tag('table', klass='table table-header-rotated'):
		table_header(pretty_names)
		with tag('tbody'):
			for build_id, resultset_dict in results.iteritems():
				with tag('tr'):
					with tag('td'):
						text('{:03d}'.format(build_id))
					for machine in machines:
						if machine in resultset_dict.keys() and test_name in resultset_dict[machine].keys():
							resultset = resultset_dict[machine]
							test = resultset[test_name]
							if test.stdout or test.stderr:
								url = '/'.join(resultset.baseurl.split('/')[:-2]) + '/' + test.identifier().replace('.', '/')
							else:
								url = ''
							td_status(test.status, url)
						else:
							with tag('td'):
								text('')


if __name__ == '__main__':
	main()
