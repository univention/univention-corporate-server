#!/usr/share/ucs-test/runner pytest-3 -s -vv --tb=native
## desc: Create and install multiple Docker Apps at once
## tags: [WIP,docker]
## timeout: 7200
## exposure: dangerous
## packages:
##   - docker.io

import pytest

from dockertest import Appcenter, tiny_app_apache


DOCKER_APP_COUNT = 20


@pytest.mark.skip()
@pytest.mark.exposure('dangerous')
def test_app_scaling(appcenter: Appcenter, app_name: str, app_version: str) -> None:
    apps = []

    try:
        for i in range(DOCKER_APP_COUNT):
            app = tiny_app_apache(app_name, app_version)
            app.set_ini_parameter(
                WebInterface=f'/{app.app_name}',
                WebInterfacePortHTTP='80',
                WebInterfacePortHTTPS='443',
                AutoModProxy='True',
            )
            app.add_to_local_appcenter()

            apps.append(app)

        appcenter.update()

        for app in apps:
            app.install()

        for app in apps:
            app.verify(joined=False)
            app.configure_tinyapp_modproxy()
            app.verify_basic_modproxy_settings_tinyapp()

    finally:
        for app in apps:
            app.uninstall()
            app.remove()
