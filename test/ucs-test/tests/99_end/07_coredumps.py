#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Check for unexpected systemd coredumps
## roles-not: [basesystem]
## packages:
##  - systemd-coredump
## tags: []
## exposure: safe

import collections
import json
import subprocess

import pytest
from pytest_subtests import SubTests


IGNORE_EXE = {
    '/usr/sbin/rsyslogd',
    '/usr/libexec/samba/rpcd_spoolss',  # Bug #59550: triggered by 59_udm.64_test_udm_printers function test_create_printer_and_check_printing_works
}


def coredumpctl_json():
    proc = subprocess.run(['coredumpctl', '--json=short', 'list'], capture_output=True, text=True, check=False)

    # coredumpctl returns 1 if no cores are found. stdout is empty then.
    if not proc.stdout.strip():
        return []

    if proc.returncode != 0:
        pytest.fail('coredumpctl failed with exit code %s\nSTDOUT:\n%s\nSTDERR:\n%s' % (proc.returncode, proc.stdout, proc.stderr))

    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        pytest.fail('Could not parse coredumpctl JSON output: %s\n%s' % (exc, proc.stdout))


def dump_id(dump):
    # PID is usually enough for this test run. Add time/exe to printed output for humans.
    return str(dump.get('pid'))


def dump_summary(dump):
    return 'PID=%s EXE=%s COMM=%s SIGNAL=%s TIME=%s' % (
        dump.get('pid'),
        dump.get('exe'),
        dump.get('comm'),
        dump.get('signal'),
        dump.get('time'),
    )


def print_coredump_info(dump):
    ident = dump_id(dump)

    print('\n===== coredumpctl info %s =====' % ident)
    subprocess.run(['coredumpctl', 'info', ident], check=False)


def group_by_exe(dumps):
    grouped = collections.defaultdict(list)
    for dump in dumps:
        grouped[dump.get('exe') or '<unknown exe>'].append(dump)
    return dict(sorted(grouped.items()))


# provoke a coredump to test this via:
# python3 -c 'import ctypes; ctypes.string_at(0)'
#
# analyse with:
# apt install univention-directory-listener-dbgsym univention-directory-notifier-dbgsym libc6-dbg libldap2-dbgsym python3-dbg
# coredumpctl debug "$ID" will open gdb interactively
def test_no_coredumps(subtests: SubTests):
    subprocess.call(['coredumpctl', 'list'])
    dumps = coredumpctl_json()

    grouped = group_by_exe(dumps)

    for exe, exe_dumps in grouped.items():
        with subtests.test(exe=exe):
            for dump in exe_dumps:
                print('  %s' % dump_summary(dump))
                print_coredump_info(dump)

            if exe in IGNORE_EXE:
                pytest.skip('Ignored coredumps for EXE=%s' % exe)

            pytest.fail('\n'.join(['Unexpected coredumps found for EXE=%s:' % exe] + ['  %s' % dump_summary(dump) for dump in exe_dumps]))
