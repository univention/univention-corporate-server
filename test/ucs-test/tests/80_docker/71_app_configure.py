#!/usr/share/ucs-test/runner pytest-3 -s -vv --tb=native
## desc: Test the .configure script for Apps
## tags: [docker]
## exposure: dangerous
## packages:
##   - docker.io

import pytest

from dockertest import tiny_app


@pytest.mark.exposure('dangerous')
def test_app_configure(appcenter, app_name, app_version):
    app = tiny_app(app_name, app_version)
    try:
        app.set_ini_parameter(
            DockerScriptConfigure='/tmp/configure',
            DockerScriptSetup='/tmp/setup')
        app.add_script(configure='''#!/bin/sh
set -x
echo "Configuring the App"
echo -n "$(more /etc/univention/base.conf | sed -ne 's|^test/configure/param: ||p')"  > /tmp/configure.output
exit 0
''')
        app.add_script(setup='#!/bin/sh')
        app.add_to_local_appcenter()
        appcenter.update()
        app.install()
        app.verify()
        configured_file = app.file('/tmp/configure.output')
        app.configure({'test/configure/param': 'test1'})
        assert open(configured_file).read() == 'test1'
        app.configure({'test/configure/param': 'test2'})
        assert open(configured_file).read() == 'test2'
        app.configure({'test/configure/param': None})
        assert open(configured_file).read() == ''
    finally:
        app.uninstall()
        app.remove()
