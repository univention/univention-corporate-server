#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Check for failed systemd services before the test run
## tags: []
## exposure: safe

import subprocess

import pytest


IGNORE_UNITS = {
    # 'some-known-broken.service',
}


def run_command(args):
    return subprocess.run(args, capture_output=True, text=True, check=False)


def list_failed_units():
    proc = run_command([
        'systemctl',
        'list-units',
        '--type=service',
        '--state=failed',
        '--no-legend',
        '--no-pager',
        '--plain',
    ])

    if proc.returncode != 0:
        pytest.fail(
            'systemctl list-units failed with exit code %s\nSTDOUT:\n%s\nSTDERR:\n%s'
            % (proc.returncode, proc.stdout, proc.stderr),
        )

    units = []
    for line in proc.stdout.splitlines():
        if not line.strip():
            continue
        # UNIT LOAD ACTIVE SUB DESCRIPTION
        fields = line.split(None, 4)
        if fields:
            units.append(fields[0])
    return units


def print_unit_status(unit):
    print('\n===== systemctl status %s =====' % unit)
    subprocess.run(
        ['systemctl', 'status', unit, '--no-pager', '--full'],
        check=False,
    )

    print('\n===== journalctl -u %s -n 30 =====' % unit)
    subprocess.run(
        ['journalctl', '-u', unit, '-n', '30', '--no-pager', '--output=short-monotonic'],
        check=False,
    )


@pytest.mark.parametrize('unit', list_failed_units())
def test_no_failed_systemd_services(unit):
    if unit in IGNORE_UNITS:
        pytest.skip('Ignored failed systemd service: %s' % unit)

    print_unit_status(unit)
    pytest.fail('Systemd service is in failed state: %s' % unit)


# def test_no_failed_systemd_services_summary():
#     failed_units = list_failed_units()
#     ignored = sorted(unit for unit in failed_units if unit in IGNORE_UNITS)
#     unexpected = sorted(unit for unit in failed_units if unit not in IGNORE_UNITS)
#
#     if ignored:
#         print('Ignored failed systemd services:')
#         for unit in ignored:
#             print('  %s' % unit)
#
#     assert not unexpected, 'Unexpected failed systemd services: %s' % ', '.join(unexpected)
