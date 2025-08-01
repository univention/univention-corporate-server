#!/usr/share/ucs-test/runner pytest-3 -s -vvv
## desc: Tests the Univention Self Service
## tags: [apptest]
## roles: [domaincontroller_slave]
## exposure: dangerous
## packages:
## - univention-self-service
## - univention-self-service-passwordreset-umc

import subprocess


SERVICE = 'univention-self-service-passwordreset-umc.service'


def test_memcached_service_disabled_on_replicas():
    cmd = subprocess.run(['systemctl', 'show', SERVICE], check=True, capture_output=True)
    lines = cmd.stdout.decode().split('\n')[:-1]

    unit_status = dict(line.split('=', maxsplit=1) for line in lines)

    attributes_to_check = {
        'UnitFileState': 'disabled',
        'ActiveState': 'inactive',
    }

    for key, value in attributes_to_check.items():
        assert value == unit_status[key]
