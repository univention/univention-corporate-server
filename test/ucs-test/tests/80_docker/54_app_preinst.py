#!/usr/share/ucs-test/runner pytest-3 -s -vv --tb=native
## desc: Check the preinst script
## tags: [docker]
## exposure: dangerous
## packages:
##   - docker.io

import subprocess

import pytest

from dockertest import Appcenter, AppFailure, tiny_app


@pytest.mark.exposure('dangerous')
@pytest.mark.parametrize("fail_in_preinst", [False, True])
def test_create_app(appcenter: Appcenter, fail_in_preinst: bool, app_name: str, app_version: str) -> None:
    app = tiny_app(app_name, app_version)
    try:
        app.add_script(preinst='''#!/bin/bash
set -x -e
echo "Test preinst script"
if [ "%(exit_code)d" = "0" ]; then
    ucr set appcenter/apps/%(app_name)s/docker/params="-e FOO=bar -e repository_app_center_server=my.server"
fi
exit %(exit_code)d
''' % {'exit_code': (1 if fail_in_preinst else 0), 'app_name': app_name})

        app.add_to_local_appcenter()

        appcenter.update()

        try:
            app.install()
            app.verify(joined=False)
        except AppFailure:
            if not fail_in_preinst:
                raise
        else:
            if fail_in_preinst:
                raise ValueError('Should not have been installed!')
            else:
                output = subprocess.check_output(['univention-app', 'shell', app_name, 'env'], text=True)
                if 'FOO=bar' not in output or 'repository_app_center_server=my.server' not in output:
                    raise ValueError('Setting docker/params does not work')

    finally:
        app.uninstall()
        app.remove()
