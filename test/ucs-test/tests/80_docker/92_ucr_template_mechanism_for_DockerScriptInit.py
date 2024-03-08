#!/usr/share/ucs-test/runner pytest-3 -s -l -vv --tb=native
## desc: Test ucr template mechanism for Docker apps
## tags: [docker]
## exposure: dangerous
## packages:
##   - docker.io

import json
import subprocess

import pytest

from univention.testing.ucr import UCSTestConfigRegistry
from univention.testing.utils import fail

from dockertest import tiny_app


def check_docker_arg_against_ucrv(container_id, ucrv):
    docker_inspect = subprocess.check_output(["docker", "inspect", f"{container_id}"], close_fds=True)
    args = json.loads(docker_inspect)[0]['Args']
    first_arg = args[0].split("=", 1)[1]
    if first_arg != ucrv:
        fail(f'\nThe container argument is not equal to the ucr variable it is checked against.\nDocker container argument: {first_arg}\nUCRV: {ucrv}\n')


@pytest.mark.exposure('dangerous')
def test_ucr_template_mechanism_for_docker_script_init(appcenter, app_name, app_version):
    with UCSTestConfigRegistry() as ucr:
        ucr.load()
        app = tiny_app(app_name, app_version)
        try:
            app.set_ini_parameter(
                DockerScriptSetup='/tmp/setup',
                DockerScriptInit='/sbin/init --test=@%@ldap/base@%@',
            )
            app.add_script(setup='#!/bin/sh')
            app.add_to_local_appcenter()
            appcenter.update()
            app.install()
            app.verify()
            check_docker_arg_against_ucrv(app.container_id, ucr.get('ldap/base'))
        finally:
            try:
                app.uninstall()
            except Exception:
                fail('Could not uninstall app. Trying to remove..')
            app.remove()
