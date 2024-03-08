#!/usr/share/ucs-test/runner pytest-3 -s -l -vv --tb=native
## desc: Test univention-app reinitialize
## tags: [docker]
## exposure: dangerous
## bugs: [50718]
## packages:
##   - docker.io

import subprocess

import pytest

from dockertest import App


DOCKER_COMPOSE = '''
version: '2.0'

services:
    test1:
        image: {image}
        ports:
            - "8000:8000"
        links:
            - test2:test2
        command: /sbin/init
        restart: always
    test2:
        image: {image}
        command: /sbin/init
        restart: always
'''.replace('\t', '  ')

SETTINGS = '''
[TEST_KEY]
Type = String
Show = Install
Description = Just a test
InitialValue = 1

[EMPTY_KEY]
Type = String
Show = Install, Settings
Description = Shall not have a value, especially not "None"
InitialValue =
'''


@pytest.mark.exposure('dangerous')
def test_docker_reinitialize(appcenter, app_name):
    store_data = '#!/bin/sh'
    configure_host = f'''#!/bin/sh
if [ "$1" = "settings" ]; then
univention-app reinitialize {app_name}
fi
'''

    app = App(name=app_name, version='1', build_package=False, call_join_scripts=False)
    try:
        app.set_ini_parameter(
            DockerMainService='test1',
            DockerScriptSetup='',
        )
        app.add_script(compose=DOCKER_COMPOSE.format(image='docker-test.software-univention.de/alpine:3.6'))
        app.add_script(settings=SETTINGS)
        app.add_script(store_data=store_data)
        app.add_script(configure_host=configure_host)
        app.add_to_local_appcenter()
        appcenter.update()
        app.install()
        app.verify()
        env = subprocess.check_output(f'univention-app shell {app_name} env', shell=True, text=True)
        assert 'TEST_KEY=1' in env, env
        subprocess.call(f'univention-app configure {app_name} --set TEST_KEY=2', shell=True)
        env = subprocess.check_output(f'univention-app shell {app_name} env', shell=True, text=True)
        assert 'TEST_KEY=2' in env, env
        assert 'EMPTY_KEY' not in env, env
    finally:
        app.uninstall()
        app.remove()
