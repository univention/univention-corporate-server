import os
import time

import pytest

from dockertest import Appcenter, get_app_name, get_app_version


@pytest.fixture()
def appcenter():
    # Appcenter doesn't delete itself instantly. If a new test is run directly after running a test the test will fail
    wait_timeout = 5
    while wait_timeout > 0:
        if not os.path.exists("/var/www/meta-inf"):
            break
        time.sleep(1)
        wait_timeout -= 1
    with Appcenter() as appcenter:
        yield appcenter


@pytest.fixture()
def app_name():
    return get_app_name()


@pytest.fixture()
def app_version():
    return get_app_version()
