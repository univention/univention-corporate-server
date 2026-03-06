#!/usr/share/ucs-test/runner pytest-3 -s -l -vv --tb=native
## desc: Test docker compose network overlap avoidance
## tags: [docker]
## exposure: dangerous
## packages:
##   - docker.io

from ipaddress import IPv4Address, IPv4Network

import pytest

from univention.appcenter.docker import docker_get_existing_subnets
from univention.config_registry import ConfigRegistry, handler_set, handler_unset

from dockertest import App


DOCKER_COMPOSE = '''
version: '2.0'

services:
    test1:
        image: docker-test.software-univention.de/alpine:3.6
        command: /sbin/init
        restart: always
'''.replace('\t', '  ')


def _first_free_subnet():
    """Return the first /24 in the compose pool not blocked by gateway or existing Docker networks."""
    ucr = ConfigRegistry()
    ucr.load()
    pool = IPv4Network(ucr.get('appcenter/docker/compose/network', '172.16.1.1/16'), strict=False)
    gateway = IPv4Address(pool.exploded.split('/')[0])
    used = set(docker_get_existing_subnets())
    for subnet in pool.subnets(24 - pool.prefixlen):
        if gateway in subnet:
            continue
        if any(s.overlaps(subnet) for s in used):
            continue
        return subnet
    raise RuntimeError('No free /24 subnet available in compose pool')


@pytest.fixture
def dummy_interface():
    subnet = _first_free_subnet()
    handler_set([
        f'interfaces/testdummy/address={subnet[1]}',
        'interfaces/testdummy/netmask=255.255.255.0',
    ])
    yield subnet
    handler_unset(['interfaces/testdummy/address', 'interfaces/testdummy/netmask'])


@pytest.mark.exposure('dangerous')
def test_network_overlap_compose_install(appcenter, app_name, app_version, dummy_interface):
    app = App(name=app_name, version=app_version, build_package=False, call_join_scripts=False)
    try:
        app.set_ini_parameter(DockerMainService='test1')
        app.add_script(compose=DOCKER_COMPOSE)
        app.add_script(setup='#!/bin/sh')
        app.add_script(store_data='#!/bin/sh')
        app.add_to_local_appcenter()
        appcenter.update()
        app.install()
        ucr = ConfigRegistry()
        ucr.load()
        app_network = IPv4Network(ucr[f'appcenter/apps/{app_name}/ip'], strict=False)
        assert not app_network.overlaps(dummy_interface)
    finally:
        app.uninstall()
        app.remove()
