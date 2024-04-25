#!/usr/share/ucs-test/runner python3
## desc: Test reconnect mechanism of uldap
## tags: [reconnect]
## roles-not:
##  - basesystem
##  - memberserver
## packages:
##  - python3-univention
## bugs:
##  - 34292
## exposure: dangerous

import subprocess
from contextlib import contextmanager
from time import sleep

import ldap

import univention.uldap
from univention.testing.ucr import UCSTestConfigRegistry
from univention.testing.utils import fail, start_slapd, stop_slapd


@contextmanager
def _cleanup():
    yield
    print('CLEANUP')
    _start_slapd()
    # Give the system a few seconds otherwise the following test case might be fail
    sleep(15)


def _get_connection():
    return univention.uldap.getMachineConnection(ldap_master=False)


def _search(lo):
    lo.searchDn('cn=users')


def _dump_journal():
    subprocess.call(['journalctl', '-xn'])


def _stop_slapd():
    stop_slapd()
    _dump_journal()


def _start_slapd():
    start_slapd()
    _dump_journal()


def _start_delyed(delay):
    subprocess.Popen('sleep %s; invoke-rc.d slapd start' % delay, shell=True)


def _wait_for_slapd_to_be_started():
    # This could be done a little bit better
    sleep(5)


def _print_test_header(header):
    print('\n************************************************************************')
    print(header)
    print('************************************************************************')


def _give_systemd_some_time():
    sleep(5)


with UCSTestConfigRegistry() as ucr, _cleanup():
    ucr.handler_set(['ldap/client/retry/count=10'])

    _give_systemd_some_time()
    _print_test_header('Test: connect, search, stop, start, search')
    lo = _get_connection()
    _search(lo)
    _stop_slapd()
    _start_slapd()
    _search(lo)
    _wait_for_slapd_to_be_started()

    _give_systemd_some_time()
    _print_test_header('Test: stop, connect - start after 9 seconds, search')
    _stop_slapd()
    _start_delyed(delay=8)
    lo = _get_connection()
    _search(lo)
    _wait_for_slapd_to_be_started()

    _give_systemd_some_time()
    _print_test_header('Test: connect, stop,  - start after 9 seconds, search')
    lo = _get_connection()
    _stop_slapd()
    _start_delyed(delay=8)
    _search(lo)
    _wait_for_slapd_to_be_started()

    _give_systemd_some_time()
    _print_test_header('Test: stop, connect - start after 11 seconds (which is too late), search')
    _stop_slapd()
    _start_delyed(delay=11)
    try:
        lo = _get_connection()
        _search(lo)
    except ldap.SERVER_DOWN:
        pass
    else:
        fail('Search was successful')
    _wait_for_slapd_to_be_started()

    _give_systemd_some_time()
    _print_test_header('Test: connect, stop - start after 11 seconds (which is too late), search')
    lo = _get_connection()
    _stop_slapd()
    _start_delyed(delay=11)
    try:
        _search(lo)
    except ldap.SERVER_DOWN:
        pass
    else:
        fail('Search was successful')
    _wait_for_slapd_to_be_started()
