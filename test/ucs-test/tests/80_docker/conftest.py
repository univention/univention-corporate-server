import os
import time
from typing import Iterator

import pytest

from dockertest import Appcenter, get_app_name, get_app_version


@pytest.fixture()
def appcenter() -> Iterator[Appcenter]:
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
def app_name() -> str:
    return get_app_name()


@pytest.fixture()
def app_version() -> str:
    return get_app_version()
