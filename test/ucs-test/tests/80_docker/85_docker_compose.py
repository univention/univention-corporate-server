#!/usr/share/ucs-test/runner pytest-3 -s -l -vv --tb=native
## desc: Test docker compose
## tags: [docker]
## exposure: dangerous
## packages:
##   - docker.io

import subprocess
from ipaddress import IPv4Address, IPv4Network

import pytest
from ruamel import yaml

from univention.appcenter.docker import docker_get_existing_subnets
from univention.config_registry import ConfigRegistry

from dockertest import App, get_app_name


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
    ucr = ConfigRegistry()
    ucr.load()
    docker0_net = IPv4Network('%s' % (ucr.get('appcenter/docker/compose/network', '172.16.1.1/16'),), False)
    gateway, netmask = docker0_net.exploded.split('/', 1)  # '172.16.1.1', '16'
    prefixlen_diff = 24 - int(netmask)
    target_subnet = None
    for network in docker0_net.subnets(prefixlen_diff):
        if IPv4Address('%s' % (gateway,)) in network:
            continue
        if any(app_network.overlaps(network) for app_network in docker_get_existing_subnets()):
            continue
        target_subnet = network
        break
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
        app.verify()
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
        app.verify()
        images = subprocess.check_output(['docker', 'images'], text=True)
        assert alpine_checksum not in images, images
        app.execute_command_in_container(f'ls /var/lib/univention-appcenter/apps/{name}/data/test1.txt')
        image = subprocess.check_output(['docker', 'inspect', app.container_id, '--format={{.Config.Image}}'], text=True).strip()
        assert image == 'docker-test.software-univention.de/alpine:3.7'
        ucr.load()
        network = ucr.get('appcenter/apps/' + name + '/ip')
        # assert network == '172.16.1.0/24', network

        assert network == target_subnet.exploded
        yml_file = f'/var/lib/univention-appcenter/apps/{name}/compose/docker-compose.yml'
        content = yaml.load(open(yml_file), yaml.RoundTripLoader, preserve_quotes=True)
        assert content['networks']['appcenter_net']['ipam']['config'][0]['subnet'] == target_subnet.exploded
        # assert content['services']['test1']['networks']['appcenter_net']['ipv4_address'] == '172.16.1.2'
        assert content['services']['test1']['networks']['appcenter_net']['ipv4_address'] == target_subnet[2].exploded
        # assert content['services']['test2']['networks']['appcenter_net']['ipv4_address'] == '172.16.1.3'
        assert content['services']['test2']['networks']['appcenter_net']['ipv4_address'] == target_subnet[3].exploded
        assert content['services']['test2']['environment']['TEST_KEY'] == 'This is a test', content['services']['test2']['environment']
    finally:
        app.uninstall()
        app.remove()
