#!/usr/share/ucs-test/runner pytest-3 -s -vv --tb=native
## desc: Create and install a simple docker app without the DockerImage parameter
## tags: [docker]
## exposure: dangerous
## packages:
##   - docker.io

import pytest

from univention.testing.utils import package_installed

from dockertest import App


@pytest.mark.exposure('dangerous')
def test_missing_docker_img(appcenter, app_name, app_version):
    app = App(name=app_name, version=app_version)

    try:
        # DockerImage is missing, this should not work
        app.set_ini_parameter()
        app.add_to_local_appcenter()

        appcenter.update()

        app.install()

        # The package must be installed locally
        assert package_installed(app.package_name)

    finally:
        app.uninstall()
        app.remove()
