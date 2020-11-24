#!/usr/share/ucs-test/runner /usr/bin/py.test-3 -svv --tb=native
# -*- coding: utf-8 -*-
from __future__ import print_function

import os
import sys
import pipes
import tempfile
import subprocess
import json
import glob

import pytest

from univention.config_registry.handler import run_filter, EXECUTE_TOKEN
from univention.config_registry import ConfigRegistry

ucr = ConfigRegistry()
ucr.load()

SCRIPT = r'''#!/bin/bash
cat < /dev/stdin > /tmp/py{0}.in
python{0} -m coverage run /tmp/py{0}.in &>/tmp/py{0}.out
echo $? >> /tmp/py{0}.out
'''

ALLOWED_DIFFERENCES = [
	'/etc/univention/templates/files/usr/share/univention-management-console/meta.json',
	'/etc/univention/templates/files/etc/aliases',
	'/etc/univention/templates/files/etc/simplesamlphp/00authsources.php',
	'/etc/univention/templates/files/etc/univention/directory/reports/config.ini',
	'/etc/univention/templates/files/etc/listfilter.secret',
	'/etc/univention/templates/files/etc/security/packetfilter.d/10_univention-firewall_start.sh',
	'/etc/univention/templates/files/etc/dhcp/dhclient.conf',  # different IP address received, different date
	'/etc/univention/templates/files/var/lib/dovecot/sieve/default.sieve',  # different date if not commited in the same second
	'/etc/univention/templates/files/usr/share/univention-management-console/i18n/de/apps.mo',  # po-lib adds date
] + glob.glob('/etc/univention/templates/files/etc/logrotate.d/*') + glob.glob('/etc/univention/templates/files/etc/security/*.conf')


@pytest.fixture(scope="module")
def python_versions():
	try:
		with tempfile.NamedTemporaryFile(delete=False, suffix='.py') as fd1, tempfile.NamedTemporaryFile(delete=False, suffix='.py') as fd2:
			for pyversion, fd in (('2', fd1), ('3', fd2)):
				fd.write(SCRIPT.format(pyversion, os.path.basename(fd.name)).encode('utf-8'))
				fd.close()
				os.chmod(fd.name, 0o755)
			yield (('2', fd1), ('3', fd2))
	finally:
		for fd in (fd1, fd2):
			os.unlink(fd.name)


def pytest_generate_tests(metafunc):
	tempfiles = [os.path.join(path, filename) for path, dirs, files in os.walk('/etc/univention/templates/files/') for filename in files]
	tempfiles = [pytest.param(path, marks=pytest.mark.xfail) if path in ALLOWED_DIFFERENCES else path for path in tempfiles if EXECUTE_TOKEN.search(open(path, 'rb').read())]
	metafunc.parametrize('ucr_config_file', tempfiles)


def test_configfile_python_compatibility(ucr_config_file, python_versions):
	with open(ucr_config_file) as fd:
		template = fd.read()

	result = {}
	for pyversion, fd in python_versions:
		sys.executable = fd.name
		run_filter(template, ucr)

		with open('/tmp/py{0}.out'.format(pyversion), 'rb') as x:
			compiled, _, rc = x.read().decode('ISO8859-1').rstrip('\n').rpartition('\n')
			result[pyversion] = {
				'success': rc == '0',
				'compiled': compiled,
				'coverage': subprocess.check_output(r'python{0} -m coverage report | grep /tmp/py{0}.in | egrep -o [0-9]+%\$ || echo 0%'.format(pyversion), shell=True).decode('UTF-8', 'replace')
			}
			if ucr_config_file.endswith('.json'):
				try:
					result[pyversion]['compiled'] = json.dumps(json.loads(result[pyversion]['compiled']), sort_keys=True)
				except ValueError:
					result[pyversion]['json_failed'] = True
			if os.path.exists('.coverage'):
				os.unlink('.coverage')

	print('', ucr_config_file, end=':\n', sep='\n')
	for key, res in result.items():
		print('Python%s: ' % (key,), end='')
		print('|%s' % ('✅' if res['success'] else '❎'), end='')
		print('|%s' % (res['coverage'],), end='')

	result = {
		'python': result,
		'package': subprocess.check_output('dpkg -S %s 2>/dev/null | cut -d: -f1' % (pipes.quote(ucr_config_file),), shell=True).decode('UTF-8', 'replace'),
		'diff': subprocess.check_output('diff -u /tmp/py[23].out || true', shell=True).decode('UTF-8', 'replace').replace('/tmp/py', ucr_config_file),
	}

	assert all(res['success'] for res in result['python'].values()), result
	assert result['python']['2']['compiled'] == result['python']['3']['compiled'], result
