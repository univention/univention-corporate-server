#!/usr/share/ucs-test/runner pytest-3 -s
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
from time import sleep

import ldap
import pytest

import univention.config_registry
import univention.uldap


ucr = univention.config_registry.ConfigRegistry()
ucr.load()


def _cleanup(old_retry_count):
    print('CLEANUP')
    _set_retry_count(old_retry_count)
    _start_slapd()
    # Give the system a few seconds otherwise the following test case might be fail
    sleep(15)


def _get_connection():
    return univention.uldap.getMachineConnection(ldap_master=False)


def _search(lo):
    lo.searchDn('cn=users')


def _dump_journal():
    subprocess.Popen(['journalctl', '-xn']).wait()


def _stop_slapd():
    rc = subprocess.Popen(['systemctl', 'stop', 'slapd']).wait()
    _dump_journal()
    return rc


def _start_slapd():
    rc = subprocess.Popen(['systemctl', 'start', 'slapd']).wait()
    _dump_journal()
    return rc


def _start_delayed(delay):
    subprocess.Popen('sleep %s; systemctl start slapd' % delay, shell=True)


def _wait_for_slapd_to_be_started():
    # This could be done a little bit better
    sleep(5)


def _set_retry_count(count):
    if count:
        univention.config_registry.handler_set(['ldap/client/retry/count=%s' % count])
    else:
        univention.config_registry.handler_unset(['ldap/client/retry/count'])


def _print_test_header(header):
    print('\n************************************************************************')
    print(header)
    print('************************************************************************')


def _give_systemd_some_time():
    sleep(5)


old_retry_count = ucr.get('ldap/client/retry/count')

_set_retry_count(10)


@pytest.fixture(scope='session', autouse=True)
def cleanup():
    yield
    _cleanup(old_retry_count)


@pytest.mark.parametrize('operations', [
    ["connect", ("search", True), "stop", ("start", 0), ("search", True)],
    ["stop", ("start", 7), "connect", ("search", True)],
    ["connect", "stop", ("start", 7), ("search", True)],
    ["stop", ("start", 11), ("search", False)],
    ["connect", "stop", ("start", 11), ("search", False)],
])
def test_reconnect_uldap(operations):
    _give_systemd_some_time()
    _print_test_header('Test: %r' % operations)
    lo = None
    for op in operations:
        if isinstance(op, tuple):
            if op[0] == 'start':
                if op[1]:
                    _start_delayed(delay=op[1])
                else:
                    _start_slapd()
            elif op[0] == 'search':
                try:
                    if not lo:
                        lo = _get_connection()
                    _search(lo)
                except ldap.SERVER_DOWN:
                    if op[1]:
                        raise

            else:
                raise Exception('Unknown operation: %s' % op[0])
        else:
            if op == 'connect':
                lo = _get_connection()
            elif op == 'stop':
                _stop_slapd()
            else:
                raise Exception('Unknown operation: %s' % op)
    _wait_for_slapd_to_be_started()
