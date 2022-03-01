#!/usr/share/ucs-test/runner /usr/bin/py.test-3 -svv --tb=native
# -*- coding: utf-8 -*-
## desc: Check Python 2 + 3 compatibility and idempotency of UCR templates
## tags: [apptest]
## exposure: safe

from __future__ import print_function

import glob
import json
import os
import subprocess
import sys
import tempfile
from difflib import unified_diff
from typing import Dict, Set  # noqa F401

import py.path
import pytest

from univention.config_registry import ConfigRegistry
from univention.config_registry.handler import EXECUTE_TOKEN, run_filter

ucr = ConfigRegistry()
ucr.load()

VERSIONS = (2, 3)
BASE_DIR = "/etc/univention/templates/files/"

ALLOWED_DIFFERENCES = [
	'/etc/univention/templates/files/usr/share/univention-management-console/meta.json',
	'/etc/univention/templates/files/usr/share/univention-portal/apps.json',
	'/etc/univention/templates/files/etc/aliases',
	'/etc/univention/templates/files/etc/simplesamlphp/00authsources.php',
	'/etc/univention/templates/files/etc/univention/directory/reports/config.ini',
	'/etc/univention/templates/files/etc/listfilter.secret',
	'/etc/univention/templates/files/etc/security/packetfilter.d/10_univention-firewall_start.sh',
	'/etc/univention/templates/files/etc/dhcp/dhclient.conf',  # different IP address received, different date
	'/etc/univention/templates/files/var/lib/dovecot/sieve/default.sieve',  # different date if not commited in the same second
	'/etc/univention/templates/files/usr/share/univention-management-console/i18n/de/apps.mo',  # po-lib adds date
	'/etc/univention/templates/files/etc/mysql/mariadb.conf.d/60-ucr.cnf',  # not really different, but difference due to dict iteration
] + glob.glob('/etc/univention/templates/files/etc/security/*.conf')
IGNORE = {
}  # type: Dict[str, Set[int]]

SCRIPT = r'''#!/bin/sh
cat >{1[tmp]}
python{0} -m coverage run {1[tmp]} >{1[out]} 2>&1
exec echo "$?" >{1[ret]}
'''


@pytest.fixture(scope='session')
def tmpfile(request):
	tmpdir = py.path.local(tempfile.mkdtemp())
	request.addfinalizer(lambda: tmpdir.remove(rec=1))
	return lambda pyver, suffix: tmpdir.join("ucr{0}.{1}".format(pyver, suffix))


@pytest.fixture(scope="module")
def python_versions(tmpfile):
	result = [
		(pyver, dict((suf, tmpfile(pyver, suf)) for suf in ("py", "tmp", "out", "ret")))
		for pyver in VERSIONS
	]
	for (pyver, fn) in result:
		fn["py"].write(SCRIPT.format(pyver, fn))
		fn["py"].chmod(0o755)

	return result


def pytest_generate_tests(metafunc):
	tempfiles = [
		pytest.param(path, marks=pytest.mark.xfail) if path in ALLOWED_DIFFERENCES else path
		for path in (
			os.path.join(path, filename)
			for path, dirs, files in os.walk(BASE_DIR)
			for filename in files
		) if EXECUTE_TOKEN.search(open(path, 'rb').read())
	]
	metafunc.parametrize('ucr_config_file', tempfiles)


@pytest.fixture(scope='session')
def dpkg():
	etc = {}
	cmd_dpkg = ["dpkg", "-S", os.path.join(BASE_DIR, '*')]
	proc = subprocess.Popen(cmd_dpkg, stdout=subprocess.PIPE)
	assert proc.stdout
	for line in proc.stdout:
		pkg, fn = line.decode('UTF-8', 'replace').strip().split(': ')
		etc[fn] = pkg
	assert not proc.wait()
	return etc


def test_configfile_python_compatibility(ucr_config_file, python_versions, dpkg):
	with open(ucr_config_file) as fd:
		template = fd.read()

	msg = []
	python = {}
	for (pyver, fn) in python_versions:
		sys.executable = fn["py"]
		run_filter(template, ucr)

		data = fn["out"].read_text('ISO8859-1').rstrip('\n')
		ret = int(fn["ret"].read().strip())

		cmd_ucr = ["python{0}".format(pyver), "-m", "coverage", "report"]
		cov = subprocess.check_output(cmd_ucr).decode('UTF-8', 'replace')
		try:
			line, = [line for line in cov.splitlines() if str(fn["tmp"]) in line]
			_name, _stmts, _miss, coverage = line.split()
		except ValueError:
			coverage = "?"

		python[pyver] = {
			'success': ret == 0,
			'compiled': data,
			'coverage': coverage,
		}
		if ucr_config_file.endswith('.json'):
			try:
				python[pyver]['compiled'] = json.dumps(json.loads(data), sort_keys=True)
			except ValueError:
				python[pyver]['json_failed'] = True

		if os.path.exists('.coverage'):
			os.unlink('.coverage')

		msg.append('Py%s:|%s|%s' % (
			pyver,
			'✅' if ret == 0 else '❎',
			coverage,
		))

	print('\t'.join(msg), end='\t')

	try:
		diff = ''.join(unified_diff(
			*(python[pyver]["compiled"].splitlines(keepends=True) for pyver in VERSIONS),
			*(str(pyver) for pyver in VERSIONS),
		))
	except LookupError:
		diff = ""

	details = {
		'python': python,
		'package': dpkg.get(ucr_config_file, ""),
		'diff': diff,
	}
	print(diff)

	ignore = IGNORE.get(ucr_config_file, set())
	assert all(res['success'] for pyver, res in python.items() if pyver not in ignore), details
	assert len({res['compiled'] for pyver, res in python.items() if pyver not in ignore}) == 1, details
