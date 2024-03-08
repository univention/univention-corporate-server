#!/usr/share/ucs-test/runner pytest-3 -s -l -vv --tb=native
## desc: Test the .configure script for Apps (reinitialize)
## tags: [docker]
## exposure: dangerous
## bugs: [53761]
## packages:
##   - docker.io

import pytest

from dockertest import tiny_app


def assert_content(app, expected):
    app.reload_container_id()
    configured_file = app.file('/tmp/configure.output')
    print('Searching in', configured_file, 'for', expected)
    content = open(configured_file).read()
    assert content == expected, f'{content!r} != {expected!r}'


@pytest.mark.exposure('dangerous')
def test_app_configure_reinitialize(appcenter, app_name, app_version):
    app = tiny_app(app_name, app_version)
    try:
        app.set_ini_parameter(
            DockerScriptConfigure='/tmp/configure',
        )
        app.add_script(settings='''[CONFIGURE_PARAM]
Type = String
Description = Just a simple parameter
Show = Install, Settings
''')
        app.add_script(configure_host=f'''#!/bin/sh
set -x
if [ "$1" = "settings" ]; then
echo "Recreating the App from outside"
univention-app reinitialize {app.app_name}
fi
exit 0
''')
        app.add_script(configure='''#!/bin/sh
set -x
echo "Configuring the App"
echo -n "$CONFIGURE_PARAM"  > /tmp/configure.output
exit 0
''')
        app.add_to_local_appcenter()
        appcenter.update()
        app.install()
        app.verify()
        app.configure({'CONFIGURE_PARAM': 'test1'})
        assert_content(app, 'test1')
        app.configure({'CONFIGURE_PARAM': 'test2'})
        assert_content(app, 'test2')
        app.configure({'CONFIGURE_PARAM': None})
        assert_content(app, '')
    finally:
        app.uninstall()
        app.remove()
