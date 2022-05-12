#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Create and move computer, should keep SSL certificate
## tags: [udm-computers,apptest]
## bugs: [41230]
## roles: [domaincontroller_master]
## exposure: careful
## versions:
##  4.1-2: fixed

from subprocess import PIPE, Popen
from time import sleep

import pytest

from univention.testing.strings import random_string


def get_ssl(name):
	for i in range(10):
		cmd = ('univention-certificate', 'list')
		proc = Popen(cmd, stdout=PIPE)
		for line in proc.stdout:
			seq, fqdn = line.split(None, 1)
			if fqdn.startswith(name.encode('UTF-8')):
				return int(seq, 16)
		print(i)
		sleep(1)
	raise LookupError('not found')


@pytest.mark.tags('udm-computers', 'apptest')
@pytest.mark.roles('domaincontroller_master')
@pytest.mark.exposure('careful')
@pytest.mark.parametrize('role', ['computers/domaincontroller_master', 'computers/domaincontroller_backup', 'computers/domaincontroller_slave', 'computers/memberserver'])
def test_move_computer_ssl(udm, role):
			"""Create and move computer, should keep SSL certificate"""
			# bugs: [41230]
			test_ou = udm.create_object('container/ou', name=random_string())
			name = random_string()
			computer = udm.create_object(role, name=name)
			old_seq = get_ssl(name)

			udm.move_object(role, dn=computer, position=test_ou)
			new_seq = get_ssl(name)

			assert old_seq == new_seq, 'New SSL certificate for "%s": %x -> %x' % (name, old_seq, new_seq)
