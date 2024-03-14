#!/usr/share/ucs-test/runner pytest-3 -s -vv --tb=native
## desc: Create and install a simple docker app and check ports redirection constraints
## tags: [docker]
## exposure: dangerous
## packages:
##   - docker.io

import pytest

from univention.testing.utils import is_port_open

from dockertest import Appcenter, UCSTest_DockerApp_InstallationFailed, get_app_version, tiny_app


@pytest.mark.exposure('dangerous')
def test_app_ports_conflicts_redirect(appcenter, app_version):
    exclusive = tiny_app(name='exclusive', version=app_version)
    redirect = tiny_app(name='redirect', version=app_version)
    dummy = tiny_app(name='dummy', version=app_version)

    for port in [21, 23, 40021, 40023]:
        assert not is_port_open(port)

    try:
        exclusive.set_ini_parameter(
            PortsExclusive='23,24,40023',
            DockerScriptSetup='/usr/sbin/%s-setup')
        exclusive.add_script(setup='#!/bin/sh')

        redirect.set_ini_parameter(
            PortsRedirection='40021:21,40023:23',
            DockerScriptSetup='/usr/sbin/%s-setup')
        redirect.add_script(setup='#!/bin/sh')

        dummy.set_ini_parameter(
            DockerScriptSetup='/usr/sbin/%s-setup')
        dummy.add_script(setup='#!/bin/sh')

        exclusive.add_to_local_appcenter()
        redirect.add_to_local_appcenter()
        dummy.add_to_local_appcenter()
        appcenter.update()

        # check if installation fails
        # if exclusive port is already used
        redirect.install()
        redirect.verify(joined=False)
        with pytest.raises(UCSTest_DockerApp_InstallationFailed):
            exclusive.install()

        # another app should be fine
        dummy.install()
        dummy.verify(joined=False)
    finally:
        exclusive.uninstall()
        exclusive.remove()
        redirect.uninstall()
        redirect.remove()
        dummy.uninstall()
        dummy.remove()
