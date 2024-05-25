#!/usr/share/ucs-test/runner pytest-3 -s -vv --tb=native
## desc: Create and install a simple docker app
## tags: [docker]
## exposure: dangerous
## packages:
##   - docker.io

import pytest

from dockertest import App, Appcenter, AppFailure


@pytest.mark.exposure('dangerous')
def test_app_installation_fail_with_missing_package(appcenter: Appcenter, app_name: str, app_version: str) -> None:
    app = App(name=app_name, version=app_version, container_version='5.0', build_package=False)

    try:
        app.set_ini_parameter(DefaultPackages='foobar')
        app.add_to_local_appcenter()

        appcenter.update()

        with pytest.raises(AppFailure):
            app.install()
    finally:
        app.uninstall()
        app.remove()
