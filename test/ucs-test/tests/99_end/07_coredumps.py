#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Check for unexpected systemd coredumps
## roles-not: [basesystem]
## packages:
##  - systemd-coredump
## tags: []
## exposure: safe

import json
import subprocess

import pytest


IGNORE_EXE = {
    '/usr/sbin/rsyslogd',
    '/usr/libexec/samba/rpcd_spoolss',  # Bug #59550: triggered by 59_udm.64_test_udm_printers function test_create_printer_and_check_printing_works
}


def coredumpctl_json():
    proc = subprocess.run(['coredumpctl', '--json=short', 'list'], capture_output=True, text=True, check=False)

    if not proc.stdout.strip():
        return []

    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        pytest.fail('Could not parse coredumpctl JSON output: %s\n%s' % (exc, proc.stdout))

    # coredumpctl returns 1 if no cores are found. but stdout is empty then. so we already returned.
    if proc.returncode != 0:
        pytest.fail('coredumpctl failed with exit code %s\nSTDOUT:\n%s\nSTDERR:\n%s' % (proc.returncode, proc.stdout, proc.stderr))


# provoke a coredump, to test this via:
# python3 -c 'import ctypes; ctypes.string_at(0)'

# analyse with: apt install univention-directory-listener-dbgsym univention-directory-notifier-dbgsym libc6-dbg libldap2-dbgsym python3-dbg
# coredumpctl debug "$ID" will open gdb
def test_no_coredumps():
    subprocess.call(['coredumpctl', 'list'])
    dumps = coredumpctl_json()

    unexpected = []
    ignored = []

    for dump in dumps:
        exe = dump.get('exe')
        if exe in IGNORE_EXE:
            ignored.append(dump)
        else:
            unexpected.append(dump)

    if ignored:
        print('Ignored coredumps:')
        for dump in ignored:
            print('  PID=%s EXE=%s COMM=%s TIME=%s' % (dump.get('pid'), dump.get('exe'), dump.get('comm'), dump.get('time')))

    assert not unexpected, '\n'.join(
        ['Unexpected coredumps found:']
        + [
            '  PID=%s EXE=%s COMM=%s SIGNAL=%s TIME=%s' % (dump.get('pid'), dump.get('exe'), dump.get('comm'), dump.get('signal'), dump.get('time'))
            for dump in unexpected
        ],
    )
