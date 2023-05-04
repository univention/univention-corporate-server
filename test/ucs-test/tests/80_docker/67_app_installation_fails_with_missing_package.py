#!/usr/share/ucs-test/runner python3
## desc: Create and install a simple docker app
## tags: [docker]
## exposure: dangerous
## packages:
##   - docker.io

import pytest

from dockertest import Appcenter, UCSTest_DockerApp_InstallationFailed, tiny_app


if __name__ == '__main__':
    with Appcenter() as appcenter:
        app = tiny_app()

        try:
            app.set_ini_parameter(DefaultPackages='foobar')
            app.add_to_local_appcenter()

            appcenter.update()

            with pytest.raises(UCSTest_DockerApp_InstallationFailed):
                app.install()
        finally:
            app.uninstall()
            app.remove()
