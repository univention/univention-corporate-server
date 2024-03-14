#!/usr/share/ucs-test/runner pytest-3 -s -l -vv --tb=native
## desc: Test docker network isolation
## tags: [docker]
## exposure: dangerous
## packages:
##   - docker.io

import re
import subprocess
import pytest

from univention.testing.utils import restart_firewall

from dockertest import App, get_app_name


DOCKER_COMPOSE = '''
version: '2.0'

services:
    test1:
        image: {image}
        ports:
            - "8000:8000"
        command: /sbin/init
        restart: always
    test2:
        image: {image}
        ports:
            - "9000:9000"
        command: /sbin/init
'''.replace('\t', '  ')

@pytest.mark.exposure('dangerous')    # cleanup remnants from previous tests
def test_docker_iptables(appcenter, app_name):
    restart_firewall()

    setup = '#!/bin/sh'
    store_data = '#!/bin/sh'

    app = App(name=app_name, version='1', build_package=False, call_join_scripts=False)
    try:
        app.set_ini_parameter(
            DockerMainService='test1',
        )
        app.add_script(compose=DOCKER_COMPOSE.format(image='docker-test.software-univention.de/alpine:3.7'))
        app.add_script(setup=setup)
        app.add_script(store_data=store_data)
        app.add_to_local_appcenter()
        appcenter.update()
        app.install()
        app.verify(joined=False)

        iptables_save_after_installation = subprocess.check_output(['iptables-save'], text=True)
        print(" iptables rules before firewall restart:\n" + iptables_save_after_installation)
        docker_iptables_rules = []
        for line in iptables_save_after_installation.split("\n"):
            if not re.match('^#.*', line) and not re.match('^:.*ACCEPT.*', line):
                docker_iptables_rules.append(line)

        restart_firewall()

        iptables_save_after_firewall_restart = subprocess.check_output(['iptables-save'], text=True)
        print(" iptables rules after firewall restart:\n" + iptables_save_after_firewall_restart)
        for rule in docker_iptables_rules:
            assert rule in iptables_save_after_firewall_restart, "iptables rules are inconsistent"
        print("=== iptables rules are consistent!")

    finally:
        app.uninstall()
        app.remove()
