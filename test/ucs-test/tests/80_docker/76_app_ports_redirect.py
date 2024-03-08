#!/usr/share/ucs-test/runner pytest-3 -s -vv --tb=native
## desc: Create and install a simple docker app and check ports redirect
## tags: [docker]
## exposure: dangerous
## packages:
##   - docker.io

# from textwrap import dedent

import pytest

from univention.testing.utils import is_port_open, is_udp_port_open, restart_firewall

from dockertest import tiny_app


@pytest.mark.exposure('dangerous')
def test_app_ports_redirect(appcenter):
    app = tiny_app()
    ports = ['4021:21', '4023:23']
    udp_ports = ['6100:6100', '7999:7999']
    packages = ['telnetd', 'proftpd']

    # check ports are unused
    for port in ports:
        host_port, _container_port = port.split(':')
        assert not is_port_open(host_port)

    try:
        # check ports exclusive
        app.set_ini_parameter(
            # DockerScriptInit='/usr/sbin/proftpd -n',
            # DockerScriptInit='/bin/sh',
            # DockerImage='debian:buster-slim',
            DockerImage='instantlinux/proftpd',
            DockerInjectEnvFile='main',
            PortsRedirection=','.join(ports),
            PortsRedirectionUDP=','.join(udp_ports),
            DefaultPackages=','.join(packages),
            # DockerScriptSetup='/usr/sbin/%s-setup' % app.app_name
        )
        app.add_script(env='\nPASV_ADDRESS=0.0.0.0\n')
#            app.add_script(setup=dedent('''\
#                #!/bin/bash
#                apt update
#                apt install --assume-yes telnetd proftpd-basic
#                proftpd
#            '''))
        app.add_to_local_appcenter()
        appcenter.update()
        app.install()

        # check ports are open
        for port in ports:
            host_port, _container_port = port.split(':')
            assert is_port_open(host_port)
        for port in udp_ports:
            host_port, _container_port = port.split(':')
            assert is_udp_port_open(host_port)

        restart_firewall()

        # check ports are open
        for port in ports:
            host_port, _container_port = port.split(':')
            assert is_port_open(host_port)
        for port in udp_ports:
            host_port, _container_port = port.split(':')
            assert is_udp_port_open(host_port)
    finally:
        app.uninstall()
        app.remove()

    # check ports are unused
    for port in ports:
        host_port, _container_port = port.split(':')
        assert not is_port_open(host_port)
