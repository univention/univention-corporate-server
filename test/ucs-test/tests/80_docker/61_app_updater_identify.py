#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Check updater/identify in a new Docker App
## tags: [docker]
## exposure: dangerous
## packages:
##   - docker.io

import pytest

from dockertest import tiny_app


@pytest.mark.exposure('dangerous')
def test_app_updater_identify(appcenter):
    app = tiny_app()

    try:
        app.add_to_local_appcenter()

        appcenter.update()

        app.install()

        app.verify()

        identify = app.execute_command_in_container("env | sed -rne 's/UPDATER_IDENTIFY=//p'")
        print(f'Identify: {identify}')
        assert identify.strip() == 'Docker App'
    finally:
        app.uninstall()
        app.remove()
