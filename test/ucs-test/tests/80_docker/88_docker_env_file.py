#!/usr/share/ucs-test/runner pytest-3 -s -l -vv --tb=native
## desc: Test docker compose - with env file
## tags: [docker]
## exposure: dangerous
## packages:
##   - docker.io

import subprocess

import pytest

from univention.config_registry import ConfigRegistry

from dockertest import App


DOCKER_COMPOSE = '''
version: '2.0'

services:
    test1:
        image: {image}
        command: /sbin/init
        restart: always
    test2:
        image: {image}
        command: /sbin/init
        restart: always
'''.replace('\t', '  ')

ENV = '''
REDIS_PORT_6379_TCP_ADDR=test2
REDIS_PORT_6379_TCP_PORTc=6379
TEST_HOSTNAME=@%@hostname@%@
'''


@pytest.mark.exposure('dangerous')
def test_docker_env_file(appcenter, app_name):
    setup = '#!/bin/sh'
    store_data = '#!/bin/sh'

    app = App(name=app_name, version='1', build_package=False, call_join_scripts=False)
    try:
        app.set_ini_parameter(
            DockerMainService='test1',
            DockerInjectEnvFile='main',
        )
        app.add_script(compose=DOCKER_COMPOSE.format(image='docker-test.software-univention.de/alpine:3.6'))
        app.add_script(env=ENV)
        app.add_script(setup=setup)
        app.add_script(store_data=store_data)
        app.add_to_local_appcenter()
        appcenter.update()
        app.install()
        app.verify()
        env_file = f'/var/lib/univention-appcenter/apps/{app_name}/compose/{app_name}.env'
        subprocess.call(['ls', '-la', env_file])
        env_content = open(env_file).read()
        ucr = ConfigRegistry()
        ucr.load()
        assert (f'TEST_HOSTNAME={ucr.get("hostname")}') in env_content, env_content
        env_container = subprocess.check_output(['univention-app', 'shell', app_name, 'env'], text=True)
        assert (f'TEST_HOSTNAME={ucr.get("hostname")}') in env_container, env_container
    finally:
        app.uninstall()
        app.remove()
