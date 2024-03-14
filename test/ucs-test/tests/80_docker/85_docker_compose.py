#!/usr/share/ucs-test/runner pytest-3 -s -l -vv --tb=native
## desc: Test docker compose
## tags: [docker]
## exposure: dangerous
## packages:
##   - docker.io

import subprocess
import pytest

from ruamel import yaml

from dockertest import App, Appcenter, get_app_name


DOCKER_COMPOSE = '''
version: '2.0'

services:
    test1:
        image: {image}
        ports:
            - "8000:8000"
        environment:
            REDIS_PORT_6379_TCP_ADDR: test2
            REDIS_PORT_6379_TCP_PORT: 6379
        links:
            - test2:test2
        command: /sbin/init
        restart: always
    test2:
        image: {image}
        volumes:
            - /var/lib/univention-appcenter/apps/ethercalc/redis:/data
        environment:
            TEST_KEY: "@%@85_docker_compose/test_key@%@"
        command: /sbin/init
        restart: always
'''.replace('\t', '  ')

SETTINGS = '''
[85_docker_compose/test_key]
Type = String
Show = Install
Description = Just a test
InitialValue = This is a test
'''

@pytest.mark.exposure('dangerous')
def test_docker_compose(appcenter):
    name = get_app_name()
    setup = '#!/bin/sh'
    store_data = '#!/bin/sh'

    alpine_checksum = 'f80194ae2e0c'
    images = subprocess.check_output(['docker', 'images'], text=True)
    if alpine_checksum in images:
        print('CAUTION. Checksum already found in docker images... Lets see...')
        subprocess.call(['docker', 'ps', '-a'])
    app = App(name=name, version='1', build_package=False, call_join_scripts=False)
    try:
        app.set_ini_parameter(
            DockerMainService='test1',
        )
        app.add_script(compose=DOCKER_COMPOSE.format(image='docker-test.software-univention.de/alpine:3.5'))
        app.add_script(settings=SETTINGS)
        app.add_script(setup=setup)
        app.add_script(store_data=store_data)
        app.add_to_local_appcenter()
        appcenter.update()
        app.install()
        app.verify(joined=False)
        images = subprocess.check_output(['docker', 'images'], text=True)
        assert alpine_checksum in images, images
        app.execute_command_in_container(f'touch /var/lib/univention-appcenter/apps/{name}/data/test1.txt')

        app = App(name=name, version='2', build_package=False, call_join_scripts=False)
        app.set_ini_parameter(
            DockerMainService='test1',
        )
        app.add_script(compose=DOCKER_COMPOSE.format(image='docker-test.software-univention.de/alpine:3.7'))
        app.add_script(setup=setup)
        app.add_script(store_data=store_data)
        app.add_to_local_appcenter()
        appcenter.update()
        app.upgrade()
        app.verify(joined=False)
        images = subprocess.check_output(['docker', 'images'], text=True)
        assert alpine_checksum not in images, images
        app.execute_command_in_container(f'ls /var/lib/univention-appcenter/apps/{name}/data/test1.txt')
        image = subprocess.check_output(['docker', 'inspect', app.container_id, '--format={{.Config.Image}}'], text=True).strip()
        assert image == 'docker-test.software-univention.de/alpine:3.7'
        from univention.config_registry import ConfigRegistry
        ucr = ConfigRegistry()
        ucr.load()
        network = ucr.get('appcenter/apps/' + name + '/ip')
        assert network == '172.16.1.0/24', network
        yml_file = f'/var/lib/univention-appcenter/apps/{name}/compose/docker-compose.yml'
        content = yaml.load(open(yml_file), yaml.RoundTripLoader, preserve_quotes=True)
        assert content['networks']['appcenter_net']['ipam']['config'][0]['subnet'] == '172.16.1.0/24'
        assert content['services']['test1']['networks']['appcenter_net']['ipv4_address'] == '172.16.1.2'
        assert content['services']['test2']['networks']['appcenter_net']['ipv4_address'] == '172.16.1.3'
        assert content['services']['test2']['environment']['TEST_KEY'] == 'This is a test', content['services']['test2']['environment']
    finally:
        app.uninstall()
        app.remove()
